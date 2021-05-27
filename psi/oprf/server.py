import numpy as np
from Crypto.Hash import SHAKE256, SHA256

from .. import base
from ..extension import Receiver
from ..pair import Pair
from ..serialize import bytes_to_bit_arr, int_to_bytes, bit_arr_to_bytes
from ..utils import rand_binary_arr


class Server(object):
    _pair: Pair
    _s: np.ndarray
    _q: np.ndarray
    _codewords: int

    def __init__(self, pair: Pair, codewords: int = 128):
        self._pair = pair
        if codewords < 128:
            raise ValueError(f"codewords {codewords} is too small,"
                             f" it should be greater equal than 128 to ensure security")
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
                    assert m == len(q_col), f"base OT message length should be all the same, but the round {i} is not"
                q_cols.append(q_col)
        else:
            receiver = Receiver(self._pair, self._s, 128)
            receiver.prepare()

            for i in range(self._s.size):
                q_col = receiver.recv()
                if m == 0:
                    m = len(q_col)
                else:
                    assert m == len(q_col), f"base OT message length should be all the same, but the round {i} is not"
                q_cols.append(q_col)
        self._pair.barrier()

        self._q = np.vstack([bytes_to_bit_arr(col) for col in q_cols]).T

    def _encode(self, data: bytes) -> bytes:
        shake = SHAKE256.new(data)
        length = (self._codewords + 7) // 8
        return shake.read(length)

    @property
    def max_count(self) -> int:
        if self._q is None:
            return 0
        else:
            return self._q.shape[0]

    def _eval_op(self, i: int, enc_data: np.ndarray):
        qi = self._q[i, :]
        return qi ^ (self._s & enc_data)

    def eval(self, i: int, data: bytes) -> bytes:
        if i >= self.max_count:
            raise IndexError(f"i is greater than oprf instance count {self.max_count}")
        enc_data = self._encode(data)
        enc_data_arr = bytes_to_bit_arr(int_to_bytes(self._codewords) + enc_data)

        res = self._eval_op(i, enc_data_arr)
        return SHA256.new(bit_arr_to_bytes(res)[4:]).digest()
