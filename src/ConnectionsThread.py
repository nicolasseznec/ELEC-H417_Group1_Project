import pickle
import threading
import socket


class ConnectionThread(threading.Thread):
    def __init__(self, message_queue, disonnection_queue, sock, client_address, timeout=20.0):
        super().__init__()

        self.message_queue = message_queue
        self.disonnection_queue = disonnection_queue

        self.sock = sock
        self.client_address = client_address
        self.flag = threading.Event()

        self.sock.settimeout(timeout)
        # self.sock.settimeout(2.0)

    def run(self):
        while not self.flag.is_set():
            try:
                # TODO : Receive data properly
                data = self.sock.recv(4096)
                # print(f"received from {self.client_address} on {self}")
                msg = pickle.loads(data)
                if msg:
                    self.message_queue.put((msg, self))

            except socket.timeout:
                self.flag.set()

            except EOFError:
                pass

            except Exception as e:
                self.flag.set()
                raise e

        self.sock.close()
        self.disonnection_queue.put(self.client_address)
        # print(f"ended connection thread {self.client_address}")

    def send(self, data):
        # self.sock.sendall(data.encode(ENCODING))
        self.sock.sendall(data)

    def stop(self):
        self.flag.set()
