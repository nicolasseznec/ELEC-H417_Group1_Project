import time
import unittest
import sys
import os
from time import sleep

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")

from src.Node import *

LOCALHOST = "127.0.0.1"


class TestNode(unittest.TestCase):

    def test(self):
        self.connection_test()
        self.message_test()

    def connection_test(self):
        node0 = Node(LOCALHOST, 1000, 0)
        node1 = Node(LOCALHOST, 1010, 1)

        node0.send_message_to("Hello", "msg", (LOCALHOST, 1010))
        node1.send_message_to("Hi", "msg", (LOCALHOST, 1000))

        time.sleep(0.01)

        node0.stop_connection()
        node1.stop_connection()

    def message_test(self):
        node1 = Node(LOCALHOST, 1010, 1)
        message = node1.construct_message("Hello", "Message", 3)

        self.assertEqual(message["data"], "Hello")
        self.assertEqual(message["type"], "Message")
        self.assertEqual(message["sender"], 1)
        self.assertEqual(message["receiver"], 3)
        node1.stop_connection()


if __name__ == '__main__':
    unittest.main()
