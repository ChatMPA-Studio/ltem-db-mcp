# Tutorial 08: Testing Your MCP Server

**Time:** 60 minutes  
**Difficulty:** Intermediate

## Learning Objectives

- Write comprehensive tests for MCP servers
- Test tools and resources
- Create integration tests
- Set up CI/CD testing
- Achieve good test coverage

## Prerequisites

- Completed [Tutorial 07: Docker Deployment](quick-07-docker-deployment.md)
- pytest installed
- Understanding of testing concepts

## Test Types

### 1. Smoke Tests
Quick tests that verify basic functionality

### 2. Unit Tests
Test individual functions and tools

### 3. Integration Tests
Test multiple components working together

### 4. End-to-End Tests
Test complete workflows from start to finish

## Step 1: Install Testing Dependencies

Update `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.11.0"
]
```

Install:
```bash
pip install -e ".[dev]"
```

## Step 2: Update Smoke Tests

Update `tests/test_smoke.py`:

```python
"""Smoke tests - quick validation of basic functionality."""

import pytest
from mcp_server.server import mcp
from mcp_server.db import test_connection

def test_server_importable():
    """Verify MCP server can be imported."""
    assert mcp is not None
    assert mcp.name is not None

def test_database_connection():
    """Verify database is accessible."""
    result = test_connection()
    assert result is not None
    assert "version" in result or "error" not in result

def test_core_tools_registered():
    """Verify core tools are registered."""
    tools = mcp.list_tools()
    tool_names = [t.name for t in tools]
    
    core_tools = ["health_check", "list_tables", "describe_table_tool"]
    for tool in core_tools:
        assert tool in tool_names, f"Core tool '{tool}' not registered"

def test_resources_registered():
    """Verify resources are registered."""
    resources = mcp.list_resources()
    assert len(resources) > 0, "No resources registered"

def test_tools_directory_exists():
    """Verify tools directory structure."""
    from pathlib import Path
    tools_dir = Path("tools")
    assert tools_dir.exists(), "tools/ directory not found"
    assert (tools_dir / "__init__.py").exists(), "tools/__init__.py not found"
```

Run smoke tests:
```bash
pytest tests/test_smoke.py -v
```

## Step 3: Create Tool Tests

Create `tests/test_tools.py`:

```python
"""Tests for MCP tools."""

import json
import pytest
from mcp_server.server import mcp

def test_health_check_tool():
    """Test health_check tool."""
    tools = mcp.list_tools()
    tool_names = [t.name for t in tools]
    assert "health_check" in tool_names

def test_list_tables_tool():
    """Test list_tables tool."""
    tools = mcp.list_tools()
    tool_names = [t.name for t in tools]
    assert "list_tables" in tool_names

def test_tool_has_description():
    """Verify all tools have descriptions."""
    tools = mcp.list_tools()
    for tool in tools:
        assert tool.description, f"Tool '{tool.name}' missing description"

def test_tool_has_parameters():
    """Verify tools have parameter schemas."""
    tools = mcp.list_tools()
    for tool in tools:
        # inputSchema should exist even if empty
        assert hasattr(tool, 'inputSchema'), f"Tool '{tool.name}' missing inputSchema"

@pytest.mark.asyncio
async def test_health_check_execution():
    """Test health_check tool execution."""
    # This requires async testing
    # Actual execution would depend on your MCP setup
    pass
```

## Step 4: Create Resource Tests

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
    
    # Check for schema-related resources
    schema_resources = [uri for uri in resource_uris if "schema" in uri.lower()]
    assert len(schema_resources) > 0, "No schema resources found"

def test_metadata_resources_exist():
    """Verify metadata resources are registered."""
    resources = mcp.list_resources()
    resource_uris = [r.uri for r in resources]
    
    # Check for metadata resources
    metadata_resources = [uri for uri in resource_uris if "metadata" in uri.lower()]
    assert len(metadata_resources) > 0, "No metadata resources found"

def test_resource_has_description():
    """Verify all resources have descriptions."""
    resources = mcp.list_resources()
    for resource in resources:
        assert resource.description, f"Resource '{resource.uri}' missing description"

