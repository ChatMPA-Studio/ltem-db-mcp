# Troubleshooting Guide

**Purpose:** Common issues and solutions for MCP server deployment and operation

**Version:** 1.0.0  
**Last Updated:** February 16, 2026

---

## Authentication Issues

### Issue: 401 Unauthorized

**Symptoms:**
```bash
curl https://mcp.example.com/ltem/mcp
# Response: 401 Unauthorized
```

**Causes:**
1. Missing Basic Auth credentials
2. Incorrect username/password
3. Caddy Basic Auth not configured

**Solutions:**

```bash
# 1. Include auth credentials
curl -u username:password https://mcp.example.com/ltem/mcp

# 2. Verify Caddy config
sudo cat /etc/caddy/Caddyfile | grep basicauth

# 3. Regenerate password hash
caddy hash-password

# 4. Update Caddyfile and reload
sudo nano /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

---

### Issue: 403 Forbidden

**Symptoms:**
```bash
curl -u user:pass https://mcp.example.com/ltem/mcp
# Response: 403 Forbidden
```

**Causes:**
1. User has auth but insufficient permissions
2. IP whitelist blocking request
3. CORS policy blocking request

**Solutions:**

```bash
# Check Caddy access logs
sudo tail -f /var/log/caddy/access.log

# Verify no IP restrictions
sudo cat /etc/caddy/Caddyfile | grep -i "remote_ip"

# Test from different IP/location
```

---

## Routing Issues

### Issue: 502 Bad Gateway

**Symptoms:**
```bash
curl https://mcp.example.com/ltem/mcp
# Response: 502 Bad Gateway
```

**Causes:**
1. Container not running
2. Container crashed
3. Wrong port in Caddy config
4. Network connectivity issue

**Solutions:**

```bash
# 1. Check container status
docker compose ps
# Expected: STATUS = Up (healthy)

# 2. If not running, start it
docker compose up -d

# 3. Check container logs
docker compose logs --tail=50

# 4. Verify Caddy can reach container
docker compose exec caddy ping ltem-mcp

# 5. Check Caddy config
sudo cat /etc/caddy/Caddyfile | grep "reverse_proxy ltem-mcp"
# Should be: reverse_proxy ltem-mcp:8000
```

---

### Issue: 404 Not Found

**Symptoms:**
```bash
curl https://mcp.example.com/ltem/mcp
# Response: 404 Not Found
```

**Causes:**
1. Wrong subpath in URL
2. Caddy handle block missing
3. Typo in Caddyfile

**Solutions:**

```bash
# 1. Verify correct subpath
# Should be: /ltem/ (with trailing slash)
curl https://mcp.example.com/ltem/

# 2. Check Caddyfile handle blocks
sudo cat /etc/caddy/Caddyfile

# Expected:
# handle /ltem/* {
#     uri strip_prefix /ltem
#     reverse_proxy ltem-mcp:8000
# }

# 3. Reload Caddy
sudo systemctl reload caddy
```

---

## Container Health Issues

### Issue: Container Keeps Restarting

**Symptoms:**
```bash
docker compose ps
# STATUS: Restarting (1) 5 seconds ago
```

**Causes:**
1. Application crash on startup
2. Database connection failure
3. Missing environment variables
4. Port already in use

**Solutions:**

```bash
# 1. Check logs for error
docker compose logs --tail=100

# 2. Common errors and fixes:

# Error: "Can't connect to MySQL server"
# Fix: Check database host/credentials in .env
cat .env | grep LTEM_DB

# Error: "Port 8000 already in use"
# Fix: Change PORT in .env or stop conflicting service
netstat -tulpn | grep 8000

# Error: "ModuleNotFoundError"
# Fix: Rebuild container
docker compose build --no-cache
docker compose up -d

# 3. Test database connection
docker compose exec ltem-mcp python -c "from mcp_server.db import get_connection; get_connection()"
```

---

### Issue: Container Unhealthy

**Symptoms:**
```bash
docker compose ps
# STATUS: Up (unhealthy)
```

**Causes:**
1. Health check endpoint failing
2. Application running but not responding
3. Health check timeout too short

**Solutions:**

```bash
# 1. Check health check logs
docker inspect ltem-mcp | grep -A 10 Health

# 2. Test health endpoint manually
docker compose exec ltem-mcp curl http://localhost:8000/health

# 3. If health endpoint works, increase timeout in docker-compose.yml
# healthcheck:
#   timeout: 10s  # Increase if needed
#   interval: 30s
#   retries: 3

# 4. Restart container
docker compose restart
```

---

## Environment Variable Issues

### Issue: Environment Variables Not Loaded

**Symptoms:**
```python
# In logs:
KeyError: 'LTEM_DB_HOST'
```

**Causes:**
1. `.env` file missing
2. `.env` file not in correct location
3. Syntax error in `.env` file
4. docker-compose.yml not loading `.env`

**Solutions:**

```bash
# 1. Verify .env exists
ls -la .env

