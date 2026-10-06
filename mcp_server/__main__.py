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
from starlette.middleware import Middleware
from starlette.middleware.gzip import GZipMiddleware

from mcp_server.config import PORT, MCP_BASE_PATH, setup_logging, print_startup_summary
from mcp_server.db import warm_pool
from mcp_server.server import mcp


def build_app():
	"""The ASGI app, built apart from serving it so tests can drive it in-process."""
	# stateless_http=True: no session state kept between requests, required so
	# N replicas behind the ALB can each answer any request interchangeably
	# (see arquitectura-resultante-mcp.pdf, sección 07). Auth is attached to the
	# FastMCP instance itself in mcp_server/server.py, not as Starlette
	# middleware, so its transport enforces it on every request.
	return mcp.http_app(
		path=MCP_BASE_PATH,
		stateless_http=True,
		# Answer with plain JSON instead of an SSE stream: Starlette's
		# GZipMiddleware never compresses text/event-stream, and no tool
		# streams progress or logs mid-call, so SSE bought nothing here.
		# MCP clients must accept both (the spec requires it).
		json_response=True,
		# Results are JSON text that compresses 10-25x (get_nrsi_data: 7.7 MB
		# to 0.6 MB). Level 6 instead of Starlette's default 9: on that
		# response 9 saves 8% more bytes but takes 5x the CPU (217 vs 43 ms).
		# Clients that don't send Accept-Encoding: gzip get it uncompressed.
		middleware=[Middleware(GZipMiddleware, minimum_size=1024, compresslevel=6)],
	)


if __name__ == "__main__":
	setup_logging()
	print_startup_summary()
	warm_pool()
	# Keep idle connections open longer than the ALB's idle timeout (60 s
	# unless configured otherwise; uvicorn's default is 5 s), so the ALB
	# never reuses a connection uvicorn already closed — that surfaces as a
	# sporadic 502.
	uvicorn.run(build_app(), host="0.0.0.0", port=PORT, timeout_keep_alive=65)
