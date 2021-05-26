from Crypto.PublicKey import ECC

from ..cipher import shake
from ..pair import Pair
from ..serialize import key_to_bytes, bytes_to_key, point_to_bytes
from ..utils import pack


def send(pair: Pair, m0: bytes, m1: bytes, curve: str = "secp256r1"):
    sk = ECC.generate(curve=curve)
    pk = sk.public_key()

    pk_bytes = key_to_bytes(pk)
    pair.send(pk_bytes)

    bk_bytes = pair.recv()
    bk = bytes_to_key(bk_bytes)

    # cipher key for m0 and m1
    ck0 = bk.pointQ * sk.d
    ck1 = (-pk.pointQ + bk.pointQ) * sk.d

    cipher_m0 = shake.encrypt(point_to_bytes(ck0), m0)
    cipher_m1 = shake.encrypt(point_to_bytes(ck1), m1)
    pair.send(pack(cipher_m0, cipher_m1))
