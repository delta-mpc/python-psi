import logging

from psi.pair import make_pair, Address
from psi.psi import Server

logging.basicConfig(
    format="%(asctime)s.%(msecs)03d - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO
)

if __name__ == '__main__':
    host = "127.0.0.1"
    local_port = 2345
    peer_port = 1234
    local = Address(host, local_port)
    peer = Address(host, peer_port)

    words = [i.to_bytes(4, "big") for i in range(500, 1000)]

    with make_pair(local, peer) as pair:
        server = Server(pair, words)
        logging.info("start prepare")
        server.prepare()
        logging.info("finish prepare")

        logging.info("start intersection")
        res = server.intersect()
        logging.info("finish intersection")
        print(sorted([int.from_bytes(val, "big") for val in res]))

        pair.barrier()
