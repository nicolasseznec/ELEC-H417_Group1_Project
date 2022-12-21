import json
import pickle
import random
import time
import uuid

from NodeServerThread import *
from src.constants import LOCALHOST
from utils import *
from WaitingThread import *
from Key import *
from Table import *
from Request import *


class Node:
    def __init__(self, host, port, index):
        self.host = host
        self.port = port
        self.id = index

        self.private_key, self.public_key = generate_self_keys()

        self.table = Table()
        # Pending messages with a set of Msg_id : (sender_host, sender_port, [key1, key2, key3])
        self.pending_request = {}

        # Pending key lists of the diffie hellman exchange
        self.pending_key_list = {}
        self.waiting_threads = {}

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

    def connect_to(self, addr):
        return self.node_server.connect_to(addr)

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
        receiver = (msg["receiver"][0], msg["receiver"][1])
        if msg["sender"][0] != self.host or msg["sender"][1] != self.port:
            print("Not the right sender")

        dumped_message = pickle.dumps(msg)
        if receiver not in self.node_server.connection_threads:
            connection = self.connect_to(receiver)
        else:
            connection = self.node_server.connection_threads[receiver]
        connection.send(dumped_message)
        # self.node_server.connection_threads.pop(receiver)

    def data_handler(self, msg):
        """
        Receive a message in input,
        if it is not the receiver -> return
        else -> manage the data by transferring etc...
        """
        # msg = str_to_dict(data)
        print("Node " + str(self.id) + " received : " + str(msg))
        if msg["receiver"][0] != self.host or msg["receiver"][1] != self.port:
            print("wrong addr")
            return

        msg_type = msg["type"]

        if msg_type == "key":
            self.reply_with_key(msg)  # Reply with public key
            return

        if msg_type == "msg":
            if msg["msg_id"] in self.pending_request:
                # Last point on the way back
                self.handle_response(msg)
                return
            if msg["msg_id"] in self.pending_key_list:
                decrypted_data = unpack_onion(self.pending_key_list[msg["msg_id"]], msg)
                self.update_pending_key_list(msg["msg_id"], decrypted_data)  # Getting the public key back
                return

            line = (msg["msg_id"], (msg["sender"][0], msg["sender"][1]))
            if line not in self.table.transfer_table:
                # Decrypt
                encrypted_data = msg["data"]

                key = self.table.get_key(msg["msg_id"], msg["sender"])
                if key is not None:
                    decrypted_data = decrypt_cbc(key, encrypted_data)
                else:
                    return

                typed = decrypted_data["type"]
                if typed == "request":
                    # Exit Node
                    self.handle_request(msg["msg_id"], (msg["sender"][0], msg["sender"][1]), decrypted_data["data"])
                    return

                # Add the transfer in the table
                self.table.new_transfer(msg["msg_id"], (msg["sender"][0], msg["sender"][1]),
                                        decrypted_data["msg_id"],
                                        (decrypted_data["receiver"][0], decrypted_data["receiver"][1]))
                if typed == "msg" or typed == "key":
                    # Transfer it
                    self.send_message(decrypted_data)

            else:
                # encryption
                data = pickle.dumps(msg)
                key = self.table.get_key(msg["msg_id"], (msg["sender"][0], msg["sender"][1]))
                encrypted_data = encrypt_cbc(key, data)
                # Transferring the message
                msg_id, receiver = self.table.get_transfer(msg["msg_id"], (msg["sender"][0], msg["sender"][1]))
                message = self.construct_message(encrypted_data, "msg", receiver, msg_id)
                self.send_message(message)

    def launch_key_exchange(self, hop_list, id_list):
        """
        Diffie Hellman exchange
        """
        key_list = []
        for i in range(len(hop_list)):
            hop = hop_list[i]

            if i == 0:
                sender = None
            else:
                sender = hop_list[i - 1]

            id = id_list[0]
            private_key, public_key = generate_self_keys()
            message = self.construct_message(public_key, "key", hop, id_list[i], sender)
            message = self.onion_pack(hop_list[:i], key_list, id_list, message)
            self.pending_key_list[id] = key_list

            # Waiting thread
            timer = time.time()
            waiting_thread = WaitingThread()
            self.waiting_threads[id] = waiting_thread
            waiting_thread.start()
            self.send_message(message)
            waiting_thread.join()
            print(f"waiting :  {time.time() - timer}")

            key_list = self.pending_key_list[id]
            key_list[-1] = generate_shared_keys(private_key, key_list[-1])
            self.pending_key_list.pop(id)

        return key_list

    def message_tor_send(self, request):
        """
        Sends a message in the tor network from A to Z
        """
        # node_list = self.generate_path()
        hop_list = ((LOCALHOST, 101), (LOCALHOST, 102), (LOCALHOST, 103))
        node_list = hop_list
        id_list = generate_id_list(len(node_list))
        key_list = self.launch_key_exchange(node_list, id_list)
        self.pending_request[id_list[0]] = key_list
        message = self.construct_message(request, "request", sender="", id=id_list[-1])
        message = self.onion_pack(node_list, key_list, id_list, message)
        self.send_message(message)

    def onion_pack(self, hop_list, key_list, id_list, root_message, i=None):
        """
        Packs the root_message in an onion recursively
        """
        # Set the initial index value if not provided
        if i is None:
            i = len(key_list) - 1
        if i < 0:
            return root_message

        encryption = encrypt_cbc(key_list[i], root_message)
        msg_id = id_list[i]
        if i != 0:
            sender = hop_list[i - 1]
        else:
            sender = (self.host, self.port)
        message = self.construct_message(encryption, "msg", hop_list[i], id=msg_id, sender=sender)

        if i == 0:
            return message
        else:
            return self.onion_pack(hop_list, key_list, id_list, message, i=i - 1)

    def handle_response(self, msg):
        """
        Final decryption of the response
        """
        key_list = self.pending_request.get(msg["msg_id"])
        self.pending_request.pop(msg["msg_id"])
        decrypted_data = unpack_onion(key_list, msg)

        print(decrypted_data)

    def handle_request(self, id, addr, request):
        """
        Exit node action
        """
        response = exec_request(request)

        print("Node " + str(self.id) + str(self.table.key_table))
        print((id, addr))
        key = self.table.get_key(id, addr)
        # print(key)
        encrypted_response = encrypt_cbc(key, response)
        message = self.construct_message(encrypted_response, "msg", addr, id)
        # message = self.construct_message("Hello", "msg", addr, id=10)
        # print(message)
        self.send_message(message)

    def reply_with_key(self, msg):
        """
        Reply in the DH exchange
        """
        private_key, public_key = generate_self_keys()
        shared_keys = generate_shared_keys(private_key, msg["data"])
        self.table.new_key(msg["msg_id"], (msg["sender"][0], msg["sender"][1]), shared_keys)
        reply = self.construct_message(public_key, "msg", msg["sender"], msg["msg_id"])
        self.send_message(reply)

    def update_pending_key_list(self, id, public_key):
        self.pending_key_list[id].append(public_key)
        self.waiting_threads[id].wake()
        self.waiting_threads.pop(id)