# 2. Check .env syntax (no spaces around =)
cat .env
# Correct: LTEM_DB_HOST=localhost
# Wrong:   LTEM_DB_HOST = localhost

# 3. Verify docker-compose.yml loads .env
cat docker-compose.yml | grep env_file
# Should have: env_file: .env

# 4. Restart container to reload env
docker compose down
docker compose up -d

# 5. Verify env vars inside container
docker compose exec ltem-mcp env | grep LTEM_DB
```

---

### Issue: Database Credentials Not Working

**Symptoms:**
```
Access denied for user 'mcp_readonly'@'host'
```

**Causes:**
1. Wrong password in `.env`
2. User doesn't exist in database
3. User doesn't have permissions
4. Host mismatch in MySQL user

**Solutions:**

```bash
# 1. Verify credentials in .env
cat .env | grep LTEM_DB

# 2. Test credentials directly
mysql -h $LTEM_DB_HOST -u $LTEM_DB_USER -p$LTEM_DB_PASSWORD $LTEM_DB_NAME

# 3. Check user exists in MySQL
mysql -u root -p -e "SELECT User, Host FROM mysql.user WHERE User='mcp_readonly';"

# 4. Check user permissions
mysql -u root -p -e "SHOW GRANTS FOR 'mcp_readonly'@'%';"

# 5. Recreate user if needed
mysql -u root -p <<EOF
DROP USER IF EXISTS 'mcp_readonly'@'%';
CREATE USER 'mcp_readonly'@'%' IDENTIFIED BY 'new_password';
GRANT SELECT ON ecological_monitoring.* TO 'mcp_readonly'@'%';
FLUSH PRIVILEGES;
EOF
```

---

## Database Connectivity Issues

### Issue: Can't Connect to Database

**Symptoms:**
```
pymysql.err.OperationalError: (2003, "Can't connect to MySQL server")
```

**Causes:**
1. Database host unreachable
2. Database not running
3. Firewall blocking connection
4. Wrong port

**Solutions:**

```bash
# 1. Test connectivity from container
docker compose exec ltem-mcp ping $LTEM_DB_HOST

# 2. Test port connectivity
docker compose exec ltem-mcp nc -zv $LTEM_DB_HOST $LTEM_DB_PORT

# 3. Check database is running
# On database server:
systemctl status mysql

# 4. Check firewall allows connection
# On database server:
sudo ufw status | grep 3306

# 5. Verify database host in .env
# If database is on same machine as MCP:
# Use: LTEM_DB_HOST=host.docker.internal (not localhost)
```

---

### Issue: Table Not Found

**Symptoms:**
```
pymysql.err.ProgrammingError: (1146, "Table 'db.table' doesn't exist")
```

**Causes:**
1. Wrong database name
2. Table actually doesn't exist
3. Case sensitivity issue

**Solutions:**

```bash
# 1. List tables in database
docker compose exec ltem-mcp python -c "
from mcp_server.db import execute_select
rows = execute_select('SHOW TABLES')
print([list(r.values())[0] for r in rows])
"

# 2. Check database name
docker compose exec ltem-mcp python -c "
from mcp_server.db import execute_select
rows = execute_select('SELECT DATABASE() as db')
print(rows[0]['db'])
"

# 3. Verify table name case
# MySQL on Linux is case-sensitive
# Check exact table name in database
```

---

## MCP Protocol Issues

### Issue: Invalid JSON-RPC Response

**Symptoms:**
```json
{
  "error": {
    "code": -32700,
    "message": "Parse error"
  }
}
```

**Causes:**
1. Malformed JSON in request
2. Missing required fields
3. Wrong Content-Type header

**Solutions:**

```bash
# 1. Validate JSON
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | jq .

# 2. Include required headers
curl -H "Content-Type: application/json" \
     -H "Accept: application/json, text/event-stream" \
     ...

# 3. Use proper JSON-RPC format
# Required fields: jsonrpc, id, method, params
```

---

### Issue: Method Not Found

**Symptoms:**
```json
{
  "error": {
    "code": -32601,
    "message": "Method not found"
  }
}
```

**Causes:**
1. Typo in method name
2. Method not implemented
3. Wrong MCP protocol version

**Solutions:**

```bash
# Valid methods:
# - initialize
# - tools/list
# - tools/call
# - resources/list
# - resources/read

# Check method spelling
curl ... -d '{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",  # Correct
  "params": {}
}'
```

---

### Issue: Tool Not Found

**Symptoms:**
```json
{
  "error": {
    "code": -32602,
    "message": "Tool not found: tool_name"
  }
}
```

**Causes:**
1. Tool name typo
2. Tool not registered
3. Tool module not loaded

**Solutions:**

```bash
# 1. List available tools
curl ... -d '{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}' | jq '.result.tools[].name'

# 2. Check tool is registered
docker compose exec ltem-mcp python -c "
from mcp_server.server import mcp
print([t.name for t in mcp.list_tools()])
"

