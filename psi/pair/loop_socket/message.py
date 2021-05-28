from typing import NamedTuple

from ...serialize import int_to_bytes, bytes_to_int


class Message(NamedTuple):
    id: int
    data: bytes

    def encode(self) -> bytes:
        body = int_to_bytes(self.id) + self.data
        return body

    @classmethod
    def decode(cls, body: bytes) -> 'Message':
        id = bytes_to_int(body[:4])
        res = cls(data=body[4:], id=id)
        return res
