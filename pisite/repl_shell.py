#!/usr/bin/env python3

import os
import getpass
import subprocess
import sys
import threading
import shlex
import traceback
import signal
import gc
import json

# this file should be run as a shell program under a specific unix user
class REPLShell:

    GOOD_PASSWORD_STRING = "SUCCESS GOOD_PASSWORD"
    SETUP_DONE_STRING = "SUCCESS SETUP_DONE"
    FAILED_EXEC_STRING = "FAILED EXEC"
    VALIDATION_TABLE_PATH_RELATIVE = ".pisite/validationtable.json"
    NOT_ALLOWED_STRING = "FAILED INVALID COMMAND"
    RESULTS_RC_STRING = "RESULTS RC"
    RESULTS_START_STRING = "RESULTS START"
    RESULTS_DONE_STRING = "RESULTS DONE"

    TIMEOUT=3 #seconds

    def __init__(self):
        print("repl user is %s" % getpass.getuser())
        os.chdir(os.path.expanduser("~")) # go to user's home directory
        print("repl cwd is %s" % os.getcwd())
        print("repl python executable is %s" % subprocess.run(["which", "python"], stdout=subprocess.PIPE).stdout.decode().rsplit("\n"))

        # set up validation table
        # raise exceptions here if there's a problem
        
        # load validation table
        absolute_filepath = os.path.join(os.path.expanduser("~"), REPLShell.VALIDATION_TABLE_PATH_RELATIVE)
        with open(absolute_filepath, 'r') as f:
            self._validation_table = json.load(f)

        # set the execution path prefix, this is where all scripts exist
        self._execution_path_prefix = os.path.join(absolute_filepath, os.path.pardir)

        # add signal handlers
        for sig in [signal.SIGINT, signal.SIGINT, signal.SIGTERM]:
            signal.signal(sig, self.signal_handler)

        # keep track of current subprocess in case we need to kill it
        self._current_subproc = None

        # set to false to stop the main execution loop
        self._loop_on_stdin = True
        
        self._stdin_listening_thread = threading.Thread(target=self.listen_on_stdin)
        self._stdin_listening_thread.start()

    def signal_handler(self, signal, frame):
        print("repl recieved signal %s" % signal, file=sys.stderr)
        
        # tell main loop not to loop again
        self._loop_on_stdin = False

        # kill the current subprocess if there is one
        if self._current_subproc is not None:
            print("repl killing current subprocess %s" % self._current_subproc.pid, file=sys.stderr)
            self._current_subproc.terminate()
            self._current_subproc.kill()
        
        # bail out
        sys.exit()

    def listen_on_stdin(self):
        
        while self._loop_on_stdin:
            line = sys.stdin.readline().rstrip("\n")

            if line == "":
                print("repl sees blank stdin line, exiting...")
                break
            else:
                print("repl sees on stdin: %s" % line)
                self._handle_line(line)
            
            # if it hasn't terminated, kill it
            # probably unnecessary
            if self._current_subproc is not None and self._current_subproc.poll() is None:
                self._current_subproc.kill()
            
            # attempt to mitigate memory usage temporarily
            # probably unnecessary
            self._current_subproc = None
            out_complete = None
            del out_complete
            err_complete = None
            del err_complete
            gc.collect()

    def _handle_line(self, line):
        try:
            # tokens[0] must be KEY in validation table
            # tokens[1:] are arguments 
            
            # split line into tokens
            exec_cmd = shlex.split(line)

            # make sure first token is a KEY in validation table
            if exec_cmd[0] not in self._validation_table:
                print("{} {}".format(REPLShell.NOT_ALLOWED_STRING, line))
                return # exit function

            # replace relative (to script dir) path with absolute script path 
            exec_cmd[0] = os.path.abspath(os.path.join(self._execution_path_prefix, self._validation_table[exec_cmd[0]]))

            print("repl exec_cmd is %s" % exec_cmd)

            # make sure shell is false
            # universal_newlines converts text to string instead of bytes
            self._current_subproc = subprocess.Popen(exec_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, bufsize=1, universal_newlines=True)

            # this gets really fucken huge if lots of data is output by subprocess (e.g. GNU coreutil's `yes`)
            # https://stackoverflow.com/a/24126616
            # tl;dr this data must be stored somewhere
            # TODO: read the first X lines of output one by one and save the rest to a file? then serve the file if needed,
            #       need to use threads
            out_complete, err_complete = self._current_subproc.communicate(timeout=REPLShell.TIMEOUT, input=None)
            
            # might not be necessary
            # sys.stdout.flush()
            # sys.stderr.flush()

            returncode = self._current_subproc.returncode

            print("{}{}".format(REPLShell.RESULTS_RC_STRING, returncode))

            print(REPLShell.RESULTS_START_STRING)
            print(out_complete[:-1]) # strip out last line (blank)
            print(REPLShell.RESULTS_DONE_STRING)

            print(REPLShell.RESULTS_START_STRING, file=sys.stderr)
            print(err_complete[:-1], file=sys.stderr) # strip out last line (blank)
            print(REPLShell.RESULTS_DONE_STRING, file=sys.stderr)

            # print("repl ran %s\nrepl exec output: %s\nrepl exec err: %s\nrepl exec return code: %s" %
            #     (exec_cmd, 
            #     out_complete.replace("\n", "\\n"), 
            #     err_complete.replace("\n", "\\n"), 
            #     returncode))
        except Exception as e: # TODO: which errors to catch???
            print("%s;e=%s;line=%s" % (REPLShell.FAILED_EXEC_STRING, e, line), file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            
                

if __name__ == "__main__":
    print(REPLShell.GOOD_PASSWORD_STRING, file=sys.stderr)
    repl = REPLShell()
