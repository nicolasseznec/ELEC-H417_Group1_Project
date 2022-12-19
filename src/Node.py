import json
import random
import time

from NodeServerThread import *


class Node:
    def __init__(self, host, port, index):
        self.host = host
        self.port = port
        self.id = index

        # Pending messages with a list of Msg_id : (sender_host, sender_port)
        self.pending_msg = {}

        # Message first sent from this Node
        self.self_messages = {}

        self.active_nodes = []  # each element of the liste is a tuple (addresse, port, publicKey)

        self.node_server = NodeServerThread(self)
        # TODO : start connection

    def start_connection(self):
        self.node_server.start()

    def stop_connection(self):
        self.node_server.stop()

    def connect_to(self, host, port):  # TODO : take address
        return self.node_server.connect_to(host, port)

    def broadcast_to_network(self, message):
        self.node_server.broadcast_to_network(message)

    def construct_message(self, data, msg_type, receiver=None, overload=None):
        if overload is None:
            overload = {}
        dico = {"data": data, "type": msg_type, "time": str(time.time()), "sender": self.id, "receiver": receiver}
        msg_id = random.randint(0, 100)  # To be determined (not random imo)
        dico["msg_id"] = msg_id

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

            # TODO : use an encryption/decryption module
            if not msg["msg_id"] in self.pending_msg:
                # decryption
                encrypted_data = msg["data"]
                print(encrypted_data)
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

    def handle_response(self, msg):
        """
        Final decryption of the response
        """
        pass
