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
from Input import *


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

        self.input_handler = InputHandler(self)
        # self.active_nodes = {(LOCALHOST, 101), (LOCALHOST, 102), (LOCALHOST, 103), (LOCALHOST, 104), (LOCALHOST, 105), (LOCALHOST, 106)}
        self.active_nodes = set()
        self.message_queue = Queue()
        self.stop_flag = threading.Event()
        self.node_server = self.create_server()

        threading.Thread(target=self.handle_messages).start()
        # threading.Thread(target=self.handle_user_input).start()

    def create_server(self):
        node_server = NodeServerThread(self)
        node_server.start()
        return node_server

    def stop_connection(self):
        self.node_server.stop()
        self.stop_flag.set()
        self.input_handler.stop()

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
            dico["msg_id"] = uuid.uuid4()
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
            print("Not enough nodes : ", n)
            print(self.active_nodes)
            return None
        else:
            path = random.sample(self.active_nodes, 3)
            if not (self.host, self.port) in path:
                return path
            else:
                return self.generate_path()

    def handle_user_input(self):
        """
        Handle user input commands.
        """
        if not self.input_handler.isAlive():
            self.input_handler.start()

    def handle_messages(self):
        """
        Handle any message received by one of the connection threads.
        """
        while not self.stop_flag.is_set():
            try:
                while not self.message_queue.empty():
                    msg, connection = self.message_queue.get()
                    if msg:
                        self.data_handler(msg, connection)

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
            connection.start()
        else:
            connection = self.node_server.connection_threads[receiver]
        connection.send(dumped_message)
        # self.node_server.connection_threads.pop(receiver)

    def data_handler(self, msg, connection):
        """
        Receive a message in input,
        handles it in order to transfer it, reply, ...
        """
        # msg = str_to_dict(data)
        print("Node " + str(self.id) + " received : " + str(msg))

        if not self.check_message_validity(msg):
            return

        msg_type = msg["type"]
        sender = msg["sender"]
        self.node_server.connection_threads[
            sender] = connection  # Register the connection thread with the actual sender
        connection.client_address = sender

        if msg_type == "key":
            self.reply_with_key(msg)  # Reply with public key
            return

        if msg_type == "ping":
            self.update_active_nodes(msg["data"])
            return

        if msg_type == "msg":
            if msg["msg_id"] in self.pending_request:  # TODO maybe
                # Last point on the way back
                self.handle_response(msg)
                return
            if msg["msg_id"] in self.pending_key_list:
                decrypted_data = unwrap_onion(self.pending_key_list[msg["msg_id"]], msg)
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
                if not self.check_data_validity(decrypted_data):
                    return
                msg_type = decrypted_data["type"]
                if msg_type == "request":
                    # Exit Node
                    self.handle_request(msg["msg_id"], (msg["sender"][0], msg["sender"][1]), decrypted_data["data"])
                    return

                # Add the transfer in the table
                self.table.new_transfer(msg["msg_id"], (msg["sender"][0], msg["sender"][1]),
                                        decrypted_data["msg_id"],
                                        (decrypted_data["receiver"][0], decrypted_data["receiver"][1]))
                if msg_type == "msg" or msg_type == "key":
                    # Transfer it
                    self.send_message(decrypted_data)

            else:
                # encryption
                data = pickle.dumps(msg)
                key = self.table.get_key(line[0], line[1])
                encrypted_data = encrypt_cbc(key, data)
                # Transferring the message
                msg_id, receiver = self.table.get_transfer(line[0], line[1])
                message = self.construct_message(encrypted_data, "msg", receiver, msg_id)
                # Check if the message is marked
                if msg.get("mark"):
                    self.table.drop_path(msg["msg_id"], (msg["sender"][0], msg["sender"][1]))
                    mark_message(message)
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

    def message_tor_send(self, content, msg_type):
        """
        Sends a message in the tor network from A to Z
        """
        node_list = self.generate_path()
        if not node_list:
            return
        id_list = generate_id_list(len(node_list))
        key_list = self.launch_key_exchange(node_list, id_list)
        self.pending_request[id_list[0]] = key_list
        message = self.construct_message(content, msg_type, sender=node_list[-1])
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
        decrypted_data = unwrap_onion(key_list, msg)

        print(decrypted_data)

    def handle_request(self, id, addr, request):
        """
        Exit node action
        """
        response = exec_request(request)

        key = self.table.get_key(id, addr)
        encrypted_response = encrypt_cbc(key, response)
        message = self.construct_message(encrypted_response, "msg", addr, id)
        mark_message(message)
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

    def check_message_validity(self, message):
        mandatory_keys = ["data", "type", "receiver", "msg_id", "sender"]
        if isinstance(message, dict):
            for key in mandatory_keys:
                if key not in message:
                    return False

            if message["receiver"][0] != self.host or message["receiver"][1] != self.port:
                # wrong address
                return False
            return True

    def update_active_nodes(self, active_nodes):
        self.active_nodes = active_nodes
        # self.handle_user_input()
        # print(f"Received active nodes : {active_nodes}")

    def check_data_validity(self, decrypted_data):
        mandatory_keys = ["data", "type", "receiver", "msg_id", "sender"]
        if isinstance(decrypted_data, dict):
            for key in mandatory_keys:
                if key not in decrypted_data:
                    return False
            return True

    def register(self, user, pw, addr):
        """
        Register through the tor network
        :param user: username
        :param pw: password
        :param addr: (host, port) of the authentication server
        """
        hop_list = self.generate_path()
        hop_list.append(addr)   # the address of the auth server
        if not hop_list:
            return
        id_list = generate_id_list(len(hop_list))
        key_list = self.launch_key_exchange(hop_list, id_list)
        self.pending_request[id_list[0]] = key_list
        message = self.construct_message(pw, "register")    # Only the server will see it
        message["user"] = user
        message = self.onion_pack(hop_list, key_list, id_list, message)
        self.send_message(message)




