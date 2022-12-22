from src.AuthServerThread import AuthServerThread
from src.Key import generate_self_keys, generate_shared_keys, decrypt_cbc
from src.Node import Node
from src.Request import check_request_validity
from constants import *


class Authentication(Node):
    def __init__(self, host, port, index):
        super().__init__(host, port, index)

        # {(msg_id, addr) : shared_key}
        self.key_table = {}

        # {user : pw}
        self.user_pw_table = {}

    def create_server(self):
        server = AuthServerThread(self)
        server.start()
        return server

    def data_handler(self, msg, connection):
        print(f"Auth server received {msg}")
        if not self.check_message_validity(msg):
            return

        if msg["type"] == "key":
            self.reply_with_key(msg)

        if msg["type"] == "msg":
            line = (msg["msg_id"], msg["sender"])
            if line in self.key_table:
                encrypted_data = msg["data"]
                key = self.key_table.get(line)
                decrypted_data = decrypt_cbc(key, encrypted_data)
                if not self.check_data_validity(decrypted_data):
                    return

                # pw = decrypted_data["data"]
                user = decrypted_data["user"]
                if user in self.user_pw_table:
                    if self.user_pw_table[user] == decrypted_data.get("pw"):
                        print(f"{user} is authenticated!!")
                        # Do what you want
                else:
                    # Registration
                    self.user_pw_table[user] = decrypted_data["data"]
                    print(f"user {user} successfully registered")

    def reply_with_key(self, msg):
        private_key, public_key = generate_self_keys()
        shared_key = generate_shared_keys(private_key, msg["data"])
        self.key_table[(msg["msg_id"], msg["sender"])] = shared_key
        reply = self.construct_message(public_key, "msg", msg["sender"], msg["msg_id"])
        self.send_message(reply)

    def check_message_validity(self, message):
        mandatory_keys = ["data", "type", "receiver", "msg_id", "sender"]
        if isinstance(message, dict):
            for key in mandatory_keys:
                if key not in message:
                    return False

            if message["receiver"][0] == self.host or message["receiver"][1] == self.port:
                # wrong address
                return True
        return False

    def check_data_validity(self, data):
        mandatory_keys = ["type", "data", "user"]
        if isinstance(data, dict):
            for key in mandatory_keys:
                if key not in data:
                    return False
            return True
        return False


