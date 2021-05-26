import random
import time

from psi.extension import Receiver
from psi.pair import make_pair

if __name__ == '__main__':
    local = ("127.0.0.1", 2345)
    peer = ("127.0.0.1", 5678)

    m = 1000
    r = [random.randint(0, 1) for _ in range(m)]
    t1 = time.time()
    with make_pair(local, peer, timeout=10) as pair:
        receiver = Receiver(pair, r, 256)
        receiver.prepare()
        print("prepare complete")

        for i, b in enumerate(r):
            msg = receiver.recv().decode("utf-8")
            assert msg == str(i) + str(b)
        pair.barrier()
    t2 = time.time()
    print(t2 - t1)