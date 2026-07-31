"""Database connection and query execution for LTEM ecological monitoring."""

import pymysql
import pymysql.cursors

from mcp_server import config
from mcp_server.security import validate_sql, enforce_limit, DEFAULT_TIMEOUT, DEFAULT_MAX_ROWS


def get_connection() -> pymysql.connections.Connection:
	"""Create a new database connection using config settings.

	Raises RuntimeError if connection fails.
	"""
	conn_kwargs = dict(
		host=config.DB_HOST,
		port=config.DB_PORT,
		user=config.DB_USER,
		password=config.DB_PASSWORD,
		database=config.DB_NAME,
		cursorclass=pymysql.cursors.DictCursor,
		read_timeout=DEFAULT_TIMEOUT,
		write_timeout=DEFAULT_TIMEOUT,
		connect_timeout=10,
		charset='utf8mb4',
	)

	# Optional TLS (OFF by default). With a CA bundle the server cert is
	# verified; without one, the connection is encrypted but unverified.
	if config.DB_SSL:
		conn_kwargs["ssl"] = (
			{"ca": config.DB_SSL_CA} if config.DB_SSL_CA else {"check_hostname": False}
		)

	return pymysql.connect(**conn_kwargs)


def execute_select(
	sql: str,
	params: tuple | list | dict | None = None,
	max_rows: int = DEFAULT_MAX_ROWS,
) -> list[dict]:
	"""Execute a validated SELECT query and return results as list of dicts.

	Args:
		sql: SQL SELECT statement
		params: Query parameters for parameterized queries
		max_rows: Maximum rows to return (auto-injected LIMIT)

	Returns:
		List of row dictionaries

	Raises:
		ValueError: If SQL fails validation
		RuntimeError: If database connection fails
	"""
	validate_sql(sql)
	sql = enforce_limit(sql, max_rows)

	conn = get_connection()
	try:
		with conn.cursor() as cursor:
			cursor.execute(sql, params)
			rows = cursor.fetchall()
			return rows
	finally:
		conn.close()


def execute_raw(sql: str) -> list[dict]:
	"""Execute a SHOW or DESCRIBE statement (no LIMIT injection).

	Used for schema discovery only. Still validates SQL safety.
	"""
	validate_sql(sql)

	conn = get_connection()
	try:
		with conn.cursor() as cursor:
			cursor.execute(sql)
			return cursor.fetchall()
	finally:
		conn.close()


def test_connection() -> dict:
	"""Test database connectivity and return server info."""
	conn = get_connection()
	try:
		with conn.cursor() as cursor:
			cursor.execute("SELECT VERSION() AS version")
			version = cursor.fetchone()
			cursor.execute("SELECT DATABASE() AS db_name")
			db_info = cursor.fetchone()
			cursor.execute("SELECT CURRENT_USER() AS `db_user`")
			user_info = cursor.fetchone()
			return {
				"status": "connected",
				"version": version["version"] if version else None,
				"database": db_info["db_name"] if db_info else None,
				"user": user_info["db_user"] if user_info else None,
			}
	finally:
		conn.close()
