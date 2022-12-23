import threading
from time import sleep


class WaitingThread(threading.Thread):
    """
    Thread waiting until its flag is set
    """
    def __init__(self):
        super().__init__()

        self.flag = threading.Event()

    def run(self):
        while not self.flag.is_set():
            self.flag.wait()

    def wake(self):
        self.flag.set()
