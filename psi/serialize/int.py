__all__ = ["int_to_bytes", "bytes_to_int"]


def int_to_bytes(value: int):
    byte_length = (value.bit_length() + 7) // 8
    byte_length = (byte_length + 3) // 4 * 4
    byte_length = 4 if byte_length == 0 else byte_length
    return value.to_bytes(byte_length, "big")


def bytes_to_int(data: bytes):
    return int.from_bytes(data, "big")
