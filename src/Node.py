import json
import random
import time
import uuid

from NodeServerThread import *
from utils import *
from WaitingThread import *
from Key import *
from Table import *


class Node:
    def __init__(self, host, port, index):
        self.host = host
        self.port = port
        self.id = index

        self.private_key, self.public_key = generate_self_keys()

        self.table = Table()
        # Pending messages with a list of Msg_id : (sender_host, sender_port)
        self.pending_msg = {}

        # Pending key lists of the diffie hellman exchange
        self.pending_key_list = {}

        # Message first sent from this Node
        self.self_messages = {}

        self.active_nodes = []  # each element of the liste is a tuple (addresse, port, publicKey)

        self.message_queue = Queue()
        self.stop_flag = threading.Event()
        self.node_server = NodeServerThread(self)

        self.node_server.start()
        threading.Thread(target=self.handle_messages).start()
        threading.Thread(target=self.handle_user_input).start()

    def stop_connection(self):
        self.node_server.stop()
        self.stop_flag.set()

    def connect_to(self, host, port):  # TODO : take address
        return self.node_server.connect_to(host, port)

    def broadcast_to_network(self, message):
        self.node_server.broadcast_to_network(message)

    def construct_message(self, data, type, receiver=None, id=None, sender=None, overload=None):
        if overload is None:
            overload = {}
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
        return {**dico, **overload}

    def generate_path(self):
        n = len(self.active_nodes)
        if n < 5:
            print("Not enough nodes")
            return
        else:
            return random.sample(self.active_nodes, 3)

    def send_message_to(self, data, msg_type, receiver):
        message = self.construct_message(data, msg_type, receiver)
        dumped_message = json.dumps(message)

        if receiver not in self.node_server.connection_threads:
            self.connect_to(receiver[0], receiver[1])

        connection = self.node_server.connection_threads[receiver]
        connection.send(dumped_message)
        self.node_server.connection_threads.pop(receiver)

    def handle_user_input(self):
        """
        Handle user input commands.
        """
        pass

    def handle_messages(self):
        """
        Handle any message received by one of the connection threads.
        """
        while not self.stop_flag.is_set():
            try:
                while not self.message_queue.empty():
                    msg = self.message_queue.get()
                    if msg:
                        self.data_handler(msg)

            except Exception as e:
                self.stop_connection()
                raise e

    def send_message(self, msg):
        # TODO refactor with the connected node list
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
            return

        msg_type = msg["type"]

        if msg_type == "key":
            if msg["msg_id"] in self.pending_key_list:
                self.pending_key_list[msg["msg_id"]].append(msg["data"])  # Getting the public key back
            else:
                self.reply_with_key(msg)  # Reply with public key
            return

        if msg_type == "msg":
            if msg["msg_id"] in self.self_messages:
                # Last point on the way back
                self.handle_response(msg)
                return

            # TODO : use an encryption/decryption module
            if not msg["msg_id"] in self.pending_msg:   # decryption
                encrypted_data = msg["data"]
                print("Node " + str(self.id) + " : " + str(encrypted_data))

                key = self.table.get_key(msg["msg_id"], msg["sender"])
                if key is not None:
                    decrypted_data = decrypt_cbc(key, encrypted_data)
                    decrypted_data = str_to_dict(decrypted_data)
                    if decrypted_data is None:  # Not a dict
                        return
                else:
                    return
                if decrypted_data["type"] == "request":
                    self.handle_request(decrypted_data["data"])
                if decrypted_data["type"] == "msg":
                    self.send_message(decrypted_data)

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

    def launch_key_exchange(self, hop_list, id_list):
        """
        Diffie Hellmann exchange
        To be continued...............
        """
        key_list = []
        for hop in hop_list:
            id = id_list[0]
            private_key, public_key = generate_self_keys()
            message = self.construct_message(public_key, "key", hop)
            message = self.onion_pack(hop_list[:len(key_list)], key_list, id_list, message)

            self.pending_key_list[id] = key_list
            # Waiting thread
            dh_thread = WaitingThread(id, self)
            dh_thread.start()
            self.send_message(message)
            dh_thread.join()
            key_list = self.pending_key_list[id]
            key_list[-1] = generate_shared_keys(private_key, key_list[-1])
            self.pending_key_list.pop(id)
        return key_list

    def message_tor_send(self, host, port, msg):
        """
        Sends a message in the tor network from A to Z
        """
        node_list = self.generate_path()
        id_list = generate_id_list(len(node_list))
        key_list = self.launch_key_exchange(node_list, id_list)
        message = self.construct_message(msg, "msg", (host, port))
        message = self.onion_pack(node_list, key_list, id_list, message)
        self.send_message(message)

    def onion_pack(self, hop_list, key_list, id_list, root_message):
        """
        Packs the root_message in an onion
        """
        message = root_message
        if len(hop_list) != len(key_list):
            return

        for i in reversed(range(len(hop_list))):
            encryption = encrypt(message, key_list[i])
            msg_id = id_list[i]
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

    def handle_request(self, decrypted_data):
        """
        Exit node action
        """
        pass

    def reply_with_key(self, msg):
        """
        Reply in the DH exchange
        """
        private_key, public_key = generate_self_keys()
        shared_keys = generate_shared_keys(private_key, msg["data"])
        self.table.new_key(msg["msg_id"], msg["sender"], shared_keys)
        reply = self.construct_message(public_key, "key", msg["sender"], msg["msg_id"])
        self.send_message(reply)
