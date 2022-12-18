import json
import random
import time
import rsa
from random import randrange

from ConnectionsThread import *
from src.ConnectionsThread import NodeServerThread


class Node:
    def __init__(self, host, port, index):
        self.host = host
        self.port = port
        self.id = index

        self.msg_storage = {}

        # Pending messages with a list of Msg_id : (sender_host, sender_port)
        self.pending_msg = {}

        # Message first sent from this Node
        self.self_messages = {}

        self.keyPublic, self.keyPrivate = rsa.newkeys(512)  # Generate the public and the private key
        self.listNodes = []  # each element of the liste is a tuple (addresse, port, publicKey)

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

    def construct_message(self, data, type, receiver=None, overload={}):
        dico = {"data": data, "type": type, "time": str(time.time()), "sender": self.id, "receiver": receiver}
        msg_id = random.randint(0, 100)  # To be determined (not random imo)
        dico["msg_id"] = msg_id
        # overload can change the values of the dictionnary if necessary
        message = {**dico, **overload}
        return message

    def encrypt_message(self, msg, path_list):
        encrypt1 = json.dumps(msg)
        encrypt1 = rsa.encrypt(encrypt1.encode("utf-8"), path_list[2][2])  # path_list(2)(2) donne la publicKey de exitNode
        encrypt2 = self.construct_message(encrypt1, "msg", receiver=(path_list[2][0], path_list[2][1]))

        # (path_list(1)(0),path_list(1)(1)) -> donne un tuple avec address et port du prochain hop

        encrypt2 = json.dumps(encrypt2)
        encrypt2 = rsa.encrypt(encrypt2.encode("utf-8"), path_list[1][2])

        encrypt3 = self.construct_message(encrypt2, "msg", receiver=(path_list[1][0], path_list[1][1]))
        encrypt3 = json.dumps(encrypt3)
        encrypt3 = rsa.encrypt(encrypt3.encode("utf-8"), path_list(0)(2))

        final_message = self.construct_message(encrypt3, "msg", (path_list[0][0], path_list[0][1]))

        return final_message
        
    def generate_path(self):
        n = len(self.listNodes)
        if n < 5:
            print("Not enough nodes")
            return
        else:
            return random.sample(self.listNodes, 3)

    def send_message_to(self, data, type, receiver):
        message = self.construct_message(data, type, receiver)

        connection = self.connected_nodes[receiver]
        dumped_message = json.dumps(message)
        connection.send(dumped_message)

    def data_handler(self, data):
        """
        Receive a message in input,
        if it is not the receiver -> return
        else -> manage the data by transferring etc...
        """
        msg = json.loads(data)
        if msg["receiver"][0] != self.host or msg["receiver"][1] != self.port:
            # wrong address
            return

        if msg["type"] == "msg":
            if msg["msg_id"] in self.self_messages:
                # Last point on the way back
                self.handle_response(msg)
                return

            if not msg["msg_id"] in self.pending_msg:
                # decryption
                encrypted_data = msg["data"]
                decrypted_data = rsa.decrypt(encrypted_data.decode('utf-8'), self.keyPrivate)
                decrypted_msg = json.loads(decrypted_data)

                # Transferring the message
                self.send_message_to(decrypted_msg["data"], "msg", decrypted_msg["receiver"])

                # Add the message+sender in the pending list
                self.pending_msg[msg["msg_id"]] = msg["sender"]

            else:
                # encryption
                data = json.dumps(msg)
                encrypted_data = rsa.encrypt(data.encode('utf-8'), self.keyPublic)

                # Transferring the message
                receiver = self.pending_msg.get(msg["msg_id"])
                self.send_message_to(encrypted_data, "msg", receiver)

                # Remove the message because it is on its way back
                self.pending_msg.pop(msg["msg_id"])

    def print_message(self, sender, msg):
        print("Node " + self.id + "received Message from : " + str(sender))
        print("Content : " + msg)

    def handle_response(self, msg):
        """
        Final decryption of the response
        """
        pass
