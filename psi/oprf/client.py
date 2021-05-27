from typing import Sequence

import numpy as np
from Crypto.Hash import SHAKE256, SHA256

from .. import base
from ..extension import Sender
from ..pair import Pair
from ..serialize import bytes_to_bit_arr, int_to_bytes, bit_arr_to_bytes
from ..utils import rand_binary_arr


class Client(object):
    _pair: Pair
    _r: np.ndarray
    _t: np.ndarray
    _codewords: int

    def __init__(self, pair: Pair, r: Sequence[bytes], codewords: int = 128):
        self._pair = pair
        if codewords < 128:
            raise ValueError(f"codewords {codewords} is too small,"
                             f" it should be greater equal than 128 to ensure security")
        self._codewords = codewords

        self._r = np.empty((len(r), self._codewords), dtype=np.uint8)
        codewords_bytes = int_to_bytes(self._codewords)
        for i, word in enumerate(r):
            word_arr = bytes_to_bit_arr(codewords_bytes + self._encode(word))
            self._r[i] = word_arr

    def _encode(self, data: bytes):
        shake = SHAKE256.new(data)
        length = (self._codewords + 7) // 8
        return shake.read(length)

    def prepare(self):
        m = self._r.shape[0]
        self._t = rand_binary_arr((m, self._codewords))
        u = self._t ^ self._r
        if self._codewords == 128:
            for i in range(self._codewords):
                ti_bytes = bit_arr_to_bytes(self._t[:, i])
                ui_bytes = bit_arr_to_bytes(u[:, i])
                base.send(self._pair, ti_bytes, ui_bytes)
        else:
            sender = Sender(self._pair, 128)
            sender.prepare()

            for i in range(self._codewords):
                ti_bytes = bit_arr_to_bytes(self._t[:, i])
                ui_bytes = bit_arr_to_bytes(u[:, i])
                sender.send(ti_bytes, ui_bytes)
        self._pair.barrier()

    @property
    def max_count(self) -> int:
        if self._r is None:
            return 0
        return self._r.shape[0]

    def eval(self, i: int) -> bytes:
        if i >= self.max_count:
            raise IndexError(f"i is greater than oprf instance count {self.max_count}")
        ti = self._t[i, :]
        return SHA256.new(bit_arr_to_bytes(ti)[4:]).digest()
