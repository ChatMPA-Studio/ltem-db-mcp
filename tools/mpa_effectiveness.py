"""MPA effectiveness analysis tools — protection comparisons, Cabo Pulmo recovery, BACI."""

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


def register(mcp: FastMCP) -> None:
	"""Register MPA effectiveness tools with the MCP server."""

	@mcp.tool()
	def compare_protection_levels(metric: str = "biomass") -> str:
		"""Compare ecological metrics across protection levels using Kruskal-Wallis + pairwise Mann-Whitney.

		Args:
			metric: Metric to compare — 'biomass', 'abundance', or 'richness'
		"""
		allowed_metrics = {"biomass", "abundance", "richness"}
		if metric not in allowed_metrics:
			return json.dumps({
				"error": f"metric must be one of: {', '.join(sorted(allowed_metrics))}",
			})

		# Build the aggregation expression
		if metric == "biomass":
			agg_expr = "SUM(Biomass)"
			having = "HAVING transect_value IS NOT NULL AND transect_value > 0"
		elif metric == "abundance":
			agg_expr = "SUM(Quantity)"
			having = "HAVING transect_value > 0"
		else:  # richness
			agg_expr = "COUNT(DISTINCT Species)"
			having = ""

		# Get protection level — try Protection_status or MPA column
		sql = (
			f"SELECT MPA, Year, Reef, Transect, {agg_expr} AS transect_value "
			"FROM ltem_historical_database "
			"WHERE Biomass IS NOT NULL "
			"GROUP BY MPA, Year, Reef, Transect "
			f"{having}"
		)
		rows = execute_select(sql)

		# Group by protection level
		groups: dict[str, list[float]] = defaultdict(list)
		for r in rows:
			val = _safe_float(r["transect_value"])
			if val is not None and val > 0:
				groups[str(r["MPA"])].append(val)

		summary = []
		for level in sorted(groups.keys()):
			arr = np.array(groups[level])
			summary.append({
				"protection_level": level,
				"n_transects": len(arr),
				"mean": round(float(np.mean(arr)), 2),
				"median": round(float(np.median(arr)), 2),
				"std": round(float(np.std(arr, ddof=1)), 2) if len(arr) > 1 else 0,
			})

		# Kruskal-Wallis across all groups
		valid_groups = [np.array(v) for v in groups.values() if len(v) >= 2]
		kw_result = None
		if len(valid_groups) >= 2:
			stat, pval = sp_stats.kruskal(*valid_groups)
			kw_result = {
				"H_statistic": round(float(stat), 4),
				"p_value": round(float(pval), 6),
				"significant": bool(pval < 0.05),
			}

		# Pairwise Mann-Whitney
		pairwise = {}
		group_names = sorted(groups.keys())
		for i, g1 in enumerate(group_names):
			for g2 in group_names[i + 1:]:
				a1 = np.array(groups[g1])
				a2 = np.array(groups[g2])
				if len(a1) >= 2 and len(a2) >= 2:
					stat, pval = sp_stats.mannwhitneyu(a1, a2, alternative='two-sided')
					pairwise[f"{g1} vs {g2}"] = {
						"U_statistic": round(float(stat), 2),
						"p_value": round(float(pval), 6),
						"significant": bool(pval < 0.05),
					}

		return json.dumps({
			"data": summary,
			"meta": {
				"parameters": {"metric": metric},
				"row_count": len(summary),
				"aggregation": f"Transect-level {metric} by protection level",
				"kruskal_wallis": kw_result,
				"pairwise_mann_whitney": pairwise,
			},
		})

	@mcp.tool()
	def cabo_pulmo_recovery(
		baseline_years: list[int] | None = None,
	) -> str:
		"""Cabo Pulmo recovery trajectory — annual biomass with recovery factor vs baseline.

		Args:
			baseline_years: Years to use as baseline (default [1998, 1999, 2000])
		"""
		if baseline_years is None:
			baseline_years = [1998, 1999, 2000]

		# Get annual mean biomass for Cabo Pulmo
		sql = (
			"SELECT Year, "
			"AVG(transect_biomass) AS mean_biomass, "
			"COUNT(*) AS n_transects "
			"FROM ("
			"  SELECT Year, Reef, Transect, SUM(Biomass) AS transect_biomass "
			"  FROM ltem_historical_database "
			"  WHERE Region = 'Cabo Pulmo' AND Biomass IS NOT NULL "
			"  GROUP BY Year, Reef, Transect"
			") sub "
			"GROUP BY Year ORDER BY Year"
		)
		rows = execute_select(sql)
		rows = _serialize_rows(rows)

		# Calculate baseline
		baseline_rows = [r for r in rows if r["Year"] in baseline_years]
		baseline_biomass = (
			np.mean([r["mean_biomass"] for r in baseline_rows])
			if baseline_rows else None
		)

		# Recovery factor
		for r in rows:
			if baseline_biomass and baseline_biomass > 0 and r["mean_biomass"]:
				r["recovery_factor"] = round(r["mean_biomass"] / baseline_biomass, 2)
			else:
				r["recovery_factor"] = None

		return json.dumps({
			"data": rows,
			"meta": {
				"parameters": {"baseline_years": baseline_years},
				"row_count": len(rows),
				"baseline_biomass": round(float(baseline_biomass), 2) if baseline_biomass else None,
				"aggregation": "Annual mean transect biomass for Cabo Pulmo",
			},
		})

	@mcp.tool()
	def compare_all_metrics() -> str:
		"""Multi-metric comparison across protection levels (biomass, abundance, richness)
		with Cabo Pulmo advantage percentage.
		"""
		sql = (
			"SELECT MPA, "
			"AVG(transect_biomass) AS mean_biomass, "
			"AVG(transect_abundance) AS mean_abundance, "
			"AVG(transect_richness) AS mean_richness, "
			"COUNT(*) AS n_transects "
			"FROM ("
			"  SELECT MPA, Year, Reef, Transect, "
			"  SUM(Biomass) AS transect_biomass, "
			"  SUM(Quantity) AS transect_abundance, "
			"  COUNT(DISTINCT Species) AS transect_richness "
			"  FROM ltem_historical_database "
			"  GROUP BY MPA, Year, Reef, Transect"
			") sub "
			"GROUP BY MPA ORDER BY MPA"
		)
		rows = execute_select(sql)
		rows = _serialize_rows(rows)

		# Find Cabo Pulmo row for advantage calculation
		cp_row = next((r for r in rows if r["MPA"] and "Cabo Pulmo" in str(r["MPA"])), None)

		if cp_row:
			for r in rows:
				if r != cp_row:
					for metric_col in ["mean_biomass", "mean_abundance", "mean_richness"]:
						cp_val = cp_row.get(metric_col) or 0
						other_val = r.get(metric_col) or 0
						adv_key = f"cp_advantage_{metric_col.replace('mean_', '')}_pct"
						if other_val > 0:
							r[adv_key] = round((cp_val - other_val) / other_val * 100, 1)
						else:
							r[adv_key] = None

		return json.dumps({
			"data": rows,
			"meta": {
				"row_count": len(rows),
				"aggregation": "Multi-metric means by protection level",
			},
		})

	@mcp.tool()
	def trophic_comparison() -> str:
		"""Trophic group proportions by protection level."""
		sql = (
			"SELECT MPA, TrophicGroup AS trophic_group, "
			"SUM(Biomass) AS total_biomass "
			"FROM ltem_historical_database "
			"WHERE Biomass IS NOT NULL AND TrophicGroup IS NOT NULL "
			"GROUP BY MPA, TrophicGroup"
		)
		rows = execute_select(sql)
		rows = _serialize_rows(rows)

		# Pivot by MPA
		mpas: dict[str, dict] = defaultdict(dict)
		for r in rows:
			mpa = str(r["MPA"])
			mpas[mpa][r["trophic_group"]] = r["total_biomass"]

		# Calculate proportions
		result = {}
		for mpa, groups in sorted(mpas.items()):
			total = sum(v for v in groups.values() if v)
			result[mpa] = {
				g: {"biomass": v, "proportion": round(v / total, 4) if total else 0}
				for g, v in groups.items()
				if v
			}

		return json.dumps({
			"data": result,
			"meta": {
				"row_count": len(result),
				"aggregation": "Trophic biomass proportions by protection level",
			},
		})

	@mcp.tool()
	def size_comparison() -> str:
		"""Size class proportions by protection level, with large fish (>40cm) percentage."""
		sql = (
			"SELECT MPA, "
			"CASE "
			"  WHEN Size < 10 THEN '0-10' "
			"  WHEN Size >= 10 AND Size < 20 THEN '10-20' "
			"  WHEN Size >= 20 AND Size < 30 THEN '20-30' "
			"  WHEN Size >= 30 AND Size < 40 THEN '30-40' "
			"  WHEN Size >= 40 THEN '40+' "
			"END AS size_class, "
			"SUM(Quantity) AS abundance "
			"FROM ltem_historical_database "
			"WHERE Size IS NOT NULL "
			"GROUP BY MPA, size_class"
		)
		rows = execute_select(sql)
		rows = _serialize_rows(rows)

		# Pivot by MPA
		mpas: dict[str, dict[str, float]] = defaultdict(dict)
		for r in rows:
			mpa = str(r["MPA"])
			mpas[mpa][r["size_class"]] = r["abundance"] or 0

		result = {}
		for mpa, classes in sorted(mpas.items()):
			total = sum(classes.values())
			large_fish = classes.get("40+", 0)
			result[mpa] = {
				"size_classes": {
					sc: {
						"abundance": v,
						"proportion": round(v / total, 4) if total else 0,
					}
					for sc, v in sorted(classes.items())
				},
				"total_abundance": total,
				"large_fish_pct": round(large_fish / total * 100, 2) if total else 0,
			}

		return json.dumps({
			"data": result,
			"meta": {
				"row_count": len(result),
				"aggregation": "Size class proportions by protection level",
			},
		})

	@mcp.tool()
	def baci_analysis(
		before_years: list[int] | None = None,
		after_years: list[int] | None = None,
	) -> str:
		"""Before-After-Control-Impact analysis for Cabo Pulmo MPA.

		Compares biomass changes in Cabo Pulmo (Impact) vs unprotected sites (Control)
		between before and after periods.

		Args:
			before_years: Pre-protection years (default [1998, 1999, 2000])
			after_years: Post-protection years (default [2018, 2019, 2020])
		"""
		if before_years is None:
			before_years = [1998, 1999, 2000]
		if after_years is None:
			after_years = [2018, 2019, 2020]

		all_years = before_years + after_years
		placeholders = ",".join(["%s"] * len(all_years))

		sql = (
			"SELECT MPA, Year, Reef, Transect, SUM(Biomass) AS transect_biomass "
			"FROM ltem_historical_database "
			f"WHERE Year IN ({placeholders}) AND Biomass IS NOT NULL "
			"GROUP BY MPA, Year, Reef, Transect"
		)
		rows = execute_select(sql, params=tuple(all_years))

		# Classify into BACI groups
		groups = {
			"impact_before": [],
			"impact_after": [],
			"control_before": [],
			"control_after": [],
		}

		for r in rows:
			val = _safe_float(r["transect_biomass"])
			if val is None or val <= 0:
				continue
			is_impact = r["MPA"] and "Cabo Pulmo" in str(r["MPA"])
			is_before = r["Year"] in before_years

			if is_impact and is_before:
				groups["impact_before"].append(val)
			elif is_impact and not is_before:
				groups["impact_after"].append(val)
			elif not is_impact and is_before:
				groups["control_before"].append(val)
			elif not is_impact and not is_before:
				groups["control_after"].append(val)

		# BACI effect = (Impact_After - Impact_Before) - (Control_After - Control_Before)
		means = {k: float(np.mean(v)) if v else None for k, v in groups.items()}
		counts = {k: len(v) for k, v in groups.items()}

		baci_effect = None
		if all(means[k] is not None for k in means):
			impact_change = means["impact_after"] - means["impact_before"]
			control_change = means["control_after"] - means["control_before"]
			baci_effect = round(impact_change - control_change, 2)

		# Test with Mann-Whitney on after period
		mw_result = None
		if len(groups["impact_after"]) >= 2 and len(groups["control_after"]) >= 2:
			stat, pval = sp_stats.mannwhitneyu(
				groups["impact_after"], groups["control_after"], alternative='two-sided'
			)
			mw_result = {
				"U_statistic": round(float(stat), 2),
				"p_value": round(float(pval), 6),
				"significant": bool(pval < 0.05),
			}

		return json.dumps({
			"data": {
				"means": {k: round(v, 2) if v else None for k, v in means.items()},
				"sample_sizes": counts,
				"baci_effect": baci_effect,
			},
			"meta": {
				"parameters": {
					"before_years": before_years,
					"after_years": after_years,
				},
				"row_count": sum(counts.values()),
				"aggregation": "Before-After-Control-Impact analysis",
				"mann_whitney_after": mw_result,
			},
		})

	@mcp.tool()
	def spillover_analysis() -> str:
		"""Analyze biomass by distance from Cabo Pulmo (spillover effect).

		Uses Latitude/Longitude columns from the historical database directly.
		"""
		# Cabo Pulmo approximate center: 23.443, -109.425
		sql = (
			"SELECT Reef, Region, Latitude, Longitude, MPA, "
			"AVG(Biomass) AS mean_biomass, "
			"COUNT(*) AS n_observations "
			"FROM ltem_historical_database "
			"WHERE Biomass IS NOT NULL AND Latitude IS NOT NULL "
			"GROUP BY Reef, Region, Latitude, Longitude, MPA "
			"ORDER BY Latitude"
		)
		rows = execute_select(sql)

		rows = _serialize_rows(rows)

		# Calculate approximate distance from Cabo Pulmo center
		cp_lat, cp_lon = 23.443, -109.425
		for r in rows:
			if r.get("Latitude") and r.get("Longitude"):
				# Simple Euclidean distance in degrees (rough but sufficient for ranking)
				dlat = r["Latitude"] - cp_lat
				dlon = r["Longitude"] - cp_lon
				r["distance_from_cp_deg"] = round((dlat**2 + dlon**2)**0.5, 4)
			else:
				r["distance_from_cp_deg"] = None

		# Sort by distance
		rows.sort(key=lambda x: x.get("distance_from_cp_deg") or 999)

		return json.dumps({
			"data": rows,
			"meta": {
				"row_count": len(rows),
				"aggregation": "Mean biomass by reef with distance from Cabo Pulmo",
				"cp_center": {"latitude": cp_lat, "longitude": cp_lon},
			},
		})
