"""SQL validation and safety guardrails for LTEM database access."""

import re

# Tables allowed for querying
ALLOWED_TABLES = {
	'ltem_historical_database',
	'ltem_monitoring_species',
	'ltem_monitoring_reefs',
	'species_traits',
}

# SQL keywords that indicate write/destructive operations
DENIED_KEYWORDS = [
	'INSERT', 'UPDATE', 'DELETE', 'ALTER', 'DROP', 'CREATE',
	'TRUNCATE', 'REPLACE', 'GRANT', 'REVOKE', 'CALL', 'LOAD',
	'OUTFILE', 'INTO', 'SET', 'LOCK', 'UNLOCK',
]

DEFAULT_MAX_ROWS = 5000
DEFAULT_TIMEOUT = 20

# ---------------------------------------------------------------------------
# Precompiled regex patterns.
#
# validate_sql() and enforce_limit() run on every single query now that
# db.py pools connections — the TCP+auth handshake that used to dominate a
# query's latency is gone, so what used to be negligible overhead next to
# it (rebuilding and re-caching these patterns on every call) is worth
# paying once at import time instead.
# ---------------------------------------------------------------------------

_SELECT_SHOW_DESCRIBE_RE = re.compile(r'^(SELECT|SHOW|DESCRIBE|DESC)\b')
_SELECT_INTO_RE = re.compile(r'\bSELECT\b.*\bINTO\b')
_DENIED_KEYWORD_PATTERNS = [
	(keyword, re.compile(r'\b' + keyword + r'\b'))
	for keyword in DENIED_KEYWORDS
	if keyword != 'INTO'  # INTO gets the SELECT...INTO-specific check above
]
_TABLE_REF_RE = re.compile(r'(?:FROM|JOIN)\s+`?(\w+)`?')
_LIMIT_RE = re.compile(r'\bLIMIT\s+(\d+)')
_LIMIT_SUB_RE = re.compile(r'\bLIMIT\s+\d+', flags=re.IGNORECASE)
_SELECT_START_RE = re.compile(r'^\s*(SELECT)\b')


def validate_sql(sql: str) -> None:
	"""Validate that SQL is a safe SELECT statement.

	Raises ValueError if the query is not allowed.
	"""
	if not sql or not sql.strip():
		raise ValueError("Empty SQL query")

	normalized = sql.strip().upper()

	# Must start with SELECT or SHOW or DESCRIBE
	if not _SELECT_SHOW_DESCRIBE_RE.match(normalized):
		raise ValueError("Only SELECT, SHOW, and DESCRIBE statements are allowed")

	# SELECT ... INTO (e.g. INTO OUTFILE) is the one denied keyword that
	# needs a shape-specific check instead of a plain word-boundary search:
	# "INTO" also shows up harmlessly in table/column names.
	if _SELECT_INTO_RE.search(normalized):
		raise ValueError("SQL contains denied keyword: INTO")

	# Check for the remaining denied keywords (as whole words, not substrings)
	for keyword, pattern in _DENIED_KEYWORD_PATTERNS:
		if pattern.search(normalized):
			raise ValueError(f"SQL contains denied keyword: {keyword}")

	# Check that only whitelisted tables are referenced
	_validate_table_references(normalized)


def _validate_table_references(normalized_sql: str) -> None:
	"""Check that only whitelisted tables appear in FROM/JOIN clauses."""
	# Extract table names from FROM and JOIN clauses
	# Match: FROM table, JOIN table, FROM `table`
	referenced = _TABLE_REF_RE.findall(normalized_sql)

	allowed_upper = {t.upper() for t in ALLOWED_TABLES}
	# Also allow INFORMATION_SCHEMA for DESCRIBE/SHOW equivalents
	allowed_upper.add('INFORMATION_SCHEMA')
	allowed_upper.add('COLUMNS')
	allowed_upper.add('TABLES')

	for table in referenced:
		if table.upper() not in allowed_upper:
			raise ValueError(
				f"Table '{table}' is not in the whitelist. "
				f"Allowed: {', '.join(sorted(ALLOWED_TABLES))}"
			)


def enforce_limit(sql: str, max_rows: int = DEFAULT_MAX_ROWS) -> str:
	"""Inject or cap LIMIT clause to prevent oversized result sets."""
	normalized = sql.strip().upper()

	# Check if LIMIT already exists
	limit_match = _LIMIT_RE.search(normalized)
	if limit_match:
		existing_limit = int(limit_match.group(1))
		if existing_limit > max_rows:
			# Replace with capped limit
			sql = _LIMIT_SUB_RE.sub(f'LIMIT {max_rows}', sql)
		return sql

	# No LIMIT found — only add for SELECT statements (not SHOW/DESCRIBE)
	if _SELECT_START_RE.match(normalized):
		# Strip trailing semicolon before adding LIMIT
		sql = sql.rstrip().rstrip(';')
		sql = f"{sql} LIMIT {max_rows}"

	return sql


def sanitize_table_name(name: str) -> str:
	"""Validate and return a table name from the whitelist.

	Raises ValueError if the table is not allowed.
	"""
	if name not in ALLOWED_TABLES:
		raise ValueError(
			f"Table '{name}' is not allowed. "
			f"Allowed: {', '.join(sorted(ALLOWED_TABLES))}"
		)
	return name
