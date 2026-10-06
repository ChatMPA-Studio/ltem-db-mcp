"""Centralized configuration — read, validate, and expose environment variables.

All configuration is loaded once at import time. Missing required variables
cause an immediate, descriptive exit so problems surface during container
startup rather than at request time.
"""

import logging
import os
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

from dotenv import load_dotenv

# Load .env from project root (parent of mcp_server/)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require(name: str) -> str:
    """Return env var value or exit with a clear error."""
    value = os.getenv(name)
    if not value:
        print(
            f"FATAL: Required environment variable {name} is not set.\n"
            f"       Copy .env.example to .env and fill in credentials.",
            file=sys.stderr,
        )
        sys.exit(1)
    return value


def _parse_database_url(url: str) -> dict:
    """Parse a DATABASE_URL into individual components.

    Supports: mysql://user:pass@host:port/dbname
    User and password are percent-decoded (urlparse leaves them encoded).
    """
    parsed = urlparse(url)
    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 3306,
        "user": unquote(parsed.username or "root"),
        "password": unquote(parsed.password or ""),
        "name": parsed.path.lstrip("/") or "ecological_monitoring",
    }


# ---------------------------------------------------------------------------
# Server settings
# ---------------------------------------------------------------------------

PORT: int = int(os.getenv("PORT", "8000"))
MCP_BASE_PATH: str = os.getenv("MCP_BASE_PATH", "/mcp")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

# ---------------------------------------------------------------------------
# Database settings
# ---------------------------------------------------------------------------
# DATABASE_URL takes precedence over individual LTEM_DB_* variables.
# This makes the template portable across different deployment environments.

DATABASE_URL: str | None = os.getenv("DATABASE_URL")

if DATABASE_URL:
    _db = _parse_database_url(DATABASE_URL)
    DB_HOST: str = _db["host"]
    DB_PORT: int = _db["port"]
    DB_USER: str = _db["user"]
    DB_PASSWORD: str = _db["password"]
    DB_NAME: str = _db["name"]
else:
    DB_HOST = _require("LTEM_DB_HOST")
    DB_PORT = int(os.getenv("LTEM_DB_PORT", "3306"))
    DB_USER = os.getenv("LTEM_DB_USER", "mcp_ltem_ro")
    DB_PASSWORD = _require("LTEM_DB_PASSWORD")
    DB_NAME = os.getenv("LTEM_DB_NAME", "ecological_monitoring")


# ---------------------------------------------------------------------------
# TLS / SSL settings (optional, OFF by default)
# ---------------------------------------------------------------------------
# The RDS instance supports TLS but does not require it, so the default is a
# plain connection (unchanged behavior). Set DB_SSL=true to encrypt the
# connection; point DB_SSL_CA at Amazon's RDS CA bundle to also verify the
# server certificate.

DB_SSL: bool = os.getenv("DB_SSL", "false").strip().lower() in ("1", "true", "yes", "on")
DB_SSL_CA: str | None = os.getenv("DB_SSL_CA") or None


# ---------------------------------------------------------------------------
# Connection pool settings
# ---------------------------------------------------------------------------
# Every tool call used to open and close its own MySQL connection (TCP +
# auth handshake per call). DB_POOL_MAX is the hard cap on connections held
# open against RDS; requests beyond it block instead of erroring (see
# db.py's use of PooledDB(blocking=True)).

DB_POOL_MIN: int = int(os.getenv("DB_POOL_MIN", "1"))
DB_POOL_MAX: int = int(os.getenv("DB_POOL_MAX", "10"))
# Defaults to DB_POOL_MAX: with a smaller cache, connections opened during a
# burst beyond it are closed when returned, and the next burst reopens them.
DB_POOL_MAX_CACHED: int = int(os.getenv("DB_POOL_MAX_CACHED", str(DB_POOL_MAX)))


# ---------------------------------------------------------------------------
# Auth settings (API key per investigator, validated against DynamoDB)
# ---------------------------------------------------------------------------
# Off by default: the DynamoDB table this validates against is provisioned
# separately (Terraform, infra repo) and doesn't exist in every environment
# yet. With AUTH_ENABLED=false the server behaves exactly as it does today —
# this flag is what lets the auth code ship ahead of that table existing.

AUTH_ENABLED: bool = os.getenv("AUTH_ENABLED", "false").strip().lower() in ("1", "true", "yes", "on")
AUTH_DYNAMODB_TABLE: str = os.getenv("AUTH_DYNAMODB_TABLE", "chatmpa-mcp-auth")
AUTH_AWS_REGION: str = os.getenv("AUTH_AWS_REGION", "us-west-2")
AUTH_CACHE_TTL_SECONDS: int = int(os.getenv("AUTH_CACHE_TTL_SECONDS", "60"))
AUTH_CACHE_MAX_ENTRIES: int = int(os.getenv("AUTH_CACHE_MAX_ENTRIES", "1000"))
AUTH_REQUIRED_SCOPE: str = "ltem"


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def setup_logging() -> None:
    """Configure root logger based on LOG_LEVEL."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def print_startup_summary() -> None:
    """Log a safe configuration summary (no passwords)."""
    logger = logging.getLogger("mcp_server.config")
    logger.info("=== MCP Server Configuration ===")
    logger.info("  Port:        %s", PORT)
    logger.info("  Base Path:   %s", MCP_BASE_PATH)
    logger.info("  Log Level:   %s", LOG_LEVEL)
    logger.info("  DB Host:     %s", DB_HOST)
    logger.info("  DB Port:     %s", DB_PORT)
    logger.info("  DB User:     %s", DB_USER)
    logger.info("  DB Name:     %s", DB_NAME)
    logger.info("  DB Password: %s", "****" if DB_PASSWORD else "NOT SET")
    logger.info(
        "  DB Pool:     min=%s max_cached=%s max=%s", DB_POOL_MIN, DB_POOL_MAX_CACHED, DB_POOL_MAX
    )
    logger.info(
        "  Auth:        %s",
        f"enabled (table={AUTH_DYNAMODB_TABLE}, region={AUTH_AWS_REGION})" if AUTH_ENABLED else "disabled",
    )
    if DATABASE_URL:
        logger.info("  Source:      DATABASE_URL")
    else:
        logger.info("  Source:      LTEM_DB_* env vars")
    logger.info("================================")
