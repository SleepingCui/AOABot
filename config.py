import logging
import os
from dataclasses import dataclass, field

import yaml

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.yml")

DEFAULT_TEMPLATE = """\
token: "your-token-here"

prefix: "!"

allowed_commands:
  - analyze
  - decode
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
    url: str = "http://127.0.0.1:7890"


@dataclass
class Config:
    token: str = "your-token-here"
    prefix: str = "!"
    allowed_commands: list = field(
        default_factory=lambda: ["analyze", "decode", "ping", "help", "botinfo", "reload", "shutdown"]
    )
    owner_ids: list = field(default_factory=list)
    proxy: ProxyConfig = field(default_factory=ProxyConfig)

    @property
    def allowed_set(self) -> set:
        return set(self.allowed_commands)

    def to_dict(self) -> dict:
        return {
            "token": self.token,
            "prefix": self.prefix,
            "allowed_commands": list(self.allowed_commands),
            "owner_ids": list(self.owner_ids),
            "proxy": {
                "enabled": self.proxy.enabled,
                "url": self.proxy.url,
            },
        }


def _default_config_yaml() -> str:
    return DEFAULT_TEMPLATE


def ensure_config(path: str = CONFIG_PATH) -> bool:
    if os.path.exists(path):
        return False

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(_default_config_yaml())
    logger.warning("Created default config at %s. Please fill in your token before restarting.", path)
    return True


def load_config(path: str = CONFIG_PATH) -> Config:
    if ensure_config(path):
        raise SystemExit(1)

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
            url=str(proxy_raw.get("url", "http://127.0.0.1:7890") or "").strip(),
        ),
    )