import errno
import logging
import queue
import selectors
import socket
import threading
import time
from collections import defaultdict, deque
from enum import IntEnum
from typing import Optional, Union, Tuple, DefaultDict, Deque

from .message import Message
from .pipe import make_pipe, Pipe
from ..pair import Address
from ...serialize import bytes_to_int, int_to_bytes

AddrType = Union[Address, Tuple[str, int]]

_logger = logging.getLogger()


class LoopConnectState(IntEnum):
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
        self._id_counter = 0
        self._register_lock = threading.Lock()

        self._send_buffer: Deque[Tuple[Message, Pipe]] = deque()
        self._recv_buffer: DefaultDict[int, Deque[Message]] = defaultdict(deque)

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
                self._sel.register(
                    local, selectors.EVENT_READ | selectors.EVENT_WRITE, data=local_id
                )
            return local_id, remote
        raise TimeoutError(
            f"unable to make connection with peer after {timeout} seconds"
        )

    def unregister(self, local_id: int):
        pipe = None
        for key in self._sel.get_map().values():
            if key.data == local_id:
                pipe = key.fileobj
        self._sel.unregister(pipe)

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
        connect_state = LoopConnectState.INIT

        peer_sock: Optional[socket.socket] = None

        try:
            # connect loop
            while (
                not self._stop_event.is_set()
                and connect_state != LoopConnectState.READY
            ):
                events = self._sel.select(0)
                for key, event in events:
                    if (
                        key.data == "server"
                        and (event & selectors.EVENT_READ)
                        and connect_state
                        in [
                            LoopConnectState.INIT,
                            LoopConnectState.SERVER_SUCCESS,
                            LoopConnectState.CLIENT_SUCCESS,
                        ]
                    ):
                        sock, addr = server_sock.accept()
                        if addr[0] == self._peer[0] and (
                            connect_state != 1 or addr[1] == self._peer[1]
                        ):
                            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                            sock.setblocking(False)
                            if connect_state == LoopConnectState.INIT:
                                self._sel.register(
                                    sock, selectors.EVENT_READ, data="peer"
                                )
                                peer_sock = sock
                                connect_state = LoopConnectState.SERVER_SUCCESS
                            elif connect_state == LoopConnectState.SERVER_SUCCESS:
                                self._sel.register(
                                    sock,
                                    selectors.EVENT_READ | selectors.EVENT_WRITE,
                                    data="pair",
                                )
                                self._sock = sock
                                self._mode = "server"
                                connect_state = LoopConnectState.READY
                                server_sock.close()
                                self._sel.unregister(server_sock)
                                peer_sock.close()
                                self._sel.unregister(peer_sock)
                            elif connect_state == LoopConnectState.CLIENT_SUCCESS:
                                self._sel.register(
                                    sock, selectors.EVENT_READ, data="peer"
                                )
                                peer_sock = sock
                                connect_state = LoopConnectState.BOTH_SUCCESS
                    elif (
                        key.data == "client"
                        and (event & selectors.EVENT_WRITE)
                        and connect_state
                        in [
                            LoopConnectState.INIT,
                            LoopConnectState.SERVER_SUCCESS,
                            LoopConnectState.CLIENT_SUCCESS,
                            LoopConnectState.READY,
                        ]
                    ):
                        if connect_state in [
                            LoopConnectState.INIT,
                            LoopConnectState.SERVER_SUCCESS,
                        ]:
                            err = client_sock.getsockopt(
                                socket.SOL_SOCKET, socket.SO_ERROR
                            )
                            if err == 0:
                                if connect_state == LoopConnectState.INIT:
                                    connect_state = LoopConnectState.CLIENT_SUCCESS
                                elif connect_state == LoopConnectState.SERVER_SUCCESS:
                                    connect_state = LoopConnectState.BOTH_SUCCESS
                            elif errno.errorcode[err] == "EINPROGRESS":
                                continue
                            else:
                                self._sel.unregister(client_sock)
                                client_sock.close()
                        elif connect_state == LoopConnectState.CLIENT_SUCCESS:
                            client_sock.close()
                            self._sel.unregister(client_sock)
                            server_sock.close()
                            self._sel.unregister(server_sock)

                            sock = socket.socket(
                                family=socket.AF_INET, type=socket.SOCK_STREAM
                            )
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
                    elif (
                        key.data == "peer"
                        and (event & selectors.EVENT_READ)
                        and connect_state == LoopConnectState.BOTH_SUCCESS
                    ):
                        data = peer_sock.recv()
                        peer_ts = int(data.decode("utf-8"))
                        if ts < peer_ts:
                            connect_state = LoopConnectState.SERVER_SUCCESS
                        else:
                            connect_state = LoopConnectState.CLIENT_SUCCESS
                        key.fileobj.close()
                        self._sel.unregister(key.fileobj)
                    elif (
                        key.data == "pair"
                        and (event & selectors.EVENT_WRITE)
                        and connect_state == LoopConnectState.CLIENT_SUCCESS
                    ):
                        err = key.fileobj.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
                        if err == 0:
                            self._sel.modify(
                                key.fileobj,
                                selectors.EVENT_READ | selectors.EVENT_WRITE,
                                data="pair",
                            )
                            self._sock = key.fileobj
                            self._mode = "client"
                            connect_state = LoopConnectState.READY
                        elif errno.errorcode[err] == "EINPROGRESS":
                            continue
                        else:
                            key.fileobj.close()
                            self._sel.unregister(key.fileobj)
            # notify main loop that connection is made
            self._connect_event.set()
            # main loop
            while not self._stop_event.is_set():
                events = self._sel.select(0)
                for key, event in events:
                    if isinstance(key.data, int) and (event & selectors.EVENT_READ):
                        # fetch data from local pair
                        pipe: Pipe = key.fileobj
                        try:
                            msg = pipe.recv(block=False)
                            self._send_buffer.append((msg, pipe))
                            _logger.debug(f"fetch msg {msg}")
                        except queue.Empty:
                            pass
                    if isinstance(key.data, int) and (event & selectors.EVENT_WRITE):
                        local_id: int = key.data
                        pipe: Pipe = key.fileobj
                        buffer = self._recv_buffer[local_id]
                        try:
                            msg = buffer.popleft()
                            pipe.send(msg, block=False)
                            _logger.debug(f"dispatch msg {msg}")
                        except IndexError:
                            pass
                    if (
                        len(self._send_buffer) > 0
                        and key.data == "pair"
                        and (event & selectors.EVENT_WRITE)
                    ):
                        _logger.debug(f"send buffer: {self._send_buffer}")
                        words = []
                        pipes = []
                        while True:
                            try:
                                msg, pipe = self._send_buffer.popleft()
                                word = msg.encode()
                                words.append(int_to_bytes(len(word)) + word)
                                pipes.append(pipe)
                            except IndexError:
                                break
                        if len(words) > 0:
                            data = b"".join(words)
                            self._sock.sendall(data)
                            _logger.debug(f"send data {data}")
                            for pipe in pipes:
                                pipe.task_done()
                    if key.data == "pair" and (event & selectors.EVENT_READ):
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
