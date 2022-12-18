import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")

from src.Node import *

LOCALHOST = "127.0.0.1"


class TestNode(unittest.TestCase):

    def test(self):
        self.node0 = Node("", 1000, 0)
        self.node1 = Node("", 101, 1)
        self.node2 = Node("", 102, 2)
        self.node3 = Node("", 103, 3)

        self.connection_test()
        self.message_test()

    def connection_test(self):
        self.node0.start_connection()
        self.node1.start_connection()
        self.node2.start_connection()
        self.node3.start_connection()

        self.node1.connect_to(LOCALHOST, 1000)
        self.node2.connect_to(LOCALHOST, 101)
        self.node2.connect_to(LOCALHOST, 103)
        self.node3.connect_to(LOCALHOST, 1000)

        self.node0.broadcast_to_network("Hello I'm node 0")
        self.node1.broadcast_to_network("Hello I'm node 1")
        self.node2.broadcast_to_network("Hello I'm node 2")
        self.node3.broadcast_to_network("Hello I'm node 3")

        self.node0.stop_connection()
        self.node1.stop_connection()
        self.node2.stop_connection()
        self.node3.stop_connection()

    def message_test(self):
        message = self.node1.construct_message("Hello", "Message", 3)

        self.assertEqual(message["data"], "Hello")
        self.assertEqual(message["type"], "Message")
        self.assertEqual(message["sender"], 1)
        self.assertEqual(message["receiver"], 3)


if __name__ == '__main__':
    unittest.main()
