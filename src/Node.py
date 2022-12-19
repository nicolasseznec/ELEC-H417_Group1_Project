import json
import random
import time
from random import randrange

from NodeServerThread import *
from utils import *
from WaitingThread import *
from Key import *


class Node:
    def __init__(self, host, port, index):
        self.host = host
        self.port = port
        self.id = index

        self.private_key, self.public_key = generate_self_keys()

        # Pending messages with a list of Msg_id : (sender_host, sender_port)
        self.pending_msg = {}

        # Pending key lists of the diffie hellman exchange
        self.pending_key_list = {}

        # Message first sent from this Node
        self.self_messages = {}

        self.available_nodes = []  # each element of the liste is a tuple (addresse, port, publicKey)

        # (host, port) : connection_thread
        self.connected_nodes = {}

        self.connection = NodeServerThread(self)

    def start_connection(self):
        self.connection.start()

    def stop_connection(self):
        self.connection.stop()

    def connect_to(self, host, port):
        return self.connection.connect_to(host, port)

    def broadcast_to_network(self, message):
        self.connection.broadcast_to_network(message)

    def construct_message(self, data, type, receiver=None, id=None, sender=None, overload={}):
        dico = {"type": type, "time": str(time.time()), "receiver": receiver}
        if id is not None:
            dico["msg_id"] = id
        else:
            dico["msg_id"] = random.randint(0, 100)
        if sender is not None:
            dico["sender"] = sender
        else:
            dico["sender"] = (self.host, self.port)
        dico["data"] = data
        # overload can change the values of the dictionnary if necessary
        message = {**dico, **overload}
        return message

    def generate_path(self):
        n = len(self.available_nodes)
        if n < 5:
            print("Not enough nodes")
            return
        else:
            return random.sample(self.available_nodes, 3)

    def send_message_to(self, data, type, receiver):
        message = self.construct_message(data, type, receiver)

        connection = self.connect_to(receiver[0], receiver[1])
        dumped_message = json.dumps(message)
        connection.send(dumped_message)
        self.connected_nodes.pop(receiver)

    def send_message(self, msg):
        receiver = msg["receiver"]
        if msg["sender"][0] != self.host or msg["sender"][1] != self.port:
            print("Not the right sender")
            print(str(self.port) + "   " + str(msg["sender"][1]))
        connection = self.connect_to(receiver[0], receiver[1])
        dumped_message = json.dumps(msg)
        connection.send(dumped_message)

    def data_handler(self, data):
        """
        Receive a message in input,
        if it is not the receiver -> return
        else -> manage the data by transferring etc...
        """
        msg = str_to_dict(data)
        if msg["receiver"][0] != self.host or msg["receiver"][1] != self.port:
            # wrong address
            print("wrong address")
            return

        msg_type = msg["type"]

        if msg_type == "key":
            shared_key = generate_shared_keys(self.private_key, msg["data"])
            if msg["key_id"] in self.pending_key_list:
                # Coming back
                self.pending_key_list[msg["key_id"]].append(shared_key)
            else:
                # self.look_table[msg["sender"]] = shared_key
                return

        if msg_type == "msg":
            if msg["msg_id"] in self.self_messages:
                # Last point on the way back
                self.handle_response(msg)
                return

            # TODO : use an encryption/decryption module
            if not msg["msg_id"] in self.pending_msg:
                # decryption
                encrypted_data = msg["data"]
                print("Node " + str(self.id) + " : " + str(encrypted_data))
                # encrypt(encrypted_data, key)
                decrypted_data = encrypt(encrypted_data, self.public_key)
                if type(decrypted_data) is dict:
                    if decrypted_data["type"] == "request":
                        self.handle_request(decrypted_data["data"])
                    if decrypted_data["type"] == "msg":
                        self.send_message(decrypted_data)
                else:
                    return

            else:
                # encryption
                data = json.dumps(msg)
                # encrypted_data = rsa.encrypt(data.encode('utf-8'), self.keyPublic)
                # Transferring the message
                # receiver = self.pending_msg.get(msg["msg_id"])
                # self.send_message_to(encrypted_data, "msg", receiver)

                # Remove the message because it is on its way back
                # self.pending_msg.pop(msg["msg_id"])

    def print_message(self, sender, msg):
        print("Node " + self.id + "received Message from : " + str(sender))
        print("Content : " + msg)

    def launch_key_exchange(self, hop_list):
        """
        Diffie Hellmann exchange
        To be continued...............
        """
        key_list = []
        for hop in hop_list:
            id = random.randint(0, 100)
            overload = {"key_id": id}
            message = self.construct_message(self.public_key, "key", hop, overload)
            message = self.onion_pack(hop_list[:len(key_list)], key_list, message)

            self.pending_key_list[id] = key_list
            # Waiting thread
            dh_thread = WaitingThread(id, self)
            dh_thread.start()
            self.send_message(message)
            dh_thread.join()
            key_list = self.pending_key_list[id]
            self.pending_key_list.pop(id)
        return key_list

    def message_tor_send(self, host, port, msg):
        """
        Onion packs a message and sends it
        """
        node_list = self.generate_path()
        key_list = self.launch_key_exchange(node_list)
        message = self.construct_message(msg, "msg", (host, port))
        message = self.onion_pack(node_list, key_list, message)
        self.send_message(message)

    def onion_pack(self, hop_list, key_list, root_message):
        message = root_message
        if len(hop_list) != len(key_list):
            return

        for i in reversed(range(len(hop_list))):
            encryption = encrypt(message, key_list[i])
            msg_id = random.randint(0, 100)  # TO be discussed
            if i != 0:
                sender = hop_list[i - 1]
            else:
                sender = (self.host, self.port)
            message = self.construct_message(encryption, "msg", hop_list[i], id=msg_id, sender=sender)

        return message

    def handle_response(self, msg):
        """
        Final decryption of the response
        """
        pass

    def send_test(self, msg, hop_list):
        message = self.construct_message("Hello", "request", receiver="http://etc", sender=hop_list[2])
        message = self.onion_pack(hop_list, [1, 2, 3], message)
        self.send_message(message)

    def handle_request(self, decrypted_data):
        """
        Exit node action
        """
        pass
