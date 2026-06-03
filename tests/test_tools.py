"""Test MCP tool invocations via HTTP.

These tests call actual tools through the JSON-RPC interface and verify
the response structure. Requires the server to be running.

Start the server:
    python -m mcp_server

Run tests:
    pytest tests/test_tools.py -v
"""

import json
import os

import pytest

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

_REQ_ID = 0


def _call_tool(name: str, arguments: dict | None = None) -> dict:
	"""Call an MCP tool and return the parsed result content."""
	global _REQ_ID
	_REQ_ID += 1
	with httpx.Client(timeout=30) as client:
		resp = client.post(
			BASE_URL,
			headers=HEADERS,
			json={
				"jsonrpc": "2.0",
				"id": _REQ_ID,
				"method": "tools/call",
				"params": {
					"name": name,
					"arguments": arguments or {},
				},
			},
		)
	data = resp.json()
	if "error" in data:
		pytest.fail(f"JSON-RPC error: {data['error']}")
	# MCP tool results are in result.content[0].text
	result = data.get("result", {})
	content = result.get("content", [])
	if content and isinstance(content, list):
		text = content[0].get("text", "{}")
		return json.loads(text)
	return result


def _server_available() -> bool:
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
class TestHealthCheck:
	"""Test the health_check tool."""

	def test_returns_ok_status(self):
		result = _call_tool("health_check")
		assert result["status"] in ("ok", "connected")

	def test_includes_version(self):
		result = _call_tool("health_check")
		assert "version" in result

	def test_includes_database_name(self):
		result = _call_tool("health_check")
		assert result.get("database") == "ecological_monitoring"


@skip_if_no_server
class TestListTables:
	"""Test the list_tables tool."""

	def test_returns_tables_array(self):
		result = _call_tool("list_tables")
		assert "tables" in result
		assert isinstance(result["tables"], list)

	def test_includes_core_tables(self):
		result = _call_tool("list_tables")
		tables = result["tables"]
		for expected in ("ltem_historical_database", "ltem_monitoring_species", "ltem_monitoring_reefs"):
			assert expected in tables, f"Missing table: {expected}"

	def test_includes_count(self):
		result = _call_tool("list_tables")
		assert result["count"] >= 3


@skip_if_no_server
class TestDescribeTable:
	"""Test the describe_table_tool."""

	def test_returns_columns(self):
		result = _call_tool("describe_table_tool", {"table": "ltem_historical_database"})
		assert "columns" in result
		assert len(result["columns"]) > 0

	def test_includes_expected_columns(self):
		result = _call_tool("describe_table_tool", {"table": "ltem_historical_database"})
		col_names = [c["Field"] for c in result["columns"]]
		for expected in ("Year", "Region", "Species", "Biomass"):
			assert expected in col_names, f"Missing column: {expected}"

	def test_invalid_table_returns_error(self):
		result = _call_tool("describe_table_tool", {"table": "nonexistent_table"})
		assert "error" in result


@skip_if_no_server
class TestGetRegions:
	"""Test the get_regions tool."""

	def test_returns_data(self):
		result = _call_tool("get_regions")
		assert "data" in result
		assert len(result["data"]) > 0

	def test_includes_cabo_pulmo(self):
		result = _call_tool("get_regions")
		regions = [r["Region"] for r in result["data"]]
		assert "Cabo Pulmo" in regions

	def test_returns_at_least_five_regions(self):
		result = _call_tool("get_regions")
		assert len(result["data"]) >= 5


@skip_if_no_server
class TestGetObservations:
	"""Test the get_observations tool."""

	def test_returns_data_with_limit(self):
		result = _call_tool("get_observations", {"region": "Cabo Pulmo", "limit": 5})
		assert "data" in result
		assert len(result["data"]) <= 5

	def test_returns_expected_columns(self):
		result = _call_tool("get_observations", {"region": "Cabo Pulmo", "limit": 1})
		if result["data"]:
			row = result["data"][0]
			for field in ("Year", "Region", "Species"):
				assert field in row, f"Missing field: {field}"


# ---------------------------------------------------------------------------
# Reporting tools
# ---------------------------------------------------------------------------

