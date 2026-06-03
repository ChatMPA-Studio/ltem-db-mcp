# MCP Server Template Guide

How to create a new MCP server from this repository. This template provides a production-ready structure for exposing any MySQL database as structured analysis tools via the Model Context Protocol (MCP).

## Quick Start

```bash
# 1. Copy the repo
cp -r ltem-db-mcp/ your-domain-mcp/
cd your-domain-mcp/

# 2. Clean domain-specific content
rm -rf tools/biomass.py tools/fish_community.py tools/mpa_effectiveness.py \
       tools/temporal_trends.py tools/reporting.py tools/data_quality.py \
       tools/invertebrates.py tools/ecosystem_indicators.py
rm -rf skills/ltem-*
rm -rf docs/ltem-scripts/

# 3. Keep the infrastructure
#    mcp_server/       — server, config, db, security (customize these)
#    tools/__init__.py  — keep (required for auto-discovery)
#    tools/data_access.py — keep as starting point (get_regions, get_observations)
#    Dockerfile, docker-compose.yml, tests/, scripts/
```

## Files to Customize

### Required Changes

| File | What to Change |
|------|---------------|
| `mcp_server/server.py` | Line 24: Change `FastMCP("LTEM Database")` to your server name |
| `mcp_server/server.py` | Resources section (lines 30-108): Replace LTEM-specific resources with your domain |
| `mcp_server/config.py` | Lines 77-81: Rename `LTEM_DB_*` env var prefix to match your domain |
| `mcp_server/security.py` | Lines 6-10: Replace `ALLOWED_TABLES` with your database tables |
| `.env.example` | Update variable names and defaults |
| `pyproject.toml` | Update name, version, description |
| `README.md` | Rewrite for your domain |
| `CHANGELOG.md` | Start fresh with v1.0.0 |

### Optional Changes

| File | What to Change |
|------|---------------|
| `mcp_server/db.py` | Only if switching from MySQL to PostgreSQL (swap PyMySQL for psycopg2) |
| `docker-compose.yml` | Change container name and HOST_PORT |
| `Dockerfile` | Usually no changes needed |
| `resources/data_dictionary.md` | Document your database schema |

## Adding Tools

Tools live in `tools/` as Python modules. Each module must have a `register(mcp)` function. The server auto-discovers them at startup — no manual imports needed.

### Minimal Tool Module

Create `tools/your_domain.py`:

```python
"""Your domain analysis tools."""

import json

from fastmcp import FastMCP
from mcp_server.db import execute_select


def _safe_float(v):
    """Convert Decimal/numeric DB types to JSON-serializable floats."""
    if v is None:
        return None
    if hasattr(v, 'as_integer_ratio'):
        return float(v)
    return v


def _serialize_rows(rows):
    """Make all values in a list of dicts JSON-safe."""
    return [{k: _safe_float(v) for k, v in r.items()} for r in rows]


def register(mcp: FastMCP) -> None:
    """Register tools with the MCP server."""

    @mcp.tool()
    def your_summary(region: str | None = None) -> str:
        """Summarize data by region.

        Args:
            region: Filter by region name (optional)
        """
        clauses, params = [], []
        if region:
            clauses.append("Region = %s")
            params.append(region)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = (
            f"SELECT Region, COUNT(*) AS n, AVG(value) AS mean_value "
            f"FROM your_table {where} "
            f"GROUP BY Region ORDER BY mean_value DESC"
        )
        rows = execute_select(sql, params=tuple(params) if params else None)
        return json.dumps({
            "data": _serialize_rows(rows),
            "meta": {"row_count": len(rows)},
        })
```

### Key Patterns

- **Always use parameterized queries** (`%s` placeholders, never f-strings for user input)
- **Return JSON strings** with `{"data": ..., "meta": {...}}` structure
- **Use `_safe_float()`** to handle MySQL Decimal types
- **Use `execute_select()`** from `mcp_server.db` — it handles connection pooling, validation, and limits
- **Optional parameters** use `str | None = None` type hints
- **Docstrings** become the tool description in the MCP protocol — keep them clear

### Statistical Tools

For tools that compute statistics (correlations, trend tests, etc.), add scipy/numpy:

```python
import numpy as np
from scipy import stats

# Inside your tool function:
tau, p_value = stats.kendalltau(years, values)
```

## Adding Skills

Skills are agent-agnostic analysis guides in `skills/`. Any AI agent can read them.

### Create a Skill

1. Create directory: `skills/your-skill-name/`
2. Create `skills/your-skill-name/SKILL.md`:

```yaml
---
name: your-skill-name
description: One-line description of the analysis this skill performs.
---

# Skill Title

## Purpose
What questions this skill helps answer.

## MCP Tools Available

| Tool | Parameters | Purpose |
|------|-----------|---------|
| `your_summary` | `region?` | Summarize data by region |

## Core Workflow

1. **Scope** — Call `get_regions` to see available data
2. **Analyze** — Call domain tools with filters
3. **Interpret** — Use the guide below to contextualize results

## Interpretation Guide

| Metric | Low | Medium | High |
|--------|-----|--------|------|
| Your metric | <X | X-Y | >Y |

## Success Criteria

A complete analysis includes:
- Summary statistics for the target scope
- Comparison across relevant groups
- Ecological interpretation
```

3. Optionally add `skills/your-skill-name/references/methodology.md` for detailed methodology

## Security Configuration

### Table Whitelist

Edit `mcp_server/security.py`:

```python
ALLOWED_TABLES = {
    'your_main_table',
    'your_reference_table',
    'your_lookup_table',
}
```

Only tables in this set can be queried. All others are blocked.

### Database User

Create a read-only MySQL user for the MCP server:

```sql
CREATE USER 'mcp_readonly'@'%' IDENTIFIED BY 'strong_password_here';
GRANT SELECT ON your_database.* TO 'mcp_readonly'@'%';
FLUSH PRIVILEGES;
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Server
PORT=8000
MCP_BASE_PATH=/mcp
LOG_LEVEL=INFO

# Database (option A: individual vars)
LTEM_DB_HOST=your-db-host.com
LTEM_DB_PORT=3306
LTEM_DB_USER=mcp_readonly
LTEM_DB_PASSWORD=your_password
LTEM_DB_NAME=your_database

# Database (option B: single URL — takes precedence)
# DATABASE_URL=mysql://user:pass@host:3306/dbname
```

Rename the `LTEM_DB_*` prefix in `config.py` to match your domain (e.g., `SST_DB_*`).

## Docker Deployment

### Build and Run

```bash
docker compose build
docker compose up -d
docker compose logs -f  # watch logs
```

### Assign a Unique Port

Each MCP server needs its own HOST_PORT in `.env`:

```bash
# .env
HOST_PORT=8002  # LTEM is 8001, SST could be 8002, etc.
```

The container always listens on PORT internally (default 8000). HOST_PORT maps it to the host.

### Health Check

```bash
# Check container health
docker compose ps

# Manual health check
curl http://localhost:8002/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}'
```

## Caddy Reverse Proxy

Add a route block for the new MCP in your Caddyfile:

```
handle /your-domain/* {
    uri strip_prefix /your-domain
    reverse_proxy localhost:8002
}
```

Then reload Caddy:

```bash
sudo systemctl reload caddy
```

## Testing

### Adapt Smoke Tests

Edit `tests/test_smoke.py`:

1. **TestEnvironment** — Update env var names if you renamed the prefix
2. **TestConnectivity** — Update expected database name
3. **TestSchemaDiscovery** — Update expected table names
4. **TestEcologyTools** — Replace with domain-specific queries
5. **TestSecurityGuardrails** — Keep as-is (tests the security layer generically)

### Run Tests

```bash
# Offline tests (no server needed, just DB access)
pytest tests/test_smoke.py -v

# HTTP tests (requires running server)
python -m mcp_server &
pytest tests/test_tools.py -v
```

## Deployment Script

`scripts/deploy.sh` handles safe updates on the server:

```bash
ssh your-server "cd /opt/your-domain-mcp && bash scripts/deploy.sh"
```

The script backs up the current state, pulls code, rebuilds Docker, restarts, and verifies health.

## Full Customization Checklist

- [ ] Copy repo and remove LTEM-specific tool modules
- [ ] Rename `FastMCP("LTEM Database")` in `server.py`
- [ ] Replace MCP resources in `server.py` with your domain metadata
- [ ] Update `ALLOWED_TABLES` in `security.py`
- [ ] Rename env var prefix in `config.py` (if desired)
- [ ] Update `.env.example` with your database credentials
- [ ] Create a read-only database user
- [ ] Write your first tool module in `tools/`
- [ ] Write `resources/data_dictionary.md` for your schema
- [ ] Update `pyproject.toml` (name, version, description)
- [ ] Assign a unique `HOST_PORT` in `.env`
- [ ] Add Caddy route for the new MCP
- [ ] Write domain-specific skills in `skills/`
- [ ] Adapt and run tests
- [ ] Update README.md and CHANGELOG.md
- [ ] Build Docker image and deploy
