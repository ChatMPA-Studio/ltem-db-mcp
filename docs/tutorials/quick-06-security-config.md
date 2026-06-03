# Tutorial 06: Security Configuration

**Time:** 45 minutes  
**Difficulty:** Intermediate

## Learning Objectives

- Implement table whitelisting
- Create read-only database users
- Add query validation
- Set row limits and timeouts
- Follow security best practices

## Prerequisites

- Completed [Tutorial 05: Analysis Skills](quick-05-analysis-skills.md)
- Database administrator access (for creating users)

## Security Principles

1. **Least Privilege** - Grant minimum necessary permissions
2. **Defense in Depth** - Multiple security layers
3. **Fail Secure** - Default to deny access
4. **Audit Trail** - Log security-relevant events

## Step 1: Configure Table Whitelist

Update `mcp_server/security.py`:

```python
"""Security configuration and validation."""

from typing import Set

# Table whitelist - ONLY these tables can be accessed
ALLOWED_TABLES: Set[str] = {
    "your_main_table",
    "lookup_table",
    "metadata_table"
}

# Maximum rows per query
MAX_ROWS = 5000

# Query timeout (seconds)
QUERY_TIMEOUT = 30

# Allowed SQL operations (read-only)
ALLOWED_OPERATIONS = {"SELECT", "SHOW", "DESCRIBE"}


def validate_table_access(table: str) -> None:
    """Validate table is in whitelist.
    
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
    if limit > MAX_ROWS:
        return MAX_ROWS
    return limit


def validate_query(query: str) -> None:
    """Validate query contains only allowed operations.
    
    Args:
        query: SQL query to validate
        
    Raises:
        ValueError: If query contains disallowed operations
    """
    query_upper = query.upper().strip()
    
    # Check for allowed operations
    operation = query_upper.split()[0]
    if operation not in ALLOWED_OPERATIONS:
        raise ValueError(
            f"Operation '{operation}' not allowed. "
            f"Allowed: {', '.join(ALLOWED_OPERATIONS)}"
        )
    
    # Check for dangerous keywords
    dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE"]
    for keyword in dangerous_keywords:
        if keyword in query_upper:
            raise ValueError(f"Dangerous keyword '{keyword}' detected in query")
```

## Step 2: Create Read-Only Database User

### MySQL

```sql
-- Create read-only user
CREATE USER 'mcp_readonly'@'%' IDENTIFIED BY 'secure_password_here';

-- Grant SELECT only on specific database
GRANT SELECT ON your_database.* TO 'mcp_readonly'@'%';

-- Grant SHOW and DESCRIBE for schema discovery
GRANT SHOW VIEW ON your_database.* TO 'mcp_readonly'@'%';

-- Apply changes
FLUSH PRIVILEGES;

-- Verify permissions
SHOW GRANTS FOR 'mcp_readonly'@'%';
```

### PostgreSQL

```sql
-- Create read-only user
CREATE USER mcp_readonly WITH PASSWORD 'secure_password_here';

-- Grant CONNECT
GRANT CONNECT ON DATABASE your_database TO mcp_readonly;

-- Grant USAGE on schema
GRANT USAGE ON SCHEMA public TO mcp_readonly;

-- Grant SELECT on all tables
GRANT SELECT ON ALL TABLES IN SCHEMA public TO mcp_readonly;

-- Grant SELECT on future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public 
GRANT SELECT ON TABLES TO mcp_readonly;

-- Verify permissions
\du mcp_readonly
```

## Step 3: Update Database Connection

Update `.env` to use read-only user:

```bash
# Use read-only credentials
MYDB_USER=mcp_readonly
MYDB_PASSWORD=secure_password_here

# Keep admin credentials separate (for migrations only)
# MYDB_ADMIN_USER=admin
# MYDB_ADMIN_PASSWORD=admin_password
```

## Step 4: Add Query Timeout

Update `mcp_server/db.py`:

```python
import os
import pymysql
from pymysql.cursors import DictCursor
from mcp_server.security import QUERY_TIMEOUT

def get_connection():
    """Get database connection with security settings."""
    return pymysql.connect(
        host=os.getenv("MYDB_HOST"),
        port=int(os.getenv("MYDB_PORT", "3306")),
        user=os.getenv("MYDB_USER"),
        password=os.getenv("MYDB_PASSWORD"),
        database=os.getenv("MYDB_NAME"),
        cursorclass=DictCursor,
        charset='utf8mb4',
        connect_timeout=10,          # Connection timeout
        read_timeout=QUERY_TIMEOUT,  # Query timeout
        write_timeout=QUERY_TIMEOUT
    )

def execute_select(query: str, params: tuple = None) -> List[Dict]:
    """Execute SELECT with timeout and validation.
    
    Args:
        query: SQL query
        params: Query parameters
        
    Returns:
        List of result dictionaries
        
    Raises:
        ValueError: If query validation fails
        TimeoutError: If query exceeds timeout
    """
    from mcp_server.security import validate_query
    
    # Validate query
    validate_query(query)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(query, params or ())
        results = cursor.fetchall()
        return results
    except pymysql.err.OperationalError as e:
        if "timeout" in str(e).lower():
            raise TimeoutError(f"Query exceeded {QUERY_TIMEOUT}s timeout")
        raise
    finally:
        cursor.close()
        conn.close()
```

## Step 5: Add Input Validation

Create `mcp_server/validation.py`:

