import os
import subprocess
import socket
import ssl
import signal
import time

def signal_handler(signal, frame):
    print("received signal, exiting...")
    exit(-1)

if __name__ == "__main__":
    for sig in [signal.SIGINT, signal.SIGINT, signal.SIGTERM]:
        signal.signal(sig, signal_handler)

    # cd to directory where this file is located
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print("current directory: %s" % os.getcwd())

    # os.mkfifo("testfifo.fifo")
    # os.system("ls")

    # create socket
    sock = socket.socket(socket.AF_UNIX)

    # create ssl context
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

    # require ssl cert
    ssl_context.verify_mode = ssl.CERT_REQUIRED

    # verify the client's cert
    ssl_context.load_verify_locations("testkeys/client.pem")

    # load ssl keys
    ssl_context.load_cert_chain("testkeys/server.pem", "testkeys/server.key")

    path = "testsocket.sock"

    # delete old socket file
    try:
        os.remove(path)
    except FileNotFoundError:
        pass

    data = b"this is a message from the server"
    real_length = len(data)

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as insecure_socket:

        # cannot reuse AF_UNIX socket, would need to use locks
        #secure_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # reuse socket

        # bind to socket
        insecure_socket.bind(path)

        print("insecure socket is {}".format(insecure_socket))

        # begin listening on socket
        insecure_socket.listen()

        # accept a connection
        connected_socket, addr = insecure_socket.accept()

        with ssl_context.wrap_socket(connected_socket, 
        server_side=True,
        do_handshake_on_connect=False) as secure_socket:

            secure_socket.do_handshake()

            print("secure socket is {}".format(secure_socket))
            
            print("server connected to address: {}, with connection: {}".format(addr, secure_socket))
            print("server ssl socket version: {}".format(secure_socket.version()))

            # get peer cert
            peer_cert = secure_socket.getpeercert()
            print("server sees peer cert: {}".format(peer_cert))

            while True:
                data = secure_socket.recv(real_length)
                if not data:
                    break
                print(data)
                secure_socket.sendall(data)

    #print("data length: %s\nrecv length: %s" % real_length % length_recv)

