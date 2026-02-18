"""REST client for Home Assistant API."""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class HAClient:
    """Home Assistant REST API client with Bearer token auth."""

    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._http = httpx.Client(
            base_url=f"{self.base_url}/api",
            timeout=15.0,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )

    def close(self) -> None:
        self._http.close()

    def get(self, path: str) -> Any:
        """GET request. Returns parsed JSON."""
        resp = self._http.get(path)
        resp.raise_for_status()
        return resp.json()

    def post(self, path: str, data: Any = None) -> Any:
        """POST request. Returns parsed JSON."""
        resp = self._http.post(path, json=data or {})
        resp.raise_for_status()
        return resp.json()
