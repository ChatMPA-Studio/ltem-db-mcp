#!/usr/bin/env bash
# =============================================================================
# smoke_test.sh — Quick verification that the MCP server is responding
#
# Usage:
#   bash scripts/smoke_test.sh                    # localhost:8000/mcp
#   bash scripts/smoke_test.sh http://host:port   # custom base URL
#   bash scripts/smoke_test.sh http://host/ltem   # behind reverse proxy
# =============================================================================

set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"
MCP_PATH="${MCP_BASE_PATH:-/mcp}"
ENDPOINT="${BASE_URL}${MCP_PATH}"

# If a full URL with path was given (e.g., http://host/ltem), use it directly
if [[ "$1" == *"/"*"/"*"/"* ]]; then
    ENDPOINT="$1"
fi

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0

run_test() {
    local name="$1"
    local result="$2"
    local check="$3"

    if echo "$result" | grep -q "$check"; then
        echo -e "  ${GREEN}PASS${NC} $name"
        PASS=$((PASS + 1))
    else
        echo -e "  ${RED}FAIL${NC} $name"
        echo -e "       Expected to find: $check"
        echo -e "       Got: $(echo "$result" | head -c 200)"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== LTEM MCP Server Smoke Tests ==="
echo "Endpoint: $ENDPOINT"
echo ""

# ---------------------------------------------------------------------------
# Test 1: Initialize handshake
# ---------------------------------------------------------------------------
echo "1. MCP Initialize Handshake"
INIT=$(curl -sf -X POST "$ENDPOINT" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -d '{
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "smoke-test", "version": "1.0"}
        }
    }' 2>/dev/null || echo "CONNECTION_FAILED")

run_test "JSON-RPC response received" "$INIT" '"jsonrpc"'
run_test "Server name present" "$INIT" '"serverInfo"'

# ---------------------------------------------------------------------------
# Test 2: List tools
# ---------------------------------------------------------------------------
echo ""
echo "2. List Tools"
TOOLS=$(curl -sf -X POST "$ENDPOINT" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -d '{
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }' 2>/dev/null || echo "CONNECTION_FAILED")

run_test "Tools list returned" "$TOOLS" '"tools"'
run_test "health_check tool present" "$TOOLS" 'health_check'

# ---------------------------------------------------------------------------
# Test 3: Call health_check tool
# ---------------------------------------------------------------------------
echo ""
echo "3. Health Check Tool"
HEALTH=$(curl -sf -X POST "$ENDPOINT" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -d '{
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "health_check",
            "arguments": {}
        }
    }' 2>/dev/null || echo "CONNECTION_FAILED")

run_test "Health check responded" "$HEALTH" '"result"'

# ---------------------------------------------------------------------------
# Test 4: Call list_tables tool
# ---------------------------------------------------------------------------
echo ""
echo "4. List Tables Tool"
TABLES=$(curl -sf -X POST "$ENDPOINT" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -d '{
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "list_tables",
            "arguments": {}
        }
    }' 2>/dev/null || echo "CONNECTION_FAILED")

run_test "Tables list responded" "$TABLES" '"result"'

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "=== Results: ${PASS} passed, ${FAIL} failed ==="

if [ $FAIL -gt 0 ]; then
    echo -e "${YELLOW}Some tests failed. Check the endpoint and server logs.${NC}"
    exit 1
else
    echo -e "${GREEN}All smoke tests passed!${NC}"
    exit 0
fi
