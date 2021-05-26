import errno
import logging
import queue
import selectors
import socket
import threading
import time
from collections import defaultdict
from enum import IntEnum
from typing import Optional, Union, Tuple, List, Dict

from .message import Message
from .pipe import make_pipe, Pipe
from ..pair import Address
from ...serialize import bytes_to_int, int_to_bytes

AddrType = Union[Address, Tuple[str, int]]

_logger = logging.getLogger()


class LoopState(IntEnum):
    INIT = 0
    SERVER_SUCCESS = 1
    CLIENT_SUCCESS = 2
    BOTH_SUCCESS = 3
    READY = 4


class LoopThread(threading.Thread):
    def __init__(self, local: AddrType, peer: AddrType):
        super(LoopThread, self).__init__(daemon=True)
        self._local = local
        self._peer = peer

        self._sel = selectors.DefaultSelector()
        self._mode: Optional[str] = None
        self._sock: Optional[socket.socket] = None

        self._stop_event = threading.Event()
        self._connect_event = threading.Event()

        self._register_count = 0
        self._registry: Dict[int, Pipe] = {}
        self._id_counter = 0
        self._register_lock = threading.Lock()

        self._send_buffer: List[Message] = []
        self._recv_buffer: Dict[int, List[Message]] = defaultdict(list)

    @property
    def local_addr(self):
        return self._local

    @property
    def peer_addr(self):
        return self._peer

    def register(self, timeout: Optional[float] = None) -> Tuple[int, Pipe]:
        if self._connect_event.wait(timeout):
            with self._register_lock:
                local_id = self._id_counter
                self._id_counter += 1

                local, remote = make_pipe()
                self._registry[local_id] = local
            return local_id, remote
        raise TimeoutError(f"unable to make connection with peer after {timeout} seconds")

    def unregister(self, local_id: int):
        with self._register_lock:
            self._registry.pop(local_id)

    def _fetch(self):
        with self._register_lock:
            for pipe in self._registry.values():
                n = 50
                while n > 0:
                    try:
                        msg = pipe.recv(block=False)
                        self._send_buffer.append(msg)
                        n -= 1
                        _logger.debug(f"fetch msg: {msg}")
                    except queue.Empty:
                        break

    def _dispatch(self):
        with self._register_lock:
            for i, pipe in self._registry.items():
                buffer = self._recv_buffer[i]
                if len(buffer) > 0:
                    for msg in buffer:
                        pipe.send(msg, block=False)
                        _logger.debug(f"dispatch msg: {msg}")
                    self._recv_buffer[i] = []

    def _send(self):
        if len(self._send_buffer) > 0:
            _logger.debug(f"send buffer: {self._send_buffer}")
            words = []
            ids = []
            for msg in self._send_buffer:
                _logger.debug(f"send msg: {msg}")
                data = msg.encode()
                words.append(int_to_bytes(len(data)) + data)
                ids.append(msg.id)

            frame = b"".join(words)
            self._sock.sendall(frame)
            for i in ids:
                pipe = self._registry[i]
                pipe.task_done()
            self._send_buffer = []

    def _recv(self):
        if len(self._registry) == 0:
            return

        data_arr = []
        while True:
            try:
                data = self._sock.recv(4096)
                if not data:
                    break
                data_arr.append(data)
            except BlockingIOError as e:
                if errno.errorcode[e.errno] == "EAGAIN":
                    break
                raise e

        # parse
        if len(data_arr) > 0:
            data = b"".join(data_arr)
            n = 0
            length = 0
            while n < len(data):
                if length == 0:
                    length = bytes_to_int(data[n: n + 4])
                    n += 4
                msg = Message.decode(data[n: n + length])
                n += length
                self._recv_buffer[msg.id].append(msg)
                _logger.debug(f"recv msg: {msg}")
                length = 0

    def run(self):
        server_sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.setblocking(False)
        server_sock.bind(self._local)
        server_sock.listen(10)

        client_sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client_sock.setblocking(False)
        try:
            client_sock.connect(self._peer)
        except BlockingIOError as e:
            if errno.errorcode[e.errno] != "EINPROGRESS":
                raise e

        self._sel.register(server_sock, selectors.EVENT_READ, data="server")
        self._sel.register(client_sock, selectors.EVENT_WRITE, data="client")

        ts = int(time.time() * 1000)
        state = LoopState.INIT

        try:
            # connect loop
            while not self._stop_event.is_set() and state != LoopState.READY:
                events = self._sel.select(0)
                for key, event in events:
                    if key.data == "server" and (event & selectors.EVENT_READ) \
                            and state in [LoopState.INIT, LoopState.SERVER_SUCCESS, LoopState.CLIENT_SUCCESS]:
                        sock, addr = server_sock.accept()
                        if addr[0] == self._peer[0] and (state != 1 or addr[1] == self._peer[1]):
                            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                            sock.setblocking(False)
                            if state == LoopState.INIT:
                                self._sel.register(sock, selectors.EVENT_READ, data="peer")
                                state = LoopState.SERVER_SUCCESS
                            elif state == LoopState.SERVER_SUCCESS:
                                self._sel.register(sock, selectors.EVENT_READ | selectors.EVENT_WRITE, data="pair")
                                self._sock = sock
                                self._mode = "server"
                                state = LoopState.READY
                                server_sock.close()
                                self._sel.unregister(server_sock)
                            elif state == LoopState.CLIENT_SUCCESS:
                                self._sel.register(sock, selectors.EVENT_READ, data="peer")
                                state = LoopState.BOTH_SUCCESS
                    elif key.data == "client" and (event & selectors.EVENT_WRITE) \
                            and state in [LoopState.INIT, LoopState.SERVER_SUCCESS,
                                          LoopState.CLIENT_SUCCESS, LoopState.READY]:
                        if state in [LoopState.INIT, LoopState.SERVER_SUCCESS]:
                            err = client_sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
                            if err == 0:
                                if state == LoopState.INIT:
                                    state = LoopState.CLIENT_SUCCESS
                                elif state == LoopState.SERVER_SUCCESS:
                                    state = LoopState.BOTH_SUCCESS
                            elif errno.errorcode[err] == "EINPROGRESS":
                                continue
                            else:
                                self._sel.unregister(client_sock)
                                client_sock.close()
                        elif state == LoopState.CLIENT_SUCCESS:
                            client_sock.close()
                            self._sel.unregister(client_sock)
                            server_sock.close()
                            self._sel.unregister(server_sock)

                            sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
                            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                            sock.setblocking(False)
                            sock.bind(self._local)
                            try:
                                sock.connect(self._peer)
                            except BlockingIOError as e:
                                if errno.errorcode[e.errno] != "EINPROGRESS":
                                    raise e
                            self._sel.register(sock, selectors.EVENT_WRITE, data="pair")
                        else:
                            client_sock.sendall(str(ts).encode("utf-8"))
                            client_sock.close()
                            self._sel.unregister(client_sock)
                    elif key.data == "peer" and (event & selectors.EVENT_READ) and state == LoopState.BOTH_SUCCESS:
                        data = key.fileobj.recv()
                        peer_ts = int(data.decode("utf-8"))
                        if ts < peer_ts:
                            state = LoopState.SERVER_SUCCESS
                        else:
                            state = LoopState.CLIENT_SUCCESS
                        key.fileobj.close()
                        self._sel.unregister(key.fileobj)
                    elif key.data == "pair" and (event & selectors.EVENT_WRITE) and state == LoopState.CLIENT_SUCCESS:
                        err = key.fileobj.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
                        if err == 0:
                            self._sel.modify(key.fileobj, selectors.EVENT_READ | selectors.EVENT_WRITE, data="pair")
                            self._sock = key.fileobj
                            self._mode = "client"
                            state = LoopState.READY
                        elif errno.errorcode[err] == "EINPROGRESS":
                            continue
                        else:
                            key.fileobj.close()
                            self._sel.unregister(key.fileobj)
            # notify main loop that connection is made
            self._connect_event.set()
            # main loop
            while not self._stop_event.is_set():
                # fetch msg from local pairs
                self._fetch()
                events = self._sel.select(0)
                for key, event in events:
                    if key.data == "pair" and (event & selectors.EVENT_WRITE):
                        self._send()
                    if key.data == "pair" and (event & selectors.EVENT_READ):
                        self._recv()
                # dispatch msg to local pairs
                self._dispatch()
        finally:
            if self._sock is not None:
                self._sock.close()
                self._sel.unregister(self._sock)
            self._sel.close()


class Loop(object):
    _pool = {}
    _lock = threading.Lock()

    def __init__(self, local: AddrType, peer: AddrType):
        key = (*local, *peer)
        with self._lock:
            if key not in self._pool or (not self._pool[key].is_alive()):
                loop = LoopThread(local, peer)
                loop.start()
                self._pool[key] = loop
            self.loop: LoopThread = self._pool[key]

    @property
    def local_addr(self):
        return self.loop.local_addr

    @property
    def peer_addr(self):
        return self.loop.peer_addr

    def register(self, timeout: Optional[float] = None) -> Tuple[int, Pipe]:
        return self.loop.register(timeout)

    def unregister(self, local_id: int):
        return self.loop.unregister(local_id)
