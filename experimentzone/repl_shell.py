#!/usr/bin/env python3

import os
import getpass
import subprocess
import sys
import multiprocessing.connection
import threading

# this file should be run as a shell program under a specific unix user
class REPLShell:

    GOOD_PASSWORD_STRING = "SUCCESS GOOD_PASSWORD"
    SETUP_DONE_STRING = "SUCCESS SETUP_DONE"
    END_STRING = "END"
    EXEC_STRING = "EXEC "
    FAILED_EXEC_STRING = "FAILED EXEC"

    def __init__(self):
        print("repl user is %s" % getpass.getuser())
        print("repl cwd is %s" % os.getcwd())
        print("repl python executable is %s" % subprocess.run(["which", "python"], stdout=subprocess.PIPE).stdout.decode())
        
        # send signal to invoker that initial was successful
        print(REPLShell.SETUP_DONE_STRING, file=sys.stderr)

        self._stdin_listening_thread = threading.Thread(target=self.listen_on_stdin)
        self._stdin_listening_thread.start()

    def listen_on_stdin(self):
        while True:
            line = sys.stdin.readline().rstrip("\n")

            print("repl sees on stdin: %s" % line)
            if line == REPLShell.END_STRING:
                print(REPLShell.END_STRING, file=sys.stderr)
                break
            elif line.startswith(REPLShell.EXEC_STRING):
                try:
                    exec_cmd = line.split(" ")[1:]
                    proc = subprocess.Popen(exec_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                    out, err = proc.communicate()
                    returncode = proc.returncode
                    print("repl ran %s\nrepl exec output: %s\nrepl exec err: %s\nrepl exec return code: %s" % (exec_cmd, out, err, returncode))
                except: # TODO: which errors to catch???
                    print("%s: %s" % (REPLShell.FAILED_EXEC_STRING, line), file=sys.stderr)
                

if __name__ == "__main__":
    print(REPLShell.GOOD_PASSWORD_STRING, file=sys.stderr)
    repl = REPLShell()
