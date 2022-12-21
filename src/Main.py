import time

from constants import LOCALHOST
from Node import *
from DirectoryNode import DirectoryNode


def main():
    # Initialization
    # -------- 1. Get the list of Nodes ----------
    # (use a directory authority ?)
    # Retrieve the list each time
    # Register the new node as part of relays

    # -------- 2. Establish the circuit ----------
    # Select the guard, middle and exit node
    # Build the circuit step by step, retreiving the key of each node

    # -------- 3. Send message -------------------
    # encrypt in layers
    # send to guard node

    # -------- 4. Recieve message ----------------
    # Recieve encrypted message
    # decrypt layers
    pass

    # node0 = Node(LOCALHOST, 1000, 0)
    # node1 = Node(LOCALHOST, 101, 1)
    # node2 = Node(LOCALHOST, 102, 2)
    # node3 = Node(LOCALHOST, 103, 3)
    #
    # hop_list = ((LOCALHOST, 101), (LOCALHOST, 102), (LOCALHOST, 103))
    # id_list = generate_id_list(3)
    # key_list = node0.launch_key_exchange(hop_list, id_list)
    # print(key_list)
    # sleep(30)
    #
    # node0.stop_connection()
    # node1.stop_connection()
    # node2.stop_connection()
    # node3.stop_connection()

    dirNode = DirectoryNode(DIRECTORY_NODE_HOST, DIRECTORY_NODE_PORT, 1000)
    node1 = Node(LOCALHOST, 101, 1)
    node2 = Node(LOCALHOST, 102, 2)

    time.sleep(10)
    node1.stop_connection()
    time.sleep(60)  # Node 2 should ping once before dirNode noticed that node1 disconnected, and once after
    node2.stop_connection()
    dirNode.stop_connection()


if __name__ == '__main__':
    main()
