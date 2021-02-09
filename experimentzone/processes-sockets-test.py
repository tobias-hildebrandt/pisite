# import subprocess

# proc = subprocess.Popen(["/bin/sh"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

# (stdout, stderr) = proc.communicate("whoami")

# for line in stdout.splitlines():
#     print(line)

# import pty, os

# (proc_id, fd) = pty.fork()
# print("current proc id: %s\ncurrent fd: %s" % (str(proc_id), str(fd)))

# (parent, child) = pty.openpty()


# print("parent ttyname: %s" % os.ttyname(parent))
# print("child ttyname: %s" % os.ttyname(child))

import multiprocessing
import multiprocessing.connection
import os
import tempfile
import time

# # using multiprocessing pipe
# def child_process(connection):
#     connection.send("im a string")
#     connection.send(123123)
#     connection.send({"thing": 123, 5555: [1,2,3]})

# parent_connection, child_connection = multiprocessing.Pipe()
# child_proc = multiprocessing.Process(target=child_process, args=(child_connection,))
# child_proc.start()
# for _ in range(3):
#     print(parent_connection.recv())
# child_proc.join()

def communication_loop(connection, name, *messages):
    for message in messages:
        print("%s sent %s" % (name, message))
        connection.send(message)
    keep_listening = True
    while keep_listening:
        try:
            data = connection.recv() # will block
        except EOFError:
            connection.close()
            break
        if not str(data).startswith("ack"):
            connection.send("ack %s" % data)
        print("%s heard %s" % (name, data))
        if data is None:
            print("%s responding with None and breaking" % name)
            connection.send(None)
            break

# using listener and client, high level API for sockets
def child_process(address):
    connection = multiprocessing.connection.Client(address=address, family='AF_UNIX') # doesn't block

    communication_loop(connection, "child", "test123", 123, None)

directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "") # join to "" to guarentee trailing slash
temp_file = tempfile.NamedTemporaryFile(dir=directory, prefix="socket-", suffix=".sock").name
print("temp file is %s" % temp_file)
# make sure listener is set up before client is set up (doesn't need to start accepting though)
listener = multiprocessing.connection.Listener(address=temp_file, family='AF_UNIX') # doesnt block # address=None will create temp file in /tmp/pymp-*
print("socket file is %s" % listener.address)
child_process = multiprocessing.Process(target=child_process, args=(listener.address, )) 

# time.sleep(1)
child_process.start() 
# time.sleep(1)

connection = listener.accept() # blocks until connection

# os.chdir(os.path.dirname(os.path.abspath(__file__)))
# os.system("ls")

print("----- process information")
os.system("ps aux | grep -e \"python[ 3] *%s\"" % __file__)
print("----- socket information")
os.system("fuser -uv %s" % temp_file)
print("-----")

communication_loop(connection, "parent", "hello there")

child_process.join()

