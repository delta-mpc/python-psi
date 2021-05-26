import time

from psi.extension import Sender
from psi.pair import make_pair

if __name__ == '__main__':
    local = ("127.0.0.1", 5678)
    peer = ("127.0.0.1", 2345)

    t1 = time.time()
    with make_pair(local, peer, timeout=10) as pair:
        sender = Sender(pair, 256)
        sender.prepare()
        print("prepare complete")

        for i in range(sender.max_count):
            m0 = (str(i) + '0').encode("utf-8")
            m1 = (str(i) + '1').encode("utf-8")

            sender.send(m0, m1)
        pair.barrier()
    t2 = time.time()
    print(t2 - t1)
