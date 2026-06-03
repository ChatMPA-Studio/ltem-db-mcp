# LTEM Database MCP Server

An [MCP](https://modelcontextprotocol.io/) (Model Context Protocol) server that provides AI assistants with structured access to Mexico's Long-Term Ecological Monitoring (LTEM) reef fish database. Built with [FastMCP 2.x](https://github.com/jlowin/fastmcp) and designed for production deployment behind a reverse proxy.

**Version:** 1.1.0
**Database:** MySQL 8 on AWS RDS (`ecological_monitoring`, ~449K observations, 1998-2025)
**Transport:** HTTP/SSE (Docker) or stdio (local development)

## What This Does

The LTEM database tracks reef fish communities across 14 regions in the Gulf of California and Mexican Pacific since 1998. This MCP server exposes **34 tools** for querying, analyzing, and comparing ecological data — from simple species lists to statistical trend analysis and MPA effectiveness assessments.

AI assistants connect via HTTP/SSE (Server-Sent Events) and use JSON-RPC 2.0 to call tools. All database access is read-only, parameterized, and validated against a table whitelist.

## Architecture

```
Client (Claude, etc.)
    │  JSON-RPC 2.0 over HTTP
    ▼
[Caddy Reverse Proxy]  ← Basic Auth + TLS
    │  http://127.0.0.1:8001
    ▼
[Docker Container]
    │  FastMCP HTTP/SSE on port 8000
    ▼
[MCP Server]
    │  SQL validation → parameterized queries
    ▼
[MySQL 8 on AWS RDS]  ← read-only user
```

## Quick Start

### Local Development (without Docker)

```bash
# 1. Clone and enter the repo
git clone <repo-url> && cd ltem-db-mcp

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

# 3. Install with dev dependencies
pip install -e ".[dev]"

# 4. Configure credentials
cp .env.example .env
# Edit .env — fill in LTEM_DB_PASSWORD

# 5. Run smoke tests (validates DB connectivity)
pytest tests/test_smoke.py -v

# 6a. Start HTTP server (for AI clients)
python -m mcp_server

# 6b. Or start stdio server (for local MCP clients)
fastmcp run mcp_server/server.py:mcp --transport stdio
```

### Docker

```bash
# Build
docker build -t ltem-mcp .

# Run (standalone)
docker run --rm -p 8000:8000 --env-file .env ltem-mcp

# Run (with docker compose — binds to localhost only)
docker compose up --build -d

# View logs
docker compose logs -f ltem-mcp

# Stop
docker compose down
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LTEM_DB_HOST` | Yes* | — | MySQL host address |
| `LTEM_DB_PORT` | No | `3306` | MySQL port |
| `LTEM_DB_USER` | No | `mcp_ltem_ro` | MySQL username |
| `LTEM_DB_PASSWORD` | Yes* | — | MySQL password |
| `LTEM_DB_NAME` | No | `ecological_monitoring` | Database name |
| `DATABASE_URL` | No | — | Alternative: `mysql://user:pass@host:port/db` |
| `PORT` | No | `8000` | HTTP server port inside container |
| `HOST_PORT` | No | `8001` | Port exposed on host (docker compose) |
| `MCP_BASE_PATH` | No | `/mcp` | MCP endpoint path |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

\* Not required if `DATABASE_URL` is set.

## Tool Inventory (59 tools)

| Category | Tools | Description |
|---|---|---|
| **Core** (4) | `health_check`, `list_tables`, `describe_table`, `schema_snapshot` | DB connectivity and schema discovery |
| **Data Access** (5) | `get_regions`, `get_reefs`, `get_species_list`, `get_observations`, `survey_effort_summary` | Raw data queries with filters |
| **Fish Community** (5) | `calculate_diversity`, `species_composition`, `trophic_structure`, `size_structure`, `community_comparison` | Diversity indices, composition, Bray-Curtis |
| **Biomass** (7) | `biomass_by_region`, `biomass_by_depth`, `trophic_biomass`, `environmental_correlations`, `sst_biomass_relationship`, `chl_productivity_relationship`, `latitudinal_gradient` | Biomass analysis and environmental drivers |
| **MPA Effectiveness** (7) | `compare_protection_levels`, `cabo_pulmo_recovery`, `compare_all_metrics`, `trophic_comparison`, `size_comparison`, `baci_analysis`, `spillover_analysis` | Protection level comparisons, BACI analysis |
| **Temporal Trends** (6) | `annual_time_series`, `trend_analysis`, `regional_trends`, `change_point_detection`, `seasonal_patterns`, `moving_window` | Time series, Mann-Kendall, change points |
| **Reporting** (4) | `numeralia_historical`, `numeralia_by_label`, `numeralia_by_region`, `consistent_reefs` | Summary statistics and survey effort |
| **Data Quality** (5) | `detect_outliers_mad`, `detect_outliers_quantile`, `sample_size_assessment`, `transect_coverage_audit`, `data_completeness_report` | Outlier detection, sample size checks, completeness |
| **Invertebrates** (6) | `invertebrate_summary`, `invertebrate_species_list`, `coral_warm_cold_ratio`, `invertebrate_latitudinal_gradient`, `invertebrate_temporal_trends`, `bleaching_assessment` | Invertebrate community analysis |
| **Ecosystem Indicators** (6) | `nrsi_by_reef`, `nrsi_bootstrapped`, `nrsi_regional_summary`, `functional_group_biomass`, `functional_group_temporal`, `functional_group_by_region` | NRSI and functional group analysis |
| **Report Generation** (4) | `generate_mpa_report`, `generate_temporal_report`, `generate_community_report`, `generate_quality_report` | Automated HTML/PDF reports with visualizations |

5 MCP resources are also available: `ltem://schema`, `ltem://regions`, `ltem://sampling-protocol`, `ltem://protection-categories`, `ltem://trophic-groups`.

### Report Generation

The server includes automated report generation tools that create publication-ready HTML and PDF reports with embedded Matplotlib visualizations:

- **MPA Effectiveness Report**: Biomass comparisons, Cabo Pulmo recovery, BACI analysis
- **Temporal Trends Report**: Time series, Mann-Kendall tests, change point detection
- **Community Structure Report**: Diversity indices, species composition, trophic structure
- **Data Quality Report**: Outlier detection, sample size assessment, completeness checks

Reports include statistical tables, interpretation guidelines, and colorblind-safe visualizations. PDF generation requires WeasyPrint (`pip install WeasyPrint`).

## Testing

### Smoke Tests (requires DB credentials)

```bash
# Run all smoke tests
pytest tests/test_smoke.py -v

# Run security tests only
pytest tests/test_smoke.py::TestSecurityGuardrails -v
```

### HTTP Tests (requires running server)

```bash
# Start the server first
python -m mcp_server &

# Then run HTTP tests
pytest tests/test_initialize.py tests/test_tools.py -v

# Or use the smoke test scripts
bash scripts/smoke_test.sh                           # Linux
powershell scripts/smoke_initialize.ps1              # Windows

# Test against a remote server
bash scripts/smoke_test.sh http://206.189.163.235/ltem
powershell scripts/smoke_initialize.ps1 -BaseUrl http://206.189.163.235/ltem -McpPath ""
```

### Manual curl Test (Linux)

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "test", "version": "1.0"}
    }
  }'
