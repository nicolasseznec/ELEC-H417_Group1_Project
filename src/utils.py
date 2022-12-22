import json
import pickle
import uuid
from random import randint

from src.Key import decrypt_cbc


def byte_to_dict(string):
    try:
        if isinstance(string, str):
            return string
        if isinstance(string, bytes):
            return pickle.loads(string)

    except json.decoder.JSONDecodeError:
        return None


def dict_to_byte(dict):
    if type(dict) is bytes:
        return bytes
    else:
        try:
            return_value = pickle.dumps(dict)
        except json.decoder.JSONDecodeError:
            return None
    return return_value


def generate_id_list(length):
    """
    Generates a random list of msg_id of the desired length
    """
    return_list = []
    for i in range(length):
        # id = randint(0, 100)
        id = uuid.uuid4()
        return_list.append(id)
    return return_list


def unwrap_onion(key_list, msg):
    """
    Decrypt an onion message recursively
    """
    if not isinstance(msg, dict):
        return msg
    elif not key_list:
        return msg["data"]
    # Recursive case: decrypt the message and call the function again
    else:
        key = key_list[0]
        encrypted_data = msg["data"]
        decrypted_data = decrypt_cbc(key, encrypted_data)
        decrypted_data = byte_to_dict(decrypted_data)
        return unwrap_onion(key_list[1:], decrypted_data)


def mark_message(message):
    message["mark"] = 1
