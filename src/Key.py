import hashlib
import json
import math
import pickle
from base64 import b64encode, b64decode
from pyDH import DiffieHellman

from Crypto.Cipher import AES
from Crypto.Util import Padding


g = 2
p = 7919
bits = 128


def generate_self_keys():
    # private_key = random.getrandbits(bits)
    # public_key = pow(g, private_key, p)
    # return private_key, public_key
    dh = DiffieHellman()
    return dh, dh.gen_public_key()


def generate_shared_keys(private_key, public_key):
    # shared_key = pow(public_key, private_key, p)
    # print(shared_key)
    # shared_key_bytes = shared_key.to_bytes(bits // 8, 'big')  # convert to byte string
    shared_key = private_key.gen_shared_key(public_key)
    shared_key_bytes = shared_key.encode()
    hash_function = hashlib.shake_256()
    hash_function.update(shared_key_bytes)
    hashed_key = hash_function.digest(16)  # Need 16 bytes long key for ECB decryption
    return hashed_key


def encrypt_cbc(key, plaintext):
    # if type(plaintext) is dict:
    #     print(plaintext)
    #     plaintext = pickle.dumps(plaintext)
    pt_byte = pickle.dumps(plaintext)

    # Create the cipher object and set the mode to ECB
    cipher = AES.new(key, AES.MODE_ECB)

    # Pad the plaintext to a multiple of the block size (16 bytes)
    padded_plaintext = Padding.pad(pt_byte, 16)
    ciphertext = cipher.encrypt(padded_plaintext)
    # result = b64encode(ciphertext)
    # return result
    return ciphertext

def decrypt_cbc(key, ciphertext):
    # Create the cipher object and set the mode to ECB
    cipher = AES.new(key, AES.MODE_ECB)
    # ciphertext = b64decode(ciphertext)
    decrypted_text = cipher.decrypt(ciphertext)
    unpadded_text = Padding.unpad(decrypted_text, 16)
    # result = unpadded_text.decode('utf-8')
    result = pickle.loads(unpadded_text)
    return result


# a, A = generate_self_keys()
# b, B = generate_self_keys()
# keyA = generate_shared_keys(a, B)
# keyB = generate_shared_keys(b, A)
# # print(len(keyA))
# cipher = encrypt_cbc(keyA, "Hello guys")
# print(cipher)
# print(decrypt_cbc(keyB, cipher))

