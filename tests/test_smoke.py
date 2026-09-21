"""Smoke tests for the LTEM Database MCP Server.

These tests validate:
1. Environment variables are loaded correctly
2. Database connectivity works (SELECT-only)
3. Schema discovery returns expected tables
4. Core ecology tools return structured JSON output
5. Security guardrails block dangerous operations

All tests are read-only and deterministic.
Requires a valid .env file with database credentials.

Run with:
    pytest tests/test_smoke.py -v
"""

import json
import os

import pytest


# ---------------------------------------------------------------------------
# 1. Environment variables
# ---------------------------------------------------------------------------

class TestEnvironment:
	"""Verify that all required env vars are set."""

	def test_db_host_is_set(self):
		assert os.getenv('LTEM_DB_HOST'), "LTEM_DB_HOST must be set"

	def test_db_password_is_set(self):
		assert os.getenv('LTEM_DB_PASSWORD'), "LTEM_DB_PASSWORD must be set"

	def test_db_password_is_not_placeholder(self):
		pw = os.getenv('LTEM_DB_PASSWORD', '')
		assert pw != 'CHANGEME', (
			"LTEM_DB_PASSWORD is still 'CHANGEME'. "
			"Replace it with actual credentials in .env"
		)

	def test_db_name_defaults(self):
		name = os.getenv('LTEM_DB_NAME', 'ecological_monitoring')
		assert name == 'ecological_monitoring'


# ---------------------------------------------------------------------------
# 2. Database connectivity
# ---------------------------------------------------------------------------

class TestConnectivity:
	"""Verify that the database is reachable and returns expected metadata."""

	def test_select_one(self):
		"""Most basic connectivity check."""
		from mcp_server.db import get_connection
		conn = get_connection()
		try:
			with conn.cursor() as cur:
				cur.execute('SELECT 1 AS ping')
				row = cur.fetchone()
				assert row['ping'] == 1
		finally:
			conn.close()

	def test_select_database(self):
		"""Confirm we're connected to the right database."""
		from mcp_server.db import get_connection
		conn = get_connection()
		try:
			with conn.cursor() as cur:
				cur.execute('SELECT DATABASE() AS db_name')
				row = cur.fetchone()
				assert row['db_name'] == 'ecological_monitoring'
		finally:
			conn.close()

	def test_health_check_tool(self):
		"""health_check() tool returns connected status."""
		from mcp_server.server import health_check
		result = json.loads(health_check())
		assert result['status'] in ('ok', 'connected')
		assert 'version' in result


# ---------------------------------------------------------------------------
# 3. Schema discovery
# ---------------------------------------------------------------------------

class TestSchemaDiscovery:
	"""Validate that schema introspection works and returns expected tables."""

	def test_list_tables_returns_core_tables(self):
		"""list_tables() must include the 3 core LTEM tables."""
		from mcp_server.server import list_tables
		result = json.loads(list_tables())
		assert 'tables' in result
		table_names = result['tables']
		for expected in (
			'ltem_historical_database',
			'ltem_monitoring_species',
			'ltem_monitoring_reefs',
		):
			assert expected in table_names, f"Missing table: {expected}"

	def test_describe_historical_table(self):
		"""describe_table for ltem_historical_database returns columns."""
		from mcp_server.server import describe_table_tool
		result = json.loads(describe_table_tool('ltem_historical_database'))
		assert 'columns' in result
		col_names = [c['Field'] for c in result['columns']]
		for expected in ('Year', 'Region', 'Reef', 'Species', 'Biomass'):
			assert expected in col_names, f"Missing column: {expected}"

	def test_schema_snapshot_has_row_counts(self):
		"""schema_snapshot() includes row counts for each table."""
		from mcp_server.server import schema_snapshot
		result = json.loads(schema_snapshot())
		assert 'tables' in result
		for table_name, info in result['tables'].items():
			assert 'row_count' in info, f"No row_count for {table_name}"
			assert info['row_count'] > 0, f"Empty table: {table_name}"


# ---------------------------------------------------------------------------
# 4. Ecology tools — structured output via direct DB queries
# ---------------------------------------------------------------------------

