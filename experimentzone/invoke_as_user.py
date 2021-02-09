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

# TODO: decide if reading repl's stdout is even necessary
# TODO: implement a real repl
# TODO: use sockets to communicate between repl and invoker?
# TODO: decide if repl should simply have a queue or create worker processes that can work in parallel

def monitor_stream(process, stream_name):
    # TODO: only check return value if readline hangs?
    # TODO: capture stderr too OR **redirect proc's stderr to stdout**
    # live capture stdout line by line

    while True:
        if stream_name == "stdout":
            line = process.stdout.readline().strip() # read one line of text from the pipe
        elif stream_name == "stderr":
            line = process.stderr.readline().strip() # read one line of text from the pipe
        else:
            logging.info("monitor_stream given invalid stream %s" % stream_name)

        return_value = proc.poll() # get return value or None if still running

        if return_value is not None: # has terminated
            logging.info("process has terminated, breaking stream %s..." % stream_name)
            break
        if line is not None and line != "":
            if stream_name == "stdout":
                end = handle_stdout(line)
            elif stream_name == "stderr":
                end = handle_stderr(line)
            if end:
                logging.info("got end string, breaking %s..." % stream_name)
                break
    logging.info("done with monitor_stream for %s" % stream_name)

def handle_stdout(line):
    logging.info("repl stdout: %s" % line)
    return False # don't worry about ending via message from stdout

def handle_stderr(line):
    logging.info("repl stderr: %s" % line)
    if line == repl_test.REPLBoss.SETUP_DONE_STRING:
        return True # tell loop we should end
    else:
        return False
        
if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ""))
    logging.info("invoker user is %s" % getpass.getuser())
    logging.info("invoker cwd is %s" % os.getcwd())
    user = "testuser"
    password = "testuser"
    #command = "./testscript.sh"
    command = "'python repl_test.py'"
    command_as_user = "su {} -c {}".format(user, command)
    args = shlex.split(command_as_user)
    logging.info("invoker args are {}".format(args))
    # bufsize=1, universal_newlines=True turn on line buffering instead of default buffering
    proc = subprocess.Popen(args,  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, universal_newlines=True)
    #logging.info("trying to write now")
    try:
        proc.stdin.write("%s\n" % password)
    except IOError as e:
        if e.errno == errno.EPIPE or e.errno == errno.EINVAL:
            # EPIPE = broken pipe, EINVAL = invalid argument
            # break
            logging.info("error writing") 
        else:
            # Raise any other error.
            raise e
    logging.info("invoker done piping password")
    #sys.stdout.flush()
    
    thread_stdout = threading.Thread(target=monitor_stream, args=(proc, "stdout"))
    thread_stderr = threading.Thread(target=monitor_stream, args=(proc, "stderr"))
    
    thread_stderr.start()
    thread_stdout.start()
    
    # wait until process terminates, get output
    #out, err = proc.communicate()
    #logging.info(out)
    #logging.info(err)

    proc.stdin.close()
    thread_stderr.join()
    thread_stdout.join()
    proc.wait()
