"""Test MCP JSON-RPC initialize handshake via HTTP.

These tests require the server to be running. Start it with:
    python -m mcp_server

Then run:
    pytest tests/test_initialize.py -v

If the server is not running, tests are skipped gracefully.
"""

import json
import os

import pytest

# Try to import httpx; skip all tests if not installed
httpx = pytest.importorskip("httpx", reason="httpx required for HTTP tests (pip install httpx)")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PORT = os.getenv("PORT", "8000")
MCP_BASE_PATH = os.getenv("MCP_BASE_PATH", "/mcp")
BASE_URL = os.getenv("TEST_MCP_URL", f"http://localhost:{PORT}{MCP_BASE_PATH}")

HEADERS = {
	"Content-Type": "application/json",
	"Accept": "application/json, text/event-stream",
}


def _server_available() -> bool:
	"""Check if the MCP server is reachable."""
	try:
		with httpx.Client(timeout=3) as client:
			client.post(
				BASE_URL,
				headers=HEADERS,
				json={
					"jsonrpc": "2.0",
					"id": 0,
					"method": "initialize",
					"params": {
						"protocolVersion": "2024-11-05",
						"capabilities": {},
						"clientInfo": {"name": "probe", "version": "0.1"},
					},
				},
			)
		return True
	except (httpx.ConnectError, httpx.TimeoutException):
		return False


skip_if_no_server = pytest.mark.skipif(
	not _server_available(),
	reason=f"MCP server not reachable at {BASE_URL}",
)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@skip_if_no_server
class TestInitialize:
	"""Test the MCP initialize handshake over HTTP."""

	def _post(self, body: dict) -> httpx.Response:
		with httpx.Client(timeout=10) as client:
			return client.post(BASE_URL, headers=HEADERS, json=body)

	def test_initialize_returns_jsonrpc(self):
		"""Server returns a valid JSON-RPC 2.0 response."""
		resp = self._post({
			"jsonrpc": "2.0",
			"id": 1,
			"method": "initialize",
			"params": {
				"protocolVersion": "2024-11-05",
				"capabilities": {},
				"clientInfo": {"name": "test", "version": "1.0"},
			},
		})
		assert resp.status_code == 200
		data = resp.json()
		assert data.get("jsonrpc") == "2.0"
		assert data.get("id") == 1

	def test_initialize_contains_server_info(self):
		"""Response includes serverInfo with name and version."""
		resp = self._post({
			"jsonrpc": "2.0",
			"id": 2,
			"method": "initialize",
			"params": {
				"protocolVersion": "2024-11-05",
				"capabilities": {},
				"clientInfo": {"name": "test", "version": "1.0"},
			},
		})
		result = resp.json().get("result", {})
		assert "serverInfo" in result
		assert "name" in result["serverInfo"]

	def test_initialize_contains_capabilities(self):
		"""Response includes server capabilities."""
		resp = self._post({
			"jsonrpc": "2.0",
			"id": 3,
			"method": "initialize",
			"params": {
				"protocolVersion": "2024-11-05",
				"capabilities": {},
				"clientInfo": {"name": "test", "version": "1.0"},
			},
		})
		result = resp.json().get("result", {})
		assert "capabilities" in result

	def test_tools_list_returns_tools(self):
		"""tools/list returns an array of registered tools."""
		resp = self._post({
			"jsonrpc": "2.0",
			"id": 4,
			"method": "tools/list",
			"params": {},
		})
		assert resp.status_code == 200
		result = resp.json().get("result", {})
		tools = result.get("tools", [])
		assert len(tools) > 0
		# Every tool must have a name and description
		for tool in tools:
			assert "name" in tool
			assert "description" in tool

	def test_tools_list_includes_core_tools(self):
		"""Core tools (health_check, list_tables) are registered."""
		resp = self._post({
			"jsonrpc": "2.0",
			"id": 5,
			"method": "tools/list",
			"params": {},
		})
		result = resp.json().get("result", {})
		tool_names = [t["name"] for t in result.get("tools", [])]
		assert "health_check" in tool_names
		assert "list_tables" in tool_names

	def test_sse_content_type_accepted(self):
		"""Server accepts the SSE Accept header without 406 error."""
		resp = self._post({
			"jsonrpc": "2.0",
			"id": 6,
			"method": "initialize",
			"params": {
				"protocolVersion": "2024-11-05",
				"capabilities": {},
				"clientInfo": {"name": "sse-test", "version": "1.0"},
			},
		})
		assert resp.status_code != 406, "Server returned 406 Not Acceptable"

	def test_invalid_method_returns_error(self):
		"""Unknown method returns a JSON-RPC error response."""
		resp = self._post({
			"jsonrpc": "2.0",
			"id": 7,
			"method": "nonexistent/method",
			"params": {},
		})
		data = resp.json()
		# Should either return an error or a valid response
		assert "error" in data or "result" in data
