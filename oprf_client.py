import logging

from psi.oprf import Client
from psi.pair import make_pair, Address

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

    with make_pair(local, peer, 10) as pair:
        client = Client(pair, words, 512)
        logging.info("start preparing")
        client.prepare()
        logging.info("finish preparing")

        for i in range(1000):
            peer_val = pair.recv().hex()
            local_val = client.eval(i).hex()
            logging.info(f"{i} {local_val} {peer_val}")
            assert local_val == peer_val, f"{i}th oprf is not correct"
        pair.barrier()
