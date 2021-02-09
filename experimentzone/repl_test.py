#!/usr/bin/env python3

import os
import getpass
import subprocess
import sys
import multiprocessing.connection

# stdout is redirected to invoker until setup is done
class REPLBoss:

    GOOD_PASSWORD_STRING = "SUCCESS GOOD_PASSWORD"
    SETUP_DONE_STRING = "SUCCESS SETUP_DONE"
    FAIL_SOCKET_STRING = "FAILURE BAD_SOCKET"
    FAIL_NO_SOCKET_GIVEN = "FAILURE NO_SOCKET_GIVEN"

    def __init__(self, path_to_socket):
        print("repl user is %s" % getpass.getuser())
        print("repl cwd is %s" % os.getcwd())
        print("repl python executable is %s" % subprocess.run(["which", "python"], stdout=subprocess.PIPE).stdout.decode())
        if path_to_socket == "" or path_to_socket is None:
            print("repl given path to socket is empty")
        else:
            print("repl given path to socket is %s" % path_to_socket)

        # do setup
        # set up connection to invoker
        try:
            self._connection_to_invoker = multiprocessing.connection.Client(address=path_to_socket, family='AF_UNIX')
        except OSError:
            print(REPLBoss.FAIL_SOCKET_STRING, file=sys.stderr)
            #exit(-1)

        # send signal to invoker to stop listening on stdout and switch to socket
        print(REPLBoss.SETUP_DONE_STRING, file=sys.stderr)


if __name__ == "__main__":
    print(REPLBoss.GOOD_PASSWORD_STRING, file=sys.stderr)
    arg = ""
    try:
        arg = sys.argv[1]
    except IndexError:
        print(REPLBoss.FAIL_NO_SOCKET_GIVEN, file=sys.stderr)
        #exit(-2)
    repl = REPLBoss(arg)