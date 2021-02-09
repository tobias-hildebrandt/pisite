import os
import subprocess
import socket

# cd to directory where this file is located
os.chdir(os.path.dirname(os.path.abspath(__file__)))
print("current directory: %s" % os.getcwd())

# os.mkfifo("testfifo.fifo")
# os.system("ls")

sock = socket.socket(socket.AF_UNIX)

path = "testsocket.sock"

data = b"1234"
real_length = len(data)

with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # reuse socket
    sock.bind(path)
    sock.listen()
    conn, addr = sock.accept()
    with conn:
        print('Connected by %s' % addr)
        while True:
            data = conn.recv(real_length)
            if not data:
                break
            print(data)
            conn.sendall(data)

#print("data length: %s\nrecv length: %s" % real_length % length_recv)
