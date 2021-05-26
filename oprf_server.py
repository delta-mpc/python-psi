import logging

from psi.oprf import Server
from psi.pair import make_pair, Address

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

    with make_pair(local, peer, 10) as pair:
        server = Server(pair, 512)
        logging.info("start preparing")
        server.prepare()
        logging.info("finish preparing")

        for i in range(1000):
            word = i.to_bytes(4, "big")
            res = server.eval(i, word)
            pair.send(res)
            logging.info(f"{i} {res.hex()}")
        pair.barrier()
