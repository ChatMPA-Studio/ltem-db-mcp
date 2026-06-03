# Tutorial 07: Docker Deployment

**Time:** 60 minutes  
**Difficulty:** Intermediate

## Learning Objectives

- Build Docker images for MCP server
- Configure docker-compose
- Deploy with Caddy reverse proxy
- Manage environment variables securely
- Test production deployment

## Prerequisites

- Completed [Tutorial 06: Security Configuration](quick-06-security-config.md)
- Docker and Docker Compose installed
- Basic Docker knowledge

## Step 1: Review Dockerfile

The template includes a production-ready Dockerfile:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Copy application code
COPY mcp_server/ ./mcp_server/
COPY tools/ ./tools/
COPY skills/ ./skills/
COPY resources/ ./resources/
COPY metadata/ ./metadata/

# Create non-root user
RUN useradd -m -u 1000 mcpuser && chown -R mcpuser:mcpuser /app
USER mcpuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python healthcheck.py || exit 1

# Run server
CMD ["python", "-m", "uvicorn", "mcp_server.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Step 2: Configure docker-compose.yml

Update `docker-compose.yml`:

```yaml
version: '3.8'

services:
  mcp-server:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: my-mcp-server
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - MYDB_HOST=${MYDB_HOST}
      - MYDB_PORT=${MYDB_PORT}
      - MYDB_USER=${MYDB_USER}
      - MYDB_PASSWORD=${MYDB_PASSWORD}
      - MYDB_NAME=${MYDB_NAME}
      - PORT=8000
      - MCP_BASE_PATH=/mcp
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
    networks:
      - mcp-network
    healthcheck:
      test: ["CMD", "python", "healthcheck.py"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  caddy:
    image: caddy:2-alpine
    container_name: mcp-caddy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    networks:
      - mcp-network
    depends_on:
      - mcp-server

networks:
  mcp-network:
    driver: bridge

volumes:
  caddy_data:
  caddy_config:
```

## Step 3: Create Caddyfile

Create `Caddyfile` for reverse proxy:

```
# Development (HTTP only)
:80 {
    reverse_proxy /mcp/* mcp-server:8000
    
    # CORS headers
    header {
        Access-Control-Allow-Origin *
        Access-Control-Allow-Methods "GET, POST, OPTIONS"
        Access-Control-Allow-Headers "Content-Type, Authorization"
    }
    
    # Logging
    log {
        output file /var/log/caddy/access.log
    }
}

# Production (HTTPS with automatic certificates)
# your-domain.com {
#     reverse_proxy /mcp/* mcp-server:8000
#     
#     # Security headers
#     header {
#         Strict-Transport-Security "max-age=31536000;"
#         X-Content-Type-Options "nosniff"
#         X-Frame-Options "DENY"
#         X-XSS-Protection "1; mode=block"
#     }
#     
#     # Rate limiting
#     rate_limit {
#         zone dynamic {
#             key {remote_host}
#             events 100
#             window 1m
#         }
#     }
# }
```

## Step 4: Create Health Check Script

Create `healthcheck.py`:

```python
#!/usr/bin/env python3
"""Health check script for Docker container."""

import sys
import os

def check_health():
    """Perform health checks."""
    try:
        # Check database connection
        from mcp_server.db import test_connection
        result = test_connection()
        
        if not result:
            print("Database connection failed")
            return False
        
        print("Health check passed")
        return True
        
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

if __name__ == "__main__":
    sys.exit(0 if check_health() else 1)
```

## Step 5: Build and Run

### Build Image

```bash
# Build image
docker compose build

# Or build with no cache
docker compose build --no-cache
```

### Run Locally

```bash
# Start services
docker compose up -d

# View logs
docker compose logs -f mcp-server

# Check health
docker compose ps
```

### Test Deployment

```bash
# Test health endpoint
curl http://localhost/mcp/health

# Test MCP endpoint
curl http://localhost/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'
```

## Step 6: Environment Variables

### Development (.env)

```bash
# Database
MYDB_HOST=your-dev-db.com
MYDB_PORT=3306
MYDB_USER=mcp_readonly
MYDB_PASSWORD=dev_password
MYDB_NAME=dev_database

# Server
PORT=8000
MCP_BASE_PATH=/mcp
LOG_LEVEL=DEBUG
```

### Production (.env.production)

```bash
# Database
MYDB_HOST=your-prod-db.com
MYDB_PORT=3306
MYDB_USER=mcp_readonly
MYDB_PASSWORD=${PROD_DB_PASSWORD}  # From secrets
MYDB_NAME=prod_database

# Server
PORT=8000
MCP_BASE_PATH=/mcp
LOG_LEVEL=INFO

# Security
ALLOWED_ORIGINS=https://your-domain.com
```

**Never commit `.env` files!** Use environment-specific files and secrets management.

## Step 7: Production Deployment

### Option A: Manual Deployment

```bash
# On production server
git pull origin main

# Copy production env
cp .env.production .env

# Build and start
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verify
docker compose ps
docker compose logs -f
```

### Option B: CI/CD with GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker image
        run: docker compose build
      
      - name: Run tests
        run: docker compose run --rm mcp-server pytest
      
      - name: Deploy to server
        if: startsWith(github.ref, 'refs/tags/v')
        env:
          SSH_KEY: ${{ secrets.SSH_KEY }}
          SERVER_HOST: ${{ secrets.SERVER_HOST }}
        run: |
          # SSH and deploy
          ssh -i $SSH_KEY user@$SERVER_HOST << 'EOF'
            cd /app/mcp-server
            git pull
            docker compose up -d --build
          EOF
```

## Step 8: Monitoring and Logs

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f mcp-server

# Last 100 lines
docker compose logs --tail=100 mcp-server
```

### Monitor Resources

```bash
# Container stats
docker stats

# Disk usage
docker system df
```

### Log Rotation

Add to `docker-compose.yml`:

```yaml
services:
  mcp-server:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Step 9: Backup and Restore

### Backup

```bash
# Backup volumes
docker run --rm \
  -v mcp_caddy_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/caddy-data-$(date +%Y%m%d).tar.gz /data
```

### Restore

```bash
# Restore volumes
docker run --rm \
  -v mcp_caddy_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/caddy-data-20240101.tar.gz -C /
```

## Step 10: Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose logs mcp-server

# Check health
docker compose ps

# Inspect container
docker inspect my-mcp-server
```

### Database Connection Issues

```bash
# Test from container
docker compose exec mcp-server python -c "from mcp_server.db import test_connection; print(test_connection())"

# Check network
docker compose exec mcp-server ping your-db-host
```

### Port Conflicts

```bash
# Check what's using port 8000
lsof -i :8000

# Change port in docker-compose.yml
ports:
  - "8001:8000"  # External:Internal
```

## Common Issues

### Issue: "Cannot connect to Docker daemon"

**Solution:** Start Docker service:
```bash
sudo systemctl start docker
```

### Issue: "Port already in use"

**Solution:** Stop conflicting service or change port:
```bash
docker compose down
# Or change port in docker-compose.yml
```

### Issue: Container exits immediately

**Solution:** Check logs for errors:
```bash
docker compose logs mcp-server
```

## Production Checklist

- [ ] Dockerfile reviewed and optimized
- [ ] docker-compose.yml configured
- [ ] Caddyfile created with HTTPS
- [ ] Health check script working
- [ ] Environment variables set
- [ ] Secrets managed securely
- [ ] Logs configured with rotation
- [ ] Monitoring set up
- [ ] Backup strategy implemented
- [ ] Deployment tested locally
- [ ] Production deployment successful
- [ ] SSL certificates working
- [ ] Rate limiting configured

## Security Best Practices

### 1. Use Non-Root User

```dockerfile
RUN useradd -m -u 1000 mcpuser
USER mcpuser
```

### 2. Minimize Image Size

```dockerfile
FROM python:3.11-slim  # Use slim variant
RUN apt-get clean && rm -rf /var/lib/apt/lists/*
```

### 3. Use Multi-Stage Builds

```dockerfile
# Build stage
FROM python:3.11 as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
```

### 4. Scan for Vulnerabilities

```bash
# Scan image
docker scan my-mcp-server:latest
```

## Next Steps

✅ Your MCP server is now deployed!

**Next tutorial:** [Testing MCP](quick-08-testing-mcp.md)

Learn how to:
- Write comprehensive tests
- Test tools and resources
- Integration testing
- CI/CD testing

## Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Caddy Documentation](https://caddyserver.com/docs/)
- [Docker Security](https://docs.docker.com/engine/security/)
