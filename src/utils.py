# TODO
import json


def encrypt(data, key):
    return data


def str_to_dict(string):
    try:
        return_value = json.loads(string)

    except json.decoder.JSONDecodeError:
        return None

    return return_value


