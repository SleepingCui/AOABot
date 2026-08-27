import os
import shutil
from dataclasses import dataclass, field

import yaml

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.yml")
EXAMPLE_PATH = os.path.join(PROJECT_ROOT, "config.example.yml")

DEFAULT_TEMPLATE = """\


token: "your-token-here"

prefix: "!"

allowed_commands:
  - analyze
  - ping
  - help
  - botinfo
  - reload
  - shutdown

owner_ids: []

proxy:
  enabled: false
  url: "http://127.0.0.1:7890"
"""


@dataclass
class ProxyConfig:
    enabled: bool = False
    url: str = ""


@dataclass
class Config:
    token: str
    prefix: str = "!"
    allowed_commands: list = field(default_factory=list)
    owner_ids: list = field(default_factory=list)
    proxy: ProxyConfig = field(default_factory=ProxyConfig)

    @property
    def allowed_set(self) -> set:
        return set(self.allowed_commands)


def ensure_config(path: str = CONFIG_PATH) -> bool:

    if os.path.exists(path):
        return False

    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(EXAMPLE_PATH):
        shutil.copyfile(EXAMPLE_PATH, path)
        source = "config.example.yml"
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(DEFAULT_TEMPLATE)
        source = "built-in template"

    print("Config file does not exist. Created default config file:", path)
    return True


def load_config(path: str = CONFIG_PATH) -> Config:
    ensure_config(path)

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    token = str(raw.get("token", "") or "").strip()
    if not token or token == "your-token-here":
        raise ValueError("token is not configured")

    proxy_raw = raw.get("proxy", {}) or {}
    return Config(
        token=token,
        prefix=str(raw.get("prefix", "!") or "!"),
        allowed_commands=list(raw.get("allowed_commands", []) or []),
        owner_ids=list(raw.get("owner_ids", []) or []),
        proxy=ProxyConfig(
            enabled=bool(proxy_raw.get("enabled", False)),
            url=str(proxy_raw.get("url", "") or "").strip(),
        ),
    )
