"""Shared pytest fixtures for LTEM MCP Server tests."""

import os
import sys
from pathlib import Path

import pytest

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session", autouse=True)
def load_env():
	"""Load .env and fail clearly if credentials are missing."""
	from mcp_server import config  # noqa: F401 — triggers env loading

	missing = []
	for var in ("LTEM_DB_HOST", "LTEM_DB_PASSWORD"):
		val = os.getenv(var)
		if not val or val == "CHANGEME":
			missing.append(var)
	if missing:
		pytest.fail(
			f"Missing or placeholder credentials: {', '.join(missing)}. "
			f"Create a .env file from .env.example and fill in real values."
		)


@pytest.fixture(scope="session")
def mcp_server():
	"""Return the initialized MCP server instance with all tools registered."""
	from mcp_server.server import mcp
	return mcp


@pytest.fixture(scope="session")
def db_connection():
	"""Provide a single database connection for the test session."""
	from mcp_server.db import get_connection
	conn = get_connection()
	yield conn
	conn.close()
