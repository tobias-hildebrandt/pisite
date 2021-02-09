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
# TODO: make into a class
# TODO: make sure that we see "Password: " + good password string as first line on stderr
# TODO: real logging levels and stuff
# TODO: reset environment on su login?

def monitor_stream(process, stream_name):
    # TODO: only check return value if readline hangs?
    # TODO: capture stderr too OR **redirect proc's stderr to stdout**
    # live capture stdout line by line

    while True:
        if stream_name == "stdout":
            line = process.stdout.readline().rstrip("\n") # read one line of text from the pipe
        elif stream_name == "stderr":
            line = process.stderr.readline().rstrip("\n") # read one line of text from the pipe
        else:
            logging.info("monitor_stream given invalid stream %s" % stream_name)

        return_value = proc.poll() # get return value or None if still running

        if return_value is not None: # has terminated
            logging.info("invoker sees process has terminated, breaking stream %s..." % stream_name)
            break
        if line is not None and line != "":
            if stream_name == "stdout":
                end = handle_stdout(line)
            elif stream_name == "stderr":
                end = handle_stderr(line)
            if end:
                logging.info("invoker got %s end string" % stream_name)
                break
    logging.info("invoker done with monitor_stream for %s" % stream_name)

def handle_stdout(line):
    logging.info("repl's stdout: %s" % line)
    return False # don't worry about ending via message from stdout

def handle_stderr(line):
    logging.info("repl's STDERR: %s" % line)
    if line == repl_test.REPLBoss.END_STRING:
        return True # tell loop we should end
    else:
        return False

def write_to_stdin(*lines):
    for line in lines:
        try:
            proc.stdin.write("%s\n" % line)
        except IOError as e:
            if e.errno == errno.EPIPE or e.errno == errno.EINVAL:
                # EPIPE = broken pipe, EINVAL = invalid argument
                # break
                logging.info("error writing") 
            else:
                # Raise any other error.
                raise e

def give_repl_exec_commands(*lines):
    exec_lines = list()
    for line in lines:
        exec_lines.append(repl_test.REPLBoss.EXEC_STRING + line)
    write_to_stdin(*exec_lines)
        
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
    write_to_stdin(password)
    logging.info("invoker done piping password")
    
    #sys.stdout.flush()
    
    thread_stdout = threading.Thread(target=monitor_stream, args=(proc, "stdout"))
    thread_stderr = threading.Thread(target=monitor_stream, args=(proc, "stderr"))
    
    thread_stderr.start()
    thread_stdout.start()

    write_to_stdin("hello there", "testing123", "can you hear me?")
    give_repl_exec_commands("echo hellothere")
    give_repl_exec_commands("./testscript.sh")
    give_repl_exec_commands("this should fail")
    write_to_stdin(repl_test.REPLBoss.END_STRING)
    
    # wait until process terminates, get output
    #out, err = proc.communicate()
    #logging.info(out)
    #logging.info(err)

    proc.stdin.close()
    thread_stderr.join()
    thread_stdout.join()
    proc.wait()
