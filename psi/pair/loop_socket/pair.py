from typing import Tuple, Union

from .loop import Loop
from .message import Message
from ..pair import Pair, Address

AddrType = Union[Address, Tuple[str, int]]


class LoopSocketPair(Pair):
    def __init__(self, local: AddrType, peer: AddrType, timeout: float):
        if not isinstance(local, Address):
            local = Address(*local)
        if not isinstance(peer, Address):
            peer = Address(*peer)
        self._local = local
        self._peer = peer
        self._timeout = timeout

        self._loop = Loop(local, peer)
        self._id, self._pipe = self._loop.register(3 * timeout)

    def send(self, data: bytes):
        msg = Message(data=data, id=self._id)
        self._pipe.send(msg, block=False)

    def recv(self) -> bytes:
        msg = self._pipe.recv(block=True, timeout=self._timeout)
        return msg.data

    def barrier(self):
        self.send("barrier".encode("utf-8"))
        self._pipe.join()
        msg = self.recv().decode("utf-8")
        assert msg == "barrier"

    def close(self):
        self._loop.unregister(self._id)
