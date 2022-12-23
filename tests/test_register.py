from src.Authentication import *
from src.DirectoryNode import *

auth = Authentication(AUTHENTICATION_SERV_HOST, AUTHENTICATION_SERV_PORT, 11)
dN = DirectoryNode(DIRECTORY_NODE_HOST, DIRECTORY_NODE_PORT, 10)
sleep(2)
node0 = Node(LOCALHOST, 1000, 0)
node1 = Node(LOCALHOST, 101, 1)
node2 = Node(LOCALHOST, 102, 2)
node3 = Node(LOCALHOST, 103, 3)
node4 = Node(LOCALHOST, 104, 4)
node5 = Node(LOCALHOST, 105, 5)
node6 = Node(LOCALHOST, 106, 6)


def connection_test():
    sleep(10)
    # constants.DEBUG = True
    node5.register("darkLordXX", "1234", (AUTHENTICATION_SERV_HOST, AUTHENTICATION_SERV_PORT))


if __name__ == '__main__':
    connection_test()
