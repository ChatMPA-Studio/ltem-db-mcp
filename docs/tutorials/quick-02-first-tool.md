# Tutorial 02: Create Your First MCP Tool

**Time:** 45 minutes  
**Difficulty:** Beginner

## Learning Objectives

- Create a custom tool module
- Write parameterized SQL queries
- Return JSON responses
- Handle errors gracefully
- Test your tool

## Prerequisites

- Completed [Tutorial 01: Setup New MCP](quick-01-setup-new-mcp.md)
- Working MCP server with database connection
- Basic SQL knowledge

## What is an MCP Tool?

An MCP tool is a function that:
- Has a clear, specific purpose
- Accepts typed parameters
- Returns JSON-serializable data
- Handles errors gracefully
- Is automatically discovered by the MCP server

**Tools are atoms** - they do one thing well.

## Step 1: Create Tool Module

Create `tools/data_access.py`:

```python
"""Data access tools for querying the database."""

import json
from typing import Optional
from mcp_server.db import execute_select
from mcp_server.security import validate_table_access

def register(mcp):
    """Register data access tools with the MCP server."""
    
    @mcp.tool()
    def get_records(
        table: str,
        limit: int = 100,
        offset: int = 0
    ) -> str:
        """Get records from a table with pagination.
        
        Args:
            table: Table name to query
            limit: Maximum number of records (default: 100, max: 1000)
            offset: Number of records to skip (default: 0)
        
        Returns:
            JSON string with records and metadata
        """
        try:
            # Validate table access
            validate_table_access(table)
            
            # Enforce limits
            limit = min(limit, 1000)
            
            # Build query
            query = f"""
                SELECT *
                FROM {table}
                LIMIT %s OFFSET %s
            """
            
            # Execute query
            rows = execute_select(query, (limit, offset))
            
            # Return JSON response
            return json.dumps({
                "data": rows,
                "meta": {
                    "table": table,
                    "count": len(rows),
                    "limit": limit,
                    "offset": offset
                }
            })
            
        except Exception as e:
            return json.dumps({
                "error": str(e),
                "table": table
            })
```

## Step 2: Understand Tool Structure

### Function Signature

```python
@mcp.tool()
def tool_name(param1: type, param2: type = default) -> str:
    """Docstring becomes tool description."""
```

**Key points:**
- Decorator: `@mcp.tool()`
- Type hints: Required for all parameters
- Return type: Always `str` (JSON string)
- Docstring: Shown to AI - be clear and specific

### Parameter Types

Supported types:
- `str` - Text
- `int` - Integer
- `float` - Decimal number
- `bool` - True/False
- `Optional[type]` - Can be None
- `list[type]` - Array of values

### Return Format

Always return JSON string:

```python
return json.dumps({
    "data": result_data,
    "meta": metadata_dict
})
```

## Step 3: Add Database Helper

Update `mcp_server/db.py` with query helpers:

```python
def execute_select(query: str, params: tuple = None) -> List[Dict]:
    """Execute SELECT query and return results as list of dicts.
    
    Args:
        query: SQL query with %s placeholders
        params: Tuple of parameters for query
        
    Returns:
        List of dictionaries (one per row)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(query, params or ())
        results = cursor.fetchall()
        return results
    finally:
        cursor.close()
        conn.close()


def execute_select_one(query: str, params: tuple = None) -> Optional[Dict]:
    """Execute SELECT query and return first result.
    
    Args:
        query: SQL query with %s placeholders
        params: Tuple of parameters for query
        
    Returns:
        Dictionary for first row, or None if no results
    """
    results = execute_select(query, params)
    return results[0] if results else None
```

## Step 4: Add Security Validation

Update `mcp_server/security.py`:

```python
def validate_table_access(table: str) -> None:
    """Validate that table is in whitelist.
    
    Args:
        table: Table name to validate
        
    Raises:
        ValueError: If table not in ALLOWED_TABLES
    """
    if table not in ALLOWED_TABLES:
        raise ValueError(
            f"Access denied: Table '{table}' not in whitelist. "
            f"Allowed tables: {', '.join(sorted(ALLOWED_TABLES))}"
        )


def validate_row_limit(limit: int) -> int:
    """Validate and cap row limit.
    
    Args:
        limit: Requested row limit
        
    Returns:
        Capped limit (max MAX_ROWS)
    """
    return min(limit, MAX_ROWS)
```

## Step 5: Create More Tools

Add filtering and aggregation tools to `tools/data_access.py`:

