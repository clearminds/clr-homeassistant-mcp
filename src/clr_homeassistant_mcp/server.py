"""Home Assistant MCP Server — FastMCP tools for smart home control."""

import argparse
import logging
import logging.config
import sys
from typing import Any

from fastmcp import FastMCP

from clr_homeassistant_mcp.config import HAInstance, Settings
from clr_homeassistant_mcp.ha_client import HAClient
from clr_homeassistant_mcp.middleware import ToolValidationMiddleware

mcp = FastMCP("HomeAssistant")
mcp.add_middleware(ToolValidationMiddleware())
_clients: dict[str, HAClient] = {}
_instances: dict[str, HAInstance] = {}
_default_instance: str = "default"

WRITE_TOOLS = ["ha_turn_on", "ha_turn_off", "ha_toggle", "ha_trigger_scene", "ha_call_service"]


def _get_client(instance: str | None = None) -> HAClient:
    """Get the HAClient for the given instance, or the default.

    Args:
        instance: Instance name to look up.  Uses the default instance
            when ``None``.

    Returns:
        The HAClient associated with the requested instance.

    Raises:
        ValueError: If the requested instance name is not configured.
    """
    name = instance or _default_instance
    if name not in _clients:
        available = ", ".join(_clients.keys()) or "(none)"
        raise ValueError(f"Unknown instance '{name}'. Available: {available}")
    return _clients[name]


# ── Info tools ───────────────────────────────────────────────────────


@mcp.tool
def ha_instances() -> list[dict[str, str]]:
    """List all configured Home Assistant instances.

    Returns instance names with their URLs and which is the default.
    """
    return [
        {
            "name": name,
            "url": inst.url,
            "default": name == _default_instance,
        }
        for name, inst in _instances.items()
    ]


@mcp.tool
def ha_status(instance: str | None = None) -> dict[str, Any]:
    """Get Home Assistant server status and version.

    Args:
        instance: Instance name (omit for default).

    Returns API status including version and state.
    """
    client = _get_client(instance)
    config = client.get("/config")
    return {
        "location_name": config.get("location_name"),
        "version": config.get("version"),
        "state": config.get("state"),
        "components_count": len(config.get("components", [])),
        "unit_system": config.get("unit_system", {}).get("temperature"),
        "time_zone": config.get("time_zone"),
    }


# ── Entity tools ─────────────────────────────────────────────────────


@mcp.tool
def ha_list_entities(
    domain: str | None = None,
    instance: str | None = None,
) -> list[dict[str, Any]]:
    """List entities, optionally filtered by domain.

    Args:
        domain: Entity domain filter (e.g. "switch", "light", "sensor",
                "climate", "cover", "media_player", "automation", "scene").
                Omit to list all entities.
        instance: Instance name (omit for default).

    Returns list of entities with id, state, and friendly name.
    """
    client = _get_client(instance)
    states = client.get("/states")
    results = []
    for entity in states:
        eid = entity.get("entity_id", "")
        if domain and not eid.startswith(f"{domain}."):
            continue
        results.append(
            {
                "entity_id": eid,
                "state": entity.get("state"),
                "friendly_name": entity.get("attributes", {}).get("friendly_name"),
            }
        )
    return results


@mcp.tool
def ha_get_state(
    entity_id: str,
    instance: str | None = None,
) -> dict[str, Any]:
    """Get the full state and attributes of an entity.

    Args:
        entity_id: The entity ID (e.g. "sensor.living_room_temperature").
        instance: Instance name (omit for default).

    Returns entity state with all attributes.
    """
    client = _get_client(instance)
    data = client.get(f"/states/{entity_id}")
    return {
        "entity_id": data.get("entity_id"),
        "state": data.get("state"),
        "attributes": data.get("attributes"),
        "last_changed": data.get("last_changed"),
        "last_updated": data.get("last_updated"),
    }


# ── Service tools ────────────────────────────────────────────────────


@mcp.tool
def ha_turn_on(
    entity_id: str,
    brightness_pct: int | None = None,
    instance: str | None = None,
) -> str:
    """Turn on a switch, light, or other entity.

    Args:
        entity_id: The entity ID (e.g. "switch.office_lamp", "light.living_room").
        brightness_pct: Brightness percentage (1-100) for lights. Ignored for switches.
        instance: Instance name (omit for default).

    Returns confirmation message.
    """
    client = _get_client(instance)
    domain = entity_id.split(".")[0]
    data: dict[str, Any] = {"entity_id": entity_id}
    if brightness_pct is not None and domain == "light":
        data["brightness_pct"] = brightness_pct
    client.post(f"/services/{domain}/turn_on", data)
    return f"Turned on {entity_id}"


