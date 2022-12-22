from src.AuthServerThread import AuthServerThread
from src.Key import generate_self_keys, generate_shared_keys, decrypt_cbc
from src.Node import Node
from src.Request import check_request_validity
from constants import *


class Authentication(Node):
    def __init__(self, host, port, index):
        super().__init__(host, port, index)

        # {user : shared_key}
        self.user_key_table = {}

        # {user : pw}
        self.user_pw_table = {}

    def create_server(self):
        server = AuthServerThread(self)
        server.start()
        return server

    def data_handler(self, msg, connection):
        if not self.check_message_validity(msg):
            return

        if msg["type"] == "key":
            self.reply_with_key(msg)

        user = msg["user"]
        if msg["type"] == "msg":
            if user in self.user_key_table:
                encrypted_data = msg["data"]
                key = self.user_key_table.get(user)
                decrypted_data = decrypt_cbc(key, encrypted_data)
                if not self.check_data_validity(decrypted_data):
                    return

                pw = decrypted_data["pw"]
                if user in self.user_pw_table:
                    if self.user_pw_table[user] == pw:
                        print(f"{user} is authenticated!!")
                        # Do what you want
                else:
                    # Registration
                    self.user_pw_table[user] = pw

    def reply_with_key(self, msg):
        private_key, public_key = generate_self_keys()
        shared_key = generate_shared_keys(private_key, msg["data"])
        self.user_key_table["user"] = shared_key
        reply = self.construct_message(public_key, "msg", msg["sender"], msg["msg_id"])
        self.send_message(reply)

    def check_message_validity(self, message):
        mandatory_keys = ["data", "type", "receiver", "msg_id", "sender", "user"]
        if isinstance(message, dict):
            for key in mandatory_keys:
                if key not in message:
                    return False

            if message["receiver"][0] == self.host or message["receiver"][1] == self.port:
                # wrong address
                return True
        return False

    def check_data_validity(self, data):
        mandatory_keys = ["pw"]
        if check_request_validity(data):
            for key in mandatory_keys:
                if key not in data:
                    return False
            return True
        return False


if __name__ == '__main__':
    Authentication(AUTHENTICATION_SERV_HOST, AUTHENTICATION_SERV_PORT, 0)
