import os
import json

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

DEFAULT_CONFIG = {
    "OPENAI_API_KEY": "",
    "GEMINI_API_KEY": "",
    "MINIMAX_API_KEY": ""
}


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        for k in DEFAULT_CONFIG:
            cfg.setdefault(k, "")
        return cfg
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_CONFIG)


def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def _load_env_file():
    path = os.path.expanduser("~/.openai.env")
    if not os.path.exists(path):
        return
    for line in open(path, encoding="utf-8").read().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

_load_env_file()


def get_api_key(provider_key_name):
    cfg = load_config()
    val = cfg.get(provider_key_name, "")
    if val:
        return val
    return os.getenv(provider_key_name, "")
