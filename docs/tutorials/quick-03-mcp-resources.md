# Tutorial 03: Add MCP Resources

**Time:** 40 minutes  
**Difficulty:** Beginner

## Learning Objectives

- Understand MCP resources vs tools
- Expose database schema as a resource
- Create documentation resources
- Make data dictionaries discoverable

## Prerequisites

- Completed [Tutorial 02: Create First Tool](quick-02-first-tool.md)
- Working MCP server with tools

## What are MCP Resources?

**Resources** are static or semi-static content that AI assistants can read:
- Database schemas
- Documentation
- Data dictionaries
- API specifications
- Configuration files

**Tools vs Resources:**
- **Tools** = Actions (query data, run analysis)
- **Resources** = Information (read schema, view docs)

## Step 1: Create Schema Resource

Add to `mcp_server/server.py`:

```python
@mcp.resource("mydb://schema/tables")
def schema_tables_resource() -> str:
    """List all tables with column information."""
    from mcp_server.schema import build_schema_snapshot
    return json.dumps(build_schema_snapshot(), indent=2)
```

Create `mcp_server/schema.py`:

```python
"""Database schema discovery utilities."""

import json
from typing import Dict, List, Any
from mcp_server.db import get_connection

def discover_tables() -> List[str]:
    """Get list of all tables in database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = [list(row.values())[0] for row in cursor.fetchall()]
    conn.close()
    return tables

def describe_table(table: str) -> List[Dict[str, Any]]:
    """Get column information for a table."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"DESCRIBE {table}")
    columns = cursor.fetchall()
    conn.close()
    return columns

def build_schema_snapshot() -> Dict[str, Any]:
    """Build complete schema snapshot with all tables and columns."""
    tables = discover_tables()
    schema = {}
    
    for table in tables:
        columns = describe_table(table)
        schema[table] = {
            "columns": columns,
            "column_count": len(columns)
        }
    
    return {
        "tables": schema,
        "table_count": len(tables)
    }
```

## Step 2: Add Data Dictionary Resource

Create `resources/data_dictionary.md`:

```markdown
# Data Dictionary

## Tables

### your_main_table

**Description:** Primary data table containing...

**Columns:**
- `id` (INT) - Primary key, auto-increment
- `name` (VARCHAR) - Entity name
- `created_at` (DATETIME) - Record creation timestamp
- `value` (DECIMAL) - Measured value

**Relationships:**
- Foreign key to `lookup_table.id`

**Indexes:**
- PRIMARY KEY on `id`
- INDEX on `created_at`

### lookup_table

**Description:** Reference data for...

**Columns:**
- `id` (INT) - Primary key
- `code` (VARCHAR) - Lookup code
- `description` (TEXT) - Full description
```

Add resource to `mcp_server/server.py`:

```python
@mcp.resource("mydb://data-dictionary")
def data_dictionary_resource() -> str:
    """Data dictionary with table and column descriptions."""
    dict_path = Path(__file__).parent.parent / "resources" / "data_dictionary.md"
    return dict_path.read_text(encoding="utf-8")
```

## Step 3: Add Metadata Resources

Expose metadata files as resources:

```python
@mcp.resource("mydb://metadata/manifest")
def metadata_manifest_resource() -> str:
    """Server metadata manifest."""
    manifest_path = Path(__file__).parent.parent / "metadata" / "manifest.json"
    if manifest_path.exists():
        return manifest_path.read_text(encoding="utf-8")
    return json.dumps({"error": "Manifest not found"})

@mcp.resource("mydb://metadata/package")
def metadata_package_resource() -> str:
    """Package metadata: name, version, description."""
    manifest_path = Path(__file__).parent.parent / "metadata" / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return json.dumps(manifest.get("package", {}), indent=2)
    return json.dumps({"error": "Manifest not found"})
```

## Step 4: Test Resources

Start MCP server and test:

```bash
fastmcp run mcp_server/server.py:mcp --transport stdio
```

Use MCP Inspector to test resources:

1. Open `http://localhost:5173`
2. Click "Resources" tab
3. You should see:
   - `mydb://schema/tables`
   - `mydb://data-dictionary`
   - `mydb://metadata/manifest`
   - `mydb://metadata/package`

