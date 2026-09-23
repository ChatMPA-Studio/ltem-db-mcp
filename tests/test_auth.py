"""Tests for mcp_server/auth.py — the per-investigator API key middleware.

Runs against a minimal Starlette app instead of the full MCP server, and
mocks mcp_server.auth.get_dynamodb_table (patched at the call site, same
convention tests/test_smoke.py uses for execute_select) — no database
connection or AWS credentials needed.
"""

import hashlib
from unittest.mock import MagicMock, patch

import pytest
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from mcp_server import auth as auth_module
from mcp_server.auth import ApiKeyMiddleware

VALID_KEY = "test-key-abc123"
VALID_HASH = hashlib.sha256(VALID_KEY.encode()).hexdigest()


def _echo(request):
	investigator_id = getattr(request.state, "investigator_id", "anonymous")
	return PlainTextResponse(investigator_id)


@pytest.fixture
def client():
	app = Starlette(routes=[Route("/", _echo)], middleware=[Middleware(ApiKeyMiddleware)])
	return TestClient(app)


@pytest.fixture(autouse=True)
def clear_cache():
	"""The in-memory hash cache is a module-level dict — tests share it
	unless cleared, and several tests below reuse VALID_HASH with
	different DynamoDB records."""
	auth_module._cache.clear()
	yield
	auth_module._cache.clear()


def _mock_table(item: dict | None = None) -> MagicMock:
	table = MagicMock()
	table.get_item.return_value = {"Item": item} if item else {}
	return table


class TestNoHeader:
	"""Internal orchestrator calls never carry a key — the security group,
	not this middleware, is what restricts who can reach the MCP task."""

	def test_request_without_authorization_header_passes_through(self, client):
		with patch("mcp_server.auth.get_dynamodb_table") as mock_get_table:
			response = client.get("/")
		assert response.status_code == 200
		assert response.text == "anonymous"
		mock_get_table.assert_not_called()


class TestValidKey:
	def test_valid_key_with_ltem_scope_passes(self, client):
		record = {
			"investigator_id": "researcher-42",
			"scopes": ["ltem", "conapesca"],
			"revoked_at": None,
		}
		with patch("mcp_server.auth.get_dynamodb_table", return_value=_mock_table(record)):
			response = client.get("/", headers={"Authorization": f"Bearer {VALID_KEY}"})
		assert response.status_code == 200
		assert response.text == "researcher-42"

	def test_second_call_within_ttl_does_not_hit_dynamodb_again(self, client):
		record = {"investigator_id": "researcher-42", "scopes": ["ltem"], "revoked_at": None}
		table = _mock_table(record)
		with patch("mcp_server.auth.get_dynamodb_table", return_value=table):
			client.get("/", headers={"Authorization": f"Bearer {VALID_KEY}"})
			client.get("/", headers={"Authorization": f"Bearer {VALID_KEY}"})
		assert table.get_item.call_count == 1


class TestRejected:
	def test_malformed_header_is_rejected(self, client):
		with patch("mcp_server.auth.get_dynamodb_table") as mock_get_table:
			response = client.get("/", headers={"Authorization": "NotBearer xyz"})
		assert response.status_code == 401
		mock_get_table.assert_not_called()

	def test_unknown_key_is_rejected(self, client):
		with patch("mcp_server.auth.get_dynamodb_table", return_value=_mock_table(None)):
			response = client.get("/", headers={"Authorization": "Bearer wrong-key"})
		assert response.status_code == 401

	def test_second_lookup_of_unknown_key_does_not_hit_dynamodb_again(self, client):
		"""Misses are cached too — a client retrying a typo'd key shouldn't
		get a GetItem on every single request."""
		table = _mock_table(None)
		with patch("mcp_server.auth.get_dynamodb_table", return_value=table):
			client.get("/", headers={"Authorization": "Bearer wrong-key"})
			client.get("/", headers={"Authorization": "Bearer wrong-key"})
		assert table.get_item.call_count == 1

	def test_revoked_key_is_rejected(self, client):
		record = {
			"investigator_id": "researcher-42",
			"scopes": ["ltem"],
			"revoked_at": "2026-01-01T00:00:00Z",
		}
		with patch("mcp_server.auth.get_dynamodb_table", return_value=_mock_table(record)):
			response = client.get("/", headers={"Authorization": f"Bearer {VALID_KEY}"})
		assert response.status_code == 401

	def test_key_without_ltem_scope_is_rejected(self, client):
		record = {"investigator_id": "researcher-42", "scopes": ["conapesca"], "revoked_at": None}
		with patch("mcp_server.auth.get_dynamodb_table", return_value=_mock_table(record)):
			response = client.get("/", headers={"Authorization": f"Bearer {VALID_KEY}"})
		assert response.status_code == 401
