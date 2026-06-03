# MCP Infrastructure Documentation

**Purpose:** Single source of truth for how MCPs run in production

**Last Updated:** February 16, 2026  
**Environment:** Production (DigitalOcean Droplet)

---

## Current Hosting

### Server Specifications

- **Provider:** DigitalOcean
- **OS:** Ubuntu 24.04 LTS
- **Instance Type:** Droplet (4GB RAM, 2 vCPUs)
- **Public IP:** `<your-droplet-ip>`
- **Domain:** `mcp.example.com` (via Caddy)

### Technology Stack

- **Container Runtime:** Docker + Docker Compose
- **Reverse Proxy:** Caddy 2.x
- **Authentication:** Basic Auth (Phase 0)
- **SSL/TLS:** Automatic via Caddy (Let's Encrypt)

---

## Network Model

### Architecture Overview

```
Internet
    ↓
Caddy (Port 80/443) ← Public ingress point
    ↓
Docker Network (bridge) ← Private network
    ├── ltem-mcp:8000
    ├── sst-mcp:8000
    └── catches-mcp:8000
```

### Key Principles

1. **Caddy is the ONLY public ingress**
   - All HTTP/HTTPS traffic goes through Caddy
   - MCP containers are NOT exposed directly to the internet
   - Caddy handles SSL/TLS termination

2. **MCP containers are private**
   - Run on Docker bridge network
   - Only accessible from Caddy
   - Internal port: 8000 (standard)
   - No host port mapping needed

3. **Subpath routing**
   - Each MCP mounted under unique subpath
   - Examples: `/ltem/`, `/sst/`, `/catches/`
   - Caddy strips prefix before forwarding

---

## Routing Standard

### Rule 1: One MCP = One Subpath

Each MCP server gets a unique subpath:

```
https://mcp.example.com/ltem/     → ltem-mcp:8000/mcp
https://mcp.example.com/sst/      → sst-mcp:8000/mcp
https://mcp.example.com/catches/  → catches-mcp:8000/mcp
```

### Rule 2: Subpath Always Ends with `/`

**Correct:**
- `/ltem/`
- `/sst/`
- `/catches/`

**Incorrect:**
- `/ltem` (missing trailing slash)
- `/ltem-mcp/` (don't include "mcp" in subpath)

### Rule 3: Internal Port is 8000

All MCP containers listen on port 8000 internally:

```yaml
# docker-compose.yml
services:
  ltem-mcp:
    ports:
      - "8000"  # Internal only, no host mapping
```

**Never expose directly to host:**
```yaml
# ❌ WRONG - Don't do this in production
ports:
  - "8001:8000"  # Bypasses Caddy security
```

---

## Caddy Configuration

### Caddyfile Location

```
/etc/caddy/Caddyfile
```

### Golden Example: Subpath Rule

```caddy
mcp.example.com {
    # LTEM MCP
    handle /ltem/* {
        uri strip_prefix /ltem
        reverse_proxy ltem-mcp:8000
    }
    
    # SST MCP
    handle /sst/* {
        uri strip_prefix /sst
        reverse_proxy sst-mcp:8000
    }
    
    # Catches MCP
    handle /catches/* {
        uri strip_prefix /catches
        reverse_proxy catches-mcp:8000
    }
    
    # Default response
    respond "MCP Server Portfolio" 200
}
```

### Explanation

1. **`handle /ltem/*`** - Match all requests starting with `/ltem/`
2. **`uri strip_prefix /ltem`** - Remove `/ltem` before forwarding
3. **`reverse_proxy ltem-mcp:8000`** - Forward to container on Docker network

**Result:** `https://mcp.example.com/ltem/mcp` → `http://ltem-mcp:8000/mcp`

### Reload Caddy

```bash
sudo systemctl reload caddy
```

---

## Authentication Standard

### Phase 0: Basic Auth at Caddy Layer

**Current Implementation:**

```caddy
mcp.example.com {
    # Basic Auth for all MCPs
    basicauth {
        user $2a$14$hashed_password_here
    }
    
    handle /ltem/* {
        uri strip_prefix /ltem
        reverse_proxy ltem-mcp:8000
    }
    # ... other MCPs
}
```

**Generate password hash:**

```bash
caddy hash-password
```

### Phase 2: OAuth/JWT (Future)

**Planned Implementation:**
- OAuth 2.0 via Caddy auth middleware
- JWT validation at Caddy layer
- Or upstream API Gateway (AWS ALB, Cloudflare)

### Rule: MCP Servers Don't Implement Auth

**In Phase 0:**
- MCP containers assume authenticated requests
- No auth logic in `mcp_server/` code
- Caddy handles all authentication

**Rationale:**
- Separation of concerns
- Easier to upgrade auth (change Caddy config only)
- MCP code stays simple

---

## Environment Variables

### Rule 1: `.env` Exists Only on Server

**On Server:**
```bash
/opt/ltem-db-mcp/.env  # Contains secrets
```

**In Repository:**
```bash
.env.example  # Template only, no secrets
```

### Rule 2: Secrets Never Committed

**Add to `.gitignore`:**
```
.env
*.env
!.env.example
```

### Rule 3: Docker Compose Loads from `.env`

**docker-compose.yml:**
```yaml
services:
  ltem-mcp:
    env_file:
      - .env  # Automatically loaded
    environment:
      - PORT=${PORT}
      - LOG_LEVEL=${LOG_LEVEL}
```

### Example `.env` Structure

```bash
# Server
PORT=8000
MCP_BASE_PATH=/mcp
LOG_LEVEL=INFO

# Database
LTEM_DB_HOST=db.example.com
LTEM_DB_PORT=3306
LTEM_DB_USER=mcp_readonly
LTEM_DB_PASSWORD=<secret>
LTEM_DB_NAME=ecological_monitoring

# Docker
COMPOSE_PROJECT_NAME=ltem-mcp
```

---

## Logs + Observability

### Minimum Logging (Phase 0)

#### 1. Caddy Access Logs

**Location:** `/var/log/caddy/access.log`

**View:**
```bash
sudo tail -f /var/log/caddy/access.log
```

**Rotation:** Automatic (systemd)

#### 2. Container Logs

**View all containers:**
```bash
cd /opt/ltem-db-mcp
docker compose logs -f
```

**View specific container:**
```bash
docker compose logs -f ltem-mcp
```

**Last 100 lines:**
```bash
docker compose logs --tail=100 ltem-mcp
```

#### 3. Application Logs

MCP servers log to stdout/stderr:
- Docker captures automatically
- Accessible via `docker compose logs`
- No file-based logging needed

### Log Retention

- **Caddy logs:** 30 days (systemd default)
- **Container logs:** Unlimited (configure if needed)

**Configure container log rotation:**
```yaml
services:
  ltem-mcp:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## AWS Migration Notes

### Target Patterns

#### Option 1: EC2 (Simple)
- Same as current DigitalOcean setup
- Ubuntu 24.04 on EC2 instance
- Docker + Caddy
- Elastic IP for static address

#### Option 2: ECS/Fargate (Portfolio Scale)
- Container orchestration
- Auto-scaling
- No server management
- ALB for routing (replaces Caddy)

### Keep Stable: Reverse Proxy + Subpath Routing

**Regardless of platform:**
- Maintain subpath routing concept
- One MCP = one subpath
- Reverse proxy handles ingress

**AWS Equivalents:**
- **Caddy** → ALB (Application Load Balancer) or API Gateway
- **Docker Network** → ECS Service Discovery or VPC
- **Subpath routing** → ALB path-based routing rules

### Phase 2 Additions

#### Container Registry
- **Current:** Local Docker builds
- **Phase 2:** GHCR (GitHub Container Registry) or ECR (AWS)

**Workflow:**
```
GitHub Actions → Build Image → Push to GHCR → Pull on server
```

---

## Deployment Workflow

### Current (Phase 0): Manual Deploy

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
```

### Future (Phase 2): Semi-Automated

```bash
# GitHub Actions builds and pushes image
# On server, just pull and restart
docker compose pull
docker compose up -d
```

---

## Health Checks

### Container Health

```bash
# Check all containers
docker compose ps

# Expected output:
# NAME        STATUS
# ltem-mcp    Up (healthy)
```

### HTTP Health Check

```bash
# Test MCP endpoint
curl -u user:pass https://mcp.example.com/ltem/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}'
```

### Caddy Health

```bash
# Check Caddy status
sudo systemctl status caddy

# Test SSL certificate
curl -I https://mcp.example.com
```

---

## Troubleshooting

### 502 Bad Gateway

**Cause:** Container not running or unreachable

**Fix:**
```bash
docker compose ps  # Check container status
docker compose up -d  # Restart if needed
```

### 404 Not Found

**Cause:** Subpath routing misconfigured

**Fix:**
```bash
# Check Caddyfile
sudo cat /etc/caddy/Caddyfile

# Verify handle blocks match subpaths
# Reload Caddy
sudo systemctl reload caddy
```

### Auth Failures

**Cause:** Basic auth credentials incorrect

**Fix:**
```bash
# Regenerate password hash
caddy hash-password

# Update Caddyfile
sudo nano /etc/caddy/Caddyfile

# Reload
sudo systemctl reload caddy
```

---

## Security Checklist

- [ ] Caddy is the only public ingress
- [ ] MCP containers not exposed to host
- [ ] Basic Auth enabled on all MCPs
- [ ] SSL/TLS certificates valid
- [ ] `.env` file not in git
- [ ] Database uses read-only user
- [ ] Firewall allows only 80/443
- [ ] SSH key-based auth only
- [ ] Regular security updates applied

---

## Maintenance

### Weekly
- [ ] Check container logs for errors
- [ ] Verify SSL certificate expiry (Caddy auto-renews)
- [ ] Review Caddy access logs

### Monthly
- [ ] Update Ubuntu packages: `sudo apt update && sudo apt upgrade`
- [ ] Update Docker: `sudo apt install docker-ce docker-ce-cli`
- [ ] Review disk usage: `df -h`

### Quarterly
- [ ] Review and rotate secrets
- [ ] Audit access logs
- [ ] Test backup/restore procedures

---

## Contact

**Infrastructure Owner:** DevOps Team  
**On-Call:** See PagerDuty rotation  
**Documentation:** This file + `DEPLOYMENT.md`

---

**Version:** 1.0.0  
**Last Review:** February 16, 2026
