import json
import random
import time

from ConnectionsThread import *
from src.ConnectionsThread import NodeServerThread


class Node:
    def __init__(self, host, port, index):
        self.host = host
        self.port = port
        self.id = index

        self.peers = []
        self.msg_storage = {}

        # Pending messages with a list of Msg_id : Sender
        self.pending_msg = {}

        # Message first sent from this Node
        self.self_messages = {}

        self.key = None  # To be done

        self.connection = NodeServerThread(self)

    def start_connection(self):
        self.connection.start()

    def stop_connection(self):
        self.connection.stop()

    def connect_to(self, host, port):
        self.connection.connect_to(host, port)

    def broadcast_to_network(self, message):
        self.connection.broadcast_to_network(message)

    def construct_message(self, data, type, overload={}):
        dico = {"data": data, "type": type, "time": str(time.time()), "sender": self.id, "receiver": None}
        msg_id = random.randint(0, 100)  # To be determined (not random imo)
        dico["msg_id"] = msg_id
        # Input can change the values of the dictionnary if necessary
        message = {**dico, **overload}
        return message

    def send_message_to(self, data, type, receiver):
        # if receiver :
        #     data.encrypt(receiver.key)        // Example
        overload = {"receiver": receiver}
        message = self.construct_message(data, type, overload)
        self.broadcast_to_network(message)

    # def broadcast_peers_list(self):
    #     """
    #     Brodcast peers connected to the network (+public key?)
    #     """
    #     message = self.construct_message(self.peers, "peers")
    #     self.broadcast_to_network(message)

    def data_handler(self, data):
        """
        Receive a message in input,
        if it is not the receiver -> return
        else -> manage the data by transferring etc...
        """
        msg = json.loads(data)
        if msg["receiver"] != self.id:
            return

        if msg["type"] == "msg":
            if msg["msg_id"] in self.self_messages:
                # Last point on the way back
                self.handle_response(msg)
                return

            if not msg["msg_id"] in self.pending_msg:
                # decryption
                encrypted_data = msg["data"]
                decrypted_data = encrypted_data.decrypt(self.key)
                decrypted_msg = json.loads(decrypted_data)

                # Create  a connection with the destination
                # if not already connected to this node
                #     self.connect_to("msg["receiver]")

                # Transferring the message
                self.send_message_to(decrypted_msg["data"], "msg", decrypted_msg["receiver"])

                # Add the message+sender in the pending list
                self.pending_msg[msg["msg_id"]] = msg["sender"]

            else:
                # encryption
                data = json.dumps(msg)
                encrypted_data = data.encrypt(self.key)

                # Transferring the message
                receiver = self.pending_msg.get(msg["msg_id"])
                self.send_message_to(encrypted_data, "msg", receiver)

                # Close the connection
                # if no other communication with this Node:
                #     self.close_connection(msg["sender])

                # Remove the message because it is on its way back
                self.pending_msg.pop(msg["msg_id"])

        # etc

    def print_message(self, sender, msg):
        print("Node " + self.id + "received Message from : " + str(sender))
        print("Content : " + msg)

    def handle_response(self, msg):
        """
        Final decryption of the response
        """
        pass
