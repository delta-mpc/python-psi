import numpy as np

from .int import int_to_bytes, bytes_to_int

__all__ = ["bit_arr_to_bytes", "bytes_to_bit_arr"]


def bit_arr_to_bytes(arr: np.ndarray) -> bytes:
    """
    :param arr: 1-d uint8 numpy array
    :return: bytes, one element in arr maps to one bit in output bytes, padding in the left
    """
    n = arr.size
    pad_width = (8 - n % 8) % 8
    arr = np.pad(arr, pad_width=((pad_width, 0),), constant_values=0)
    bs = bytes(np.packbits(arr).tolist())

    return int_to_bytes(n) + bs


def bytes_to_bit_arr(data: bytes) -> np.ndarray:
    """
    :param data: bytes, first 4 bytes is array length, and the remaining is array data
    :return:
    """
    prefix_length = 4
    n = bytes_to_int(data[:prefix_length])
    while (n + 7) // 8 != len(data) - prefix_length:
        prefix_length += 4
    arr = np.array(list(data[prefix_length:]), dtype=np.uint8)
    res = np.unpackbits(arr)[-n:]
    return res
