import hashlib
import json
import math
import pickle
from base64 import b64encode, b64decode
from pyDH import DiffieHellman

from Crypto.Cipher import AES
from Crypto.Util import Padding


def generate_self_keys():
    """
    Generate Diffie-Hellman keys
    :return: private and public key
    """
    dh = DiffieHellman()
    return dh, dh.gen_public_key()


def generate_shared_keys(private_key, public_key):
    """
    Generate the shared key in the Diffie-Hellman protocol
    :param private_key: Private key of one of the user
    :param public_key: Public key of the other user
    :return: 16 bytes hash of the shared key
    """
    shared_key = private_key.gen_shared_key(public_key)
    shared_key_bytes = shared_key.encode()
    hash_function = hashlib.shake_256()
    hash_function.update(shared_key_bytes)
    hashed_key = hash_function.digest(16)  # Need 16 bytes long key for ECB decryption
    return hashed_key


def encrypt_ecb(key, plaintext):
    """
    Encrypt an object using the ECB algorithm
    :param key: Shared key
    :param plaintext: The text to encrypt
    :return: The encrypted data
    """
    pt_byte = pickle.dumps(plaintext)

    # Create the cipher object and set the mode to ECB
    cipher = AES.new(key, AES.MODE_ECB)

    # Pad the plaintext to a multiple of the block size (16 bytes)
    padded_plaintext = Padding.pad(pt_byte, 16)
    ciphertext = cipher.encrypt(padded_plaintext)
    return ciphertext


def decrypt_ecb(key, ciphertext):
    """
    Decrypt an object using the ECB algorithm
    :param key: Shared key
    :param ciphertext: The encrypted data
    :return: The original object
    """
    # Create the cipher object and set the mode to ECB
    cipher = AES.new(key, AES.MODE_ECB)
    decrypted_text = cipher.decrypt(ciphertext)
    unpadded_text = Padding.unpad(decrypted_text, 16)
    result = pickle.loads(unpadded_text)
    return result

