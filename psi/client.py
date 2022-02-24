from psi import config
from psi.pair import make_pair, Address
from psi.psi import Client
import logging


def start_client(address: str):
    peer_host, peer_port_str = address.split(":", 2)
    peer_port = int(peer_port_str)

    local_address = Address(config.host, config.port)
    peer_address = Address(peer_host, peer_port)

    with open(config.data, mode="r", encoding="utf-8") as f:
        data = [val.rstrip().encode("utf-8") for val in f]

    with make_pair(local_address, peer_address) as pair:
        client = Client(pair, data)

        logging.info("start prepare")
        client.prepare()  # prepare stage
        logging.info("finish prepare")

        logging.info("start intersection")
        res = client.intersect()  # intersect stage, res is the intersection
        logging.info("finish intersection")

        res_strs = sorted([val.decode("utf-8") for val in res])
        with open(config.result, mode="w", encoding="utf-8") as f:
            for line in res_strs:
                f.write(line)
                f.write("\n")

        pair.barrier()
