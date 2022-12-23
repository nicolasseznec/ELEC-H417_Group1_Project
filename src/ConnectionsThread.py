import pickle
import threading
import socket


class ConnectionThread(threading.Thread):
    """
    Thread that handles the connection between two node via a socket.
    Received messages are put in the message queue of the parent node.
    """
    def __init__(self, message_queue, disonnection_queue, sock, client_address, timeout=20.0):
        super().__init__()

        self.message_queue = message_queue
        self.disonnection_queue = disonnection_queue

        self.sock = sock
        self.client_address = client_address
        self.flag = threading.Event()

        self.sock.settimeout(timeout)

    def run(self):
        while not self.flag.is_set():
            try:
                data = self.sock.recv(4096)
                # print(f"received from {self.client_address} on {self}")
                msg = pickle.loads(data)
                if msg:
                    self.message_queue.put((msg, self))

            except socket.timeout:
                self.flag.set()

            except EOFError:
                pass

            except ConnectionResetError:
                print("A Connection ended abruptly")
                self.flag.set()

            except Exception as e:
                self.flag.set()
                raise e

        self.sock.close()
        self.disonnection_queue.put(self.client_address)
        # print(f"ended connection thread {self.client_address}")

    def send(self, data):
        self.sock.sendall(data)

    def stop(self):
        self.flag.set()
