import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")

import json
import pickle
import random
import threading
import time
import uuid

from src.NodeServerThread import *
from src.constants import LOCALHOST
from src.utils import *
from src.WaitingThread import *
from src.Key import *
from src.Table import *
from src.Request import *
from src.Input import *


class Node:
    """
    Object representing a Node in the TOR network
    """
    def __init__(self, host, port, index, enable_input=False):
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

        # Information concerning a challenge response protocol
        self.pending_auth = {}

        self.enable_input = enable_input
        self.input_started = False
        self.input_handler = InputHandler(self)

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
        self.input_handler.stop()
        self.stop_flag.set()

    def connect_to(self, addr):
        return self.node_server.connect_to(addr)

    def construct_message(self, data, msg_type, receiver=None, msg_id=None, sender=None):
        """
        Construct a message in the expected pattern
        """
        dico = {"type": msg_type, "time": str(time.time()), "receiver": receiver}
        if msg_id is not None:
            dico["msg_id"] = msg_id
        else:
            dico["msg_id"] = uuid.uuid4()
        if sender is not None:
            dico["sender"] = sender
        else:
            dico["sender"] = (self.host, self.port)
        dico["data"] = data
        return dico

    def generate_path(self, length=3):
        """
        Generates a random path made by the active nodes
        :return: path : The path
        """
        n = len(self.active_nodes)
        if n < 5:
            print("Not enough nodes : ", n)
            print(self.active_nodes)
            return None
        else:
            path = random.choices([*self.active_nodes], k=length)
            if not (self.host, self.port) in path:
                return path
            else:
                return self.generate_path()

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
        """
        Send a message to the address specified in the message
        :param msg:
        """
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

    def data_handler(self, msg, connection):
        """
        Receive a message in input,
        handles it in order to transfer it, reply, ...
        """
        if constants.DEBUG:
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

        if msg_type == "msg" or msg_type == "challenge":
            if msg["msg_id"] in self.pending_request:
                # Last point on the way back
                self.handle_result(msg)
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
                    decrypted_data = decrypt_ecb(key, encrypted_data)
                else:
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
                # List of the types to transfer
                transfer_type = ["auth", "response", "msg", "key", "register"]
                if msg_type in transfer_type:
                    # Transfer it
                    self.send_message(decrypted_data)

            else:
                # encryption
                data = pickle.dumps(msg)
                key = self.table.get_key(line[0], line[1])
                encrypted_data = encrypt_ecb(key, data)
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
        Diffie Hellman exchange with every node in the hop_list
        :return The corresponding shared keys list
        """
        key_list = []
        for i in range(len(hop_list)):
            hop = hop_list[i]

            if i == 0:
                sender = None
            else:
                sender = hop_list[i - 1]

            entry_id = id_list[0]
            private_key, public_key = generate_self_keys()
            message = self.construct_message(public_key, "key", hop, id_list[i], sender)
            message = self.onion_pack(hop_list[:i], key_list, id_list, message)
            self.pending_key_list[entry_id] = key_list

            # Waiting thread
            timer = time.time()
            waiting_thread = WaitingThread()
            self.waiting_threads[entry_id] = waiting_thread
            waiting_thread.start()
            self.send_message(message)
            waiting_thread.join()
            if constants.DEBUG:
                print(f"waiting :  {time.time() - timer}")

            key_list = self.pending_key_list[entry_id]
            key_list[-1] = generate_shared_keys(private_key, key_list[-1])
            self.pending_key_list.pop(entry_id)

        return key_list

    def message_tor_send(self, content, msg_type, receiver=None):
        """
        Sends a message in the tor network from A to Z
        """
        node_list = self.generate_path()
        if not node_list:
            return
        id_list = generate_id_list(len(node_list))
        key_list = self.launch_key_exchange(node_list, id_list)
        self.pending_request[id_list[0]] = key_list
        message = self.construct_message(content, msg_type, sender=node_list[-1], receiver=receiver)
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

        encryption = encrypt_ecb(key_list[i], root_message)
        msg_id = id_list[i]
        if i != 0:
            sender = hop_list[i - 1]
        else:
            sender = (self.host, self.port)
        message = self.construct_message(encryption, "msg", hop_list[i], msg_id=msg_id, sender=sender)

        if i == 0:
            return message
        else:
            return self.onion_pack(hop_list, key_list, id_list, message, i=i - 1)

    def handle_result(self, msg):
        """
        Final decryption of the result
        """
        key_list = self.pending_request.get(msg["msg_id"])
        self.pending_request.pop(msg["msg_id"])
        decrypted_data = unwrap_onion(key_list, msg)

        if isinstance(decrypted_data, dict):
            # Challenge
            if decrypted_data["type"] == "challenge":
                user = decrypted_data.get("user")
                print(self.pending_auth)
                if not user:
                    return
                if user in self.pending_auth:
                    # Continue the challenge response process
                    # print(self.waiting_threads)
                    self.waiting_threads[user].wake()
                    self.waiting_threads.pop(user)
                    self.pending_auth[user] = decrypted_data.get("data")
                else:
                    return

        # print("Received :")
        print(decrypted_data)

    def handle_request(self, msg_id, addr, request):
        """
        Called when the exit node has to make a request
        """
        result = exec_request(request)

        key = self.table.get_key(msg_id, addr)
        
        encrypted_result = encrypt_ecb(key, result)
        message = self.construct_message(encrypted_result, "msg", addr, msg_id)

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

    def update_pending_key_list(self, msg_id, public_key):
        """
        Updates the key list of a route
        """
        self.pending_key_list[msg_id].append(public_key)
        self.waiting_threads[msg_id].wake()
        self.waiting_threads.pop(msg_id)

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

        if self.enable_input and not self.input_started:
            self.input_started = True
            self.input_handler.start()

        if constants.DEBUG:
            print(f"Received active nodes : {active_nodes}")

    def check_data_validity(self, decrypted_data):
        mandatory_keys = ["data", "type", "receiver", "msg_id", "sender"]
        if isinstance(decrypted_data, dict):
            for key in mandatory_keys:
                if not decrypted_data.get(key):
                    print(f"missing key : {key}")
                    print(decrypted_data)
                    return False
            return True
        return False

    def contact_auth_server(self, message, addr):
        """
        Sends a message through the tor network to the specified address by adding it at the end of the hop list
        """
        hop_list = self.generate_path()
        hop_list.append(addr)  # the address of the auth server
        if not hop_list:
            return
        id_list = generate_id_list(len(hop_list))
        key_list = self.launch_key_exchange(hop_list, id_list)
        self.pending_request[id_list[0]] = key_list
        message = self.onion_pack(hop_list, key_list, id_list, message)
        self.send_message(message)

    def register(self, user, pw, addr, option=0):
        """
        Register through the tor network
        :param user: username
        :param pw: password
        :param addr: (host, port) of the authentication server
        :param option: 0 is for sending the pw hash in clear, 1 is for setting a secured channel before sending password

        """
        if option == 0:
            message = self.construct_message(compute_hash([pw]), "register", sender="", receiver=addr)
            message["user"] = user
            message = pickle.dumps(message)
            self.message_tor_send(message, "register", addr)
        if option == 1:
            message = self.construct_message(compute_hash([pw]), "register", sender="")  # Only the server will see it
            message["user"] = user
            self.contact_auth_server(message, addr)

    def authenticate(self, user, pw, addr):
        """
        Triggers challenge response protocol and tries the challenge
        """
        if user in self.pending_auth:
            print("Already in a challenge-response process")
            return
        message = self.construct_message("", "auth", sender="", receiver=addr)
        message["user"] = user
        message = pickle.dumps(message)
        self.message_tor_send(message, "auth", addr)
        waiting_thread = WaitingThread()
        self.waiting_threads[user] = waiting_thread
        waiting_thread.start()
        self.pending_auth[user] = "waiting"
        waiting_thread.join()
        nonce = self.pending_auth.get(user)
        self.pending_auth.pop(user)
        if nonce == 0:
            print("Not registered, please register")
            return
        if nonce:
            pw_hash = compute_hash([pw])
            response = compute_hash([nonce, pw_hash])
            message = self.construct_message(response, "response", sender="", receiver=addr)
            message["user"] = user
            message = pickle.dumps(message)
            self.message_tor_send(message, "response", addr)


def main():

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-port", type=int)
    group.add_argument("-test", type=int, metavar="N", help="start multiple nodes for test purposes")

    args = parser.parse_args()

    if args.test:
        constants.DEBUG = True
        nodes = [Node(LOCALHOST, 100+i, i, enable_input=False) for i in range(args.test)]

    else:
        port = args.port
        Node(LOCALHOST, port, 0, enable_input=True)


if __name__ == '__main__':
    main()
