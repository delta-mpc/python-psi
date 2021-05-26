from Crypto.Hash import SHAKE256


def encrypt(secret: bytes, plaintext: bytes):
    shake = SHAKE256.new(secret)
    key = shake.read(len(plaintext))

    int_key = int.from_bytes(key, "big")
    int_pt = int.from_bytes(plaintext, "big")

    int_ct = int_key ^ int_pt
    return int_ct.to_bytes(len(plaintext), "big")


def decrypt(secret: bytes, ciphertext: bytes):
    shake = SHAKE256.new(secret)
    key = shake.read(len(ciphertext))

    int_key = int.from_bytes(key, "big")
    int_ct = int.from_bytes(ciphertext, "big")

    int_pt = int_key ^ int_ct
    return int_pt.to_bytes(len(ciphertext), "big")
