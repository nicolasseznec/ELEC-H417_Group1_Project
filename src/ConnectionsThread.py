import threading
import socket
from time import sleep

from constants import ENCODING


class ConnectionThread(threading.Thread):
    def __init__(self, message_queue, disonnection_queue, sock, client_address):
        super().__init__()

        self.message_queue = message_queue
        self.disonnection_queue = disonnection_queue

        self.sock = sock
        self.client_address = client_address
        self.flag = threading.Event()

    def run(self):
        self.sock.settimeout(10.0)

        while not self.flag.is_set():
            try:
                # TODO : Receive data properly
                data = self.sock.recv(4096)
                msg = data.decode()
                self.message_queue.put(msg)

            except socket.timeout:
                self.flag.set()

            except Exception as e:
                self.flag.set()
                raise e

            sleep(0.01)

        self.sock.settimeout(None)
        self.sock.close()
        self.disonnection_queue.put(self.client_address)

    def send(self, data):
        self.sock.sendall(data.encode(ENCODING))

    def stop(self):
        self.flag.set()
