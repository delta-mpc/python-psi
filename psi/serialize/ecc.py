from Crypto.PublicKey import ECC

__all__ = ["point_to_bytes", "key_to_bytes", "bytes_to_key"]


def point_to_bytes(point: ECC.EccPoint):
    xs = point.x.to_bytes()
    ys = bytes([2 + point.y.is_odd()])
    return xs + ys


def key_to_bytes(key: ECC.EccKey):
    if key.has_private():
        raise ValueError("only public key can be serialized to bytes to send")
    return key.export_key(format="DER", compress=True)


def bytes_to_key(data: bytes) -> ECC.EccKey:
    return ECC.import_key(data)
