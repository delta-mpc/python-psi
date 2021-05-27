import logging

from psi.pair import make_pair, Address
from psi.psi import Client

logging.basicConfig(
    format="%(asctime)s.%(msecs)03d - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO
)

if __name__ == '__main__':
    host = "127.0.0.1"
    local_port = 1234
    peer_port = 2345
    local = Address(host, local_port)
    peer = Address(host, peer_port)

    words = [i.to_bytes(4, "big") for i in range(1000)]

    with make_pair(local, peer) as pair:
        client = Client(pair, words)
        logging.info("start prepare")
        client.prepare()
        logging.info("finish prepare")

        logging.info("start intersection")
        res = client.intersect()
        logging.info("finish intersection")
        print(sorted([int.from_bytes(val, "big") for val in res]))

        pair.barrier()
