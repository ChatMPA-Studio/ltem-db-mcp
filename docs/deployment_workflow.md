# Deployment Workflow

**Purpose:** Define CI/CD rules and deployment processes for MCP servers

**Version:** 1.0.0  
**Last Updated:** February 16, 2026

---

## Baseline Workflow (Phase 0)

### Principles

1. **GitHub is source of truth** - All code changes go through GitHub
2. **main always deployable** - Never commit broken code to main
3. **Tags are immutable** - Once tagged, never change
4. **Manual deploy** - SSH + git pull + rebuild (Phase 0)
5. **Explicit rollback** - Always have a rollback plan

---

## Versioning Rules

### Semantic Versioning (X.Y.Z)

- **X (Major):** Breaking changes to API or data structure
- **Y (Minor):** New features, backward compatible
- **Z (Patch):** Bug fixes, no new features

### Branch Strategy

```
main          # Production-ready code
├── v1.2.0    # Release tags
├── v1.1.0
└── v1.0.0

develop       # Integration branch (optional)
├── feature/new-tool
├── feature/new-skill
└── bugfix/query-error
```

### Tagging Convention

```bash
# Create release tag
git tag -a v1.2.0 -m "Release 1.2.0: Add new statistical tools"
git push origin v1.2.0

# List tags
git tag -l

# Checkout specific version
git checkout v1.2.0
```

---

## Deployment Options

### Option 1: Manual Deploy (Default for Phase 0)

**When to use:** Small teams, low deployment frequency

**Process:**

```bash
# 1. SSH to server
ssh user@mcp.example.com

# 2. Navigate to project
cd /opt/ltem-db-mcp

# 3. Pull latest code
git pull origin main

# 4. Rebuild container
docker compose build

# 5. Restart service
docker compose up -d

# 6. Verify
docker compose ps
docker compose logs --tail=50

# 7. Test endpoint
curl -u user:pass https://mcp.example.com/ltem/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}'
```

**Pros:**
- Simple, no CI/CD setup needed
- Full control over deployment
- Easy to troubleshoot

**Cons:**
- Manual steps prone to error
- No automated testing
- Requires SSH access

---

### Option 2: Semi-Automated Deploy (Recommended for Phase 1)

**When to use:** Regular deployments, multiple MCPs

**Process:**

#### A. GitHub Actions Build

Create `.github/workflows/build.yml`:

```yaml
name: Build and Push Docker Image

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Login to GitHub Container Registry
        uses: docker/login-action@v2
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Extract version from tag
        id: version
        run: echo "VERSION=${GITHUB_REF#refs/tags/v}" >> $GITHUB_OUTPUT
      
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: |
            ghcr.io/${{ github.repository }}:${{ steps.version.outputs.VERSION }}
            ghcr.io/${{ github.repository }}:latest
```

#### B. Server-Side Pull

On server, create `scripts/pull_and_restart.sh`:

```bash
#!/bin/bash
set -e

PROJECT_DIR="/opt/ltem-db-mcp"
cd "$PROJECT_DIR"

echo "Pulling latest image..."
docker compose pull

echo "Restarting service..."
docker compose up -d

echo "Verifying deployment..."
sleep 5
docker compose ps
docker compose logs --tail=20

echo "✓ Deployment complete"
```

#### C. Deploy

```bash
# On server
cd /opt/ltem-db-mcp
bash scripts/pull_and_restart.sh
```

**Pros:**
- Automated image building
- Consistent builds
- Version tracking via tags

**Cons:**
- Still requires manual trigger on server
- No automated testing

---

### Option 3: Fully Automated (Phase 2)

**When to use:** High deployment frequency, multiple environments

**Process:**

1. **Push to main** → Triggers GitHub Actions
2. **Run tests** → pytest, integration tests
3. **Build image** → Push to GHCR
4. **Deploy to staging** → Automatic
5. **Run smoke tests** → Verify staging
6. **Deploy to production** → Manual approval or automatic
7. **Verify** → Health checks

**Implementation:** See Phase 2 documentation

---

## Rollback Protocol

### Quick Rollback (Same Version)

If deployment fails but code is fine:

```bash
# Restart with existing image
docker compose restart

# Or rebuild from current code
docker compose down
docker compose up -d --build
```

### Version Rollback (Previous Release)

If new version has bugs:

```bash
# 1. Identify last known-good tag
git tag -l
# Example: v1.1.0 was working

# 2. Checkout that version
git checkout v1.1.0

# 3. Rebuild and restart
docker compose down
docker compose build
docker compose up -d

# 4. Verify
docker compose logs --tail=50
```

### Image Rollback (Using GHCR)

If using container registry:

```bash
# 1. Update docker-compose.yml to use specific version
# Change: image: ghcr.io/org/ltem-mcp:latest
# To:     image: ghcr.io/org/ltem-mcp:1.1.0

# 2. Pull and restart
docker compose pull
docker compose up -d
```

---

## Pre-Deployment Checklist

Before deploying to production:

### Code Quality
- [ ] All tests pass locally: `pytest tests/ -v`
- [ ] No linting errors: `ruff check .`
- [ ] Code reviewed (if team > 1)
- [ ] CHANGELOG.md updated

