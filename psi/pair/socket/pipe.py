import queue
from typing import Optional, Any, Tuple


class Pipe(object):
    def __init__(self, send_queue: queue.Queue, recv_queue: queue.Queue):
        self._send_queue = send_queue
        self._recv_queue = recv_queue

    def send(self, item: Any, block: bool = True, timeout: Optional[float] = None):
        self._send_queue.put(item, block, timeout)

    def recv(self, block: bool = True, timeout: Optional[float] = None):
        return self._recv_queue.get(block, timeout)

    def task_done(self):
        self._recv_queue.task_done()

    def join(self):
        self._send_queue.join()


def make_pipe() -> Tuple[Pipe, Pipe]:
    q1, q2 = queue.Queue(), queue.Queue()

    local = Pipe(q1, q2)
    remote = Pipe(q2, q1)
    return local, remote