```

### Manual curl Test (Windows)

```powershell
curl.exe -X POST http://localhost:8000/mcp `
  -H "Content-Type: application/json" `
  -H "Accept: application/json, text/event-stream" `
  -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2024-11-05\",\"capabilities\":{},\"clientInfo\":{\"name\":\"test\",\"version\":\"1.0\"}}}'
```

## Reverse Proxy Setup (Caddy)

This server is designed to run behind a reverse proxy. Here's a Caddy configuration that handles Basic Auth and subpath routing for multiple MCP servers:

```caddyfile
:80 {
    # LTEM MCP Server
    handle_path /ltem/* {
        basicauth {
            # Generate hash: caddy hash-password
            your_username $2a$14$hashed_password_here
        }
        reverse_proxy localhost:8001
    }

    # Future MCP servers on different subpaths/ports:
    # handle_path /sst/* {
    #     basicauth { ... }
    #     reverse_proxy localhost:8002
    # }
}
```

With a domain and automatic TLS:

```caddyfile
mcp.yourdomain.com {
    handle_path /ltem/* {
        basicauth {
            your_username $2a$14$hashed_password_here
        }
        reverse_proxy localhost:8001
    }
}
```

## Deployment

### First-time Setup on Droplet

```bash
# 1. Clone the repo
cd /opt
git clone <repo-url> ltem-db-mcp
cd ltem-db-mcp

# 2. Create .env with production credentials
cp .env.example .env
nano .env  # Fill in real credentials

# 3. Build and start
docker compose up --build -d

# 4. Verify health
docker inspect --format='{{.State.Health.Status}}' ltem-mcp

# 5. Run smoke test
bash scripts/smoke_test.sh
```

### Subsequent Deployments

```bash
# Safe deployment with backup and verification
cd /opt/ltem-db-mcp
bash scripts/deploy.sh
```

The deploy script handles: backup current config, pull latest code, rebuild image, restart container, verify health, test initialize endpoint.

## Project Structure

```
ltem-db-mcp/
├── mcp_server/                 # Server package
│   ├── __init__.py
│   ├── __main__.py             # HTTP entry point (python -m mcp_server)
│   ├── config.py               # Environment validation and settings
│   ├── db.py                   # Database connection and query execution
│   ├── schema.py               # Schema discovery and caching
│   ├── security.py             # SQL validation, table whitelist, LIMIT enforcement
│   └── server.py               # FastMCP instance, resources, core tools, auto-discovery
├── tools/                      # MCP tool modules (auto-discovered)
│   ├── data_access.py          # Regions, reefs, species, observations, survey effort
│   ├── fish_community.py       # Diversity indices, species composition, trophic/size structure
│   ├── biomass.py              # Biomass by region/depth, trophic biomass, env correlations
│   ├── mpa_effectiveness.py    # Protection level comparisons, Cabo Pulmo recovery, BACI
│   └── temporal_trends.py      # Time series, trends, change points, seasonal patterns
├── resources/                  # Static resources
│   └── data_dictionary.md      # Database schema documentation
├── tests/                      # Test suite
│   ├── conftest.py             # Shared fixtures (env loading, DB connection)
│   ├── test_smoke.py           # Offline tests (DB queries, security guardrails)
│   ├── test_initialize.py      # HTTP tests (JSON-RPC handshake, SSE)
│   └── test_tools.py           # HTTP tests (tool invocations)
├── scripts/                    # Operations scripts
│   ├── deploy.sh               # Safe deployment workflow
│   ├── smoke_test.sh           # Linux curl-based verification
│   ├── smoke_initialize.ps1    # Windows PowerShell verification
│   ├── run_mcp.sh              # Local stdio launcher (Linux)
│   └── run_mcp.ps1             # Local stdio launcher (Windows)
├── Dockerfile                  # Multi-stage production image
├── docker-compose.yml          # Localhost-bound container with health checks
├── healthcheck.py              # TCP socket probe for Docker HEALTHCHECK
├── pyproject.toml              # Python package configuration
├── .env.example                # Template for environment variables
├── .dockerignore               # Docker build context exclusions
└── .gitignore                  # Git exclusions
```

### Adding New Tools

1. Create a new file in `tools/` (e.g., `tools/my_analysis.py`)
2. Define a `register(mcp)` function that uses `@mcp.tool()` decorators
3. The server auto-discovers and loads it on startup — no imports to update

```python
# tools/my_analysis.py
def register(mcp):
    @mcp.tool()
    def my_new_tool(region: str | None = None) -> str:
        """Description shown to AI clients."""
        from mcp_server.db import execute_select
        import json
        rows = execute_select(
            "SELECT Region, COUNT(*) AS n FROM ltem_historical_database "
            "WHERE Region = %s GROUP BY Region",
            params=(region,),
        )
        return json.dumps({"data": rows})
```

## Reusing This as a Template

This repo is designed to be copied and adapted for new MCP servers (SST, Chl-a, management plans, etc.). To create a new MCP from this template:

1. Copy the repo and rename
2. Update `pyproject.toml` (name, description)
3. Update `mcp_server/security.py` (table whitelist)
4. Update `.env.example` with new database credentials
5. Replace tools in `tools/` with domain-specific tools
6. Update `resources/data_dictionary.md`
7. Update server resources in `mcp_server/server.py`
8. Assign a different `HOST_PORT` in `.env` for the new container

## Troubleshooting

### 406 Not Acceptable

The MCP protocol requires the `Accept: application/json, text/event-stream` header. If your reverse proxy or client doesn't send it, the server returns 406. Ensure the header is passed through.

### 308 Redirect Loop

Caddy may redirect `/ltem` to `/ltem/` (trailing slash). Use `handle_path /ltem/*` (with wildcard) in your Caddyfile, and ensure the client URL matches.

### Connection Refused on Droplet

Docker Compose binds to `127.0.0.1` by default (security). The container is only accessible from localhost. Your reverse proxy must run on the same host.

```bash
# Verify the container is listening
docker compose ps
ss -tlnp | grep 8001
```

### Health Check Failing

```bash
# Check container logs
docker compose logs ltem-mcp

# Test connectivity manually
docker exec ltem-mcp python -c "from mcp_server.db import test_connection; print(test_connection())"

# Check if port is responding
curl -s http://localhost:8001/mcp -o /dev/null -w "%{http_code}"
```

### Database Connection Errors

```bash
# Verify environment variables are set
docker exec ltem-mcp env | grep LTEM_DB

# Test from inside the container
docker exec ltem-mcp python -c "
from mcp_server.db import get_connection
conn = get_connection()
print('Connected:', conn.get_server_info())
conn.close()
"
```

### Windows curl Issues

Use `curl.exe` (not PowerShell's `Invoke-WebRequest` alias). Escape double quotes in JSON with backslash:

```powershell
curl.exe -X POST http://localhost:8000/mcp `
  -H "Content-Type: application/json" `
  -H "Accept: application/json, text/event-stream" `
  -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\",\"params\":{}}'
```

Or use the PowerShell smoke test script:

```powershell
.\scripts\smoke_initialize.ps1
```

### `numpy.bool_` not JSON serializable

A known issue when scipy statistical tests return numpy booleans. All tools wrap these with `bool()` before serialization. If you see this error, it means a tool is missing the wrapper — file a bug.

## Security Model

- **Read-only MySQL user** (`mcp_ltem_ro`) — no write permissions at database level
- **SQL validation** — only `SELECT`, `SHOW`, `DESCRIBE` statements allowed
- **Table whitelist** — queries limited to 3 approved tables
- **Keyword blocking** — regex-based detection of `INSERT`, `UPDATE`, `DELETE`, `DROP`, etc.
- **Row limit** — automatic `LIMIT` injection, capped at 5,000 rows
- **Query timeout** — 20-second execution timeout
- **Non-root container** — Docker runs as UID 1000
- **Localhost binding** — Docker Compose exposes ports on `127.0.0.1` only

## Known Limitations

- **No SST/Chla columns** in the database — environmental correlation tools return graceful error messages
- **IDReef/IDSpecies type mismatch** — text in historical table, double in reference tables
- **Biomass sparsity** — some region/year combinations have very few transects
- **MPA column encoding** — Spanish text with mixed UTF-8/Latin-1 encoding
- **Schema cache** — cached per process; restart the server to pick up schema changes
- **No visualization** — by design; use Claude or chatMPA Studio for rendering

## License

Internal use — CBMC / chatMPA Studio project.
