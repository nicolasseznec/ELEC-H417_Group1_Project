import threading
from time import sleep


class WaitingThread(threading.Thread):
    def __init__(self, id, node):
        super().__init__()
        self.node = node
        self.id = id
        self.starting_point = len(node.pending_key_list[id])

        self.flag = threading.Event()

    def run(self):
        while not self.flag.is_set():
            if len(self.node.key_list[id]) > self.starting_point:
                self.flag.set()
            sleep(0.1)
