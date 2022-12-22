import pickle
import threading
import time
import random
from ConnectionsThread import ConnectionThread


class Pinger(ConnectionThread):
    def __init__(self, message_queue, disconnection_queue, sock, sender, receiver, interval=30.0):
        super().__init__(message_queue, disconnection_queue, sock, receiver, timeout=50)  # No timeout ?
        self.directory_node_addr = receiver
        self.sender = sender
        self.interval = interval
        threading.Thread(target=self.ping_loop).start()

    def construct_ping(self):
        ping = {"type": "ping", "time": str(time.time()), "receiver": self.directory_node_addr,
                "sender": self.sender, "data": "", "msg_id": random.randint(0, 100)}
        return pickle.dumps(ping)

    def ping_loop(self):
        while not self.flag.is_set():
            ping = self.construct_ping()
            print(f"{self.sender} ping !")
            self.send(ping)
            time.sleep(self.interval)