```python
"""Input validation utilities."""

import re
from typing import Any

def validate_table_name(table: str) -> None:
    """Validate table name format.
    
    Args:
        table: Table name to validate
        
    Raises:
        ValueError: If table name invalid
    """
    if not re.match(r'^[a-zA-Z0-9_]+$', table):
        raise ValueError(
            f"Invalid table name: '{table}'. "
            "Only alphanumeric and underscore allowed."
        )

def validate_column_name(column: str) -> None:
    """Validate column name format.
    
    Args:
        column: Column name to validate
        
    Raises:
        ValueError: If column name invalid
    """
    if not re.match(r'^[a-zA-Z0-9_]+$', column):
        raise ValueError(
            f"Invalid column name: '{column}'. "
            "Only alphanumeric and underscore allowed."
        )

def validate_limit(limit: int, max_limit: int = 5000) -> int:
    """Validate and cap limit parameter.
    
    Args:
        limit: Requested limit
        max_limit: Maximum allowed limit
        
    Returns:
        Validated limit
        
    Raises:
        ValueError: If limit invalid
    """
    if limit < 1:
        raise ValueError("Limit must be positive")
    return min(limit, max_limit)
```

## Step 6: Update Tools with Validation

Update tools to use validation:

```python
from mcp_server.security import validate_table_access, validate_row_limit
from mcp_server.validation import validate_table_name, validate_column_name

@mcp.tool()
def get_records(table: str, limit: int = 100) -> str:
    """Get records with security validation."""
    try:
        # Validate inputs
        validate_table_name(table)
        validate_table_access(table)
        limit = validate_row_limit(limit)
        
        # Execute query
        query = f"SELECT * FROM {table} LIMIT %s"
        rows = execute_select(query, (limit,))
        
        return json.dumps({
            "data": rows,
            "meta": {"count": len(rows), "limit": limit}
        })
        
    except ValueError as e:
        return json.dumps({"error": f"Validation error: {e}"})
    except TimeoutError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {e}"})
```

## Step 7: Add Logging

Create `mcp_server/logging_config.py`:

```python
"""Logging configuration."""

import logging
import os
from datetime import datetime

def setup_logging():
    """Configure logging for security events."""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('mcp_server.log'),
            logging.StreamHandler()
        ]
    )

def log_security_event(event_type: str, details: dict):
    """Log security-relevant events.
    
    Args:
        event_type: Type of security event
        details: Event details
    """
    logger = logging.getLogger('security')
    logger.warning(f"SECURITY: {event_type} - {details}")
```

Update tools to log security events:

```python
from mcp_server.logging_config import log_security_event

try:
    validate_table_access(table)
except ValueError as e:
    log_security_event("ACCESS_DENIED", {
        "table": table,
        "error": str(e),
        "timestamp": datetime.utcnow().isoformat()
    })
    raise
```

## Step 8: Security Testing

Create `tests/test_security.py`:

```python
"""Security tests."""

import pytest
from mcp_server.security import (
    validate_table_access,
    validate_row_limit,
    validate_query
)

def test_table_whitelist_allows_valid():
    """Valid tables should pass."""
    # Should not raise
    validate_table_access("your_main_table")

def test_table_whitelist_blocks_invalid():
    """Invalid tables should be blocked."""
    with pytest.raises(ValueError, match="not in whitelist"):
        validate_table_access("malicious_table")

def test_row_limit_caps_excessive():
    """Excessive limits should be capped."""
    result = validate_row_limit(10000)
    assert result == 5000  # MAX_ROWS

def test_query_validation_blocks_delete():
    """DELETE queries should be blocked."""
    with pytest.raises(ValueError, match="not allowed"):
        validate_query("DELETE FROM table")

def test_query_validation_allows_select():
    """SELECT queries should be allowed."""
    # Should not raise
    validate_query("SELECT * FROM table")
```

Run security tests:
```bash
pytest tests/test_security.py -v
```

## Security Checklist

- [ ] Table whitelist configured in `security.py`
- [ ] Read-only database user created
- [ ] `.env` updated with read-only credentials
- [ ] Query timeout configured
- [ ] Query validation implemented
- [ ] Input validation added
- [ ] Row limits enforced
- [ ] Security logging configured
- [ ] Security tests written and passing
- [ ] Admin credentials stored separately
- [ ] `.env` file in `.gitignore`

## Best Practices

### 1. Never Trust User Input

Always validate:
- Table names
- Column names
- Limits and offsets
- Filter values

### 2. Use Parameterized Queries

**Bad:**
```python
query = f"SELECT * FROM {table} WHERE id = {user_id}"
```

**Good:**
```python
query = f"SELECT * FROM {table} WHERE id = %s"
execute_select(query, (user_id,))
```

### 3. Principle of Least Privilege

- Use read-only database user
- Whitelist specific tables
- Limit row counts
- Set query timeouts

### 4. Defense in Depth

Multiple security layers:
1. Read-only database user
2. Table whitelist
3. Query validation
4. Input validation
5. Row limits
6. Timeouts
7. Logging

## Common Issues

### Issue: "Access denied for user"

**Solution:** Verify database user permissions:
```sql
SHOW GRANTS FOR 'mcp_readonly'@'%';
```

### Issue: Query timeout errors

**Solution:** Optimize queries or increase timeout:
```python
QUERY_TIMEOUT = 60  # Increase if needed
```

### Issue: Table not in whitelist

**Solution:** Add table to `ALLOWED_TABLES`:
```python
ALLOWED_TABLES = {
    "your_table",
    "new_table"  # Add here
}
```

## Next Steps

✅ Your MCP server is now secure!

**Next tutorial:** [Docker Deployment](quick-07-docker-deployment.md)

Learn how to:
- Build Docker images
- Configure docker-compose
- Deploy with Caddy reverse proxy
- Manage environment variables

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [SQL Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)
- [MySQL Security](https://dev.mysql.com/doc/refman/8.0/en/security.html)
