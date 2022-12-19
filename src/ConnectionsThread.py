import threading
import socket
from time import sleep

from constants import ENCODING


class ConnectionThread(threading.Thread):
    def __init__(self, node, sock, client_address):
        super().__init__()

        self.node = node

        self.sock = sock
        self.client_address = client_address
        self.flag = threading.Event()

    def run(self):
        self.sock.settimeout(10.0)

        while not self.flag.is_set():
            try:
                data = self.sock.recv(4096)
                msg = data.decode()
                # TODO : Lock and Release node?
                self.node.data_handler(msg)

            except socket.timeout:
                self.flag.set()

            except Exception as e:
                self.flag.set()
                raise e

            sleep(0.01)

        self.sock.settimeout(None)
        self.sock.close()
        self.node.node_server.connection_threads.pop(self.client_address)

    def send(self, data):
        self.sock.sendall(data.encode(ENCODING))

    def stop(self):
        self.flag.set()
