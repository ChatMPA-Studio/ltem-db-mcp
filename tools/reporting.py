"""Survey effort and numeralia reporting tools."""

import json

from fastmcp import FastMCP
from mcp_server.db import execute_select


def _safe_float(v):
	if v is None:
		return None
	if hasattr(v, 'as_integer_ratio'):
		return float(v)
	return v


def _serialize_rows(rows):
	return [{k: _safe_float(v) for k, v in r.items()} for r in rows]


def register(mcp: FastMCP) -> None:
	"""Register survey reporting tools with the MCP server."""

	@mcp.tool()
	def numeralia_historical() -> str:
		"""Grand totals for the entire LTEM historical database.

		Returns total observations, individuals counted, species, reefs,
		transects, and surveyed area.
		"""
		sql = (
			"SELECT "
			"COUNT(*) AS n_observations, "
			"SUM(Quantity) AS n_individuals, "
			"COUNT(DISTINCT Species) AS n_species, "
			"COUNT(DISTINCT Reef) AS n_reefs, "
			"COUNT(DISTINCT Region) AS n_regions, "
			"COUNT(DISTINCT CONCAT(Year, '-', Reef, '-', Habitat, '-', Transect)) AS n_transects, "
			"MIN(Year) AS first_year, "
			"MAX(Year) AS last_year, "
			"SUM(DISTINCT Area) AS total_area_m2 "
			"FROM ltem_historical_database"
		)
		rows = execute_select(sql)
		data = _serialize_rows(rows)[0] if rows else {}

		return json.dumps({
			"data": data,
			"meta": {
				"description": "Grand totals across entire LTEM historical database",
			},
		})

	@mcp.tool()
	def numeralia_by_label(year: int | None = None) -> str:
		"""Breakdown of survey effort by Label (PEC = fish, INV = invertebrates).

		Args:
			year: Filter by survey year
		"""
		conditions = ["Label IS NOT NULL"]
		params = []
		if year:
			conditions.append("Year = %s")
			params.append(year)

		where = "WHERE " + " AND ".join(conditions)

		sql = (
			"SELECT Label, "
			"COUNT(*) AS n_observations, "
			"SUM(Quantity) AS n_individuals, "
			"COUNT(DISTINCT Species) AS n_species, "
			"COUNT(DISTINCT Reef) AS n_reefs, "
			"COUNT(DISTINCT CONCAT(Year, '-', Reef, '-', Habitat, '-', Transect)) AS n_transects "
			f"FROM ltem_historical_database {where} "
			"GROUP BY Label "
			"ORDER BY Label"
		)
		rows = execute_select(sql, params=tuple(params) if params else None)
		rows = _serialize_rows(rows)

		return json.dumps({
			"data": rows,
			"meta": {
				"parameters": {"year": year},
				"row_count": len(rows),
				"description": "Survey effort breakdown by Label (PEC/INV)",
			},
		})

	@mcp.tool()
	def numeralia_by_region(
		year: int | None = None,
		label: str | None = None,
	) -> str:
		"""Regional survey effort summary with sites, species, and individuals.

		Args:
			year: Filter by survey year
			label: Filter by survey type (PEC or INV)
		"""
		conditions = []
		params = []
		if year:
			conditions.append("Year = %s")
			params.append(year)
		if label:
			conditions.append("Label = %s")
			params.append(label)

		where = "WHERE " + " AND ".join(conditions) if conditions else ""

		sql = (
			"SELECT Region, "
			"COUNT(*) AS n_observations, "
			"SUM(Quantity) AS n_individuals, "
			"COUNT(DISTINCT Species) AS n_species, "
			"COUNT(DISTINCT Reef) AS n_reefs, "
			"COUNT(DISTINCT CONCAT(Year, '-', Reef, '-', Habitat, '-', Transect)) AS n_transects, "
			"MIN(Year) AS first_year, "
			"MAX(Year) AS last_year, "
			"COUNT(DISTINCT Year) AS n_years "
			f"FROM ltem_historical_database {where} "
			"GROUP BY Region "
			"ORDER BY Region"
		)
		rows = execute_select(sql, params=tuple(params) if params else None)
		rows = _serialize_rows(rows)

		return json.dumps({
			"data": rows,
			"meta": {
				"parameters": {"year": year, "label": label},
				"row_count": len(rows),
				"description": "Survey effort by region",
			},
		})

	@mcp.tool()
	def consistent_reefs(
		min_years: int = 5,
		label: str | None = None,
	) -> str:
		"""Reefs meeting a minimum sampling frequency threshold.

		Returns reefs that have been surveyed for at least `min_years` distinct
		years, useful for filtering balanced panels in temporal analyses.

		Args:
			min_years: Minimum number of distinct survey years required (default 5)
			label: Filter by survey type (PEC or INV)
		"""
		conditions = []
		params = []
		if label:
			conditions.append("Label = %s")
			params.append(label)

		where = "WHERE " + " AND ".join(conditions) if conditions else ""

		sql = (
			"SELECT Region, Reef, "
			"COUNT(DISTINCT Year) AS years_monitored, "
			"MIN(Year) AS first_year, "
			"MAX(Year) AS last_year "
			f"FROM ltem_historical_database {where} "
			"GROUP BY Region, Reef "
			f"HAVING COUNT(DISTINCT Year) >= %s "
			"ORDER BY Region, years_monitored DESC"
		)
		params.append(min_years)
		rows = execute_select(sql, params=tuple(params))
		rows = _serialize_rows(rows)

		# Count total years in dataset for coverage calculation
		total_years_sql = "SELECT COUNT(DISTINCT Year) AS total FROM ltem_historical_database"
		if where:
			total_years_sql += f" {where}"
		total_rows = execute_select(
			total_years_sql,
			params=tuple(params[:-1]) if params[:-1] else None,
		)
		total_years = total_rows[0]["total"] if total_rows else 0

		for r in rows:
			r["coverage_pct"] = round(
				100 * r["years_monitored"] / total_years, 1
			) if total_years else 0

		return json.dumps({
			"data": rows,
			"meta": {
				"parameters": {"min_years": min_years, "label": label},
				"row_count": len(rows),
				"total_years_in_dataset": int(total_years),
				"description": f"Reefs monitored for at least {min_years} years",
			},
		})
