import os

import yaml

_config_path = os.getenv("PSI_CONFIG", "config/config.yaml")

with open(_config_path, mode="r", encoding="utf-8") as f:
    _c = yaml.safe_load(f)

host: str = _c.get("host")
port: int = _c.get("port")
data: str = _c.get("data")
result: str = _c.get("result")
