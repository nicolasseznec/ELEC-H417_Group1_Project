import time
import argparse

from constants import LOCALHOST
from Node import *
from DirectoryNode import DirectoryNode


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("port", type=int, required=True)
    args = parser.parse_args()

    port = args.port
    print(port)
    # dirNode = DirectoryNode(DIRECTORY_NODE_HOST, DIRECTORY_NODE_PORT, 1000)
    # node0 = Node(LOCALHOST, 1000, 0)
    # node1 = Node(LOCALHOST, 101, 1)
    # node2 = Node(LOCALHOST, 102, 2)
    # node3 = Node(LOCALHOST, 103, 3)
    #
    # hop_list = ((LOCALHOST, 102), (LOCALHOST, 101), (LOCALHOST, 103))
    # id_list = generate_id_list(3)
    #
    # timer = time.time()
    # key_list = node0.launch_key_exchange(hop_list, id_list)
    # print("----------------", time.time() - timer, "-----------------------")
    # print(key_list)
    #
    # node0.stop_connection()
    # node1.stop_connection()
    # node2.stop_connection()
    # node3.stop_connection()
    # dirNode.stop_connection()

    # dirNode = DirectoryNode(DIRECTORY_NODE_HOST, DIRECTORY_NODE_PORT, 1000)
    # node1 = Node(LOCALHOST, 101, 1)
    # node2 = Node(LOCALHOST, 102, 2)
    #
    # time.sleep(10)
    # node1.stop_connection()
    # time.sleep(60)  # Node 2 should ping once before dirNode noticed that node1 disconnected, and once after
    # node2.stop_connection()
    # dirNode.stop_connection()


if __name__ == '__main__':
    main()