@mcp.tool
def ha_turn_off(
    entity_id: str,
    instance: str | None = None,
) -> str:
    """Turn off a switch, light, or other entity.

    Args:
        entity_id: The entity ID (e.g. "switch.office_lamp", "light.living_room").
        instance: Instance name (omit for default).

    Returns confirmation message.
    """
    client = _get_client(instance)
    domain = entity_id.split(".")[0]
    client.post(f"/services/{domain}/turn_off", {"entity_id": entity_id})
    return f"Turned off {entity_id}"


@mcp.tool
def ha_toggle(
    entity_id: str,
    instance: str | None = None,
) -> str:
    """Toggle an entity (on→off or off→on).

    Args:
        entity_id: The entity ID.
        instance: Instance name (omit for default).

    Returns confirmation message.
    """
    client = _get_client(instance)
    domain = entity_id.split(".")[0]
    client.post(f"/services/{domain}/toggle", {"entity_id": entity_id})
    return f"Toggled {entity_id}"


@mcp.tool
def ha_trigger_scene(
    entity_id: str,
    instance: str | None = None,
) -> str:
    """Activate a scene.

    Args:
        entity_id: The scene entity ID (e.g. "scene.movie_time").
        instance: Instance name (omit for default).

    Returns confirmation message.
    """
    client = _get_client(instance)
    client.post("/services/scene/turn_on", {"entity_id": entity_id})
    return f"Activated scene {entity_id}"


@mcp.tool
def ha_call_service(
    domain: str,
    service: str,
    data: dict[str, Any] | None = None,
    instance: str | None = None,
) -> str:
    """Call any Home Assistant service.

    Generic tool for services not covered by other tools.

    Args:
        domain: Service domain (e.g. "climate", "cover", "media_player").
        service: Service name (e.g. "set_temperature", "open_cover", "play_media").
        data: Service call data dict (e.g. {"entity_id": "climate.thermostat", "temperature": 22}).
        instance: Instance name (omit for default).

    Returns confirmation message.
    """
    client = _get_client(instance)
    client.post(f"/services/{domain}/{service}", data or {})
    return f"Called {domain}.{service}"


# ── Composite init ───────────────────────────────────────────────────


def init_composite() -> FastMCP:
    """Initialize for composite mounting. Returns the FastMCP instance."""
    global _clients, _instances, _default_instance

    settings = Settings()
    _instances = settings.load_instances()
    _default_instance = settings.get_default_name()

    for name, inst in _instances.items():
        _clients[name] = HAClient(inst.url, inst.token)

    if settings.ha_read_only and WRITE_TOOLS:
        for name in WRITE_TOOLS:
            mcp.remove_tool(name)

    return mcp


# ── Main entry point ─────────────────────────────────────────────────


def main() -> None:
    """Main entry point for the Home Assistant MCP server."""
    global _clients, _instances, _default_instance

    settings = Settings()

    parser = argparse.ArgumentParser(description="Home Assistant MCP Server")
    parser.add_argument(
        "--transport", type=str, choices=["stdio", "http"], default=None
    )
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--log-level",
        type=str,
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    parser.add_argument(
        "--read-only",
        action="store_true",
        default=None,
        help="Run in read-only mode (hide write tools)",
    )
    args = parser.parse_args()

    transport = args.transport or settings.ha_transport
    log_level = args.log_level or settings.ha_log_level

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "console": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "console",
                    "stream": "ext://sys.stderr",
                }
            },
            "root": {"level": log_level, "handlers": ["console"]},
        }
    )

    logger = logging.getLogger(__name__)

    _instances = settings.load_instances()
    _default_instance = settings.get_default_name()

    if not _instances:
        logger.error(
            "No HA instances configured. Set HA_URL/HA_TOKEN or configure credentials.json"
        )
        sys.exit(1)

    for name, inst in _instances.items():
        _clients[name] = HAClient(inst.url, inst.token)
        logger.info("Loaded HA instance '%s' (%s)", name, inst.url)

    logger.info("Default instance: %s", _default_instance)
    logger.info("Starting Home Assistant MCP Server")

    read_only = args.read_only if args.read_only is not None else settings.ha_read_only
    if read_only and WRITE_TOOLS:
        for name in WRITE_TOOLS:
            mcp.remove_tool(name)
        logger.info("Read-only mode: %d write tools removed", len(WRITE_TOOLS))

    try:
        if transport == "stdio":
            mcp.run(transport="stdio")
        else:
            mcp.run(transport="http", host=args.host, port=args.port)
    except Exception as e:
        logger.error("Failed to start MCP server: %s", e)
        sys.exit(1)
    finally:
        for client in _clients.values():
            client.close()


if __name__ == "__main__":
    main()
