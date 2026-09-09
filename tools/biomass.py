"""Biomass and productivity analysis tools."""

import json
import math
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


def _biomass_warnings(rows, biomass_col="total_biomass"):
	"""Generate warnings if biomass data is sparse."""
	warnings = []
	total = len(rows)
	nulls = sum(1 for r in rows if r.get(biomass_col) is None or r.get(biomass_col) == 0)
	if total > 0 and nulls / total > 0.5:
		warnings.append(
			f"Biomass data is sparse: {nulls}/{total} rows have NULL or zero biomass"
		)
	return warnings


def register(mcp: FastMCP) -> None:
	"""Register biomass analysis tools with the MCP server."""

	@mcp.tool()
	def biomass_by_region(
		year: int | None = None,
		depth: str | None = None,
	) -> str:
		"""Mean biomass per region with Kruskal-Wallis test across regions.

		Args:
			year: Filter by year
			depth: Filter by habitat/depth
		"""
		conditions = ["Biomass IS NOT NULL"]
		params = []
		if year:
			conditions.append("Year = %s")
			params.append(year)
		if depth:
			conditions.append("Depth2 = %s")
			params.append(depth)

		where = "WHERE " + " AND ".join(conditions)

		# Get per-transect biomass sums for stats
		sql = (
			"SELECT Region, Year, Reef, Transect, SUM(Biomass) AS transect_biomass "
			f"FROM ltem_historical_database {where} "
			"GROUP BY Region, Year, Reef, Transect"
		)
		rows = execute_select(sql, params=tuple(params) if params else None)

		# Group by region
		region_data: dict[str, list[float]] = defaultdict(list)
		for r in rows:
			b = _safe_float(r["transect_biomass"])
			if b is not None and b > 0:
				region_data[str(r["Region"])].append(b)

		summary = []
		for region in sorted(region_data.keys()):
			vals = region_data[region]
			arr = np.array(vals)
			summary.append({
				"region": region,
				"n_transects": len(vals),
				"mean_biomass": round(float(np.mean(arr)), 2),
				"median_biomass": round(float(np.median(arr)), 2),
				"std_biomass": round(float(np.std(arr, ddof=1)), 2) if len(arr) > 1 else 0,
				"min_biomass": round(float(np.min(arr)), 2),
				"max_biomass": round(float(np.max(arr)), 2),
			})

		# Kruskal-Wallis test
		kw_result = None
		groups = [np.array(v) for v in region_data.values() if len(v) >= 2]
		if len(groups) >= 2:
			stat, pval = sp_stats.kruskal(*groups)
			kw_result = {
				"H_statistic": round(float(stat), 4),
				"p_value": round(float(pval), 6),
				"significant": bool(pval < 0.05),
				"n_groups": len(groups),
			}

		return json.dumps({
			"data": summary,
			"meta": {
				"parameters": {"year": year, "depth": depth},
				"row_count": len(summary),
				"aggregation": "Transect-level biomass summarized by region",
				"kruskal_wallis": kw_result,
				"warnings": _biomass_warnings(
					[{"total_biomass": s["mean_biomass"]} for s in summary]
				),
			},
		})

	@mcp.tool()
	def biomass_by_depth(region: str | None = None) -> str:
		"""Compare biomass between shallow and deep depth categories.

		Args:
			region: Filter by region
		"""
		conditions = ["Biomass IS NOT NULL", "Depth2 IS NOT NULL"]
		params = []
		if region:
			conditions.append("Region = %s")
			params.append(region)

		where = "WHERE " + " AND ".join(conditions)

		sql = (
			"SELECT Depth2, Year, Reef, Transect, SUM(Biomass) AS transect_biomass "
			f"FROM ltem_historical_database {where} "
			"GROUP BY Depth2, Year, Reef, Transect"
		)
		rows = execute_select(sql, params=tuple(params) if params else None)

		depth_data: dict[str, list[float]] = defaultdict(list)
		for r in rows:
			b = _safe_float(r["transect_biomass"])
			if b is not None and b > 0:
				depth_data[str(r["Depth2"])].append(b)

		summary = []
		for depth_cat in sorted(depth_data.keys()):
			arr = np.array(depth_data[depth_cat])
			summary.append({
				"depth_category": depth_cat,
				"n_transects": len(arr),
				"mean_biomass": round(float(np.mean(arr)), 2),
				"median_biomass": round(float(np.median(arr)), 2),
				"std_biomass": round(float(np.std(arr, ddof=1)), 2) if len(arr) > 1 else 0,
			})

		# Mann-Whitney U between Shallow and Deep
		mw_result = None
		depth_cats = sorted(depth_data.keys())
		if len(depth_cats) >= 2:
			g1 = np.array(depth_data[depth_cats[0]])
			g2 = np.array(depth_data[depth_cats[1]])
			if len(g1) >= 2 and len(g2) >= 2:
				stat, pval = sp_stats.mannwhitneyu(g1, g2, alternative='two-sided')
				mw_result = {
					"comparison": f"{depth_cats[0]} vs {depth_cats[1]}",
					"U_statistic": round(float(stat), 2),
					"p_value": round(float(pval), 6),
					"significant": bool(pval < 0.05),
				}

		return json.dumps({
			"data": summary,
			"meta": {
				"parameters": {"region": region},
				"row_count": len(summary),
				"aggregation": "Transect-level biomass by depth category (Shallow/Deep)",
				"mann_whitney": mw_result,
			},
		})

	@mcp.tool()
	def trophic_biomass(
		region: str | None = None,
		year: int | None = None,
	) -> str:
		"""Biomass breakdown by trophic group.

		Uses the pre-computed TrophicGroup column in the historical database.

		Args:
			region: Filter by region
			year: Filter by year
		"""
		conditions = ["Biomass IS NOT NULL", "TrophicGroup IS NOT NULL"]
		params = []
		if region:
			conditions.append("Region = %s")
			params.append(region)
		if year:
			conditions.append("Year = %s")
			params.append(year)

		where = "WHERE " + " AND ".join(conditions)

		# Correct aggregation: SUM at transect level, then AVG across transects
		sql = (
			"SELECT TrophicGroup AS trophic_group, "
			"AVG(transect_biomass) AS mean_biomass, "
			"SUM(transect_biomass) AS total_biomass, "
			"COUNT(*) AS n_transects "
			"FROM ("
			"  SELECT Year, Region, Reef, Transect, TrophicGroup, "
			"  SUM(Biomass) AS transect_biomass "
			f"  FROM ltem_historical_database {where} "
			"  GROUP BY Year, Region, Reef, Transect, TrophicGroup"
			") sub "
			"GROUP BY TrophicGroup "
			"ORDER BY total_biomass DESC"
		)
		rows = execute_select(sql, params=tuple(params) if params else None)
		rows = _serialize_rows(rows)

		# Update n_observations to reflect transect count
		for r in rows:
			r["n_observations"] = r.pop("n_transects", 0)

		total = sum(r["total_biomass"] for r in rows if r["total_biomass"])
		for r in rows:
			r["proportion"] = (
				round(r["total_biomass"] / total, 4) if total and r["total_biomass"] else 0
			)

		return json.dumps({
			"data": rows,
			"meta": {
				"parameters": {"region": region, "year": year},
				"row_count": len(rows),
				"aggregation": "Biomass by trophic group",
			},
		})

	@mcp.tool()
	def environmental_correlations(region: str | None = None) -> str:
		"""Spearman correlations between biomass and environmental variables (SST, Chl-a).

		Note: Environmental columns must exist in the database. Returns error if missing.

		Args:
			region: Filter by region
		"""
		conditions = ["Biomass IS NOT NULL"]
		params = []
		if region:
			conditions.append("Region = %s")
			params.append(region)

		where = "WHERE " + " AND ".join(conditions)

		# Try to get environmental columns — they may not exist
		sql = (
			"SELECT Year, Region, Reef, Transect, "
			"SUM(Biomass) AS total_biomass, "
			"AVG(SST) AS mean_sst, "
			"AVG(Chla) AS mean_chla "
			f"FROM ltem_historical_database {where} "
			"GROUP BY Year, Region, Reef, Transect "
			"HAVING total_biomass > 0"
		)
		try:
			rows = execute_select(sql, params=tuple(params) if params else None)
		except Exception as e:
			error_msg = str(e)
			if "Unknown column" in error_msg or "SST" in error_msg or "Chla" in error_msg:
				return json.dumps({
					"data": [],
					"meta": {
						"parameters": {"region": region},
						"row_count": 0,
						"warnings": [
							"Environmental columns (SST, Chla) not found in database. "
							"This analysis requires environmental data columns."
						],
					},
				})
			raise

		correlations = {}
		biomass_vals = [_safe_float(r["total_biomass"]) for r in rows if r.get("total_biomass")]

		for env_var, col in [("SST", "mean_sst"), ("Chl-a", "mean_chla")]:
			pairs = [
				(float(r["total_biomass"]), float(r[col]))
				for r in rows
				if r.get("total_biomass") and r.get(col)
			]
			if len(pairs) >= 5:
				x, y = zip(*pairs)
				rho, pval = sp_stats.spearmanr(x, y)
				correlations[env_var] = {
					"spearman_rho": round(float(rho), 4),
					"p_value": round(float(pval), 6),
					"n": len(pairs),
					"significant": bool(pval < 0.05),
				}
			else:
				correlations[env_var] = {
					"error": f"Insufficient data pairs ({len(pairs)})",
					"n": len(pairs),
				}

		return json.dumps({
			"data": correlations,
			"meta": {
				"parameters": {"region": region},
				"row_count": len(correlations),
				"aggregation": "Spearman rank correlations",
			},
		})

	@mcp.tool()
	def sst_biomass_relationship(region: str | None = None) -> str:
		"""Linear and quadratic regression of biomass vs SST.

		Args:
			region: Filter by region
		"""
		conditions = ["Biomass IS NOT NULL"]
		params = []
		if region:
			conditions.append("Region = %s")
			params.append(region)

		where = "WHERE " + " AND ".join(conditions)

		sql = (
			"SELECT Year, Region, AVG(SST) AS mean_sst, "
			"SUM(Biomass) / COUNT(DISTINCT CONCAT(Reef, '-', Transect)) AS mean_biomass "
			f"FROM ltem_historical_database {where} "
			"GROUP BY Year, Region "
			"HAVING mean_sst IS NOT NULL AND mean_biomass > 0"
		)
		try:
			rows = execute_select(sql, params=tuple(params) if params else None)
		except Exception as e:
			if "Unknown column" in str(e) or "SST" in str(e):
				return json.dumps({
					"data": [],
					"meta": {
						"warnings": ["SST column not found in database"],
						"row_count": 0,
					},
				})
			raise

		if len(rows) < 5:
			return json.dumps({
				"data": [],
				"meta": {"warnings": [f"Insufficient data points ({len(rows)})"], "row_count": 0},
			})

		x = np.array([float(r["mean_sst"]) for r in rows])
		y = np.array([float(r["mean_biomass"]) for r in rows])

		# Linear regression
		slope, intercept, r_value, p_value, std_err = sp_stats.linregress(x, y)
		linear = {
			"slope": round(float(slope), 4),
			"intercept": round(float(intercept), 4),
			"r_squared": round(float(r_value ** 2), 4),
			"p_value": round(float(p_value), 6),
		}

		# Quadratic fit
		coeffs = np.polyfit(x, y, 2)
		y_pred = np.polyval(coeffs, x)
		ss_res = np.sum((y - y_pred) ** 2)
		ss_tot = np.sum((y - np.mean(y)) ** 2)
		r2_quad = 1 - ss_res / ss_tot if ss_tot > 0 else 0

		# Optimal SST (vertex of parabola)
		optimal_sst = None
		if coeffs[0] != 0:
			optimal_sst = round(float(-coeffs[1] / (2 * coeffs[0])), 2)

		quadratic = {
			"coefficients": [round(float(c), 6) for c in coeffs],
			"r_squared": round(float(r2_quad), 4),
			"optimal_sst": optimal_sst,
		}

		return json.dumps({
			"data": {
				"linear": linear,
				"quadratic": quadratic,
				"n": len(rows),
				"sst_range": [round(float(x.min()), 2), round(float(x.max()), 2)],
			},
			"meta": {
				"parameters": {"region": region},
				"row_count": len(rows),
				"aggregation": "SST vs biomass regression",
			},
		})

	@mcp.tool()
	def chl_productivity_relationship(region: str | None = None) -> str:
		"""Log-log regression of Chl-a vs productivity (biomass).

		Args:
			region: Filter by region
		"""
		conditions = ["Biomass IS NOT NULL"]
		params = []
		if region:
			conditions.append("Region = %s")
			params.append(region)

		where = "WHERE " + " AND ".join(conditions)

		sql = (
			"SELECT Year, Region, AVG(Chla) AS mean_chla, "
			"SUM(Biomass) / COUNT(DISTINCT CONCAT(Reef, '-', Transect)) AS mean_biomass "
			f"FROM ltem_historical_database {where} "
			"GROUP BY Year, Region "
			"HAVING mean_chla IS NOT NULL AND mean_chla > 0 AND mean_biomass > 0"
		)
		try:
			rows = execute_select(sql, params=tuple(params) if params else None)
		except Exception as e:
			if "Unknown column" in str(e) or "Chla" in str(e):
				return json.dumps({
					"data": [],
					"meta": {
						"warnings": ["Chla column not found in database"],
						"row_count": 0,
					},
				})
			raise

		if len(rows) < 5:
			return json.dumps({
				"data": [],
				"meta": {"warnings": [f"Insufficient data points ({len(rows)})"], "row_count": 0},
			})

		x = np.log10([float(r["mean_chla"]) for r in rows])
		y = np.log10([float(r["mean_biomass"]) for r in rows])

		slope, intercept, r_value, p_value, std_err = sp_stats.linregress(x, y)

		return json.dumps({
			"data": {
				"log_log_slope": round(float(slope), 4),
				"log_log_intercept": round(float(intercept), 4),
				"r_squared": round(float(r_value ** 2), 4),
				"p_value": round(float(p_value), 6),
				"n": len(rows),
			},
			"meta": {
				"parameters": {"region": region},
				"row_count": len(rows),
				"aggregation": "Log-log Chl-a vs biomass regression",
			},
		})

	@mcp.tool()
	def behavioral_group_biomass(
		region: str | None = None,
		mpa: str | None = None,
		reef: str | None = None,
		year: int | None = None,
	) -> str:
		"""Fish biomass by behavioral functional group (functional_name), one row per year × group. Unit: g/m².

		Uses the species_traits lookup table (JOIN on Species) to assign each
		observation to one of 6 behavioral categories from cluster_to_create_traits.csv.
		Species with functional_name = 'Pelagic' or without a match in species_traits
		are excluded automatically.

		Aggregation (replicates run_tests.R:117-124):
		  1. SUM biomass per (year, reef, transect, functional_name)
		  2. AVG across transects per (year, reef, functional_name)
		  3. AVG across reefs per (year, functional_name)

		Preprocessing filters applied:
		  - Label = 'PEC'
		  - Biomass IS NOT NULL
		  - Family != 'Carangidae'
		  - Corredor exclusion: NOT (Region='Corredor' AND Family IN ('Haemulidae','Carangidae') AND Biomass > 3)
		  - functional_name IN the 6 valid categories

		Do not combine region and mpa — the filter is AND and the result would be
		more restrictive than either alone.

		Args:
			region: Filter by LTEM region name (e.g. "Cabo Pulmo").
			mpa: Filter by MPA name. Do not combine with region.
			reef: Filter by reef name.
			year: Filter by survey year. Omit for full time series.
		"""
		VALID_FG = (
			'GenPred_solitary', 'GenPred_schooling', 'EpiBent_schooling',
			'Crip_schooling', 'Crip_solitary', 'Plank',
		)
		fg_placeholders = ", ".join(["%s"] * len(VALID_FG))

		conditions = [
			"h.Label = 'PEC'",
			"h.Biomass IS NOT NULL",
			"h.Family != 'Carangidae'",
			f"t.functional_name IN ({fg_placeholders})",
			"NOT (h.Region = 'Corredor' AND h.Family IN ('Haemulidae', 'Carangidae') AND h.Biomass > 3)",
		]
		params: list = list(VALID_FG)

		if mpa:
			conditions.append("h.MPA = %s")
			params.append(mpa)
		if region:
			conditions.append("h.Region = %s")
			params.append(region)
		if reef:
			conditions.append("h.Reef = %s")
			params.append(reef)
		if year:
			conditions.append("h.Year = %s")
			params.append(year)

		where = "WHERE " + " AND ".join(conditions)

		sql = (
			"SELECT year, functional_name, "
			"AVG(reef_mean) AS mean_biomass, "
			"SUM(n_transects) AS n_transects "
			"FROM ("
			"  SELECT year, reef, functional_name, "
			"  AVG(transect_sum) AS reef_mean, "
			"  COUNT(*) AS n_transects "
			"  FROM ("
			"    SELECT h.Year AS year, h.Reef AS reef, h.Transect, t.functional_name, "
			"    SUM(h.Biomass) AS transect_sum "
			"    FROM ltem_historical_database h "
			"    JOIN species_traits t ON h.Species = t.Species "
			f"   {where} "
			"    GROUP BY h.Year, h.Reef, h.Transect, t.functional_name"
			"  ) transect_level "
			"  GROUP BY year, reef, functional_name"
			") reef_level "
			"GROUP BY year, functional_name "
			"ORDER BY year, functional_name"
		)

		rows = execute_select(sql, params=tuple(params))
		rows = _serialize_rows(rows)

		return json.dumps({
			"data": rows,
			"meta": {
				"parameters": {"region": region, "mpa": mpa, "reef": reef, "year": year},
				"row_count": len(rows),
				"columns": ["year", "functional_name", "mean_biomass", "n_transects"],
				"unit": "g/m²",
				"aggregation": "SUM per transect → AVG per reef → AVG per year × functional_name",
				"valid_groups": list(VALID_FG),
				"description": (
					"Mean fish biomass (g/m²) per year × behavioral functional group. "
					"Maps directly to TrophicYear schema fields."
				),
			},
		})

	@mcp.tool()
	def latitudinal_gradient() -> str:
		"""Biomass trends along a latitudinal gradient.

		Uses Latitude column from ltem_historical_database directly.
		"""
		sql = (
			"SELECT Latitude, Reef, Region, "
			"AVG(Biomass) AS mean_biomass, "
			"SUM(Quantity) AS total_abundance, "
			"COUNT(DISTINCT Species) AS species_richness "
			"FROM ltem_historical_database "
			"WHERE Biomass IS NOT NULL AND Latitude IS NOT NULL "
			"GROUP BY Latitude, Reef, Region "
			"ORDER BY Latitude"
		)
		rows = execute_select(sql)

		rows = _serialize_rows(rows)

		# Correlation of latitude vs biomass
		correlation = None
		valid = [(r["Latitude"], r["mean_biomass"]) for r in rows if r.get("Latitude") and r.get("mean_biomass")]
		if len(valid) >= 5:
			lats, biom = zip(*valid)
			rho, pval = sp_stats.spearmanr(lats, biom)
			correlation = {
				"spearman_rho": round(float(rho), 4),
				"p_value": round(float(pval), 6),
				"n": len(valid),
			}

		return json.dumps({
			"data": rows,
			"meta": {
				"row_count": len(rows),
				"aggregation": "Mean biomass by reef latitude",
				"latitude_correlation": correlation,
			},
		})
