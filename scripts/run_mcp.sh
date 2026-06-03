#!/usr/bin/env bash
# LTEM Database MCP Server — macOS/Linux Launcher
# Run from the repo root: ./scripts/run_mcp.sh

set -euo pipefail

# Resolve repo root (parent of scripts/)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$REPO_ROOT"

# Check .env exists
if [ ! -f ".env" ]; then
	echo "ERROR: .env file not found in $REPO_ROOT" >&2
	echo "Copy .env.example to .env and fill in credentials:" >&2
	echo "  cp .env.example .env" >&2
	exit 1
fi

# Check required env vars
if grep -q "CHANGEME" .env; then
	echo "ERROR: LTEM_DB_PASSWORD is still set to CHANGEME." >&2
	echo "Edit .env and set the actual database password." >&2
	exit 1
fi

if ! grep -q "LTEM_DB_PASSWORD" .env; then
	echo "ERROR: LTEM_DB_PASSWORD not found in .env file." >&2
	exit 1
fi

# Check fastmcp is available
if command -v fastmcp &>/dev/null; then
	exec fastmcp run mcp_server/server.py:mcp --transport stdio
elif python3 -m fastmcp --help &>/dev/null 2>&1; then
	echo "fastmcp not in PATH, using 'python3 -m fastmcp'..." >&2
	exec python3 -m fastmcp run mcp_server/server.py:mcp --transport stdio
elif python -m fastmcp --help &>/dev/null 2>&1; then
	echo "fastmcp not in PATH, using 'python -m fastmcp'..." >&2
	exec python -m fastmcp run mcp_server/server.py:mcp --transport stdio
else
	echo "ERROR: fastmcp not found. Install with: pip install -e ." >&2
	exit 1
fi