def test_resource_uri_format():
    """Verify resource URIs follow convention."""
    resources = mcp.list_resources()
    for resource in resources:
        # URIs should have scheme (e.g., mydb://)
        assert "://" in resource.uri, f"Resource URI '{resource.uri}' missing scheme"
```

## Step 5: Create Database Tests

Create `tests/test_database.py`:

```python
"""Tests for database operations."""

import pytest
from mcp_server.db import get_connection, execute_select
from mcp_server.security import validate_table_access

def test_database_connection():
    """Test database connection."""
    conn = get_connection()
    assert conn is not None
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    result = cursor.fetchone()
    assert result is not None
    conn.close()

def test_execute_select():
    """Test execute_select helper."""
    # Test with a safe query
    results = execute_select("SELECT 1 as test")
    assert len(results) == 1
    assert results[0]["test"] == 1

def test_execute_select_with_params():
    """Test parameterized queries."""
    query = "SELECT %s as value"
    results = execute_select(query, (42,))
    assert results[0]["value"] == 42

@pytest.mark.parametrize("table", [
    "your_main_table",
    "lookup_table"
])
def test_allowed_tables(table):
    """Test table whitelist allows valid tables."""
    # Should not raise
    validate_table_access(table)

def test_disallowed_table():
    """Test table whitelist blocks invalid tables."""
    with pytest.raises(ValueError, match="not in whitelist"):
        validate_table_access("malicious_table")
```

## Step 6: Create Security Tests

Create `tests/test_security.py`:

```python
"""Security tests."""

import pytest
from mcp_server.security import (
    validate_table_access,
    validate_row_limit,
    validate_query
)

def test_table_whitelist():
    """Test table whitelist enforcement."""
    # Valid table should pass
    validate_table_access("your_main_table")
    
    # Invalid table should fail
    with pytest.raises(ValueError):
        validate_table_access("DROP TABLE users")

def test_row_limit_enforcement():
    """Test row limits are enforced."""
    # Normal limit
    assert validate_row_limit(100) == 100
    
    # Excessive limit should be capped
    assert validate_row_limit(10000) == 5000  # MAX_ROWS

def test_query_validation_blocks_writes():
    """Test query validation blocks write operations."""
    dangerous_queries = [
        "DELETE FROM table",
        "UPDATE table SET x=1",
        "INSERT INTO table VALUES (1)",
        "DROP TABLE table",
        "ALTER TABLE table ADD COLUMN x INT"
    ]
    
    for query in dangerous_queries:
        with pytest.raises(ValueError):
            validate_query(query)

def test_query_validation_allows_reads():
    """Test query validation allows read operations."""
    safe_queries = [
        "SELECT * FROM table",
        "SHOW TABLES",
        "DESCRIBE table"
    ]
    
    for query in safe_queries:
        # Should not raise
        validate_query(query)
```

## Step 7: Create Integration Tests

Create `tests/test_integration.py`:

```python
"""Integration tests for complete workflows."""

import json
import pytest
from mcp_server.server import mcp
from mcp_server.db import execute_select

def test_complete_query_workflow():
    """Test complete data query workflow."""
    # 1. List tables
    tables_query = "SHOW TABLES"
    tables = execute_select(tables_query)
    assert len(tables) > 0
    
    # 2. Describe first table
    table_name = list(tables[0].values())[0]
    describe_query = f"DESCRIBE {table_name}"
    columns = execute_select(describe_query)
    assert len(columns) > 0
    
    # 3. Query data
    data_query = f"SELECT * FROM {table_name} LIMIT 1"
    data = execute_select(data_query)
    # Data may or may not exist, but query should succeed
    assert isinstance(data, list)

def test_metadata_to_query_workflow():
    """Test using metadata to construct queries."""
    # 1. Get schema from resource
    resources = mcp.list_resources()
    schema_resources = [r for r in resources if "schema" in r.uri.lower()]
    assert len(schema_resources) > 0
    
    # 2. Use schema info to query
    # (This would require async resource reading in practice)
    pass

