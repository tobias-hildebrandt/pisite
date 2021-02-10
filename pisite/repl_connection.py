#!/usr/bin/env python3

import os
import subprocess
import getpass
import shlex
import errno
import sys
import threading
import repl_shell
import logging
import gc
import time
import signal
# maybe use pexpect?

# TODO: add filter to repl?
# TODO: switch the repl to parallel?
# TODO: make sure that we see "Password: " + good password string as first line on stderr
# TODO: reset environment on su login?
# TODO: move repl strings into config file somewhere for portability, 
# TODO: detach repl_connection from repl_shell completely, allow for any repl implementation to be run
# TODO: not sure where validation table should be, here or in repl_shell

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

        # flush stderr so we get the "Password: " ? # TODO: remove, useless?
        self._repl_proc.stderr.flush()

        # attempt to delete the password and collect the garbage
        # python is garbage and this doesn't *actually* delete it
        # TODO: fuck python
        del password
        gc.collect()
        
        self._thread_stdout = threading.Thread(target=self._monitor_repl_stream, args=(self._repl_proc, "stdout"))
        self._thread_stderr = threading.Thread(target=self._monitor_repl_stream, args=(self._repl_proc, "stderr"))
        
        # wait until process terminates, get output
        #out, err = proc.communicate()
        #logging.info(out)
        #logging.info(err)

    def start_monitoring(self):
        self._thread_stderr.start()
        self._thread_stdout.start()

    def wait_and_close(self):
        self._repl_proc.stdin.close() # sends blank line to shell
        self._thread_stderr.join()
        self._thread_stdout.join()
        self._repl_proc.wait()

    def __del__(self):
        # remove all handlers because logger won't be deleted (they are global/static or something)
        for handler in self._logger.handlers:
            self._logger.removeHandler(handler)

    def _monitor_repl_stream(self, process, stream_name):
        # TODO: only check return value if readline hangs?
        # TODO: capture stderr too OR **redirect proc's stderr to stdout**
        # live capture stdout line by line

        while True:
            if stream_name == "stdout":
                line = process.stdout.readline().rstrip("\n") # read one line of text from the pipe
            elif stream_name == "stderr":
                line = process.stderr.readline().rstrip("\n") # read one line of text from the pipe
            else:
                self._logger.info("monitor_repl_stream given invalid stream %s" % stream_name)

            return_value = self._repl_proc.poll() # get return value or None if still running

            if return_value is not None: # has terminated
                self._logger.info("replconnection sees process has terminated, breaking stream %s..." % stream_name)
                break
            if line is not None and line != "":
                if stream_name == "stdout":
                    self._handle_stdout(line)
                elif stream_name == "stderr":
                    self._handle_stderr(line)
        self._logger.info("replconnection done with monitor_repl_stream for %s" % stream_name)

    def _handle_stdout(self, line):
        self._logger.info("repl's stdout: %s" % line)

    def _handle_stderr(self, line):
        self._logger.info("repl's STDERR: %s" % line)

    def _write_to_stdin(self, line):
        try:
            self._repl_proc.stdin.write("%s\n" % line)
        except IOError as e:
            if e.errno == errno.EPIPE or e.errno == errno.EINVAL:
                # EPIPE = broken pipe, EINVAL = invalid argument
                # break
                self._logger.info("error writing") 
            else:
                # Raise any other error.
                raise e

    def give_repl_exec_command(self, command_line):
        self._write_to_stdin(command_line)


def test_repl_shell_py():
    user = "testuser"
    password = "testpassword"
    #command = "./testscript.sh"
    command = "'python repl_shell.py'"

    repl_connection = REPLConnection(command, user, password)

    del password
    gc.collect()

    repl_connection.give_repl_exec_command("echo hellothere")
    test_string = "; echo this is a test"
    repl_connection.give_repl_exec_command("./testscript.sh %s" % test_string)
    repl_connection.give_repl_exec_command("this should fail")

    repl_connection.start_monitoring()
    # while True:
    #     repl_connection.give_repl_exec_commands(input())

    # time.sleep(2)
    # repl_connection.give_repl_exec_commands("echo past sleeping")

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

    
