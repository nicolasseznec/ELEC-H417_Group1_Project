from ConnectionsThread import *
from constants import ENCODING


class NodeServerThread(threading.Thread):
    def __init__(self, node):
        super().__init__()

        self.node = node
        self.port = node.port
        self.host = node.host
        self.id = node.id

        self.connection_threads = {}

        self.flag = threading.Event()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print("Node " + str(self.id) + " starting on port " + str(self.port))
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(10.0)
        self.sock.listen(1)

    def run(self):
        while not self.flag.is_set():
            try:
                # client_address = (host, port)
                client_sock, client_address = self.sock.accept()
                print(f"{self.id} accpeted {client_address}")
                # get the id of the other node
                connected_node_id = client_sock.recv(2048).decode(ENCODING)  # 1024 ?
                print(f"received {connected_node_id}")
                client_sock.send(str(self.id).encode(ENCODING))

                if self.id != connected_node_id:
                    client_thread = self.create_connection(client_sock, client_address)
                    client_thread.start()

                    self.connection_threads[client_address] = client_thread
                else:
                    client_sock.close()

            except socket.timeout:
                pass

            except Exception as e:
                raise e

            sleep(0.01)

        for connection in self.connection_threads.values():
            connection.stop()

        self.sock.close()
        print("Node " + str(self.id) + " stopped")

    def connect_to(self, host, port):
        address = (host, port)
        print(address)
        if address in self.connection_threads:
            # already connected
            return self.node.connected_nodes[address]

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(address)

        sock.send(str(self.id).encode(ENCODING))
        print(f"sent {self.id}")
        connected_node_id = sock.recv(1024).decode(ENCODING)
        print("connected with node: ", connected_node_id)

        thread_client = self.create_connection(sock, address)

        self.connection_threads[address] = thread_client
        return thread_client

    def broadcast_to_network(self, message):
        for node in self.connection_threads.values():
            node.send(message)

    def create_connection(self, sock, client_address):
        return ConnectionThread(self.node, sock, client_address)

    def stop(self):
        self.flag.set()
