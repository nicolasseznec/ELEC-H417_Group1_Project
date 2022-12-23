import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")

import time
import argparse

import src.constants
from src.constants import LOCALHOST
from src.Node import *
from src.DirectoryNode import DirectoryNode


def main():

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-port", type=int)
    group.add_argument("-test", type=int, metavar="N", help="start multiple nodes for test purposes")

    args = parser.parse_args()

    if args.test:
        src.constants.DEBUG = True
        nodes = [Node(LOCALHOST, 100+i, i, enable_input=False) for i in range(args.test)]

    else:
        port = args.port
        Node(LOCALHOST, port, 0, enable_input=True)


if __name__ == '__main__':
    main()
