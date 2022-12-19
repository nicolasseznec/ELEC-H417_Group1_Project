from constants import LOCALHOST
from Node import *


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

    node0 = Node(LOCALHOST, 1000, 0)
    node1 = Node(LOCALHOST, 1010, 1)

    node0.send_message_to("Hello", "msg", (LOCALHOST, 1010))
    node1.send_message_to("Hi", "msg", (LOCALHOST, 1000))

    sleep(5)

    node0.stop_connection()
    node1.stop_connection()


if __name__ == '__main__':
    main()
