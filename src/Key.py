import random

g = 2
p = 7919
bits = 32


def generate_self_keys():
    private_key = random.getrandbits(bits)
    public_key = pow(g, private_key, p)
    return private_key, public_key


def generate_shared_keys(private_key, public_key):
    shared_key = pow(public_key, private_key, p)
    return shared_key

