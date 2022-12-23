import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")

from src.Node import *
from src.constants import DIRECTORY_NODE_HOST, DIRECTORY_NODE_PORT
from src.DirectoryNodeServerThread import DirectoryNodeServerThread


class DirectoryNode(Node):
    """
    Node acting as a Directory Authority. Keeps track of currently running nodes and
    provide them with the list of active nodes.
    """
    def __init__(self, host, port, index):
        super().__init__(host, port, index, enable_input=False)

    def create_server(self):
        node_server = DirectoryNodeServerThread(self)
        node_server.start()
        return node_server

    def data_handler(self, msg, connection):
        """
        Receives a "ping" from a node to signal its activity, sends back the updated list of nodes

        :param msg: The received message
        :param connection: The connection thread that received the message
        :return:
        """
        if not self.check_message_validity(msg):
            return

        msg_type = msg["type"]

        if msg_type == "ping":
            sender = msg["sender"]
            # print(f"Directory Node received from {sender} : {msg} ")
            self.node_server.connection_threads[sender] = connection  # Register the connection thread with the actual sender
            connection.client_address = sender

            self.register_active_node(sender)
            self.reply_with_nodes(msg)  # Reply with the list of active nodes
            return

    def reply_with_nodes(self, msg):
        reply = self.construct_message(self.active_nodes, "ping", receiver=msg["sender"], msg_id=msg["msg_id"])
        # print(f"Directory node sent back {reply}")
        self.send_message(reply)

    def register_active_node(self, addr_sender):
        self.active_nodes.add(addr_sender)

    def unregister_node(self, address):
        self.active_nodes.discard(address)


def main():
    """
    Launch a Directory Node
    """
    DirectoryNode(DIRECTORY_NODE_HOST, DIRECTORY_NODE_PORT, 0)


if __name__ == '__main__':
    main()
