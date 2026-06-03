# LTEM Database MCP Server — Deployment Guide

## Overview

The LTEM MCP server runs as a Docker container exposing a
[Streamable HTTP](https://spec.modelcontextprotocol.io/specification/basic/transports/#streamable-http)
endpoint. It is designed to sit behind a reverse proxy under a subpath
(e.g. `/ltem`) alongside other MCP services on the same host.

---

## 1. Build the Docker Image

```bash
docker build -t ltem-mcp .
```

## 2. Run Locally

Pass database credentials as environment variables:

```bash
docker run --rm \
  -p 8000:8000 \
  -e LTEM_DB_HOST=<your-db-host> \
  -e LTEM_DB_PASSWORD=<your-db-password> \
  ltem-mcp
```

Or if you have a `.env` file with credentials:

```bash
docker run --rm -p 8000:8000 --env-file .env ltem-mcp
```

### Using docker compose

```bash
# Reads .env automatically
docker compose up --build
```

## 3. Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `LTEM_DB_HOST` | **yes** | — | MySQL/MariaDB host |
| `LTEM_DB_PASSWORD` | **yes** | — | Database password |
| `LTEM_DB_PORT` | no | `3306` | Database port |
| `LTEM_DB_USER` | no | `mcp_ltem_ro` | Database user |
| `LTEM_DB_NAME` | no | `ecological_monitoring` | Database name |
| `PORT` | no | `8000` | HTTP port the server binds to |
| `MCP_BASE_PATH` | no | `/mcp` | URL path for the MCP endpoint |

## 4. Verify It Works

Once the container is running, the MCP endpoint is at:

```
http://localhost:8000/mcp
```

### Quick smoke test with curl

```bash
# Send an MCP "initialize" request
curl -s http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-03-26",
      "capabilities": {},
      "clientInfo": { "name": "smoke-test", "version": "0.1.0" }
    }
  }'
```

A successful response returns JSON with `serverInfo` and `capabilities`.

### List available tools

After initializing (and receiving a `Mcp-Session` header from the response), you can list tools:

```bash
curl -s http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session: <session-id-from-init-response>" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }'
```

## 5. Reverse Proxy (Future)

When deploying behind a reverse proxy (Caddy, Nginx, Traefik) on a shared
Droplet, route a subpath to this container:

```
https://mcp.example.com/ltem  →  http://ltem-mcp:8000/mcp
```

Set `MCP_BASE_PATH` if the server itself needs to be aware of the subpath
prefix. In most setups the proxy handles path rewriting and the default
`/mcp` works as-is.

## 6. Architecture Notes

- **One container, one port** — easy to replicate for additional MCP services.
- **No filesystem dependencies** — all state comes from the remote database.
- **No secrets baked in** — credentials are injected via environment variables.
- Logs go to stdout/stderr (Docker captures them automatically).
