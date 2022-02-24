from typing import Optional

import numpy as np

from .. import base
from ..cipher import shake
from ..pair import Pair
from ..serialize import bit_arr_to_bytes, bytes_to_bit_arr, int_to_bytes
from ..utils import pack, rand_binary_arr


class Sender(object):
    _pair: Pair
    _s: np.ndarray
    _q: Optional[np.ndarray]
    _index: int = 0
    _codewords: int  # codewords length, matrix q's width, should be greater equal than 128 (for security)

    def __init__(self, pair: Pair, codewords: int = 128):
        self._pair = pair
        if codewords < 128:
            raise ValueError(
                f"codewords {codewords} is too small,"
                f" it should be greater equal than 128 to ensure security"
            )
        self._codewords = codewords

    def prepare(self):
        # s (select bits for prepare stage)
        self._s = rand_binary_arr(self._codewords)
        # q (keys)
        self._q = None
        m = 0
        q_cols = []

        if self._codewords == 128:
            # q (keys)
            for i, b in enumerate(self._s):
                q_col = base.recv(self._pair, b)  # column of q, bytes of 0,1 arr
                if m == 0:
                    m = len(q_col)
                else:
                    assert m == len(
                        q_col
                    ), f"base OT message length should be all the same, but the round {i} is not"
                q_cols.append(q_col)

        else:
            # use ote instead of ot
            from psi.extension import Receiver

            receiver = Receiver(self._pair, self._s, 128)
            receiver.prepare()

            for i in range(self._s.size):
                q_col = receiver.recv()
                if m == 0:
                    m = len(q_col)
                else:
                    assert m == len(
                        q_col
                    ), f"base OT message length should be all the same, but the round {i} is not"
                q_cols.append(q_col)
        self._pair.barrier()

        self._q = np.vstack([bytes_to_bit_arr(col) for col in q_cols]).T

    @property
    def max_count(self) -> int:
        if self._q is None:
            return 0
        else:
            return self._q.shape[0]

    def is_available(self) -> bool:
        return self._q is not None and self._index < self._q.shape[0]

    def send(self, m0: bytes, m1: bytes):
        if not self.is_available():
            raise ValueError(
                "The sender is not available now. "
                "The sender may be not prepared or have used all ot keys"
            )

        key0 = int_to_bytes(self._index) + bit_arr_to_bytes(self._q[self._index, :])
        key1 = int_to_bytes(self._index) + bit_arr_to_bytes(
            self._q[self._index, :] ^ self._s
        )

        cipher_m0 = shake.encrypt(key0, m0)
        cipher_m1 = shake.encrypt(key1, m1)

        self._pair.send(pack(cipher_m0, cipher_m1))
        self._index += 1
