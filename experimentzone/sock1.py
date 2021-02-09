import os
import subprocess
import socket

os.chdir(os.path.dirname(os.path.abspath(__file__)))
print("current directory: %s" % os.getcwd())

path = "testsocket.sock"

data = b"1234"
real_length = len(data)

with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
    sock.connect(path)
    sock.sendall(data)
    data = sock.recv(real_length)
    print("sent data, received %s" % data)

#print("data length: %s\nsent length: %s" % real_length % length_sent)
