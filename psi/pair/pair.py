import abc
from typing import NamedTuple


class Address(NamedTuple):
    host: str = ""
    port: int = 0


class Pair(abc.ABC):
    _local: Address
    _peer: Address

    @abc.abstractmethod
    def send(self, data: bytes):
        ...

    @abc.abstractmethod
    def recv(self) -> bytes:
        ...

    @abc.abstractmethod
    def close(self):
        ...

    @abc.abstractmethod
    def barrier(self):
        ...

    @property
    def local_addr(self) -> Address:
        return self._local

    @property
    def peer_addr(self) -> Address:
        return self._peer

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
