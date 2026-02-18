# clr-homeassistant-mcp

Home Assistant smart home control

## Install

```bash
pip install clr-homeassistant-mcp
# or
uvx clr-homeassistant-mcp
```

## Configuration

**Preferred:** Configuration file at `~/.config/homeassistant/credentials.json` (chmod 600):

Single instance:
```json
{
  "url": "https://homeassistant.local:8123",
  "token": "your-long-lived-access-token"
}
```

Multi-instance:
```json
{
  "instances": {
    "home": {
      "url": "https://home.example.com",
      "token": "home-token-here"
    },
    "office": {
      "url": "https://office.example.com",
      "token": "office-token-here"
    }
  },
  "default": "home"
}
```

**Alternative:** Environment variables are also supported (single instance only):

| Variable | Description | Example |
|----------|-------------|---------|
| `HA_URL` | Home Assistant URL | `https://homeassistant.local:8123` |
| `HA_TOKEN` | Long-lived access token | `your-token` |

Get token: Settings → Long-Lived Access Tokens in Home Assistant UI

See `--help` for additional options:

```bash
clr-homeassistant-mcp --help
```

## Development

```bash
git clone https://github.com/clearminds/clr-homeassistant-mcp.git
cd clr-homeassistant-mcp
uv sync
uv run clr-homeassistant-mcp
```

## License

MIT
