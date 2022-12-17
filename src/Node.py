import time

from ConnectionsThread import *


class Node:
    def __init__(self, host, port, index):

        self.host = host
        self.port = port
        self.id = index

        self.peers = []
        self.msg_list = {}

        self.key = None #To be done

        self.connection = NodeServerThread(self)

    def start_connection(self):
        self.connection.start()

    def stop_connection(self):
        self.connection.stop()

    def connect_to(self, host, port):
        self.connection.connect_to(host, port)

    def broadcast_to_network(self, message):
        self.connection.broadcast_to_network(message)

    def construct_message(self, data, type, input={}):
        dico = {"data": data, "type": type}
        dico["time"] = str(time.time())
        dico["sender"] = self.id
        dico["receiver"] = None

        # Input can change the values of the dictionnary if necessary
        message = {**dico, **input}
        return message

    def send_message_to(self, data, type, receiver=None):
        # if receiver :
        #     data.encrypt(receiver.key)        // Example
        input = {"receiver": receiver}
        message = self.construct_message(data, "decrypt", input)
        self.broadcast_to_network(message)

    def broadcast_peers_list(self):
        """
        Brodcast peers connected to the network (+public key?)
        """
        message = self.construct_message(self.peers, "peers")
        self.broadcast_to_network(message)

    def data_handler(self, data):
        """
        Receive a message in input,
        if it is not the receiver -> return
        else -> manage the data by transferring etc...
        """
        if data["receiver"] != self.id:
            return

        encrypted_data = data["data"]
        decrypted_data = encrypted_data.decrypt(self.key)
        type = decrypted_data["type"]
        if type == "transfer":
            self.send_message_to(decrypted_data["data"], decrypted_data["transfer"],
                                 receiver=decrypted_data["receiver"])

        if type == "decrypt":
            sender = decrypted_data["sender"]
            msg = decrypted_data["data"]
            self.print_message(sender, msg)

            if not sender in self.msg_list:
                self.msg_list["sender"] = []
            self.msg_list["sender"].append(msg)

        if type == "peers":
            pass

        # etc



    def print_message(self, sender, msg):
        print("Message received from : " + str(sender))
        print("Content : " + msg)
