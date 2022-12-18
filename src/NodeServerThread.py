from ConnectionsThread import *


class NodeServerThread(threading.Thread):
    def __init__(self, node):
        super().__init__()

        self.node = node
        self.port = node.port
        self.host = node.host
        self.id = node.id
        self.connection_threads = []

        self.flag = threading.Event()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print("Node " + str(self.id) + " starting on port " + str(self.port))
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(1.0)
        self.sock.listen(1)

    def run(self):
        while not self.flag.is_set():
            try:
                # client_address = (host, port)
                client_sock, client_address = self.sock.accept()

                # get the id of the other node
                connected_node_id = client_sock.recv(2048).decode("utf-8")
                client_sock.send(str(self.id).encode("utf-8"))

                if self.id != connected_node_id:
                    client_thread = self.create_connection(client_sock, client_address)
                    client_thread.start()

                    self.connection_threads.append(client_thread)
                    self.node.connected_nodes[client_address] = client_thread
                else:
                    client_sock.close()

            except socket.timeout:
                pass

            except Exception as e:
                raise e

            sleep(0.01)

        for connection in self.connection_threads:
            connection.stop()

        self.sock.close()
        print("Node " + str(self.id) + " stopped")

    def connect_to(self, host, port):
        for connection in self.connection_threads:
            if (connection.host, connection.port) in self.node.connected_nodes:
                # already connected
                return self.node.connected_nodes[(connection.host, connection.port)]

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))

        sock.send(str(self.id).encode("utf-8"))
        connected_node_id = sock.recv(1024).decode("utf-8")
        print("connected with node: ", connected_node_id)

        thread_client = self.create_connection(sock, (host, port))

        self.connection_threads.append(thread_client)
        self.node.connected_nodes[(host, port)] = thread_client
        return thread_client

    def broadcast_to_network(self, message):
        for node in self.connection_threads:
            node.send(message)

    def create_connection(self, sock, client_address):
        return ConnectionThread(self.node, sock, client_address)

    def stop(self):
        self.flag.set()
