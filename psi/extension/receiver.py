from typing import Union, Sequence

import numpy as np

from .. import base
from ..cipher import shake
from ..pair import Pair
from ..serialize import bit_arr_to_bytes, int_to_bytes
from ..utils import unpack, rand_binary_arr


class Receiver(object):
    _pair: Pair
    _r: np.ndarray  # 1-d uint8 array of 0 and 1, select bits for m OTs, length is m
    _t: np.ndarray  # OT extension matrix, shape: m * k
    _index: int = 0
    _codewords: int  # codewords length, matrix q's width, should be greater equal than 128 (for security)

    def __init__(self, pair: Pair, r: Sequence[Union[int, bool]], codewords: int = 128):
        self._pair = pair
        self._r = np.array(r, dtype=np.uint8)
        if codewords < 128:
            raise ValueError(
                f"codewords {codewords} is too small,"
                f" it should be greater equal than 128 to ensure security"
            )
        self._codewords = codewords

    def prepare(self):
        m = self._r.size
        self._t = rand_binary_arr((m, self._codewords))

        # col(u) = col(t) xor r
        u = (self._t.T ^ self._r).T
        if self._codewords == 128:
            for i in range(self._codewords):
                t_col_bytes = bit_arr_to_bytes(self._t[:, i])
                u_col_bytes = bit_arr_to_bytes(u[:, i])
                base.send(self._pair, t_col_bytes, u_col_bytes)
        else:
            from psi.extension import Sender

            sender = Sender(self._pair, 128)
            sender.prepare()
            for i in range(self._codewords):
                t_col_bytes = bit_arr_to_bytes(self._t[:, i])
                u_col_bytes = bit_arr_to_bytes(u[:, i])
                sender.send(t_col_bytes, u_col_bytes)
        self._pair.barrier()

    def is_available(self):
        return self._t is not None and self._index < self._r.size

    @property
    def max_count(self) -> int:
        if self._r is None:
            return 0
        return self._r.shape[0]

    def recv(self):
        key = int_to_bytes(self._index) + bit_arr_to_bytes(self._t[self._index, :])

        cipher_m = unpack(self._pair.recv())[self._r[self._index]]
        res = shake.decrypt(key, cipher_m)
        self._index += 1
        return res
