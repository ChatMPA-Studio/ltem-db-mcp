---
name: healthcheck
description: Minimal validation skill
version: 1.0.0
---

# Health Check Skill

## Purpose

Verify MCP server health by calling basic tools and checking responses.

**Use cases:**
- Server startup validation
- Deployment verification
- Automated monitoring
- Smoke testing

## Workflow

### Step 1: List Tables

**Tool:** `list_tables`  
**Parameters:** None  
**Expected:** Returns list of available tables

```json
{
  "tables": ["ltem_historical_database"],
  "count": 1
}
```

### Step 2: Get Regions

**Tool:** `get_regions`  
**Parameters:** None  
**Expected:** Returns list of surveyed regions

```json
{
  "regions": ["Cabo Pulmo", "La Paz", "Loreto", ...]
}
```

### Step 3: Verify Response Times

**Check:** Both tools respond within 5 seconds  
**Check:** No errors raised  
**Check:** Valid JSON returned

## Success Criteria

✅ **Pass if:**
- Both tools return valid JSON
- No exceptions raised
- Response time < 5 seconds total
- Data structures match expected format

❌ **Fail if:**
- Any tool raises exception
- Invalid JSON returned
- Timeout (>5 seconds)
- Empty or null responses

## Output

```json
{
  "status": "healthy",
  "checks": {
    "list_tables": {
      "status": "pass",
      "response_time": "0.12s",
      "tables_count": 1
    },
    "get_regions": {
      "status": "pass",
      "response_time": "0.08s",
      "regions_count": 14
    }
  },
  "total_time": "0.20s",
  "timestamp": "2026-02-16T18:00:00Z"
}
```

## Error Handling

**If database unreachable:**
```json
{
  "status": "unhealthy",
  "error": "Database connection failed",
  "checks": {
    "list_tables": {
      "status": "fail",
      "error": "Can't connect to MySQL server"
    }
  }
}
```

## Usage

**Via MCP client:**
```python
result = client.call_skill("healthcheck", {})
print(result["status"])  # "healthy" or "unhealthy"
```

**Via curl:**
```bash
curl http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "skills/call",
    "params": {
      "name": "healthcheck",
      "arguments": {}
    }
  }'
```

## Notes

- This skill requires no input parameters
- Designed for automated monitoring
- Should complete in <5 seconds
- Safe to run frequently (read-only operations)

## See Also

- [skills/registry.py](../registry.py) - Skills catalog
- [docs/skills_architecture.md](../../docs/skills_architecture.md) - Skills design
