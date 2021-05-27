import logging
import random
from typing import List

from .cuckoo import CuckooHashTable
from ..oprf import Client as OprfClient
from ..pair import Pair

_logger = logging.getLogger()


class Client(object):
    def __init__(self, pair: Pair, words: List[bytes]):
        self.n = int(1.2 * len(words))
        s = 5
        cuckoo = CuckooHashTable(self.n, s)
        for word in words:
            cuckoo.update(word)
        self.table = cuckoo.table
        self.stash = cuckoo.stash
        self.table_hash_index = cuckoo.table_hash_index

        dummy_table = []
        for key, hash_index in zip(self.table, self.table_hash_index):
            if key is None:
                key = random.getrandbits(64).to_bytes(8, "big")
            else:
                key = key + bytes([hash_index])
            dummy_table.append(key)
        for key in self.stash:
            if key is None:
                key = random.getrandbits(64).to_bytes(8, "big")
            dummy_table.append(key)

        self.pair = pair
        self.oprf_client = OprfClient(pair, dummy_table, 512)

    def prepare(self):
        self.oprf_client.prepare()

    def intersect(self) -> List[bytes]:
        peer_tables = [{}, {}, {}]
        peer_stash = {}
        for table in peer_tables:
            while True:
                key = self.pair.recv()
                if key == b"end":
                    break
                table[key] = None
        while True:
            key = self.pair.recv()
            if key == b"end":
                break
            peer_stash[key] = None

        res = []
        for i, (key, hash_index) in enumerate(zip(self.table, self.table_hash_index)):
            if key is not None:
                peer_table = peer_tables[hash_index - 1]
                local_val = self.oprf_client.eval(i)
                _logger.debug(f"hash index {hash_index}, table position {i}, "
                             f"word {int.from_bytes(key, 'big')}, val {local_val.hex()}")
                if local_val in peer_table:
                    res.append(key)
                    self.pair.send(key)

        for i, key in enumerate(self.stash):
            if key is not None:
                local_val = self.oprf_client.eval(i + self.n)
                _logger.debug(f"table position {i + self.n}, "
                             f"word {int.from_bytes(key, 'big')}, val {local_val.hex()}")
                if local_val in peer_stash:
                    res.append(key)
                    self.pair.send(key)
        self.pair.send(b"end")
        return res