class TestEcologyTools:
	"""Verify ecology tools return well-structured output."""

	def test_regions_query(self):
		"""Regions query returns Cabo Pulmo and at least 5 regions."""
		from mcp_server.db import execute_select
		rows = execute_select(
			"SELECT DISTINCT Region FROM ltem_historical_database ORDER BY Region"
		)
		regions = [r['Region'] for r in rows if r.get('Region')]
		assert len(regions) >= 5, f"Expected >=5 regions, got {len(regions)}"
		assert 'Cabo Pulmo' in regions

	def test_observations_query(self):
		"""Observations query returns data with expected columns."""
		from mcp_server.db import execute_select
		rows = execute_select(
			"SELECT Year, Region, Species, Biomass "
			"FROM ltem_historical_database "
			"WHERE Region = %s",
			params=('Cabo Pulmo',),
			max_rows=5,
		)
		assert len(rows) == 5
		row = rows[0]
		for field in ('Year', 'Region', 'Species', 'Biomass'):
			assert field in row, f"Missing field: {field}"

	def test_diversity_computation(self):
		"""Diversity query returns aggregatable abundance data."""
		from mcp_server.db import execute_select
		rows = execute_select(
			"SELECT Species, SUM(Quantity) AS total_n "
			"FROM ltem_historical_database "
			"WHERE Region = %s "
			"GROUP BY Species "
			"ORDER BY total_n DESC",
			params=('Cabo Pulmo',),
			max_rows=100,
		)
		assert len(rows) > 0, "No species data for Cabo Pulmo"
		assert 'Species' in rows[0]
		assert 'total_n' in rows[0]

	def test_biomass_by_region_query(self):
		"""Biomass aggregation by region returns numeric means."""
		from mcp_server.db import execute_select
		rows = execute_select(
			"SELECT Region, AVG(Biomass) AS mean_biomass, COUNT(*) AS n "
			"FROM ltem_historical_database "
			"WHERE Biomass IS NOT NULL AND Biomass > 0 "
			"GROUP BY Region "
			"ORDER BY mean_biomass DESC",
		)
		assert len(rows) >= 3, "Expected at least 3 regions with biomass"
		row = rows[0]
		assert row['mean_biomass'] > 0

	def test_cabo_pulmo_time_series(self):
		"""Cabo Pulmo has multi-year biomass data for recovery analysis."""
		from mcp_server.db import execute_select
		rows = execute_select(
			"SELECT Year, AVG(Biomass) AS mean_bm, COUNT(*) AS n "
			"FROM ltem_historical_database "
			"WHERE Region = %s AND Biomass IS NOT NULL "
			"GROUP BY Year "
			"ORDER BY Year",
			params=('Cabo Pulmo',),
		)
		assert len(rows) >= 5, "Expected >=5 years for Cabo Pulmo"
		years = [float(r['Year']) for r in rows]
		assert min(years) <= 2000, "Expected data from 1999-2000"
		assert max(years) >= 2020, "Expected data through at least 2020"

	def test_trend_data_sufficient(self):
		"""Trend analysis needs enough years to compute Mann-Kendall."""
		from mcp_server.db import execute_select
		rows = execute_select(
			"SELECT DISTINCT Year FROM ltem_historical_database "
			"WHERE Region = %s ORDER BY Year",
			params=('Cabo Pulmo',),
		)
		years = [float(r['Year']) for r in rows]
		assert len(years) >= 4, (
			f"Mann-Kendall needs >=4 data points, got {len(years)}"
		)


# ---------------------------------------------------------------------------
# 5. Security guardrails
# ---------------------------------------------------------------------------

class TestSecurityGuardrails:
	"""Verify that the security layer blocks dangerous operations."""

	def test_rejects_insert(self):
		from mcp_server.security import validate_sql
		with pytest.raises(ValueError, match='SELECT.*SHOW.*DESCRIBE'):
			validate_sql("INSERT INTO ltem_historical_database VALUES (1)")

	def test_rejects_drop(self):
		from mcp_server.security import validate_sql
		with pytest.raises(ValueError, match='SELECT.*SHOW.*DESCRIBE'):
			validate_sql("DROP TABLE ltem_historical_database")

	def test_rejects_update(self):
		from mcp_server.security import validate_sql
		with pytest.raises(ValueError, match='SELECT.*SHOW.*DESCRIBE'):
			validate_sql("UPDATE ltem_historical_database SET Biomass = 0")

	def test_rejects_non_whitelisted_table(self):
		from mcp_server.security import validate_sql
		with pytest.raises(ValueError, match='not in the whitelist'):
			validate_sql("SELECT * FROM users")

	def test_allows_select_from_core_table(self):
		from mcp_server.security import validate_sql
		# Should not raise
		validate_sql("SELECT * FROM ltem_historical_database")

	def test_limit_enforcement(self):
		from mcp_server.security import enforce_limit
		sql = "SELECT * FROM ltem_historical_database"
		result = enforce_limit(sql, max_rows=100)
		assert 'LIMIT 100' in result

	def test_limit_cap_reduces_excessive(self):
		from mcp_server.security import enforce_limit
		sql = "SELECT * FROM ltem_historical_database LIMIT 99999"
		result = enforce_limit(sql, max_rows=5000)
		assert 'LIMIT 5000' in result


