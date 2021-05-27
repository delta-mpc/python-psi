import secrets
from functools import reduce
from operator import mul
from typing import Tuple, Union

from ..serialize import bytes_to_bit_arr, int_to_bytes

__all__ = ["rand_binary_arr"]


def rand_binary_arr(shape: Union[int, Tuple[int, ...]]):
    if isinstance(shape, int):
        size = shape
    else:
        size = reduce(mul, shape)
    bs = secrets.randbits(size).to_bytes((size + 7) // 8, "big")
    res = bytes_to_bit_arr(int_to_bytes(size) + bs)
    res.resize(shape)
    return res
