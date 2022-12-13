from ConnectionsThread import *


class Node:
    def __init__(self, host, port, index):
        self.host = host
        self.port = port
        self.id = index

        self.connection = NodeServerThread(self)

    def start_connection(self):
        self.connection.start()

    def stop_connection(self):
        self.connection.stop()

    def connect_to(self, host, port):
        self.connection.connect_to(host, port)

    def broadcast_to_peers(self, message):
        self.connection.broadcast_to_network(message)
