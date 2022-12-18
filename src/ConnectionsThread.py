import threading
from time import sleep

from Node import *
import socket


class ConnectionThread(threading.Thread):
    def __init__(self, node, sock, client_address):
        super().__init__()
        self.node = node
        self.sock = sock

        self.id = node.id
        self.host = node.host
        self.port = node.port

        self.client_address = client_address
        self.flag = threading.Event()

    def run(self):
        self.sock.settimeout(10.0)
        while not self.flag.is_set():
            try:
                data = self.sock.recv(4096)
                msg = data.decode()
                # print(msg)
                self.node.data_handler(msg)

            except socket.timeout:
                self.flag.set()

            except Exception as e:
                self.flag.set()
                raise e

            sleep(0.01)
        self.sock.settimeout(None)
        self.sock.close()
        self.node.connected_nodes.pop(self.client_address)
        sleep(1)

    def send(self, data):
        self.sock.sendall(data.encode("utf-8"))
        self.node.connected_nodes.pop(self.client_address)

    def stop(self):
        self.flag.set()


class NodeServerThread(threading.Thread):
    def __init__(self, node):
        super().__init__()
        self.node = node

        self.host = node.host
        self.port = node.port
        self.id = node.id

        self.flag = threading.Event()

        self.connected_nodes = []
        self.messages = []

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print("Node " + str(node.id) + " starting on port " + str(self.port))
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(10.0)
        self.sock.listen(1)

    def run(self):
        while not self.flag.is_set():
            try:
                connection, client_address = self.sock.accept()

                # get the id of the other node
                connected_node_id = connection.recv(2048).decode("utf-8")
                connection.send(str(self.id).encode("utf-8"))

                if self.id != connected_node_id:
                    thread_client = self.create_connection(connection, client_address)
                    thread_client.start()

                    self.connected_nodes.append(thread_client)
                    self.node.connected_nodes[client_address] = thread_client
                else:
                    connection.close()

            except socket.timeout:
                pass

            except Exception as e:
                raise e

            sleep(0.01)

        for node in self.connected_nodes:
            node.stop()

        self.sock.close()
        print("Node " + str(self.id) + " stopped")

    def connect_to(self, host, port):
        for node in self.connected_nodes:
            if node.port == port:
                # already connected
                return True

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))

        sock.send(str(self.id).encode("utf-8"))
        connected_node_id = sock.recv(1024).decode("utf-8")
        print("connected with node: ", connected_node_id)

        thread_client = self.create_connection(sock, (host, port))

        self.connected_nodes.append(thread_client)
        self.node.connected_nodes[(host, port)] = thread_client
        return thread_client

    def broadcast_to_network(self, message):
        for node in self.connected_nodes:
            node.send(message)

    def stop(self):
        self.flag.set()

    def create_connection(self, sock, client_address):
        return ConnectionThread(self.node, sock, client_address)