Click each resource to view content.

## Step 5: Resource Best Practices

### 1. Use Descriptive URIs

**Good:**
```python
@mcp.resource("mydb://schema/tables")
@mcp.resource("mydb://docs/api-guide")
@mcp.resource("mydb://metadata/version")
```

**Bad:**
```python
@mcp.resource("resource1")
@mcp.resource("data")
```

### 2. Return Appropriate Formats

- **JSON** for structured data (schemas, metadata)
- **Markdown** for documentation
- **Plain text** for simple content

### 3. Keep Resources Lightweight

Resources should be quick to read:
- Cache expensive computations
- Limit data size
- Use pagination for large datasets

### 4. Document Resource Purpose

```python
@mcp.resource("mydb://schema/tables")
def schema_resource() -> str:
    """Complete database schema with all tables and columns.
    
    Returns JSON with:
    - tables: Dict of table names to column info
    - table_count: Total number of tables
    """
```

## Step 6: Dynamic Resources

Create resources that update based on database state:

```python
@mcp.resource("mydb://stats/summary")
def stats_summary_resource() -> str:
    """Database statistics summary."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get table sizes
    cursor.execute("""
        SELECT 
            table_name,
            table_rows,
            data_length,
            index_length
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
    """)
    
    tables = cursor.fetchall()
    conn.close()
    
    return json.dumps({
        "tables": tables,
        "total_tables": len(tables),
        "generated_at": datetime.utcnow().isoformat()
    }, indent=2)
```

## Common Issues

### Issue: Resource not appearing

**Solution:** Check that:
1. Function decorated with `@mcp.resource(uri)`
2. URI is unique
3. Function returns string
4. Server restarted after adding resource

### Issue: "File not found" for markdown resources

**Solution:** Use absolute paths:
```python
from pathlib import Path

file_path = Path(__file__).parent.parent / "resources" / "file.md"
return file_path.read_text(encoding="utf-8")
```

### Issue: JSON serialization error

**Solution:** Ensure all data is JSON-serializable:
```python
# Convert datetime to string
data["timestamp"] = datetime.now().isoformat()

# Convert Decimal to float
data["value"] = float(decimal_value)
```

## Testing Resources

Create `tests/test_resources.py`:

```python
"""Tests for MCP resources."""

import json
import pytest
from mcp_server.server import mcp

def test_schema_resource_exists():
    """Verify schema resource is registered."""
    resources = mcp.list_resources()
    resource_uris = [r.uri for r in resources]
    assert "mydb://schema/tables" in resource_uris

def test_data_dictionary_exists():
    """Verify data dictionary resource exists."""
    resources = mcp.list_resources()
    resource_uris = [r.uri for r in resources]
    assert "mydb://data-dictionary" in resource_uris

def test_schema_resource_returns_json():
    """Verify schema resource returns valid JSON."""
    # This would require async testing with pytest-asyncio
    # For now, just verify resource is callable
    from mcp_server.server import schema_tables_resource
    result = schema_tables_resource()
    data = json.loads(result)
    assert "tables" in data
```

Run tests:
```bash
pytest tests/test_resources.py -v
```

## Next Steps

✅ You now have discoverable MCP resources!

**Next tutorial:** [Statistical Tools](quick-04-statistical-tools.md)

Learn how to:
- Install scipy and numpy
- Create statistical analysis tools
- Implement correlation analysis
- Add trend detection

## Checklist

- [ ] Created `mcp_server/schema.py` with discovery functions
- [ ] Added schema resource to `server.py`
- [ ] Created `resources/data_dictionary.md`
- [ ] Added data dictionary resource
- [ ] Added metadata resources
- [ ] All resources return strings
- [ ] Resources tested with MCP Inspector
- [ ] Resource URIs are descriptive
- [ ] Documentation is clear and helpful
- [ ] Tests written and passing

## Resources

- [MCP Resources Specification](https://spec.modelcontextprotocol.io/specification/server/resources/)
- [FastMCP Resources](https://github.com/jlowin/fastmcp#resources)
