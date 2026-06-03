"""SQL validation and safety guardrails for LTEM database access."""

import re

# Tables allowed for querying
ALLOWED_TABLES = {
	'ltem_historical_database',
	'ltem_monitoring_species',
	'ltem_monitoring_reefs',
}

# SQL keywords that indicate write/destructive operations
DENIED_KEYWORDS = [
	'INSERT', 'UPDATE', 'DELETE', 'ALTER', 'DROP', 'CREATE',
	'TRUNCATE', 'REPLACE', 'GRANT', 'REVOKE', 'CALL', 'LOAD',
	'OUTFILE', 'INTO', 'SET', 'LOCK', 'UNLOCK',
]

DEFAULT_MAX_ROWS = 5000
DEFAULT_TIMEOUT = 20


def validate_sql(sql: str) -> None:
	"""Validate that SQL is a safe SELECT statement.

	Raises ValueError if the query is not allowed.
	"""
	if not sql or not sql.strip():
		raise ValueError("Empty SQL query")

	normalized = sql.strip().upper()

	# Must start with SELECT or SHOW or DESCRIBE
	if not re.match(r'^(SELECT|SHOW|DESCRIBE|DESC)\b', normalized):
		raise ValueError("Only SELECT, SHOW, and DESCRIBE statements are allowed")

	# Check for denied keywords (as whole words, not substrings)
	for keyword in DENIED_KEYWORDS:
		# Use word boundary to avoid false positives (e.g., "INTO" in "INFORMATION")
		# But be strict: deny if keyword appears as a standalone word
		pattern = r'\b' + keyword + r'\b'
		# Skip INTO check for SELECT ... INTO pattern check
		if keyword == 'INTO':
			# Allow "INTO" only as part of table names, deny SELECT INTO
			if re.search(r'\bSELECT\b.*\bINTO\b', normalized):
				raise ValueError(f"SQL contains denied keyword: {keyword}")
			continue
		if re.search(pattern, normalized):
			raise ValueError(f"SQL contains denied keyword: {keyword}")

	# Check that only whitelisted tables are referenced
	_validate_table_references(normalized)


def _validate_table_references(normalized_sql: str) -> None:
	"""Check that only whitelisted tables appear in FROM/JOIN clauses."""
	# Extract table names from FROM and JOIN clauses
	# Match: FROM table, JOIN table, FROM `table`
	table_pattern = r'(?:FROM|JOIN)\s+`?(\w+)`?'
	referenced = re.findall(table_pattern, normalized_sql)

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
	limit_match = re.search(r'\bLIMIT\s+(\d+)', normalized)
	if limit_match:
		existing_limit = int(limit_match.group(1))
		if existing_limit > max_rows:
			# Replace with capped limit
			sql = re.sub(
				r'\bLIMIT\s+\d+',
				f'LIMIT {max_rows}',
				sql,
				flags=re.IGNORECASE,
			)
		return sql

	# No LIMIT found — only add for SELECT statements (not SHOW/DESCRIBE)
	if re.match(r'^\s*(SELECT)\b', normalized):
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
