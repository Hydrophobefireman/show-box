import json
import os

CONFIG_FILE = os.path.join(os.getcwd(), ".config.json")


def open_and_parse(fn: str) -> dict:
    if os.path.isfile(fn):
        with open(fn) as f:
            return json.load(f)
    return None


def set_env_vars():
    data = open_and_parse(CONFIG_FILE)
    if data:
        for k, v in data.items():
            os.environ[k] = v
