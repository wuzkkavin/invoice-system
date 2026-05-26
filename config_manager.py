import os
import sys
import json


def _get_config_paths():
    frozen = getattr(sys, 'frozen', False)
    paths = []
    # 1) exe 同目錄 (dist/)
    if frozen:
        paths.append(os.path.join(os.path.dirname(sys.executable), "config.json"))
    # 2) 程式碼目錄 (專案根目錄)
    paths.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json"))
    return paths


CONFIG_PATHS = _get_config_paths()

DEFAULT_CONFIG = {
    "OPENAI_API_KEY": "",
    "GEMINI_API_KEY": "",
    "MINIMAX_API_KEY": ""
}


def load_config():
    for p in CONFIG_PATHS:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                for k in DEFAULT_CONFIG:
                    cfg.setdefault(k, "")
                return cfg
            except (json.JSONDecodeError, OSError):
                pass
    return dict(DEFAULT_CONFIG)


def save_config(config):
    # 存到第一個存在的路徑；都不存在則存到最後一個（專案根目錄）
    p = next((x for x in CONFIG_PATHS if os.path.exists(os.path.dirname(x))), CONFIG_PATHS[-1])
    with open(p, "w", encoding="utf-8") as f:
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
