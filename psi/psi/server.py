import random
import logging
from typing import List

from .cuckoo import position_hash
from ..oprf import Server as OprfServer
from ..pair import Pair


_logger = logging.getLogger()


class Server(object):
    def __init__(self, pair: Pair, words: List[bytes]):
        self.s = 5
        self.words = words

        self.oprf_server = OprfServer(pair, 512)
        self.pair = pair

    def prepare(self):
        self.oprf_server.prepare()

    def intersect(self):
        n = self.oprf_server.max_count - self.s
        for i in range(3):
            words = random.sample(self.words, len(self.words))
            for word in words:
                h = position_hash(i + 1, word, n)
                val = self.oprf_server.eval(h, word + bytes([i + 1]))
                _logger.debug(
                    f"hash index {i + 1}, table position {h}, word {int.from_bytes(word, 'big')}, val {val.hex()}"
                )
                self.pair.send(val)
            self.pair.send(b"end")

        for i in range(self.s):
            words = random.sample(self.words, len(self.words))
            for word in words:
                val = self.oprf_server.eval(n + i, word)
                _logger.debug(
                    f"table position {n + i}, "
                    f"word {int.from_bytes(word, 'big')}, val {val.hex()}"
                )
                self.pair.send(val)
        self.pair.send(b"end")

        res: List[bytes] = []
        while True:
            word = self.pair.recv()
            if word == b"end":
                break
            res.append(word)

        return res