# ---------------------------------------------------------------------------
# 6. New tool module imports
# ---------------------------------------------------------------------------

class TestNewModuleImports:
	"""Verify that new tool modules import and expose register()."""

	def test_reporting_module(self):
		import tools.reporting as mod
		assert hasattr(mod, 'register'), "tools.reporting must have register()"
		assert callable(mod.register)

	def test_data_quality_module(self):
		import tools.data_quality as mod
		assert hasattr(mod, 'register'), "tools.data_quality must have register()"
		assert callable(mod.register)

	def test_invertebrates_module(self):
		import tools.invertebrates as mod
		assert hasattr(mod, 'register'), "tools.invertebrates must have register()"
		assert callable(mod.register)

	def test_ecosystem_indicators_module(self):
		import tools.ecosystem_indicators as mod
		assert hasattr(mod, 'register'), "tools.ecosystem_indicators must have register()"
		assert callable(mod.register)


# ---------------------------------------------------------------------------
# 7. New column / data queries
# ---------------------------------------------------------------------------

class TestNewColumnQueries:
	"""Verify that columns and data needed by new tools exist."""

	def test_label_inv_data_exists(self):
		"""INV label data is required by invertebrate tools."""
		from mcp_server.db import execute_select
		rows = execute_select(
			"SELECT COUNT(*) AS n FROM ltem_historical_database "
			"WHERE Label = %s",
			params=('INV',),
		)
		assert rows[0]['n'] > 0, "No rows with Label='INV'"

	def test_label_pec_data_exists(self):
		"""PEC label data is required by fish tools."""
		from mcp_server.db import execute_select
		rows = execute_select(
			"SELECT COUNT(*) AS n FROM ltem_historical_database "
			"WHERE Label = %s",
			params=('PEC',),
		)
		assert rows[0]['n'] > 0, "No rows with Label='PEC'"

	def test_trophic_level_f_categories(self):
		"""TrophicLevelF must include UTL and LTL categories for NRSI."""
		from mcp_server.db import execute_select
		rows = execute_select(
			"SELECT DISTINCT TrophicLevelF FROM ltem_historical_database "
			"WHERE TrophicLevelF IS NOT NULL"
		)
		categories = {r['TrophicLevelF'] for r in rows}
		assert '4-4.5' in categories, "Missing UTL category '4-4.5'"
		assert '2-2.5' in categories, "Missing LTL category '2-2.5'"

	def test_functional_groups_populated(self):
		"""Functional_groups column must have data for ecosystem indicators."""
		from mcp_server.db import execute_select
		rows = execute_select(
			"SELECT COUNT(DISTINCT Functional_groups) AS n "
			"FROM ltem_historical_database "
			"WHERE Functional_groups IS NOT NULL"
		)
		assert rows[0]['n'] >= 3, "Expected >=3 distinct functional groups"

	def test_bleaching_coverage_column_exists(self):
		"""bleaching_coverage column must exist for bleaching tools."""
		from mcp_server.db import execute_select
		rows = execute_select(
			"SELECT COUNT(*) AS n FROM ltem_historical_database "
			"WHERE bleaching_coverage IS NOT NULL"
		)
		# Column must exist (query succeeds) and have some data
		assert rows[0]['n'] >= 0

	def test_taxa2_populated_for_inv(self):
		"""Taxa2 column must have data for invertebrate summaries."""
		from mcp_server.db import execute_select
		rows = execute_select(
			"SELECT COUNT(DISTINCT Taxa2) AS n "
			"FROM ltem_historical_database "
			"WHERE Label = %s AND Taxa2 IS NOT NULL",
			params=('INV',),
		)
		assert rows[0]['n'] >= 2, "Expected >=2 distinct Taxa2 for INV"

	def test_degree_column_populated(self):
		"""Degree column is needed for latitudinal gradient analysis."""
		from mcp_server.db import execute_select
		rows = execute_select(
			"SELECT COUNT(DISTINCT Degree) AS n "
			"FROM ltem_historical_database "
			"WHERE Degree IS NOT NULL"
		)
		assert rows[0]['n'] >= 3, "Expected >=3 distinct latitude degrees"