# 3. Verify tool module exists
ls tools/*.py
```

---

## Performance Issues

### Issue: Slow Query Response

**Symptoms:**
- Tool calls take >5 seconds
- Timeout errors

**Causes:**
1. Missing database indexes
2. Large result set
3. Complex query
4. Network latency

**Solutions:**

```bash
# 1. Check query execution time
docker compose logs | grep "Query took"

# 2. Add database indexes
mysql -u root -p ecological_monitoring <<EOF
CREATE INDEX idx_year ON ltem_historical_database(Year);
CREATE INDEX idx_region ON ltem_historical_database(Region);
CREATE INDEX idx_species ON ltem_historical_database(Species);
EOF

# 3. Reduce result set size
# Modify tool to use LIMIT
# Or increase MAX_ROWS in security.py

# 4. Enable query caching (if appropriate)
```

---

### Issue: High Memory Usage

**Symptoms:**
```bash
docker stats ltem-mcp
# MEM USAGE: 800MB / 1GB (80%)
```

**Causes:**
1. Large query results
2. Memory leak
3. Too many concurrent requests

**Solutions:**

```bash
# 1. Set memory limits in docker-compose.yml
services:
  ltem-mcp:
    deploy:
      resources:
        limits:
          memory: 512M

# 2. Reduce MAX_ROWS in security.py
# From: MAX_ROWS = 10000
# To:   MAX_ROWS = 1000

# 3. Restart container to clear memory
docker compose restart

# 4. Monitor memory over time
watch -n 5 'docker stats ltem-mcp --no-stream'
```

---

## Deployment Issues

### Issue: Git Pull Fails

**Symptoms:**
```bash
git pull origin main
# error: Your local changes would be overwritten
```

**Causes:**
1. Local changes not committed
2. Merge conflict
3. Detached HEAD state

**Solutions:**

```bash
# 1. Stash local changes
git stash
git pull origin main
git stash pop

# 2. Or discard local changes
git reset --hard origin/main
git pull origin main

# 3. If in detached HEAD
git checkout main
git pull origin main
```

---

### Issue: Docker Build Fails

**Symptoms:**
```bash
docker compose build
# ERROR: failed to solve
```

**Causes:**
1. Network issue downloading packages
2. Syntax error in Dockerfile
3. Missing dependency

**Solutions:**

```bash
# 1. Retry with no cache
docker compose build --no-cache

# 2. Check Dockerfile syntax
cat Dockerfile

# 3. Build with verbose output
docker compose build --progress=plain

# 4. Check disk space
df -h
```

---

## Diagnostic Commands

### Quick Health Check

```bash
#!/bin/bash
echo "=== MCP Server Health Check ==="

echo -n "1. Container running: "
docker compose ps | grep -q "Up" && echo "✓" || echo "✗"

echo -n "2. Container healthy: "
docker compose ps | grep -q "healthy" && echo "✓" || echo "✗"

echo -n "3. Database connection: "
docker compose exec ltem-mcp python -c "from mcp_server.db import get_connection; get_connection()" 2>/dev/null && echo "✓" || echo "✗"

echo -n "4. HTTP endpoint: "
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health | grep -q "200" && echo "✓" || echo "✗"

echo -n "5. MCP initialize: "
curl -s http://localhost:8000/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' | grep -q "serverInfo" && echo "✓" || echo "✗"
```

---

### Collect Diagnostic Info

```bash
#!/bin/bash
echo "=== Diagnostic Information ==="
echo ""
echo "Date: $(date)"
echo ""
echo "=== Container Status ==="
docker compose ps
echo ""
echo "=== Container Logs (last 50 lines) ==="
docker compose logs --tail=50
echo ""
echo "=== Environment Variables ==="
docker compose exec ltem-mcp env | grep LTEM_DB | sed 's/PASSWORD=.*/PASSWORD=***/'
echo ""
echo "=== Disk Space ==="
df -h
echo ""
echo "=== Memory Usage ==="
docker stats ltem-mcp --no-stream
```

---

## Getting Help

### Before Asking for Help

1. Check this troubleshooting guide
2. Review container logs: `docker compose logs`
3. Test with diagnostic commands above
4. Try restarting: `docker compose restart`

### Information to Include

When reporting issues, include:

- **Error message** (exact text)
- **Container logs** (last 100 lines)
- **Steps to reproduce**
- **Environment** (OS, Docker version)
- **Configuration** (.env variables, sanitized)

### Support Channels

- **Documentation:** See `docs/` directory
- **GitHub Issues:** Report bugs and feature requests
- **Email:** contact@example.com

---

## See Also

- [docs/infrastructure.md](infrastructure.md) - Hosting setup
- [docs/deployment_workflow.md](deployment_workflow.md) - Deployment process
- [docs/api_examples.md](api_examples.md) - API usage examples

---

**Version:** 1.0.0  
**Last Review:** February 16, 2026
