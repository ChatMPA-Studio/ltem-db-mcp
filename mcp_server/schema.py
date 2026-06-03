"""Schema discovery and caching for LTEM database."""

from mcp_server.db import execute_raw, execute_select

# In-memory cache (populated once per process)
_schema_cache: dict | None = None


def discover_tables() -> list[str]:
	"""Return list of table names in the database."""
	rows = execute_raw("SHOW TABLES")
	# SHOW TABLES returns rows with a single key like 'Tables_in_<dbname>'
	tables = []
	for row in rows:
		# Get the first (and only) value from each row
		tables.append(list(row.values())[0])
	return tables


def describe_table(table: str) -> list[dict]:
	"""Return column descriptions for a table.

	Returns list of dicts with Field, Type, Null, Key, Default, Extra.
	"""
	# We use SHOW COLUMNS which is equivalent to DESCRIBE
	# but we validate the table name first via security
	from mcp_server.security import sanitize_table_name
	safe_table = sanitize_table_name(table)
	rows = execute_raw(f"SHOW COLUMNS FROM `{safe_table}`")
	return rows


def get_row_count(table: str) -> int:
	"""Return approximate row count for a table."""
	from mcp_server.security import sanitize_table_name
	safe_table = sanitize_table_name(table)
	rows = execute_select(
		f"SELECT COUNT(*) AS cnt FROM `{safe_table}`",
		max_rows=1,
	)
	return rows[0]['cnt'] if rows else 0


def build_schema_snapshot() -> dict:
	"""Build a complete schema snapshot with tables, columns, types, and row counts.

	Results are cached in-memory for the process lifetime.
	"""
	global _schema_cache
	if _schema_cache is not None:
		return _schema_cache

	from mcp_server.security import ALLOWED_TABLES

	snapshot = {"tables": {}}

	for table in sorted(ALLOWED_TABLES):
		try:
			columns = describe_table(table)
			row_count = get_row_count(table)
			snapshot["tables"][table] = {
				"columns": [
					{
						"name": col["Field"],
						"type": col["Type"],
						"nullable": col["Null"] == "YES",
						"key": col.get("Key", ""),
					}
					for col in columns
				],
				"row_count": row_count,
			}
		except Exception as e:
			snapshot["tables"][table] = {"error": str(e)}

	_schema_cache = snapshot
	return snapshot


def invalidate_cache() -> None:
	"""Clear the schema cache to force re-discovery."""
	global _schema_cache
	_schema_cache = None
