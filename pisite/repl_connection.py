#!/usr/bin/env python3

import os
import subprocess
import getpass
import shlex
import errno
import sys
import threading
import repl_shell # pylint: disable=import-error
import logging
import gc
import time
import signal
import concurrent.futures
# maybe use pexpect?

# TODO: switch the repl to parallel?
# TODO: make sure that we see "Password: " + good password string as first line on stderr
# TODO: reset environment on su login?
# TODO: move repl strings into config file somewhere for portability, use format strings 
# TODO: detach repl_connection from repl_shell completely, allow for any repl implementation to be run

class REPLConnection:

    def __init__(self, repl_cmd, username, password,):

        # set up logger
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter("%(message)s")
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)

        # log some information about this object's environment
        os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ""))
        self._logger.info("replconnection user is %s" % getpass.getuser())
        self._logger.info("replconnection cwd is %s" % os.getcwd())
        
        # form command for repl
        command_as_user = "su {} -c {}".format(username, repl_cmd)
        args = shlex.split(command_as_user)
        self._logger.info("replconnection args are {}".format(args))
        
        # create repl process
        # (bufsize=1, universal_newlines=True) = turn on line buffering instead of default buffering
        self._repl_proc = subprocess.Popen(args,  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, universal_newlines=True)
        
        # write the password to the repl
        self._write_to_stdin(password)
        self._logger.info("replconnection done piping password")

        # make sure the password was successful
        success = self._verify_successful_password()

        # TODO: add real exception
        if not success:
            raise Exception("bad login details")

        # attempt to delete the password and collect the garbage
        # python is garbage and this doesn't *actually* delete it
        # TODO: fuck python
        del password
        gc.collect()

    def wait_and_close(self):
        self._repl_proc.stdin.close() # EOF to shell
        self._repl_proc.wait()

    def __del__(self):
        # remove all handlers because logger won't be deleted (they are global/static or something)
        for handler in self._logger.handlers:
            self._logger.removeHandler(handler)

    def _verify_successful_password(self):
        while True:
            try:
                line = self._repl_proc.stderr.readline().rstrip("\n")
            except Exception as e:
                print("exception raised trying to read password success on stderr: {}".format(e))
                raise e

            return_value = self._repl_proc.poll() # get return value or None if still running

            if return_value is not None: # process has terminated
                self._logger.info("replconnection sees process has terminated while waiting for password success")
                return False
            elif line is None or line == "":
                self._logger.info("replconnection sees blank or None line while looking for successful password")
            elif repl_shell.REPLShell.GOOD_PASSWORD_STRING in line:
                self._logger.info("replconnection sees good password string")
                return True
            else:
                self._logger.info("replconnection sees line while looking for successful password: {}".format(line))

    def _monitor_repl_stream(self, stream) -> (list, int):
        output = list()
        return_code = None
        started = False
        while True:
            try:
                line = stream.readline().rstrip("\n") 
            except Exception as e:
                print("exception raised trying to read line on stream {}: {}".format(stream, e), file=sys.stderr)
                break

            return_value = self._repl_proc.poll() # get return value or None if still running

            if return_value is not None: # process has terminated
                self._logger.info("replconnection sees process has terminated, breaking stream {}".format(stream))
                break
            elif line is None or line == "":
                self._logger.info("replconnection sees blank or None line on {}".format(stream))
            elif (stream is self._repl_proc.stdout) and (line.startswith(repl_shell.REPLShell.RESULTS_RC_STRING)):
                return_code = line.strip(repl_shell.REPLShell.RESULTS_RC_STRING)
            elif line == repl_shell.REPLShell.RESULTS_START_STRING:
                started = True
            elif line == repl_shell.REPLShell.RESULTS_DONE_STRING:
                started = False
                break
            elif started:
                output.append(line)
            
        #self._logger.info("replconnection done with _monitor_repl_stream for {}".format(stream))

        return (output, return_code)

    def _write_to_stdin(self, line):
        try:
            self._repl_proc.stdin.write("%s\n" % line)
        except IOError as e:
            if e.errno == errno.EPIPE or e.errno == errno.EINVAL:
                # EPIPE = broken pipe, EINVAL = invalid argument
                self._logger.info("error writing to stdin") 
            else:
                # Raise any other error.
                raise e
    
    def give_repl_exec_command(self, command_line) -> (str, str, int):
        # send the command
        self._write_to_stdin(command_line)

        # get entire stdout and return code
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(self._monitor_repl_stream, (self._repl_proc.stdout))
            out, return_code = future.result()
        
        # get entire stderr
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(self._monitor_repl_stream, (self._repl_proc.stderr))
            err, _ = future.result()

        # pack it into a tuple and return it
        return (out, err, return_code)


def test_repl_shell_py():
    user = "testuser"
    password = "testpassword"
    #command = "./testscript.sh"
    command = "'python repl_shell.py'"

    repl_connection = REPLConnection(command, user, password)

    del password
    gc.collect()

    #(out, err, return_code) = repl_connection.give_repl_exec_command("TEST_ECHO 123123123")
    print(repl_connection.give_repl_exec_command("TEST_ECHO 123123123"))
    print(repl_connection.give_repl_exec_command("TEST_ECHO 44444444444444444"))

    repl_connection.wait_and_close()

def test_sh_as_repl():
    user = "testuser"
    password = "testuser"
    command = "'sh'"

    repl_connection = REPLConnection(command, user, password)

    del password
    gc.collect()

    repl_connection._write_to_stdin("1>&2 echo \"DONE\"")
    repl_connection._write_to_stdin("echo hellothere")
    repl_connection._write_to_stdin("./testscript.sh")
    repl_connection._write_to_stdin("ps -hp $$")
    repl_connection._write_to_stdin("this should fail")
    
    # time.sleep(2)
    # repl_connection.write_to_stdin("echo past sleeping")

    repl_connection.wait_and_close()

if __name__ == "__main__":
    print("-----TESTING repl_shell.py-----")
    test_repl_shell_py()

    #print("-----TESTING sh-----")
    #test_sh_as_repl()

    
