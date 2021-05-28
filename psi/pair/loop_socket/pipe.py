import queue
import socket
from typing import Optional, Any, Tuple


class Pipe(object):
    def __init__(self, sock: socket.socket, send_queue: queue.Queue, recv_queue: queue.Queue):
        self._sock = sock
        self._send_queue = send_queue
        self._recv_queue = recv_queue

    def send(self, item: Any, block: bool = True, timeout: Optional[float] = None):
        self._send_queue.put(item, block, timeout)
        self._sock.send(b"x")

    def fileno(self):
        return self._sock.fileno()

    def recv(self, block: bool = True, timeout: Optional[float] = None):
        self._sock.recv(1)
        return self._recv_queue.get(block, timeout)

    def task_done(self):
        self._recv_queue.task_done()

    def join(self):
        self._send_queue.join()


def make_pipe() -> Tuple[Pipe, Pipe]:
    sock1, sock2 = socket.socketpair()
    q1, q2 = queue.Queue(), queue.Queue()

    local = Pipe(sock1, q1, q2)
    remote = Pipe(sock2, q2, q1)
    return local, remote