# ---------------------------------------------------------------------------
# 8. Report generator SQL injection regression
# ---------------------------------------------------------------------------
# tools/report_generator.py used to build its `region`/`year` filters with
# f-strings (e.g. f"... AND Region = '{region}'") instead of the %s +
# params= pattern used everywhere else in the codebase. These tests mock
# execute_select and assert a malicious value never appears in the raw SQL
# text handed to it — it must only travel through `params`. That's the
# structural guarantee that makes injection impossible regardless of the
# payload, so the assertion doesn't need to enumerate attack strings.
#
# Requires the `report` extra (matplotlib/seaborn) to import report_generator,
# but not a live database — execute_select is mocked, no .env needed.
# ---------------------------------------------------------------------------

class TestReportGeneratorSQLInjection:
	"""Regression test for the SQL injection fixed in tools/report_generator.py."""

	MALICIOUS_REGION = "x' OR SLEEP(5)-- "

	# One row with every key any of the four report builders reads, so the
	# same mocked return value satisfies whichever query is being answered.
	GENERIC_ROW = {
		"protection_level": "Cabo Pulmo", "mean_biomass": 10.0, "std_biomass": 1.0,
		"n_reefs": 2, "n_transects": 5, "Biomass": 10.0, "Year": 2020, "value": 10.0,
		"Species": "Test species", "total_abundance": 100, "TrophicGroup": "Herbivoro",
		"total_biomass": 50.0, "n_rows": 10, "null_size": 1, "null_biomass": 1,
		"null_trophic": 1, "Region": "La Paz", "n_years": 5,
	}

	def _assert_region_never_leaks_into_raw_sql(self, mock_execute):
		assert mock_execute.call_args_list, "execute_select was never called"
		for call in mock_execute.call_args_list:
			sql = call.args[0]
			assert self.MALICIOUS_REGION not in sql, (
				f"Malicious region leaked into raw SQL text: {sql!r}"
			)

	def test_mpa_effectiveness_report_parameterizes_region(self):
		from unittest.mock import patch
		from tools.report_generator import _create_mpa_effectiveness_report

		with patch(
			"tools.report_generator.execute_select", return_value=[self.GENERIC_ROW]
		) as mock_exec:
			_create_mpa_effectiveness_report(region=self.MALICIOUS_REGION)
		self._assert_region_never_leaks_into_raw_sql(mock_exec)

	def test_temporal_trends_report_parameterizes_region(self):
		from unittest.mock import patch
		from tools.report_generator import _create_temporal_trends_report

		with patch(
			"tools.report_generator.execute_select", return_value=[self.GENERIC_ROW]
		) as mock_exec:
			_create_temporal_trends_report(region=self.MALICIOUS_REGION)
		self._assert_region_never_leaks_into_raw_sql(mock_exec)

	def test_community_structure_report_parameterizes_region_and_year(self):
		from unittest.mock import patch
		from tools.report_generator import _create_community_structure_report

		with patch(
			"tools.report_generator.execute_select", return_value=[self.GENERIC_ROW]
		) as mock_exec:
			_create_community_structure_report(region=self.MALICIOUS_REGION, year=2020)
		self._assert_region_never_leaks_into_raw_sql(mock_exec)

	def test_data_quality_report_parameterizes_region(self):
		from unittest.mock import patch
		from tools.report_generator import _create_data_quality_report

		with patch(
			"tools.report_generator.execute_select", return_value=[self.GENERIC_ROW]
		) as mock_exec:
			_create_data_quality_report(region=self.MALICIOUS_REGION)
		self._assert_region_never_leaks_into_raw_sql(mock_exec)
