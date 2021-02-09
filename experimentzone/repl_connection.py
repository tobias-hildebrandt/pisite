#!/usr/bin/env python3

import os
import subprocess
import getpass
import shlex
import errno
import sys
import threading
import repl_test
import logging
# maybe use pexpect?

# TODO: add filter to repl?
# TODO: switch the repl to parallel?
# TODO: make sure that we see "Password: " + good password string as first line on stderr
# TODO: reset environment on su login?

class REPLConnection:

    def __init__(self, repl_cmd, username, password):

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter("%(message)s")
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ""))
        self.logger.info("replconnection user is %s" % getpass.getuser())
        self.logger.info("replconnection cwd is %s" % os.getcwd())
        
        command_as_user = "su {} -c {}".format(user, command)

        args = shlex.split(command_as_user)
        self.logger.info("replconnection args are {}".format(args))
        # bufsize=1, universal_newlines=True turn on line buffering instead of default buffering
        self._repl_proc = subprocess.Popen(args,  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, universal_newlines=True)
        #self.logger.info("trying to write now")
        self.write_to_stdin(password)
        self.logger.info("replconnection done piping password")
        
        #sys.stdout.flush()
        
        self._thread_stdout = threading.Thread(target=self._monitor_repl_stream, args=(self._repl_proc, "stdout"))
        self._thread_stderr = threading.Thread(target=self._monitor_repl_stream, args=(self._repl_proc, "stderr"))
        
        self._thread_stderr.start()
        self._thread_stdout.start()

        # wait until process terminates, get output
        #out, err = proc.communicate()
        #logging.info(out)
        #logging.info(err)

    def wait_and_close(self):
        self._repl_proc.stdin.close()
        self._thread_stderr.join()
        self._thread_stdout.join()
        self._repl_proc.wait()

    def __del__(self):
        self.wait_and_close()

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
                self.logger.info("monitor_repl_stream given invalid stream %s" % stream_name)

            return_value = self._repl_proc.poll() # get return value or None if still running

            if return_value is not None: # has terminated
                self.logger.info("replconnection sees process has terminated, breaking stream %s..." % stream_name)
                break
            if line is not None and line != "":
                if stream_name == "stdout":
                    end = self.handle_stdout(line)
                elif stream_name == "stderr":
                    end = self.handle_stderr(line)
                if end:
                    self.logger.info("replconnection got %s end string" % stream_name)
                    break
        self.logger.info("replconnection done with monitor_repl_stream for %s" % stream_name)

    def handle_stdout(self, line):
        self.logger.info("repl's stdout: %s" % line)
        return False # don't worry about ending via message from stdout

    def handle_stderr(self, line):
        self.logger.info("repl's STDERR: %s" % line)
        if line == repl_test.REPLShell.END_STRING:
            return True # tell loop we should end
        else:
            return False

    def write_to_stdin(self, *lines):
        for line in lines:
            try:
                self._repl_proc.stdin.write("%s\n" % line)
            except IOError as e:
                if e.errno == errno.EPIPE or e.errno == errno.EINVAL:
                    # EPIPE = broken pipe, EINVAL = invalid argument
                    # break
                    self.logger.info("error writing") 
                else:
                    # Raise any other error.
                    raise e

    def give_repl_exec_commands(self, *lines):
        exec_lines = list()
        for line in lines:
            exec_lines.append(repl_test.REPLShell.EXEC_STRING + line)
        self.write_to_stdin(*exec_lines)
        
if __name__ == "__main__":
    user = "testuser"
    password = "testuser"
    #command = "./testscript.sh"
    command = "'python repl_test.py'"

    repl_connection = REPLConnection(command, user, password)

    repl_connection.write_to_stdin("hello there", "testing123", "can you hear me?")
    repl_connection.give_repl_exec_commands("echo hellothere")
    repl_connection.give_repl_exec_commands("./testscript.sh")
    repl_connection.give_repl_exec_commands("this should fail")
    repl_connection.write_to_stdin(repl_test.REPLShell.END_STRING)

    repl_connection.wait_and_close()

    
