from typing import Union, Tuple

from .loop_socket import LoopSocketPair
from .pair import Pair, Address
from .socket import SocketPair

AddrType = Union[Address, Tuple[str, int]]


def make_pair(local: AddrType = Address(), peer: AddrType = Address(),
              timeout: int = 10, type: str = "socket") -> Pair:
    if type == "socket":
        return SocketPair(local, peer, timeout)
    elif type == "loop":
        return LoopSocketPair(local, peer, timeout)
    raise ValueError(f"unsupported pair type: {type}")