### Configuration
- [ ] `.env` file updated on server (if needed)
- [ ] Database migrations applied (if any)
- [ ] New environment variables documented in `.env.example`

### Testing
- [ ] Smoke tests pass: `pytest tests/test_smoke.py -v`
- [ ] Integration tests pass (if applicable)
- [ ] Manual testing completed

### Documentation
- [ ] README.md updated (if API changed)
- [ ] API examples updated (if new tools/skills)
- [ ] Metadata updated: `python scripts/generate_metadata_manifest.py`

### Backup
- [ ] Database backup created (if schema changes)
- [ ] Previous version tagged
- [ ] Rollback plan documented

---

## Post-Deployment Verification

After deployment, verify:

### 1. Container Health

```bash
# Check container status
docker compose ps

# Expected: STATUS = Up (healthy)
```

### 2. Logs

```bash
# Check for errors
docker compose logs --tail=100 | grep -i error

# Should be clean or only expected warnings
```

### 3. MCP Endpoint

```bash
# Test initialize
curl -u user:pass https://mcp.example.com/ltem/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "test", "version": "0.1"}
    }
  }'

# Expected: 200 OK with serverInfo
```

### 4. Tools List

```bash
# Verify tools are available
curl -u user:pass https://mcp.example.com/ltem/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session: <session-from-init>" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }'

# Expected: List of tools
```

### 5. Database Connectivity

```bash
# Test a simple query tool
curl -u user:pass https://mcp.example.com/ltem/mcp \
  -H "Content-Type: application/json" \
  -H "Mcp-Session: <session-from-init>" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "get_regions",
      "arguments": {}
    }
  }'

# Expected: List of regions
```

---

## Deployment Environments

### Development (Local)

```bash
# .env.development
LTEM_DB_HOST=localhost
LTEM_DB_NAME=ltem_dev
LOG_LEVEL=DEBUG
```

### Staging (Optional)

```bash
# .env.staging
LTEM_DB_HOST=staging-db.example.com
LTEM_DB_NAME=ltem_staging
LOG_LEVEL=INFO
```

### Production

```bash
# .env.production
LTEM_DB_HOST=prod-db.example.com
LTEM_DB_NAME=ecological_monitoring
LOG_LEVEL=WARNING
```

---

## Container Registry Setup (Phase 1)

### GitHub Container Registry (GHCR)

#### 1. Enable GHCR

```bash
# Create personal access token with packages:write scope
# Settings → Developer settings → Personal access tokens
```

#### 2. Login to GHCR

```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
```

#### 3. Build and Push

```bash
# Build
docker build -t ghcr.io/your-org/ltem-mcp:1.2.0 .

# Push
docker push ghcr.io/your-org/ltem-mcp:1.2.0
docker push ghcr.io/your-org/ltem-mcp:latest
```

#### 4. Pull on Server

```bash
# Update docker-compose.yml
services:
  ltem-mcp:
    image: ghcr.io/your-org/ltem-mcp:latest
    # ... rest of config

# Pull and restart
docker compose pull
docker compose up -d
```

---

## Monitoring Deployment

### Health Checks

```bash
# Continuous monitoring
watch -n 5 'docker compose ps && echo && docker compose logs --tail=5'
```

### Metrics to Track

- **Container uptime:** `docker compose ps`
- **Memory usage:** `docker stats ltem-mcp --no-stream`
- **Response time:** `curl -w "@curl-format.txt" -o /dev/null -s https://...`
- **Error rate:** `docker compose logs | grep -c ERROR`

### Alerts (Phase 2)

- Container down
- High memory usage (>80%)
- High error rate (>5%)
- Slow response time (>2s)

---

## Troubleshooting Deployments

### Issue: Container won't start

```bash
# Check logs
docker compose logs

# Common causes:
# - Missing .env file
# - Database unreachable
# - Port already in use
# - Syntax error in code
```

### Issue: Old code still running

```bash
# Force rebuild
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Issue: Database connection fails

```bash
# Test database connectivity
docker compose exec ltem-mcp python -c "from mcp_server.db import get_connection; get_connection()"

# Check .env file
docker compose exec ltem-mcp env | grep LTEM_DB
```

---

## Best Practices

### 1. Always Tag Releases

```bash
# Bad: Deploy from main without tag
git push origin main
# Deploy...

# Good: Tag first, then deploy
git tag -a v1.2.0 -m "Release 1.2.0"
git push origin v1.2.0
# Deploy v1.2.0
```

### 2. Test Before Deploying

```bash
# Run full test suite
pytest tests/ -v

# Run smoke tests
pytest tests/test_smoke.py -v

# Manual testing
docker compose up
# Test endpoints...
```

### 3. Deploy During Low Traffic

- Avoid peak hours
- Schedule maintenance windows
- Notify users if downtime expected

### 4. One Change at a Time

- Don't bundle unrelated changes
- Makes rollback easier
- Easier to identify issues

### 5. Document Everything

- Update CHANGELOG.md
- Document breaking changes
- Update API examples

---

## See Also

- [docs/infrastructure.md](infrastructure.md) - Hosting setup
- [DEPLOYMENT.md](../DEPLOYMENT.md) - Deployment instructions
- [docs/troubleshooting.md](troubleshooting.md) - Common issues

---

**Version:** 1.0.0  
**Last Review:** February 16, 2026
