import pickle
import threading
import time


class Pinger(threading.Thread):
    def __init__(self, directory_node_addr, parent, interval=30):
        super(Pinger, self).__init__()
        self.directory_node_addr = directory_node_addr
        self.parent_node = parent
        self.interval = interval

        self.flag = threading.Event()

    def stop(self):
        self.flag.set()

    def run(self):
        while not self.flag.is_set():
            thread = self.parent_node.connect_to(self.directory_node_addr)
            ping = self.construct_ping()
            thread.send(ping)

    def construct_ping(self):
        ping = {"type": "ping", "time": str(time.time()), "receiver": self.directory_node_addr,
                "sender": (self.parent_node.host, self.parent_node.port), "data": ""}
        ping = pickle.dumps(ping)
        return ping
