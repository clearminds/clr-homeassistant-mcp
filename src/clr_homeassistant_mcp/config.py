"""Configuration for Home Assistant MCP Server."""

import json
import logging
from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

CREDS_PATH = Path.home() / ".config" / "homeassistant" / "credentials.json"


class HAInstance:
    """A single Home Assistant instance.

    Attributes:
        name: Identifier for this instance (e.g. "home", "office").
        url: Base URL of the Home Assistant server (trailing slash stripped).
        token: Long-lived access token for authentication.
    """

    def __init__(self, name: str, url: str, token: str) -> None:
        self.name = name
        self.url = url.rstrip("/")
        self.token = token


class Settings(BaseSettings):
    """Settings loaded from environment variables.

    Attributes:
        ha_transport: MCP transport mode ("stdio" or "http").
        ha_log_level: Logging level name (e.g. "INFO", "DEBUG").
        ha_url: Home Assistant URL for single-instance configuration.
        ha_token: Long-lived access token for single-instance configuration.
    """

    ha_transport: str = "stdio"
    ha_log_level: str = "INFO"
    ha_read_only: bool = False

    @field_validator("ha_read_only", mode="before")
    @classmethod
    def _empty_str_to_false(cls, v: Any) -> Any:
        if v == "":
            return False
        return v

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

        Returns:
            A mapping of instance names to HAInstance objects.  Returns an
            empty dict if no instances are configured.
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
        """Get the default instance name from credentials.json.

        Returns:
            The default instance name.  Falls back to the first instance key
            if no explicit default is set, or ``"default"`` if no credentials
            file exists.
        """
        if CREDS_PATH.exists():
            data: dict[str, Any] = json.loads(CREDS_PATH.read_text())
            if "default" in data:
                return data["default"]
            if "instances" in data:
                return next(iter(data["instances"]))
        return "default"
