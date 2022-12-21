import pickle
import random
import string
import threading
import socket
import time
import uuid

import rsa

from src.constants import LOCALHOST


def generate_random_string():
    # Get all possible characters that can be used in the string
    characters = string.ascii_letters + string.digits + string.punctuation
    length = random.randint(10, 30)
    # Use the random module to generate a list of random characters
    random_string = [random.choice(characters) for _ in range(length)]

    # Return the random string as a single string
    return ''.join(random_string)


def check_data(data):
    mandatory_keys = ["data", "type", "user"]
    if isinstance(data, dict):
        for key in mandatory_keys:
            if key not in data:
                return False


class Server(threading.Thread):
    def __init__(self):
        super().__init__()
        self.pw_table = None
        self.users = None
        self.host = LOCALHOST
        self.port = 6344

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print("Challenge-Response server starting on port " + str(self.port))
        self.sock.bind((self.host, self.port))
        self.sock.settimeout(10.0)
        self.sock.listen()
        self.flag = threading.Event()
        self.private_key, self.public_key = rsa.newkeys(512)

    def run(self):
        while not self.flag.is_set():
            try:
                data = self.sock.recv(4096)
                msg = pickle.load(data)
                self.handle_data(msg)

            except Exception as e:
                raise e

    def handle_data(self, msg):
        if not self.check_message_validity(msg):
            return None

        data = msg["data"]
        data_type = data["type"]
        user = data["user"]
        if user in self.pw_table:
            response = self.construct_response(generate_random_string(), msg["sender"], msg["msg_id"])
            
            return
        else:
            # Registration
            # Maybe decrypt
            self.pw_table[user] = data["data"]

        return msg

    def check_message_validity(self, message):
        mandatory_keys = ["data", "type", "receiver", "msg_id", "sender"]
        if isinstance(message, dict):
            for key in mandatory_keys:
                if key not in message:
                    return False

            if message["receiver"][0] == self.host or message["receiver"][1] == self.port:
                # wrong address
                if check_data(message["data"]):
                    return True

        return False

    def construct_response(self, data, receiver, msg_id, overload=None):
        if overload is None:
            overload = {}
        dico = {"type": "msg", "time": str(time.time()), "receiver": receiver, "msg_id": msg_id, "data": data,
                "sender": (self.host, self.port)}
        # overload can change the values of the dictionnary if necessary
        return {**dico, **overload}
