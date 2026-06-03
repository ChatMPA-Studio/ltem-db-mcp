"""Data quality assessment and outlier detection tools."""

import json
import math
from collections import defaultdict

import numpy as np

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
	"""Register data quality tools with the MCP server."""

	@mcp.tool()
	def detect_outliers_mad(
		region: str | None = None,
		year: int | None = None,
		z_threshold: float = 3.5,
	) -> str:
		"""Detect outliers using Median Absolute Deviation (MAD) per species.

		The MAD method is robust to extreme values. A modified Z-score above
		the threshold flags potential outliers in Size and Quantity.
		Based on Iglewicz & Hoaglin (1993) recommendation of z=3.5.

		Args:
			region: Filter by region
			year: Filter by year
			z_threshold: Modified Z-score threshold (default 3.5)
		"""
		conditions = ["Species IS NOT NULL"]
		params = []
		if region:
			conditions.append("Region = %s")
			params.append(region)
		if year:
			conditions.append("Year = %s")
			params.append(year)

		where = "WHERE " + " AND ".join(conditions)

		# Fetch per-species Size and Quantity values
		sql = (
			"SELECT Species, Size, Quantity "
			f"FROM ltem_historical_database {where} "
			"ORDER BY Species"
		)
		rows = execute_select(sql, params=tuple(params) if params else None, max_rows=50000)

		# Group by species
		species_data: dict[str, dict[str, list]] = defaultdict(lambda: {"size": [], "quantity": []})
		for r in rows:
			sp = r["Species"]
			if r.get("Size") is not None:
				species_data[sp]["size"].append(float(r["Size"]))
			if r.get("Quantity") is not None:
				species_data[sp]["quantity"].append(float(r["Quantity"]))

		results = []
		for sp in sorted(species_data.keys()):
			entry = {"species": sp}
			for metric_name in ("size", "quantity"):
				vals = species_data[sp][metric_name]
				if len(vals) < 5:
					entry[f"{metric_name}_n"] = len(vals)
					entry[f"{metric_name}_flag"] = "insufficient_data"
					continue

				arr = np.array(vals)
				median = float(np.median(arr))
				mad = float(np.median(np.abs(arr - median)))

				if mad == 0:
					entry[f"{metric_name}_n"] = len(vals)
					entry[f"{metric_name}_median"] = round(median, 2)
					entry[f"{metric_name}_mad"] = 0
					entry[f"{metric_name}_flag"] = "zero_mad"
					continue

				lower = max(0, median - z_threshold * mad)
				upper = median + z_threshold * mad
				n_outliers = int(np.sum((arr < lower) | (arr > upper)))

				entry[f"{metric_name}_n"] = len(vals)
				entry[f"{metric_name}_median"] = round(median, 2)
				entry[f"{metric_name}_mad"] = round(mad, 4)
				entry[f"{metric_name}_lower"] = round(lower, 2)
				entry[f"{metric_name}_upper"] = round(upper, 2)
				entry[f"{metric_name}_n_outliers"] = n_outliers
				entry[f"{metric_name}_pct_outliers"] = round(100 * n_outliers / len(vals), 2)

			results.append(entry)

		# Filter to only species with outliers detected
		flagged = [r for r in results if (
			r.get("size_n_outliers", 0) > 0 or r.get("quantity_n_outliers", 0) > 0
		)]

		return json.dumps({
			"data": flagged,
			"meta": {
				"parameters": {"region": region, "year": year, "z_threshold": z_threshold},
				"species_analyzed": len(results),
				"species_with_outliers": len(flagged),
				"method": "Median Absolute Deviation (MAD)",
				"reference": "Iglewicz & Hoaglin, 1993",
			},
		})

	@mcp.tool()
	def detect_outliers_quantile(
		region: str | None = None,
		year: int | None = None,
		ci: float = 0.95,
	) -> str:
		"""Detect outliers using quantile bounds per species.

		Values outside the CI interval (e.g. 2.5th and 97.5th percentiles
		for ci=0.95) are flagged.

		Args:
			region: Filter by region
			year: Filter by year
			ci: Confidence interval width (default 0.95)
		"""
		conditions = ["Species IS NOT NULL"]
		params = []
		if region:
			conditions.append("Region = %s")
			params.append(region)
		if year:
			conditions.append("Year = %s")
			params.append(year)

		where = "WHERE " + " AND ".join(conditions)

		sql = (
			"SELECT Species, Size, Quantity "
			f"FROM ltem_historical_database {where} "
			"ORDER BY Species"
		)
		rows = execute_select(sql, params=tuple(params) if params else None, max_rows=50000)

		species_data: dict[str, dict[str, list]] = defaultdict(lambda: {"size": [], "quantity": []})
		for r in rows:
			sp = r["Species"]
			if r.get("Size") is not None:
				species_data[sp]["size"].append(float(r["Size"]))
			if r.get("Quantity") is not None:
				species_data[sp]["quantity"].append(float(r["Quantity"]))

		lower_q = (1 - ci) / 2
		upper_q = 1 - lower_q

		results = []
		for sp in sorted(species_data.keys()):
			entry = {"species": sp}
			for metric_name in ("size", "quantity"):
				vals = species_data[sp][metric_name]
				if len(vals) < 5:
					entry[f"{metric_name}_n"] = len(vals)
					entry[f"{metric_name}_flag"] = "insufficient_data"
					continue

				arr = np.array(vals)
				lower = float(np.quantile(arr, lower_q))
				upper = float(np.quantile(arr, upper_q))
				if metric_name == "quantity":
					lower = max(0, lower)

				n_outliers = int(np.sum((arr < lower) | (arr > upper)))

				entry[f"{metric_name}_n"] = len(vals)
				entry[f"{metric_name}_median"] = round(float(np.median(arr)), 2)
				entry[f"{metric_name}_lower"] = round(lower, 2)
				entry[f"{metric_name}_upper"] = round(upper, 2)
				entry[f"{metric_name}_n_outliers"] = n_outliers
				entry[f"{metric_name}_pct_outliers"] = round(100 * n_outliers / len(vals), 2)

			results.append(entry)

		flagged = [r for r in results if (
			r.get("size_n_outliers", 0) > 0 or r.get("quantity_n_outliers", 0) > 0
		)]

		return json.dumps({
			"data": flagged,
			"meta": {
				"parameters": {"region": region, "year": year, "ci": ci},
				"species_analyzed": len(results),
				"species_with_outliers": len(flagged),
				"method": f"Quantile bounds ({lower_q:.3f} - {upper_q:.3f})",
			},
		})

	@mcp.tool()
	def sample_size_assessment(group_by: str = "Region") -> str:
		"""Classify sample sizes as insufficient (<10), limited (10-30), or sufficient (>=30).

		Helps identify which regions, reefs, or years have adequate replication
		for parametric statistical tests.

		Args:
			group_by: Group results by 'Region', 'Reef', or 'Year'
		"""
		allowed = {"Region", "Reef", "Year"}
		if group_by not in allowed:
			return json.dumps({"error": f"group_by must be one of {allowed}"})

		sql = (
			f"SELECT {group_by}, "
			"COUNT(DISTINCT CONCAT(Year, '-', Reef, '-', Habitat, '-', Transect)) AS n_transects, "
			"COUNT(DISTINCT Species) AS n_species, "
			"COUNT(*) AS n_observations "
			f"FROM ltem_historical_database "
			f"GROUP BY {group_by} "
			f"ORDER BY {group_by}"
		)
		rows = execute_select(sql)
		rows = _serialize_rows(rows)

		for r in rows:
			n = r["n_transects"]
			if n < 10:
				r["sample_flag"] = "insufficient"
			elif n < 30:
				r["sample_flag"] = "limited"
			else:
				r["sample_flag"] = "sufficient"

		summary = defaultdict(int)
		for r in rows:
			summary[r["sample_flag"]] += 1

		return json.dumps({
			"data": rows,
			"meta": {
				"parameters": {"group_by": group_by},
				"row_count": len(rows),
				"summary": dict(summary),
				"thresholds": {"insufficient": "<10", "limited": "10-30", "sufficient": ">=30"},
			},
		})

	@mcp.tool()
	def transect_coverage_audit(
		year: int | None = None,
		region: str | None = None,
	) -> str:
		"""Audit PEC vs INV transect matching to detect coverage gaps.

		Identifies reef-year-depth-transect combinations that have PEC data
		but not INV data (or vice versa).

		Args:
			year: Filter by year
			region: Filter by region
		"""
		conditions = ["Label IS NOT NULL"]
		params = []
		if year:
			conditions.append("Year = %s")
			params.append(year)
		if region:
			conditions.append("Region = %s")
			params.append(region)

		where = "WHERE " + " AND ".join(conditions)

		# Count labels per transect unit
		sql = (
			"SELECT Year, Region, Reef, Habitat, Transect, "
			"GROUP_CONCAT(DISTINCT Label ORDER BY Label) AS labels, "
			"COUNT(DISTINCT Label) AS n_labels "
			f"FROM ltem_historical_database {where} "
			"GROUP BY Year, Region, Reef, Habitat, Transect "
			"ORDER BY Year, Region, Reef"
		)
		rows = execute_select(sql, params=tuple(params) if params else None, max_rows=50000)
		rows = _serialize_rows(rows)

		matched = [r for r in rows if r["n_labels"] >= 2]
		pec_only = [r for r in rows if r.get("labels") == "PEC"]
		inv_only = [r for r in rows if r.get("labels") == "INV"]

		return json.dumps({
			"data": {
				"matched": len(matched),
				"pec_only": len(pec_only),
				"inv_only": len(inv_only),
				"total_transect_units": len(rows),
				"match_rate_pct": round(100 * len(matched) / len(rows), 1) if rows else 0,
				"pec_only_examples": pec_only[:10],
				"inv_only_examples": inv_only[:10],
			},
			"meta": {
				"parameters": {"year": year, "region": region},
				"description": "PEC vs INV transect coverage audit",
			},
		})

	@mcp.tool()
	def data_completeness_report(region: str | None = None) -> str:
		"""Report missing data percentages for key fields by year.

		Checks NULL rates for Size, Biomass, Quantity, TrophicGroup,
		and other important analytical columns.

		Args:
			region: Filter by region
		"""
		conditions = []
		params = []
		if region:
			conditions.append("Region = %s")
			params.append(region)

		where = "WHERE " + " AND ".join(conditions) if conditions else ""

		fields_to_check = [
			"Size", "Biomass", "Quantity", "TrophicGroup", "Label",
			"Habitat", "MPA", "Latitude", "Longitude",
		]

		null_checks = ", ".join(
			f"ROUND(100.0 * SUM(CASE WHEN {f} IS NULL THEN 1 ELSE 0 END) / COUNT(*), 1) "
			f"AS pct_null_{f}"
			for f in fields_to_check
		)

		sql = (
			f"SELECT Year, COUNT(*) AS n_rows, {null_checks} "
			f"FROM ltem_historical_database {where} "
			"GROUP BY Year "
			"ORDER BY Year"
		)
		rows = execute_select(sql, params=tuple(params) if params else None)
		rows = _serialize_rows(rows)

		return json.dumps({
			"data": rows,
			"meta": {
				"parameters": {"region": region},
				"row_count": len(rows),
				"fields_checked": fields_to_check,
				"description": "Percentage of NULL values per field per year",
			},
		})
