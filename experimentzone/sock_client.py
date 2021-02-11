import os
import subprocess
import socket
import ssl

os.chdir(os.path.dirname(os.path.abspath(__file__)))
print("current directory: %s" % os.getcwd())

# create ssl context
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

# require ssl cert
ssl_context.verify_mode = ssl.CERT_REQUIRED

# verify the server's cert
ssl_context.load_verify_locations("testkeys/server.pem")

# do not check hostname
ssl_context.check_hostname = False

# load ssl keys
ssl_context.load_cert_chain("testkeys/client.pem", "testkeys/client.key")

path = "testsocket.sock"

data = b"this is a message from the client"
real_length = len(data)

with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as insecure_socket:
    with ssl_context.wrap_socket(insecure_socket) as secure_socket:

        # connect
        secure_socket.connect(path)
        print("client connected to hostname: {}".format(secure_socket.server_hostname))
        print("client ssl socket version: {}".format(secure_socket.version()))
        
        # shake my hand
        secure_socket.do_handshake()

        # get peer cert
        peer_cert = secure_socket.getpeercert()
        print("client sees peer cert: {}".format(peer_cert))

        # send the data
        secure_socket.sendall(data)

        # receive data
        data = secure_socket.recv(real_length)
        print("sent data, received %s" % data)

#print("data length: %s\nsent length: %s" % real_length % length_sent)
