import hashlib
import json
import math
import random

from Crypto.Cipher import AES
from Crypto.Util import Padding

from src.constants import ENCODING

g = 2
p = 7919
bits = 128


def generate_self_keys():
    private_key = random.getrandbits(bits)
    public_key = pow(g, private_key, p)
    return private_key, public_key


def generate_shared_keys(private_key, public_key):
    shared_key = pow(public_key, private_key, p)
    shared_key_bytes = shared_key.to_bytes(bits // 8, 'big')  # convert to byte string
    hash_function = hashlib.shake_256()
    hash_function.update(shared_key_bytes)
    hashed_key = hash_function.digest(16)  # Need 16 bytes long key for ECB decryption
    return hashed_key


def encrypt_cbc(key, plaintext):
    if type(plaintext) == "dict":
        plaintext = json.dumps(plaintext)
    pt_byte = plaintext.encode('utf-8')

    # Create the cipher object and set the mode to ECB
    cipher = AES.new(key, AES.MODE_ECB)

    # Pad the plaintext to a multiple of the block size (16 bytes)
    padded_plaintext = Padding.pad(pt_byte, 16)
    ciphertext = cipher.encrypt(padded_plaintext)
    return ciphertext


def decrypt_cbc(key, ciphertext):
    # Create the cipher object and set the mode to ECB
    cipher = AES.new(key, AES.MODE_ECB)
    decrypted_text = cipher.decrypt(ciphertext)
    unpadded_text = Padding.unpad(decrypted_text, 16)
    result = unpadded_text.decode('utf-8')
    return result

# a, A = generate_self_keys()
# b, B = generate_self_keys()
# key = generate_shared_keys(a, B)
# print(len(key))
# cipher = encrypt_cbc(key, "Hello guys")
# print(cipher)
# print(decrypt_cbc(key, cipher))
