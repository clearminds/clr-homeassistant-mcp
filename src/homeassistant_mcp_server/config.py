"""Configuration for Home Assistant MCP Server."""

import json
import logging
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

CREDS_PATH = Path.home() / ".config" / "homeassistant" / "credentials.json"


class HAInstance:
    """A single Home Assistant instance."""

    def __init__(self, name: str, url: str, token: str) -> None:
        self.name = name
        self.url = url.rstrip("/")
        self.token = token


class Settings(BaseSettings):
    """Settings loaded from environment variables."""

    ha_transport: str = "stdio"
    ha_log_level: str = "INFO"

    # Single-instance env vars (used if credentials.json has no "instances" key)
    ha_url: str = ""
    ha_token: str = ""

    def load_instances(self) -> dict[str, HAInstance]:
        """Load HA instances from credentials.json or env vars.

        Supports two formats in credentials.json:

        Single instance (legacy):
            {"url": "https://...", "token": "..."}

        Multi-instance:
            {
                "instances": {
                    "home": {"url": "https://...", "token": "..."},
                    "office": {"url": "https://...", "token": "..."}
                },
                "default": "home"
            }
        """
        instances: dict[str, HAInstance] = {}

        if CREDS_PATH.exists():
            data: dict[str, Any] = json.loads(CREDS_PATH.read_text())

            if "instances" in data:
                for name, cfg in data["instances"].items():
                    instances[name] = HAInstance(name, cfg["url"], cfg["token"])
                return instances

            # Legacy single-instance format
            if data.get("url") and data.get("token"):
                instances["default"] = HAInstance("default", data["url"], data["token"])
                return instances

        # Fallback to env vars
        if self.ha_url and self.ha_token:
            instances["default"] = HAInstance("default", self.ha_url, self.ha_token)

        return instances

    def get_default_name(self) -> str:
        """Get the default instance name from credentials.json."""
        if CREDS_PATH.exists():
            data: dict[str, Any] = json.loads(CREDS_PATH.read_text())
            if "default" in data:
                return data["default"]
            if "instances" in data:
                return next(iter(data["instances"]))
        return "default"
