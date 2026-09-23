"""Per-investigator API key auth for external (ALB) traffic.

Not wired through FastMCP's own `auth=`/`TokenVerifier` hook: once that's
configured, FastMCP's HTTP transport wraps the app in a middleware that
rejects *any* request without an `Authorization` header, including the
orchestrator's internal calls (which never carry a key — they're trusted at
the network/security-group level, per docs/infrastructure.md and the ALB
architecture doc). So this is a plain Starlette middleware, applied only
when AUTH_ENABLED, that lets header-less requests through untouched and
only validates when a header is actually present.

Keys are opaque, not JWTs: an admin panel elsewhere generates a random key,
shows it once, and stores only its SHA-256 hash in DynamoDB alongside the
investigator id and scopes. This module never sees or stores a raw key —
only the hash, and only in memory, only for AUTH_CACHE_TTL_SECONDS.
"""

import hashlib
import logging
import time
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from mcp_server import config

logger = logging.getLogger(__name__)

# hash -> (record or None if not found, expires_at monotonic timestamp).
# Caching misses too, not just hits: a client retrying an invalid/typo'd key
# shouldn't get a DynamoDB GetItem on every single request.
_cache: dict[str, tuple[dict[str, Any] | None, float]] = {}


def get_dynamodb_table():
	"""Isolated on purpose: tests patch this name, not boto3 itself, to
	swap in a fake table without touching AWS or real credentials."""
	import boto3

	return boto3.resource("dynamodb", region_name=config.AUTH_AWS_REGION).Table(
		config.AUTH_DYNAMODB_TABLE
	)


def _lookup(key_hash: str) -> dict[str, Any] | None:
	cached = _cache.get(key_hash)
	if cached is not None and cached[1] > time.monotonic():
		return cached[0]

	response = get_dynamodb_table().get_item(Key={"key_hash": key_hash})
	record = response.get("Item")
	_cache[key_hash] = (record, time.monotonic() + config.AUTH_CACHE_TTL_SECONDS)
	return record


def _unauthorized(reason: str) -> JSONResponse:
	logger.warning("auth_rejected", extra={"reason": reason})
	return JSONResponse({"error": "unauthorized", "reason": reason}, status_code=401)


class ApiKeyMiddleware(BaseHTTPMiddleware):
	"""Validates `Authorization: Bearer <key>` when present; lets requests
	with no Authorization header through untouched (internal/orchestrator
	traffic — the security group is what actually restricts who can reach
	this far, not this middleware)."""

	async def dispatch(
		self, request: Request, call_next: RequestResponseEndpoint
	) -> Response:
		header = request.headers.get("authorization")
		if header is None:
			return await call_next(request)

		scheme, _, token = header.partition(" ")
		if scheme.lower() != "bearer" or not token:
			return _unauthorized("malformed_authorization_header")

		key_hash = hashlib.sha256(token.encode()).hexdigest()
		record = _lookup(key_hash)

		if record is None:
			return _unauthorized("key_not_found")
		if record.get("revoked_at"):
			return _unauthorized("key_revoked")
		if config.AUTH_REQUIRED_SCOPE not in record.get("scopes", []):
			return _unauthorized("missing_scope")

		request.state.investigator_id = record.get("investigator_id")
		request.state.scopes = record.get("scopes")
		return await call_next(request)
