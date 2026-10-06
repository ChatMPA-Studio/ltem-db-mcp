"""One log line per tool call: total time, database time, rows read, and
response size.

Exists so a slow call in production can be split without guessing. A large
total with a small db_ms is time spent in Python or serialization; a large
`bytes` is time spent on the wire (most of a 76 s get_nrsi_data call was
the download of a 15 MB response, not the query).
"""

import logging
import time

import mcp.types as mt
from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
from fastmcp.tools import ToolResult

from mcp_server.db import db_stats

logger = logging.getLogger(__name__)


class ToolTimingMiddleware(Middleware):
	async def on_call_tool(
		self,
		context: MiddlewareContext[mt.CallToolRequestParams],
		call_next: CallNext[mt.CallToolRequestParams, ToolResult],
	) -> ToolResult:
		stats = {"queries": 0, "rows": 0, "seconds": 0.0}
		token = db_stats.set(stats)
		started = time.perf_counter()
		status, size = "error", 0
		try:
			result = await call_next(context)
			status = "error" if result.is_error else "ok"
			# Uncompressed size of the result text; gzip shrinks it on the wire.
			size = sum(len(getattr(block, "text", "")) for block in result.content)
			return result
		finally:
			db_stats.reset(token)
			logger.info(
				"tool=%s status=%s total_ms=%.0f db_ms=%.0f queries=%d rows=%d bytes=%d",
				context.message.name, status, (time.perf_counter() - started) * 1000,
				stats["seconds"] * 1000, stats["queries"], stats["rows"], size,
			)
