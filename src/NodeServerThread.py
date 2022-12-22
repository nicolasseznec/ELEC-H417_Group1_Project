from queue import Queue

from ConnectionsThread import *
from constants import ENCODING
from Pinger import Pinger
from constants import DIRECTORY_NODE_HOST, DIRECTORY_NODE_PORT


class NodeServerThread(threading.Thread):
    def __init__(self, node):
        super().__init__()

        self.node = node
        self.port = node.port
        self.host = node.host
        self.id = node.id

        self.connection_threads = {}
        self.disconnections = Queue()
        self.flag = threading.Event()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print("Node " + str(self.id) + " starting on port " + str(self.port))
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(1.0)
        self.sock.listen(1)

        self.pinger = self.create_pinger(node.message_queue, (DIRECTORY_NODE_HOST, DIRECTORY_NODE_PORT))
        # self.pinger = None

    def run(self):
        while not self.flag.is_set():
            try:
                client_sock, client_address = self.sock.accept()
                self.handle_connection(client_sock, client_address)

            except socket.timeout:
                pass

            except Exception as e:
                raise e

            while not self.disconnections.empty():
                address = self.disconnections.get()
                connection = self.connection_threads.pop(address, None)
                if connection:
                    connection.stop()

                print(f"disconnected : {address}")

        for connection in self.connection_threads.values():
            connection.stop()

        if self.pinger:
            self.pinger.stop()

        self.sock.close()
        print("Node " + str(self.id) + " stopped")

    def handle_connection(self, connection, address):
        # print(f"{self.id} accepted {address}")

        # Exchange IDs
        connected_node_id = connection.recv(2048).decode(ENCODING)
        # print(f"received {connected_node_id}")
        connection.send(str(self.id).encode(ENCODING))

        # if self.id != connected_node_id:
        client_thread = self.create_connection(connection, address)
        client_thread.start()

        # self.connection_threads[address] = client_thread
        # else:
        #     connection.close()
        # print(f"{self.id} threads : {self.connection_threads}")

    def connect_to(self, address):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(address)

        sock.send(str(self.id).encode(ENCODING))
        connected_node_id = sock.recv(1024).decode(ENCODING)
        print(f"Node {self.id} connected with node: {connected_node_id}")

        thread_client = self.create_connection(sock, address)

        self.connection_threads[address] = thread_client
        return thread_client

    def broadcast_to_network(self, message):
        for node in self.connection_threads.values():
            node.send(message)

    def create_connection(self, sock, client_address):
        return ConnectionThread(self.node.message_queue, self.disconnections, sock, client_address)

    def create_pinger(self, message_queue, address):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(address)
            sock.send(str(self.id).encode(ENCODING))
            connected_node_id = sock.recv(1024).decode(ENCODING)
            print(f"Node {self.id} connected with directory node")
            pinger = Pinger(message_queue, self.disconnections, sock, (self.host, self.port), address)
            pinger.start()
            return pinger
        except ConnectionRefusedError:
            print(f"Could not connect to Directory node at {address}")
            return None

    def stop(self):
        self.flag.set()
