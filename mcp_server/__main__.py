"""Run the LTEM Database MCP Server as an HTTP service.

Usage:
    python -m mcp_server

Environment variables:
    PORT            HTTP port to bind (default: 8000)
    MCP_BASE_PATH   Endpoint path (default: /mcp)
    LOG_LEVEL       Logging verbosity (default: INFO)
    AUTH_ENABLED    Require Authorization: Bearer <key> on every request,
                    including internal ones (default: false — see
                    mcp_server/auth.py)
"""

import uvicorn

from mcp_server.config import PORT, MCP_BASE_PATH, setup_logging, print_startup_summary
from mcp_server.server import mcp

setup_logging()
print_startup_summary()

# stateless_http=True: no session state kept between requests, required so
# N replicas behind the ALB can each answer any request interchangeably
# (see arquitectura-resultante-mcp.pdf, sección 07). Auth is attached to the
# FastMCP instance itself in mcp_server/server.py, not as Starlette
# middleware, so its transport enforces it on every request.
app = mcp.http_app(path=MCP_BASE_PATH, stateless_http=True)

uvicorn.run(app, host="0.0.0.0", port=PORT)
