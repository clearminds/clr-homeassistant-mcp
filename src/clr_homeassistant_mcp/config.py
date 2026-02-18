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
        """Load HA instances from env vars or credentials.json.

        Priority order:
        1. ~/.config/homeassistant/credentials.json - checked FIRST
        2. Environment variables (HA_URL, HA_TOKEN) - override

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

        # 1. FIRST: Load from environment variables (base/fallback)
        if self.ha_url and self.ha_token:
            instances["default"] = HAInstance("default", self.ha_url, self.ha_token)

        # 2. THEN: Override with credentials.json file (takes priority)
        if CREDS_PATH.exists():
            try:
                data: dict[str, Any] = json.loads(CREDS_PATH.read_text())

                if "instances" in data:
                    instances.clear()
                    for name, cfg in data["instances"].items():
                        instances[name] = HAInstance(name, cfg["url"], cfg["token"])
                    logger.info(f"Loaded {len(instances)} Home Assistant instance(s) from {CREDS_PATH}")
                elif data.get("url") and data.get("token"):
                    # Legacy single-instance format
                    instances["default"] = HAInstance("default", data["url"], data["token"])
                    logger.info(f"Loaded Home Assistant credentials from {CREDS_PATH}")
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load {CREDS_PATH}: {e}")

        if not instances:
            logger.warning(
                "No Home Assistant instances configured. Set HA_URL/HA_TOKEN env vars "
                f"or create {CREDS_PATH}"
            )

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
