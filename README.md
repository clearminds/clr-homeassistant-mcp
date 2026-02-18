# homeassistant-mcp-server

Home Assistant smart home control

## Install

```bash
pip install homeassistant-mcp-server
# or
uvx homeassistant-mcp-server
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
homeassistant-mcp-server --help
```

## Development

```bash
git clone https://github.com/clearminds/homeassistant-mcp-server.git
cd homeassistant-mcp-server
uv sync
uv run homeassistant-mcp-server
```

## License

MIT
