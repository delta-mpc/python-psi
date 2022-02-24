import argparse
import logging
import os

_config_str = """
log:
  level: "INFO"

host: "127.0.0.1"
port: 1234
data: "data.txt"
result: "result.txt"

"""

logging.basicConfig(
    format="%(asctime)s.%(msecs)03d - %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)


def init():
    config_file = os.getenv("PSI_CONFIG", "config/config.yaml")
    config_dir, _ = os.path.split(config_file)
    if not os.path.exists(config_dir):
        os.makedirs(config_dir, exist_ok=True)

    if not os.path.exists(config_file):
        with open(config_file, mode="w", encoding="utf-8") as f:
            f.write(_config_str)


def main():
    parser = argparse.ArgumentParser(usage="python psi")
    sub_parsers = parser.add_subparsers(
        dest="action",
        title="subcommands",
        description="valid actions",
        help="'init' to init psi config file, 'server' to start psi server, 'client' to start psi client",
    )
    sub_parsers.add_parser("init", help="init psi config file")
    server_parser = sub_parsers.add_parser("server", help="start psi server")
    server_parser.add_argument("address", type=str, help="peer address")
    client_parser = sub_parsers.add_parser("client", help="start psi client")
    client_parser.add_argument("address", type=str, help="peer address")
    args = parser.parse_args()

    if args.action == "server":
        from psi.server import start_server

        start_server(args.address)
    elif args.action == "client":
        from psi.client import start_client

        start_client(args.address)
    elif args.action == "init":
        init()
