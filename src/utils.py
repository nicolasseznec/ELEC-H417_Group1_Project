# TODO
import json
from random import randint

def str_to_dict(string):
    try:
        return_value = json.loads(string)

    except json.decoder.JSONDecodeError:
        return None

    return return_value

def dict_to_str(dict):
    if type(dict) is str:
        return dict
    else:
        try:
            return_value = json.dumps(dict)
        except json.decoder.JSONDecodeError:
            return None
    return return_value

def generate_id_list(length):
    return_list = []
    for i in range(length):
        id = randint(0, 100)
        # id = uuid.uuid4()
        return_list.append(id)
    return return_list
