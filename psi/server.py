import logging

from psi.pair import Address, make_pair
from psi import config
from psi.psi import Server


def start_server(address: str):
    peer_host, peer_port_str = address.split(":", 2)
    peer_port = int(peer_port_str)

    local_address = Address(config.host, config.port)
    peer_address = Address(peer_host, peer_port)

    with open(config.data, mode="r", encoding="utf-8") as f:
        data = [line.rstrip().encode("utf-8") for line in f]

    with make_pair(local_address, peer_address) as pair:
        server = Server(pair, data)  # psi server
        logging.info("start prepare")
        server.prepare()  # prepare stage
        logging.info("finish prepare")

        logging.info("start intersection")
        res = server.intersect()  # intersect stage, res is the intersection
        logging.info("finish intersection")

        # save result
        res_strs = sorted([val.decode("utf-8") for val in res])
        with open(config.result, mode="w", encoding="utf-8") as f:
            for line in res_strs:
                f.write(line)
                f.write("\n")

        pair.barrier()
