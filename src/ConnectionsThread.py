import threading
import socket

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
        self.sock.settimeout(2.0)

        while not self.flag.is_set():
            try:
                # TODO : Receive data properly
                data = self.sock.recv(4096)
                msg = data.decode()
                if msg:
                    self.message_queue.put(msg)

            except socket.timeout:
                self.flag.set()

            except Exception as e:
                self.flag.set()
                raise e

        self.sock.close()
        self.disonnection_queue.put(self.client_address)
        # print(f"ended connection thread {self.client_address}")

    def send(self, data):
        self.sock.sendall(data.encode(ENCODING))

    def stop(self):
        self.flag.set()