```python
@mcp.tool()
def filter_records(
    table: str,
    column: str,
    value: str,
    limit: int = 100
) -> str:
    """Filter records by column value.
    
    Args:
        table: Table name
        column: Column to filter on
        value: Value to match
        limit: Maximum records to return
        
    Returns:
        JSON with filtered records
    """
    try:
        validate_table_access(table)
        limit = validate_row_limit(limit)
        
        query = f"""
            SELECT *
            FROM {table}
            WHERE {column} = %s
            LIMIT %s
        """
        
        rows = execute_select(query, (value, limit))
        
        return json.dumps({
            "data": rows,
            "meta": {
                "table": table,
                "filter": {column: value},
                "count": len(rows)
            }
        })
        
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def count_records(table: str, group_by: Optional[str] = None) -> str:
    """Count records in a table, optionally grouped.
    
    Args:
        table: Table name
        group_by: Optional column to group by
        
    Returns:
        JSON with count(s)
    """
    try:
        validate_table_access(table)
        
        if group_by:
            query = f"""
                SELECT {group_by}, COUNT(*) as count
                FROM {table}
                GROUP BY {group_by}
                ORDER BY count DESC
            """
        else:
            query = f"SELECT COUNT(*) as count FROM {table}"
        
        rows = execute_select(query)
        
        return json.dumps({
            "data": rows,
            "meta": {
                "table": table,
                "grouped_by": group_by
            }
        })
        
    except Exception as e:
        return json.dumps({"error": str(e)})
```

## Step 6: Test Your Tools

### Manual Testing

```bash
# Start MCP server
fastmcp run mcp_server/server.py:mcp --transport stdio

# In another terminal, use MCP Inspector
mcp-inspector fastmcp run mcp_server/server.py:mcp --transport stdio
```

Test in browser:
1. Call `get_records` with your table name
2. Call `filter_records` with a column and value
3. Call `count_records` with and without grouping

### Automated Testing

Create `tests/test_data_access.py`:

```python
"""Tests for data access tools."""

import json
import pytest
from mcp_server.server import mcp


def test_get_records_tool_exists():
    """Verify get_records tool is registered."""
    tools = mcp.list_tools()
    tool_names = [t.name for t in tools]
    assert "get_records" in tool_names


def test_filter_records_tool_exists():
    """Verify filter_records tool is registered."""
    tools = mcp.list_tools()
    tool_names = [t.name for t in tools]
    assert "filter_records" in tool_names


def test_count_records_tool_exists():
    """Verify count_records tool is registered."""
    tools = mcp.list_tools()
    tool_names = [t.name for t in tools]
    assert "count_records" in tool_names
```

Run tests:
```bash
pytest tests/test_data_access.py -v
```

## Step 7: Best Practices

### 1. Use Parameterized Queries

**Bad (SQL injection risk):**
```python
query = f"SELECT * FROM {table} WHERE id = {user_id}"
```

**Good:**
```python
query = f"SELECT * FROM {table} WHERE id = %s"
rows = execute_select(query, (user_id,))
```

### 2. Always Return JSON

**Bad:**
```python
return rows  # Returns Python object
```

**Good:**
```python
return json.dumps({"data": rows, "meta": {...}})
```

### 3. Include Metadata

```python
return json.dumps({
    "data": results,
    "meta": {
        "count": len(results),
        "query_time": elapsed,
        "filters_applied": filters
    }
})
```

### 4. Handle Errors Gracefully

```python
try:
    # Tool logic
    return json.dumps({"data": results})
except ValueError as e:
    return json.dumps({"error": f"Validation error: {e}"})
except Exception as e:
    return json.dumps({"error": f"Unexpected error: {e}"})
```

### 5. Validate Inputs

```python
# Validate table access
validate_table_access(table)

# Validate limits
limit = min(limit, MAX_ROWS)

# Validate required parameters
if not column or not value:
    raise ValueError("column and value are required")
```

## Common Issues

### Issue: Tool not appearing in MCP

**Solution:** Check that:
1. Tool module is in `tools/` directory
2. Module has `register(mcp)` function
3. Function is decorated with `@mcp.tool()`
4. Server was restarted after adding tool

### Issue: "Table not in whitelist"

**Solution:** Add table to `security.py`:
```python
ALLOWED_TABLES = {
    "your_table",
    "another_table"
}
```

### Issue: SQL syntax error

**Solution:** Test query directly in MySQL:
```bash
mysql -u user -p database -e "YOUR QUERY"
```

## Next Steps

✅ You can now create custom MCP tools!

**Next tutorial:** [Add MCP Resources](quick-03-mcp-resources.md)

Learn how to:
- Expose database schema as a resource
- Create documentation resources
- Make data dictionaries discoverable

## Checklist

- [ ] Created `tools/data_access.py` module
- [ ] Added `register(mcp)` function
- [ ] Created at least 3 tools
- [ ] Added database helpers to `db.py`
- [ ] Added security validation to `security.py`
- [ ] Tools return JSON strings
- [ ] Parameterized queries used (no SQL injection)
- [ ] Error handling implemented
- [ ] Tools tested manually with MCP Inspector
- [ ] Automated tests written and passing

## Resources

- [FastMCP Tool Documentation](https://github.com/jlowin/fastmcp#tools)
- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- [SQL Injection Prevention](https://owasp.org/www-community/attacks/SQL_Injection)
