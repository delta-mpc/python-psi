import queue
import selectors
import socket
import threading
import time
from typing import Union, Tuple, Optional

from ..pair import Pair, Address
from ...serialize import int_to_bytes, bytes_to_int

AddrType = Union[Address, Tuple[str, int]]


class _ServerThread(threading.Thread):
    def __init__(self, local: AddrType, peer: AddrType):
        super(_ServerThread, self).__init__()
        self._local = local
        self._peer = peer

        self._res_queue = queue.Queue()
        self._stop_event = threading.Event()

        self._sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(self._local)
        self._sock.setblocking(False)
        self._sock.listen(10)

        self._sel = selectors.DefaultSelector()
        self._sel.register(self._sock, selectors.EVENT_READ)

    def run(self):
        while not self._stop_event.is_set():
            events = self._sel.select(0)
            if len(events) > 0:
                sock, addr = self._sock.accept()
                if addr[0] == self._peer[0]:
                    self._res_queue.put((sock, addr))
                else:
                    sock.close()

    def terminate(self):
        self._stop_event.set()
        self._sock.close()

    def get_sock_addr(
        self, block: bool = True, timeout: Optional[float] = None
    ) -> Tuple[socket.socket, socket.socket]:
        return self._res_queue.get(block=block, timeout=timeout)


class SocketPair(Pair):
    def __init__(self, local: AddrType, peer: AddrType, timeout: float):
        if not isinstance(local, Address):
            local = Address(*local)
        if not isinstance(peer, Address):
            peer = Address(*peer)
        self._local = local
        self._peer = peer
        self._timeout = timeout

        self._sock = self._connect(timeout * 3)
        self._sock.settimeout(timeout)

    def _connect(self, timeout: float) -> socket.socket:
        end = time.time() + timeout
        ts = int(time.time() * 1000)
        server_thread = _ServerThread(self._local, self._peer)
        server_thread.start()

        client_sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client_sock.settimeout(timeout)
        try:
            client_sock.connect(self._peer)
            try:
                peer_sock, _ = server_thread.get_sock_addr(block=False)
                client_sock.send(str(ts).encode("utf-8"))
                peer_ts = int(peer_sock.recv(1024).decode("utf-8"))
                if ts < peer_ts:
                    raise ConnectionRefusedError
                else:
                    raise queue.Empty
            except queue.Empty:
                server_thread.terminate()
                server_thread.join()
                client_sock.close()

                peer_sock = socket.socket(
                    family=socket.AF_INET, type=socket.SOCK_STREAM
                )
                peer_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                peer_sock.bind(self._local)
                peer_sock.connect(self._peer)
                return peer_sock

        except ConnectionRefusedError:
            now = time.time()
            while now < end:
                sock, addr = server_thread.get_sock_addr(timeout=end - now)
                if addr[1] == self._peer[1]:
                    server_thread.terminate()
                    server_thread.join()
                    return sock
                else:
                    sock.close()
                now = time.time()
        raise TimeoutError(f"connect to peer failed after {timeout} seconds")

    def send(self, data: bytes):
        self._sock.sendall(int_to_bytes(len(data)) + data)

    def recv(self) -> bytes:
        length = bytes_to_int(self._recv(4))
        data = self._recv(length)
        return data

    def _recv(self, count: int) -> bytes:
        buffer = bytearray(count)
        view = memoryview(buffer)

        while count > 0:
            n = self._sock.recv_into(view, count)
            view = view[n:]
            count -= n

        return bytes(buffer)

    def barrier(self):
        self.send(b"barrier")
        msg = self.recv()
        assert msg == b"barrier"

    def close(self):
        self._sock.close()
