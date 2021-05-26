from psi.pair import make_pair

if __name__ == '__main__':
    local = ("127.0.0.1", 2345)
    peer = ("127.0.0.1", 1234)
    with make_pair(local, peer, timeout=30) as pair:
        msg_bytes = pair.recv()
        msg = msg_bytes.decode("utf-8")
        print(msg)
        msg_bytes = pair.recv()
        msg = msg_bytes.decode("utf-8")
        print(msg)

        pair.send("你好，client".encode("utf-8"))
        print(pair.local_addr)
        print(pair.peer_addr)
