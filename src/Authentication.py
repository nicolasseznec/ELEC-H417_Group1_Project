import pickle

from src.AuthServerThread import AuthServerThread
from src.Key import generate_self_keys, generate_shared_keys, decrypt_ecb, encrypt_ecb
from src.Node import Node
from src.Request import check_request_validity
from src.constants import *
from src.utils import compute_hash, generate_nonce, mark_message


class Authentication(Node):
    def __init__(self, host, port, index):
        super().__init__(host, port, index)

        # {(msg_id, addr) : shared_key}
        self.key_table = {}

        # {user : nonce}
        self.pending_challenge = {}

        # {user : sha256(pw)}
        self.user_pw_table = {}

        # Hard coded for test purpose
        # username: user32, password:123
        self.user_pw_table["user32"] = "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"

    def create_server(self):
        server = AuthServerThread(self)
        server.start()
        return server

    def data_handler(self, msg, connection):
        print(f"Auth server received {msg}")
        if not self.check_message_validity(msg):
            return

        msg_type = msg["type"]
        if msg_type == "key":
            self.reply_with_key(msg)

        if msg_type == "auth":
            self.send_challenge(msg)

        if msg_type == "response":
            self.handle_result(msg)

        if msg_type == "register":
            self.handle_register(msg)

        if msg["type"] == "msg":
            # Secured Registration through a secured channel
            line = (msg["msg_id"], msg["sender"])
            if line in self.key_table:
                encrypted_data = msg["data"]
                key = self.key_table.get(line)
                decrypted_data = decrypt_ecb(key, encrypted_data)
                if not self.check_data_validity(decrypted_data):
                    return
                user = decrypted_data["user"]
                if user in self.user_pw_table:
                    message = "Already registered under this username"
                else:
                    # Registration
                    self.user_pw_table[user] = decrypted_data["data"]
                    message = f"{user} successfully registered"
                encrypted_data = encrypt_ecb(key, message)
                message = self.construct_message(encrypted_data, "msg", msg["sender"], msg["msg_id"])
                mark_message(message)
                self.send_message(message)

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

    def send_challenge(self, msg):
        data = msg["data"]
        data = pickle.loads(data)
        if not self.check_data_validity(data):
            print("invalid data")
            print(data)
            return
        user = data["user"]
        if user in self.user_pw_table:
            nonce = generate_nonce()
            self.pending_challenge[user] = nonce
            # The message that the user will read
            challenge = self.construct_message(nonce, "challenge")
        else:
            challenge = self.construct_message(0, "challenge")
        challenge["user"] = user
        # For transport issue
        message = self.construct_message(challenge, "msg", msg["sender"], msg["msg_id"])
        mark_message(message)
        self.send_message(message)

    def handle_result(self, msg):
        data = msg["data"]
        data = pickle.loads(data)
        if not self.check_data_validity(data):
            print("invalid data")
            return
        user = data["user"]
        if user in self.user_pw_table and user in self.pending_challenge:
            nonce = self.pending_challenge[user]
            hashed_pw = self.user_pw_table[user]
            expected_value = compute_hash([nonce, hashed_pw])

            if data["data"] == expected_value:
                message = self.construct_message("Successfully authenticated", "msg", msg["sender"], msg["msg_id"])
            else:
                message = self.construct_message("Failed the challenge", "msg", msg["sender"], msg["msg_id"])
            mark_message(message)
            self.send_message(message)

    def handle_register(self, msg):
        data = msg["data"]
        data = pickle.loads(data)
        if not self.check_data_validity(data):
            print("invalid data")
            return
        user = data["user"]
        if user in self.user_pw_table:
            message = self.construct_message("Already registered under this username", "msg", msg["sender"], msg["msg_id"])
        else:
            self.user_pw_table[user] = data["data"]
            message = self.construct_message(f"{user} successfully registered", "msg", msg["sender"], msg["msg_id"])
        mark_message(message)
        self.send_message(message)


def main():
    Authentication(AUTHENTICATION_SERV_HOST, AUTHENTICATION_SERV_PORT, 0)


if __name__ == '__main__':
    main()
