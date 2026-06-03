"""Invertebrate community analysis tools (Label='INV')."""

import json
from collections import defaultdict

import numpy as np
from scipy import stats as sp_stats

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


# Climate period boundaries (from R analysis scripts)
_PERIOD_RANGES = {
	"Historical": (1998, 2013),
	"Warming": (2014, 2024),
	"Current": (2025, 2099),
}


def register(mcp: FastMCP) -> None:
	"""Register invertebrate analysis tools with the MCP server."""

	@mcp.tool()
	def invertebrate_summary(
		region: str | None = None,
		year: int | None = None,
	) -> str:
		"""Invertebrate abundance and richness by Taxa2 and Taxa3.

		Filters to Label='INV' and summarizes key taxonomic groups
		(Asteroidea, Echinoidea, Holaxonia, Scleractinia).

		Args:
			region: Filter by region
			year: Filter by year
		"""
		conditions = ["Label = 'INV'"]
		params = []
		if region:
			conditions.append("Region = %s")
			params.append(region)
		if year:
			conditions.append("Year = %s")
			params.append(year)

		where = "WHERE " + " AND ".join(conditions)

		sql = (
			"SELECT Taxa2, Taxa3, "
			"SUM(Quantity) AS total_abundance, "
			"COUNT(DISTINCT Species) AS species_richness, "
			"COUNT(DISTINCT Reef) AS n_reefs, "
			"COUNT(DISTINCT CONCAT(Year, '-', Reef, '-', Habitat, '-', Transect)) AS n_transects "
			f"FROM ltem_historical_database {where} "
			"GROUP BY Taxa2, Taxa3 "
			"ORDER BY total_abundance DESC"
		)
		rows = execute_select(sql, params=tuple(params) if params else None)
		rows = _serialize_rows(rows)

		total = sum(r["total_abundance"] for r in rows if r.get("total_abundance"))
		for r in rows:
			r["proportion"] = (
				round(r["total_abundance"] / total, 4)
				if total and r.get("total_abundance") else 0
			)

		return json.dumps({
			"data": rows,
			"meta": {
				"parameters": {"region": region, "year": year},
				"row_count": len(rows),
				"total_abundance": total,
				"description": "Invertebrate abundance/richness by taxonomic group",
			},
		})

	@mcp.tool()
	def invertebrate_species_list(
		region: str | None = None,
		year: int | None = None,
		taxa2: str | None = None,
	) -> str:
		"""Species inventory for invertebrates with abundance totals.

		Args:
			region: Filter by region
			year: Filter by year
			taxa2: Filter by Taxa2 category (e.g. 'Asteroidea', 'Echinoidea')
		"""
		conditions = ["Label = 'INV'"]
		params = []
		if region:
			conditions.append("Region = %s")
			params.append(region)
		if year:
			conditions.append("Year = %s")
			params.append(year)
		if taxa2:
			conditions.append("Taxa2 = %s")
			params.append(taxa2)

		where = "WHERE " + " AND ".join(conditions)

		sql = (
			"SELECT Species, Taxa2, Taxa3, Phylum, "
			"SUM(Quantity) AS total_abundance, "
			"COUNT(DISTINCT Region) AS n_regions, "
			"COUNT(DISTINCT Reef) AS n_reefs "
			f"FROM ltem_historical_database {where} "
			"GROUP BY Species, Taxa2, Taxa3, Phylum "
			"ORDER BY total_abundance DESC"
		)
		rows = execute_select(sql, params=tuple(params) if params else None)
		rows = _serialize_rows(rows)

		return json.dumps({
			"data": rows,
			"meta": {
				"parameters": {"region": region, "year": year, "taxa2": taxa2},
				"row_count": len(rows),
				"description": "Invertebrate species inventory",
			},
		})

	@mcp.tool()
	def coral_warm_cold_ratio(
		region: str | None = None,
		year: int | None = None,
	) -> str:
		"""Ratio of warm corals (Scleractinia) to cold corals (Holaxonia) per reef.

		Scleractinia = warm-water hard corals; Holaxonia = cold-water gorgonians.
		Ratio shifts indicate thermal regime changes.

		Args:
			region: Filter by region
			year: Filter by year
		"""
		conditions = [
			"Label = 'INV'",
			"Taxa3 IN ('Scleractinia', 'Holaxonia')",
		]
		params = []
		if region:
			conditions.append("Region = %s")
			params.append(region)
		if year:
			conditions.append("Year = %s")
			params.append(year)

		where = "WHERE " + " AND ".join(conditions)

		# Sum abundance per reef, depth, transect, then average per reef
		sql = (
			"SELECT Region, Reef, Taxa3, "
			"AVG(transect_qty) AS mean_abundance "
			"FROM ("
			"  SELECT Region, Reef, Habitat, Transect, Taxa3, "
			"  SUM(Quantity) AS transect_qty "
			f"  FROM ltem_historical_database {where} "
			"  GROUP BY Region, Reef, Habitat, Transect, Taxa3"
			") sub "
			"GROUP BY Region, Reef, Taxa3 "
			"ORDER BY Region, Reef"
		)
		rows = execute_select(sql, params=tuple(params) if params else None)

		# Pivot to warm/cold per reef
		reef_data: dict[tuple, dict] = {}
		for r in rows:
			key = (r["Region"], r["Reef"])
			if key not in reef_data:
				reef_data[key] = {"region": r["Region"], "reef": r["Reef"], "warm": 0, "cold": 0}
			val = float(r["mean_abundance"]) if r["mean_abundance"] else 0
			if r["Taxa3"] == "Scleractinia":
				reef_data[key]["warm"] = round(val, 2)
			elif r["Taxa3"] == "Holaxonia":
				reef_data[key]["cold"] = round(val, 2)

		results = []
		for rd in reef_data.values():
			total = rd["warm"] + rd["cold"]
			rd["warm_pct"] = round(100 * rd["warm"] / total, 1) if total else 0
			rd["cold_pct"] = round(100 * rd["cold"] / total, 1) if total else 0
			rd["ratio_warm_cold"] = (
				round(rd["warm"] / rd["cold"], 2) if rd["cold"] > 0 else None
			)
			results.append(rd)

		return json.dumps({
			"data": results,
			"meta": {
				"parameters": {"region": region, "year": year},
				"row_count": len(results),
				"description": "Warm coral (Scleractinia) vs cold coral (Holaxonia) ratio per reef",
			},
		})

	@mcp.tool()
	def invertebrate_latitudinal_gradient(period: str | None = None) -> str:
		"""Invertebrate abundance by latitude degree, optionally filtered by climate period.

		Args:
			period: Climate period filter: 'Historical' (1998-2013), 'Warming' (2014-2024), or 'Current' (2025+)
		"""
		conditions = ["Label = 'INV'", "Degree IS NOT NULL"]
		params = []

		if period and period in _PERIOD_RANGES:
			start, end = _PERIOD_RANGES[period]
			conditions.append("Year >= %s AND Year <= %s")
			params.extend([start, end])

		where = "WHERE " + " AND ".join(conditions)

		sql = (
			"SELECT Degree, "
			"SUM(Quantity) AS total_abundance, "
			"AVG(Quantity) AS mean_abundance, "
			"COUNT(DISTINCT Species) AS species_richness, "
			"COUNT(DISTINCT Reef) AS n_reefs "
			f"FROM ltem_historical_database {where} "
			"GROUP BY Degree "
			"ORDER BY Degree"
		)
		rows = execute_select(sql, params=tuple(params) if params else None)
		rows = _serialize_rows(rows)

		# Spearman correlation of degree vs abundance
		correlation = None
		valid = [
			(r["Degree"], r["mean_abundance"])
			for r in rows
			if r.get("Degree") and r.get("mean_abundance")
		]
		if len(valid) >= 5:
			lats, abund = zip(*valid)
			rho, pval = sp_stats.spearmanr(lats, abund)
			correlation = {
				"spearman_rho": round(float(rho), 4),
				"p_value": round(float(pval), 6),
				"n": len(valid),
			}

		return json.dumps({
			"data": rows,
			"meta": {
				"parameters": {"period": period},
				"row_count": len(rows),
				"latitude_correlation": correlation,
				"climate_periods": _PERIOD_RANGES,
				"description": "Invertebrate abundance by latitude degree",
			},
		})

	@mcp.tool()
	def invertebrate_temporal_trends(
		region: str | None = None,
		taxa2: str | None = None,
	) -> str:
		"""Annual invertebrate abundance trends with Mann-Kendall trend test.

		Args:
			region: Filter by region
			taxa2: Filter by Taxa2 category (e.g. 'Asteroidea', 'Echinoidea')
		"""
		conditions = ["Label = 'INV'"]
		params = []
		if region:
			conditions.append("Region = %s")
			params.append(region)
		if taxa2:
			conditions.append("Taxa2 = %s")
			params.append(taxa2)

		where = "WHERE " + " AND ".join(conditions)

		# Transect-level sums, then reef means, then annual means
		sql = (
			"SELECT Year, "
			"AVG(reef_qty) AS mean_abundance, "
			"COUNT(DISTINCT reef_id) AS n_reefs "
			"FROM ("
			"  SELECT Year, CONCAT(Region, '-', Reef) AS reef_id, "
			"  AVG(transect_qty) AS reef_qty "
			"  FROM ("
			"    SELECT Year, Region, Reef, Habitat, Transect, "
			"    SUM(Quantity) AS transect_qty "
			f"    FROM ltem_historical_database {where} "
			"    GROUP BY Year, Region, Reef, Habitat, Transect"
			"  ) t1 "
			"  GROUP BY Year, Region, Reef"
			") t2 "
			"GROUP BY Year "
			"ORDER BY Year"
		)
		rows = execute_select(sql, params=tuple(params) if params else None)
		rows = _serialize_rows(rows)

		# Mann-Kendall trend test
		mk_result = None
		if len(rows) >= 4:
			years = np.array([r["Year"] for r in rows])
			values = np.array([r["mean_abundance"] for r in rows])

			# Mann-Kendall S statistic
			n = len(values)
			s = 0
			for i in range(n - 1):
				for j in range(i + 1, n):
					diff = values[j] - values[i]
					if diff > 0:
						s += 1
					elif diff < 0:
						s -= 1

			# Variance of S
			var_s = n * (n - 1) * (2 * n + 5) / 18.0
			if var_s > 0:
				if s > 0:
					z = (s - 1) / np.sqrt(var_s)
				elif s < 0:
					z = (s + 1) / np.sqrt(var_s)
				else:
					z = 0.0
				p_value = 2.0 * (1.0 - sp_stats.norm.cdf(abs(z)))
			else:
				z = 0.0
				p_value = 1.0

			# Sen's slope
			slopes = []
			for i in range(n - 1):
				for j in range(i + 1, n):
					if years[j] != years[i]:
						slopes.append((values[j] - values[i]) / (years[j] - years[i]))
			sens_slope = float(np.median(slopes)) if slopes else 0

			trend_dir = "increasing" if z > 0 and p_value < 0.05 else (
				"decreasing" if z < 0 and p_value < 0.05 else "no_trend"
			)

			mk_result = {
				"S": int(s),
				"Z": round(float(z), 4),
				"p_value": round(float(p_value), 6),
				"sens_slope": round(sens_slope, 4),
				"trend": trend_dir,
				"n_years": n,
			}

		return json.dumps({
			"data": rows,
			"meta": {
				"parameters": {"region": region, "taxa2": taxa2},
				"row_count": len(rows),
				"mann_kendall": mk_result,
				"description": "Annual invertebrate abundance trends",
			},
		})

	@mcp.tool()
	def bleaching_assessment(
		region: str | None = None,
		year: int | None = None,
	) -> str:
		"""Coral bleaching coverage distribution by reef and year.

		Uses the bleaching_coverage column from the historical database.

		Args:
			region: Filter by region
			year: Filter by year
		"""
		conditions = ["bleaching_coverage IS NOT NULL"]
		params = []
		if region:
			conditions.append("Region = %s")
			params.append(region)
		if year:
			conditions.append("Year = %s")
			params.append(year)

		where = "WHERE " + " AND ".join(conditions)

		sql = (
			"SELECT Year, Region, Reef, "
			"AVG(bleaching_coverage) AS mean_bleaching, "
			"MAX(bleaching_coverage) AS max_bleaching, "
			"MIN(bleaching_coverage) AS min_bleaching, "
			"COUNT(*) AS n_observations "
			f"FROM ltem_historical_database {where} "
			"GROUP BY Year, Region, Reef "
			"ORDER BY Year, Region, Reef"
		)
		try:
			rows = execute_select(sql, params=tuple(params) if params else None)
		except Exception as e:
			if "Unknown column" in str(e) or "bleaching_coverage" in str(e):
				return json.dumps({
					"data": [],
					"meta": {
						"parameters": {"region": region, "year": year},
						"row_count": 0,
						"warnings": [
							"bleaching_coverage column not found in database. "
							"Bleaching data may not be available."
						],
					},
				})
			raise

		rows = _serialize_rows(rows)

		# Severity classification
		for r in rows:
			mb = r.get("mean_bleaching")
			if mb is not None:
				r["mean_bleaching"] = round(mb, 2)
				if mb == 0:
					r["severity"] = "none"
				elif mb < 10:
					r["severity"] = "low"
				elif mb < 30:
					r["severity"] = "moderate"
				elif mb < 60:
					r["severity"] = "high"
				else:
					r["severity"] = "severe"

		return json.dumps({
			"data": rows,
			"meta": {
				"parameters": {"region": region, "year": year},
				"row_count": len(rows),
				"severity_scale": {
					"none": "0%",
					"low": "<10%",
					"moderate": "10-30%",
					"high": "30-60%",
					"severe": ">60%",
				},
				"description": "Coral bleaching coverage by reef and year",
			},
		})
