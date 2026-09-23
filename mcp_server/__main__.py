"""Run the LTEM Database MCP Server as an HTTP service.

Usage:
    python -m mcp_server

Environment variables:
    PORT            HTTP port to bind (default: 8000)
    MCP_BASE_PATH   Endpoint path (default: /mcp)
    LOG_LEVEL       Logging verbosity (default: INFO)
    AUTH_ENABLED    Validate Authorization: Bearer <key> for external
                    callers (default: false — see mcp_server/auth.py)
"""

import uvicorn
from starlette.middleware import Middleware

from mcp_server.auth import ApiKeyMiddleware
from mcp_server.config import AUTH_ENABLED, PORT, MCP_BASE_PATH, setup_logging, print_startup_summary
from mcp_server.server import mcp

setup_logging()
print_startup_summary()

# stateless_http=True: no session state kept between requests, required so
# N replicas behind the ALB can each answer any request interchangeably
# (see arquitectura-resultante-mcp.pdf, sección 07). Auth middleware is only
# attached when AUTH_ENABLED — see mcp_server/auth.py for why this can't be
# FastMCP's own `auth=` hook instead.
middleware = [Middleware(ApiKeyMiddleware)] if AUTH_ENABLED else []
app = mcp.http_app(path=MCP_BASE_PATH, stateless_http=True, middleware=middleware)

uvicorn.run(app, host="0.0.0.0", port=PORT)
