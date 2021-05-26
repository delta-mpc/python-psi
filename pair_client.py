from psi.pair import make_pair

if __name__ == '__main__':
    local = ("127.0.0.1", 1234)
    peer = ("127.0.0.1", 2345)
    with make_pair(local, peer, timeout=30) as pair:
        pair.send("你好，server".encode("utf-8"))
        pair.send("你好，server2".encode("utf-8"))
        msg = pair.recv().decode("utf-8")
        print(msg)
        print(pair.local_addr)
        print(pair.peer_addr)