@skip_if_no_server
class TestNumeralia:
	"""Test reporting / numeralia tools."""

	def test_numeralia_historical(self):
		result = _call_tool("numeralia_historical")
		assert "data" in result
		data = result["data"]
		for key in ("n_observations", "n_species", "n_reefs", "n_regions"):
			assert key in data, f"Missing key: {key}"
		assert data["n_observations"] > 0

	def test_numeralia_by_label(self):
		result = _call_tool("numeralia_by_label")
		assert "data" in result
		assert len(result["data"]) >= 2  # PEC and INV

	def test_numeralia_by_label_filtered(self):
		result = _call_tool("numeralia_by_label", {"year": 2020})
		assert "data" in result

	def test_numeralia_by_region(self):
		result = _call_tool("numeralia_by_region")
		assert "data" in result
		assert len(result["data"]) >= 5

	def test_numeralia_by_region_filtered(self):
		result = _call_tool("numeralia_by_region", {"label": "PEC"})
		assert "data" in result

	def test_consistent_reefs(self):
		result = _call_tool("consistent_reefs", {"min_years": 5})
		assert "data" in result
		assert "meta" in result
		if result["data"]:
			reef = result["data"][0]
			assert "years_monitored" in reef
			assert reef["years_monitored"] >= 5


# ---------------------------------------------------------------------------
# Data quality tools
# ---------------------------------------------------------------------------

@skip_if_no_server
class TestDataQuality:
	"""Test data quality tools."""

	def test_detect_outliers_mad(self):
		result = _call_tool("detect_outliers_mad", {"region": "Cabo Pulmo"})
		assert "data" in result
		assert "meta" in result
		assert "species_analyzed" in result["meta"]

	def test_detect_outliers_quantile(self):
		result = _call_tool("detect_outliers_quantile", {"region": "Cabo Pulmo"})
		assert "data" in result
		assert "meta" in result

	def test_sample_size_assessment(self):
		result = _call_tool("sample_size_assessment", {"group_by": "Region"})
		assert "data" in result
		if result["data"]:
			row = result["data"][0]
			assert "n_transects" in row
			assert "sample_flag" in row

	def test_transect_coverage_audit(self):
		result = _call_tool("transect_coverage_audit")
		assert "data" in result
		data = result["data"]
		assert "matched" in data or "match_rate_pct" in data

	def test_data_completeness_report(self):
		result = _call_tool("data_completeness_report")
		assert "data" in result
		assert "meta" in result


# ---------------------------------------------------------------------------
# Invertebrate tools
# ---------------------------------------------------------------------------

@skip_if_no_server
class TestInvertebrates:
	"""Test invertebrate survey tools."""

	def test_invertebrate_summary(self):
		result = _call_tool("invertebrate_summary")
		assert "data" in result
		assert "meta" in result
		assert len(result["data"]) > 0

	def test_invertebrate_species_list(self):
		result = _call_tool("invertebrate_species_list")
		assert "data" in result
		if result["data"]:
			sp = result["data"][0]
			assert "Species" in sp

	def test_coral_warm_cold_ratio(self):
		result = _call_tool("coral_warm_cold_ratio")
		assert "data" in result

	def test_invertebrate_latitudinal_gradient(self):
		result = _call_tool("invertebrate_latitudinal_gradient")
		assert "data" in result
		assert "meta" in result

	def test_invertebrate_latitudinal_gradient_period(self):
		result = _call_tool("invertebrate_latitudinal_gradient", {"period": "Warming"})
		assert "data" in result

	def test_invertebrate_temporal_trends(self):
		result = _call_tool("invertebrate_temporal_trends")
		assert "data" in result
		assert "meta" in result

	def test_bleaching_assessment(self):
		result = _call_tool("bleaching_assessment")
		assert "data" in result


# ---------------------------------------------------------------------------
# Ecosystem indicator tools
# ---------------------------------------------------------------------------

@skip_if_no_server
class TestEcosystemIndicators:
	"""Test NRSI and functional group tools."""

	def test_nrsi_by_reef(self):
		result = _call_tool("nrsi_by_reef")
		assert "data" in result
		assert "meta" in result
		if result["data"]:
			reef = result["data"][0]
			assert "mean_nrsi" in reef

	def test_nrsi_by_reef_filtered(self):
		result = _call_tool("nrsi_by_reef", {"region": "Cabo Pulmo"})
		assert "data" in result

	def test_nrsi_bootstrapped(self):
		result = _call_tool("nrsi_bootstrapped", {"region": "Cabo Pulmo", "n_boot": 50})
		assert "data" in result
		if result["data"]:
			reef = result["data"][0]
			assert "ci_lower" in reef
			assert "ci_upper" in reef

	def test_nrsi_regional_summary(self):
		result = _call_tool("nrsi_regional_summary")
		assert "data" in result
		assert "meta" in result

	def test_functional_group_biomass(self):
		result = _call_tool("functional_group_biomass")
		assert "data" in result
		assert len(result["data"]) > 0

	def test_functional_group_temporal(self):
		result = _call_tool("functional_group_temporal")
		assert "data" in result

	def test_functional_group_by_region(self):
		result = _call_tool("functional_group_by_region")
		assert "data" in result
