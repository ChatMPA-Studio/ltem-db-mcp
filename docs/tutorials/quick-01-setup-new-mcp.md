# Tutorial 01: Setup New MCP Server

**Time:** 30 minutes  
**Difficulty:** Beginner

## Learning Objectives

- Copy and customize the MCP template
- Configure database connection
- Understand the repository structure
- Run your first MCP server locally

## Prerequisites

- Python 3.10 or higher installed
- Access to a MySQL or PostgreSQL database
- Basic command line knowledge
- Git installed

## Step 1: Copy the Template

```bash
# Clone or copy the template repository
git clone https://github.com/your-org/mcp-template.git my-mcp-server
cd my-mcp-server

# Remove the original git history (optional)
rm -rf .git
git init
```

## Step 2: Understand the Structure

The template follows this canonical structure:

```
my-mcp-server/
├── mcp_server/          # Core MCP server code
│   ├── __init__.py
│   ├── server.py        # Main server entry point
│   ├── db.py            # Database connection
│   ├── config.py        # Configuration
│   ├── security.py      # Security rules
│   └── schema.py        # Schema discovery
├── tools/               # MCP tools (auto-discovered)
│   ├── __init__.py
│   └── example.py       # Example tool module
├── skills/              # Analysis workflows
│   ├── registry.py      # Skills catalog
│   └── contracts/       # Input/output schemas
├── resources/           # Static resources
│   └── data_dictionary.md
├── metadata/            # Server metadata
│   ├── template.json
│   └── manifest.json
├── tests/               # Test suite
│   ├── test_smoke.py
│   └── test_e2e.py
├── docs/                # Documentation
├── scripts/             # Utility scripts
├── .env.example         # Environment template
├── pyproject.toml       # Python dependencies
├── Dockerfile           # Docker image
├── docker-compose.yml   # Docker orchestration
└── README.md            # Main documentation
```

## Step 3: Customize Package Name

### Update `pyproject.toml`

```toml
[project]
name = "my-mcp-server"  # Change from "ltem-db-mcp"
version = "0.1.0"
description = "MCP server for my domain"
authors = [{name = "Your Name", email = "you@example.com"}]
```

### Update `mcp_server/server.py`

```python
# Line 24: Change server name
mcp = FastMCP("My Domain Database")  # Change from "LTEM Database"
```

## Step 4: Configure Database Connection

### Create `.env` file

```bash
cp .env.example .env
```

### Edit `.env` with your database credentials

```bash
# Database Configuration
MYDB_HOST=your-database-host.com
MYDB_PORT=3306
MYDB_USER=readonly_user
MYDB_PASSWORD=your-secure-password
MYDB_NAME=your_database

# Or use DATABASE_URL
# DATABASE_URL=mysql://user:password@host:3306/database

# Server Configuration
PORT=8000
MCP_BASE_PATH=/mcp
LOG_LEVEL=INFO
```

### Update `mcp_server/db.py`

Replace LTEM-specific connection with your database:

```python
import os
from typing import Any, Dict, List
import pymysql
from pymysql.cursors import DictCursor

def get_connection():
    """Get database connection using environment variables."""
    return pymysql.connect(
        host=os.getenv("MYDB_HOST"),
        port=int(os.getenv("MYDB_PORT", "3306")),
        user=os.getenv("MYDB_USER"),
        password=os.getenv("MYDB_PASSWORD"),
        database=os.getenv("MYDB_NAME"),
        cursorclass=DictCursor,
        charset='utf8mb4'
    )

def test_connection() -> Dict[str, Any]:
    """Test database connectivity."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT VERSION() as version, DATABASE() as database")
    result = cursor.fetchone()
    conn.close()
    return result
```

## Step 5: Update Security Configuration

### Edit `mcp_server/security.py`

Define which tables your MCP can access:

```python
# Table whitelist - only these tables can be queried
ALLOWED_TABLES = {
    "your_main_table",
    "your_lookup_table",
    "your_metadata_table"
}

# Maximum rows per query
MAX_ROWS = 5000

# Query timeout (seconds)
QUERY_TIMEOUT = 30
```

## Step 6: Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package in development mode
pip install -e .
```

## Step 7: Test Database Connection

```bash
# Run health check
python -c "from mcp_server.db import test_connection; print(test_connection())"
```

Expected output:
```json
{
  "version": "8.0.35",
  "database": "your_database"
}
```

## Step 8: Run the MCP Server

```bash
# Run with FastMCP
fastmcp run mcp_server/server.py:mcp --transport stdio
```

You should see:
```
FastMCP server running on stdio transport
Server: My Domain Database
```

## Step 9: Test with MCP Inspector

```bash
# Install MCP Inspector (if not already installed)
npm install -g @modelcontextprotocol/inspector

# Run inspector
mcp-inspector fastmcp run mcp_server/server.py:mcp --transport stdio
```

Open browser to `http://localhost:5173` and test:
1. Click "Connect"
2. Try "list_tables" tool
3. Try "health_check" tool

## Step 10: Update Documentation

### Update `README.md`

Replace LTEM-specific content with your domain:

```markdown
# My Domain MCP Server

MCP server providing access to [your domain] data via Claude and AI assistants.

## Features

- 🔧 [Number] database query tools
- 📊 [Number] analysis skills
- 🔒 Read-only access with table whitelisting
- 🐳 Docker deployment ready

## Quick Start

\`\`\`bash
cp .env.example .env
# Edit .env with your database credentials
pip install -e .
fastmcp run mcp_server/server.py:mcp --transport stdio
\`\`\`

## Available Tools

- `health_check` - Verify database connectivity
- `list_tables` - Show available tables
- `describe_table` - Get table schema
- (Add your custom tools here)
```

### Update `metadata/template.json`

```json
{
  "package": {
    "name": "my-mcp-server",
    "version": "0.1.0",
    "description": "MCP server for my domain",
    "repository": "https://github.com/your-org/my-mcp-server"
  },
  "dataset": {
    "title": "My Domain Database",
    "description": "Description of your data",
    "publisher": "Your Organization"
  }
}
```

## Testing Your Setup

Run the smoke tests:

```bash
pytest tests/test_smoke.py -v
```

Expected output:
```
tests/test_smoke.py::test_server_importable PASSED
tests/test_smoke.py::test_database_connection PASSED
tests/test_smoke.py::test_core_tools_exist PASSED
```

## Common Issues

### Issue: "Can't connect to MySQL server"

**Solution:** Check your `.env` file:
- Verify `MYDB_HOST` is correct
- Ensure database is accessible from your machine
- Test connection with `mysql` command line client

### Issue: "ModuleNotFoundError: No module named 'mcp_server'"

**Solution:** Install in development mode:
```bash
pip install -e .
```

### Issue: "Permission denied" on table access

**Solution:** Check `security.py` - ensure tables are in `ALLOWED_TABLES`

## Next Steps

✅ You now have a working MCP server!

**Next tutorial:** [Create Your First Tool](quick-02-first-tool.md)

Learn how to:
- Create a custom tool module
- Write parameterized SQL queries
- Return JSON responses
- Handle errors gracefully

## Checklist

- [ ] Template copied and renamed
- [ ] `pyproject.toml` updated with your package name
- [ ] `.env` file created with database credentials
- [ ] `db.py` updated with your connection logic
- [ ] `security.py` configured with allowed tables
- [ ] Dependencies installed (`pip install -e .`)
- [ ] Database connection tested successfully
- [ ] MCP server runs without errors
- [ ] Smoke tests pass
- [ ] README.md updated with your domain info

## Resources

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Template Documentation](../mcp_template_spec.md)
