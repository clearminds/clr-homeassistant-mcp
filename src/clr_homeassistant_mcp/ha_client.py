"""REST client for Home Assistant API."""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class HAClient:
    """Home Assistant REST API client with Bearer token auth.

    Attributes:
        base_url: Base URL of the Home Assistant server (trailing slash stripped).
    """

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
        """Close the underlying HTTP client and release resources."""
        self._http.close()

    def get(self, path: str) -> Any:
        """Send a GET request and return the parsed JSON response.

        Args:
            path: API path relative to ``/api`` (e.g. ``"/states"``).

        Returns:
            Parsed JSON response body.

        Raises:
            httpx.HTTPStatusError: If the server returns a non-2xx status code.
        """
        resp = self._http.get(path)
        resp.raise_for_status()
        return resp.json()

    def post(self, path: str, data: Any = None) -> Any:
        """Send a POST request and return the parsed JSON response.

        Args:
            path: API path relative to ``/api`` (e.g. ``"/services/light/turn_on"``).
            data: JSON-serializable payload to include in the request body.

        Returns:
            Parsed JSON response body.

        Raises:
            httpx.HTTPStatusError: If the server returns a non-2xx status code.
        """
        resp = self._http.post(path, json=data or {})
        resp.raise_for_status()
        return resp.json()