@pytest.mark.parametrize("metric", ["biomass", "abundance", "richness"])
def test_statistical_analysis_workflow(metric):
    """Test complete statistical analysis workflow."""
    # This would test a complete analysis from data retrieval
    # through statistical calculation to interpretation
    pass
```

## Step 8: Configure pytest

Create `pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --tb=short
    --cov=mcp_server
    --cov=tools
    --cov-report=term-missing
    --cov-report=html
markers =
    smoke: Quick smoke tests
    slow: Slow-running tests
    integration: Integration tests
```

## Step 9: Run Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test Types

```bash
# Smoke tests only
pytest -m smoke

# Skip slow tests
pytest -m "not slow"

# With coverage
pytest --cov=mcp_server --cov-report=html
```

### Run Specific Test File

```bash
pytest tests/test_security.py -v
```

### Run Specific Test

```bash
pytest tests/test_security.py::test_table_whitelist -v
```

## Step 10: CI/CD Testing

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: test_password
          MYSQL_DATABASE: test_db
        ports:
          - 3306:3306
        options: >-
          --health-cmd="mysqladmin ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=3
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      
      - name: Run smoke tests
        run: pytest tests/test_smoke.py -v
      
      - name: Run all tests
        env:
          MYDB_HOST: localhost
          MYDB_PORT: 3306
          MYDB_USER: root
          MYDB_PASSWORD: test_password
          MYDB_NAME: test_db
        run: pytest --cov=mcp_server --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## Testing Best Practices

### 1. Test Pyramid

```
      /\
     /E2E\      <- Few (slow, comprehensive)
    /------\
   /  Integ \   <- Some (medium speed)
  /----------\
 /   Unit     \ <- Many (fast, focused)
/--------------\
```

### 2. AAA Pattern

```python
def test_example():
    # Arrange - Set up test data
    table = "test_table"
    
    # Act - Execute the function
    result = validate_table_access(table)
    
    # Assert - Verify the outcome
    assert result is None  # No exception raised
```

### 3. Use Fixtures

```python
@pytest.fixture
def db_connection():
    """Provide database connection for tests."""
    conn = get_connection()
    yield conn
    conn.close()

def test_with_fixture(db_connection):
    """Test using fixture."""
    cursor = db_connection.cursor()
    cursor.execute("SELECT 1")
    assert cursor.fetchone() is not None
```

### 4. Parametrize Tests

```python
@pytest.mark.parametrize("limit,expected", [
    (100, 100),
    (5000, 5000),
    (10000, 5000),  # Should be capped
])
def test_row_limits(limit, expected):
    """Test various row limits."""
    assert validate_row_limit(limit) == expected
```

## Coverage Goals

- **Smoke tests:** 100% (all critical paths)
- **Unit tests:** 80%+ (tools, security, validation)
- **Integration tests:** Key workflows
- **E2E tests:** 2-3 complete scenarios

## Common Issues

### Issue: "ModuleNotFoundError" in tests

**Solution:** Install package in development mode:
```bash
pip install -e .
```

### Issue: Tests pass locally but fail in CI

**Solution:** Check environment variables and database setup in CI config

### Issue: Slow tests

**Solution:** Use markers and run fast tests first:
```bash
pytest -m "not slow"
```

## Testing Checklist

- [ ] pytest installed and configured
- [ ] Smoke tests cover critical functionality
- [ ] Unit tests for all tools
- [ ] Unit tests for security functions
- [ ] Resource tests created
- [ ] Database tests created
- [ ] Integration tests for key workflows
- [ ] pytest.ini configured
- [ ] CI/CD testing set up
- [ ] Coverage reports generated
- [ ] All tests passing

## Next Steps

✅ You now have comprehensive testing!

**Congratulations!** You've completed all 8 tutorials and built a production-ready MCP server with:

- ✅ Custom tools and resources
- ✅ Statistical analysis capabilities
- ✅ Structured analysis skills
- ✅ Security configuration
- ✅ Docker deployment
- ✅ Comprehensive testing

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://testdriven.io/blog/testing-best-practices/)
