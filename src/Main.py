from Node import *

node0 = Node("", 1000, 0)
node1 = Node("", 101, 1)
node2 = Node("", 102, 2)
node3 = Node("", 103, 3)

LOCALHOST = "127.0.0.1"


def connection_test():
    node0.start_connection()
    node1.start_connection()
    node2.start_connection()
    node3.start_connection()

    node1.connect_to(LOCALHOST, 1000)
    node2.connect_to(LOCALHOST, 101)
    node2.connect_to(LOCALHOST, 103)
    node3.connect_to(LOCALHOST, 1000)

    sleep(2)
    node0.stop_connection()
    node1.stop_connection()
    node2.stop_connection()
    node3.stop_connection()


def message_test():
    print(node1.construct_message("Hello", "Message", {"receiver": 3}))


if __name__ == '__main__':
    message_test()
