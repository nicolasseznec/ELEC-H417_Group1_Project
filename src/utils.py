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

def generate_id_list(length):
    return_list = []
    for i in range[length]:
        id = random.randint(0, 100)
        # id = uuid.uuid4()
        return_list.append(id)
    return return_list
