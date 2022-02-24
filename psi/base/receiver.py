from Crypto.PublicKey import ECC

from ..cipher import shake
from ..pair import Pair
from ..serialize import bytes_to_key, point_to_bytes, key_to_bytes
from ..utils import unpack


def recv(pair: Pair, b: int) -> bytes:
    assert b == 0 or b == 1, "b should be 0 or 1"

    ak_bytes = pair.recv()
    ak = bytes_to_key(ak_bytes)
    curve = ak.curve

    sk = ECC.generate(curve=curve)
    pk = sk.public_key()

    # choose point and pk
    if b == 1:
        point = pk.pointQ + ak.pointQ
        pk = ECC.EccKey(curve=curve, point=point)
    # send chosen public key
    pair.send(key_to_bytes(pk))

    ck = ak.pointQ * sk.d
    # receive cipher msg
    cipher_m = unpack(pair.recv())[b]

    res = shake.decrypt(point_to_bytes(ck), cipher_m)
    return res
