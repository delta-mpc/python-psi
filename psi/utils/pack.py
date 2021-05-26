from typing import Tuple

from ..serialize import int_to_bytes, bytes_to_int

__all__ = ["pack", "unpack"]


def pack(m0: bytes, m1: bytes) -> bytes:
    return int_to_bytes(len(m0)) + m0 + m1


def unpack(m: bytes) -> Tuple[bytes, bytes]:
    m0_length = bytes_to_int(m[:4])
    m0 = m[4: 4 + m0_length]
    m1 = m[4 + m0_length:]
    return m0, m1
