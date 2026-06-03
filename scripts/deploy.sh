#!/usr/bin/env bash
# =============================================================================
# deploy.sh — Safe deployment workflow for LTEM MCP Server
#
# Usage:
#   ssh root@your-droplet 'cd /opt/ltem-db-mcp && bash scripts/deploy.sh'
#
# What it does:
#   1. Backs up current docker-compose config
#   2. Pulls latest code from git
#   3. Rebuilds Docker image
#   4. Restarts container with health check verification
#   5. Tests the initialize endpoint
#   6. Shows how to view logs
# =============================================================================

set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$APP_DIR"

CONTAINER_NAME="ltem-mcp"
COMPOSE_FILE="docker-compose.yml"
BACKUP_DIR="$APP_DIR/.deploy-backups"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[DEPLOY]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
fail() { echo -e "${RED}[FAIL]${NC} $*"; exit 1; }

# ---------------------------------------------------------------------------
# Step 1: Backup current configuration
# ---------------------------------------------------------------------------
log "Step 1: Backing up current configuration..."
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

if [ -f "$COMPOSE_FILE" ]; then
    cp "$COMPOSE_FILE" "$BACKUP_DIR/${COMPOSE_FILE}.${TIMESTAMP}"
    log "  Backed up $COMPOSE_FILE"
fi
if [ -f ".env" ]; then
    cp .env "$BACKUP_DIR/.env.${TIMESTAMP}"
    log "  Backed up .env"
fi

# Keep only last 5 backups
ls -t "$BACKUP_DIR"/*.* 2>/dev/null | tail -n +11 | xargs -r rm --
log "  Backup complete"

# ---------------------------------------------------------------------------
# Step 2: Pull latest code
# ---------------------------------------------------------------------------
log "Step 2: Pulling latest code from git..."
git fetch origin
git pull origin "$(git rev-parse --abbrev-ref HEAD)"
log "  Git pull complete ($(git rev-parse --short HEAD))"

# ---------------------------------------------------------------------------
# Step 3: Rebuild Docker image
# ---------------------------------------------------------------------------
log "Step 3: Rebuilding Docker image..."
# Support both docker compose v2 and docker-compose v1
if docker compose version &>/dev/null; then
    COMPOSE="docker compose"
else
    COMPOSE="docker-compose"
fi
$COMPOSE build --no-cache
log "  Image rebuilt"

# ---------------------------------------------------------------------------
# Step 4: Restart container
# ---------------------------------------------------------------------------
log "Step 4: Restarting container..."
$COMPOSE down
$COMPOSE up -d
log "  Container started"

# ---------------------------------------------------------------------------
# Step 5: Verify container health
# ---------------------------------------------------------------------------
log "Step 5: Waiting for container to become healthy..."
MAX_WAIT=60
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
    STATUS=$(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null || echo "not_found")
    case "$STATUS" in
        healthy)
            log "  Container is healthy!"
            break
            ;;
        unhealthy)
            fail "Container is unhealthy. Check logs: $COMPOSE logs $CONTAINER_NAME"
            ;;
        *)
            sleep 5
            ELAPSED=$((ELAPSED + 5))
            echo -n "."
            ;;
    esac
done
echo ""

if [ $ELAPSED -ge $MAX_WAIT ]; then
    warn "Health check timed out after ${MAX_WAIT}s. Container status: $STATUS"
    warn "Check logs: $COMPOSE logs $CONTAINER_NAME"
fi

# ---------------------------------------------------------------------------
# Step 6: Test initialize endpoint
# ---------------------------------------------------------------------------
log "Step 6: Testing MCP initialize endpoint..."

# Read port from .env or default
PORT=$(grep -E '^PORT=' .env 2>/dev/null | cut -d= -f2 || echo "8000")
MCP_PATH=$(grep -E '^MCP_BASE_PATH=' .env 2>/dev/null | cut -d= -f2 || echo "/mcp")

INIT_RESPONSE=$(curl -sf -X POST "http://localhost:${PORT}${MCP_PATH}" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"deploy-test","version":"1.0"}}}' \
    2>/dev/null || echo "FAILED")

if echo "$INIT_RESPONSE" | grep -q '"jsonrpc"'; then
    log "  Initialize endpoint responding correctly"
else
    warn "  Initialize test returned unexpected response: $INIT_RESPONSE"
    warn "  This may be normal if the server needs more startup time"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
log "=== Deployment Complete ==="
log "  Container: $CONTAINER_NAME"
log "  Image:     $(docker inspect --format='{{.Config.Image}}' "$CONTAINER_NAME" 2>/dev/null || echo 'unknown')"
log "  Status:    $(docker inspect --format='{{.State.Health.Status}}' "$CONTAINER_NAME" 2>/dev/null || echo 'unknown')"
log "  Commit:    $(git rev-parse --short HEAD)"
echo ""
log "Useful commands:"
log "  $COMPOSE logs -f $CONTAINER_NAME     # Follow logs"
log "  docker compose restart $CONTAINER_NAME      # Restart"
log "  docker compose down                         # Stop"
log "  docker exec $CONTAINER_NAME python -c 'from mcp_server.db import test_connection; print(test_connection())'"
