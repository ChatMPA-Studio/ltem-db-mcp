"""Ecosystem indicator tools: NRSI index and functional group analysis."""

import json
import random
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


# Trophic level mapping for NRSI
# UTL = Upper Trophic Level (4-4.5), LTL = Lower Trophic Level (2-2.5), CTL = all else
_NRSI_UTL = '4-4.5'
_NRSI_LTL = '2-2.5'

# Functional group Spanish labels (from R analysis)
_FUNCTIONAL_LABELS = {
	"GenPred_solitary": "Depredadores solitarios",
	"GenPred_schooling": "Depredadores en cardumenes",
	"EpiBent_schooling": "Omnivoros en cardumen",
	"Crip_schooling": "Herbivoros en cardumen",
	"Crip_solitary": "Cripticos solitarios",
	"Plank": "Planctivoros",
	"Pelagic": "Pelagicos",
}


def _compute_nrsi(utl: float, ltl: float, ctl: float) -> float | None:
	"""Compute NRSI using the conditional formula from the R analysis.

	NRSI = (UTL + LTL - CTL) / (UTL + LTL + CTL)
	Exception: if LTL > UTL + CTL then NRSI = UTL / (UTL + CTL)
	"""
	total = utl + ltl + ctl
	if total == 0:
		return None
	if ltl > utl + ctl:
		denom = utl + ctl
		return utl / denom if denom > 0 else None
	return (utl + ltl - ctl) / total


def register(mcp: FastMCP) -> None:
	"""Register ecosystem indicator tools with the MCP server."""

	# -----------------------------------------------------------------------
	# NRSI tools
	# -----------------------------------------------------------------------

	@mcp.tool()
	def nrsi_by_reef(
		region: str | None = None,
		year: int | None = None,
	) -> str:
		"""Normalized Reef State Index (NRSI) per reef.

		NRSI uses relative biomass of upper trophic levels (TrophicLevelF='4-4.5'),
		lower trophic levels ('2-2.5'), and consumer trophic levels (everything else).
		Formula: (UTL + LTL - CTL) / (UTL + LTL + CTL).
		Conditional: if LTL > UTL + CTL, then NRSI = UTL / (UTL + CTL).

		Range: -1 (degraded) to +1 (healthy reef state).

		Args:
			region: Filter by region
			year: Filter by year
		"""
		conditions = ["Biomass IS NOT NULL", "TrophicLevelF IS NOT NULL"]
		params = []
		if region:
			conditions.append("Region = %s")
			params.append(region)
		if year:
			conditions.append("Year = %s")
			params.append(year)

		where = "WHERE " + " AND ".join(conditions)

		# Step 1: classify trophic levels and sum biomass per transect
		sql = (
			"SELECT Year, Region, Reef, Habitat, Transect, TrophicLevelF, "
			"SUM(Biomass) AS biomass "
			f"FROM ltem_historical_database {where} "
			"GROUP BY Year, Region, Reef, Habitat, Transect, TrophicLevelF"
		)
		rows = execute_select(sql, params=tuple(params) if params else None, max_rows=50000)

		# Step 2: pivot to UTL/LTL/CTL per transect
		transect_key = lambda r: (r["Year"], r["Region"], r["Reef"], r["Habitat"], r["Transect"])
		transects: dict[tuple, dict[str, float]] = defaultdict(lambda: {"UTL": 0, "LTL": 0, "CTL": 0})

		for r in rows:
			key = transect_key(r)
			bm = float(r["biomass"]) if r["biomass"] else 0
			tlf = r["TrophicLevelF"]
			if _NRSI_UTL in str(tlf):
				transects[key]["UTL"] += bm
			elif _NRSI_LTL in str(tlf):
				transects[key]["LTL"] += bm
			else:
				transects[key]["CTL"] += bm

		# Step 3: compute NRSI per transect, then average per reef
		reef_nrsi: dict[tuple, list[float]] = defaultdict(list)
		for key, levels in transects.items():
			yr, reg, reef, hab, trans = key
			nrsi_val = _compute_nrsi(levels["UTL"], levels["LTL"], levels["CTL"])
			if nrsi_val is not None:
				reef_nrsi[(reg, reef)].append(nrsi_val)

		results = []
		for (reg, reef), values in sorted(reef_nrsi.items()):
			arr = np.array(values)
			results.append({
				"region": reg,
				"reef": reef,
				"mean_nrsi": round(float(np.mean(arr)), 4),
				"median_nrsi": round(float(np.median(arr)), 4),
				"std_nrsi": round(float(np.std(arr, ddof=1)), 4) if len(arr) > 1 else 0,
				"n_transects": len(values),
			})

		return json.dumps({
			"data": results,
			"meta": {
				"parameters": {"region": region, "year": year},
				"row_count": len(results),
				"interpretation": {
					"range": "[-1, +1]",
					"positive": "Healthy reef (more top/bottom trophic levels)",
					"negative": "Degraded reef (dominated by mid-level consumers)",
					"zero": "Balanced trophic structure",
				},
				"formula": "(UTL + LTL - CTL) / (UTL + LTL + CTL); if LTL > UTL+CTL: UTL / (UTL+CTL)",
				"description": "Normalized Reef State Index per reef",
			},
		})

	@mcp.tool()
	def nrsi_bootstrapped(
		region: str | None = None,
		year: int | None = None,
		n_boot: int = 100,
	) -> str:
		"""NRSI with bootstrap confidence intervals per reef.

		Resamples transect-level NRSI values with replacement to estimate
		uncertainty around the mean NRSI.

		Args:
			region: Filter by region
			year: Filter by year
			n_boot: Number of bootstrap iterations (default 100)
		"""
		# Cap bootstrap iterations for performance
		n_boot = min(n_boot, 500)

		conditions = ["Biomass IS NOT NULL", "TrophicLevelF IS NOT NULL"]
		params = []
		if region:
			conditions.append("Region = %s")
			params.append(region)
		if year:
			conditions.append("Year = %s")
			params.append(year)

		where = "WHERE " + " AND ".join(conditions)

		sql = (
			"SELECT Year, Region, Reef, Habitat, Transect, TrophicLevelF, "
			"SUM(Biomass) AS biomass "
			f"FROM ltem_historical_database {where} "
			"GROUP BY Year, Region, Reef, Habitat, Transect, TrophicLevelF"
		)
		rows = execute_select(sql, params=tuple(params) if params else None, max_rows=50000)

		transect_key = lambda r: (r["Year"], r["Region"], r["Reef"], r["Habitat"], r["Transect"])
		transects: dict[tuple, dict[str, float]] = defaultdict(lambda: {"UTL": 0, "LTL": 0, "CTL": 0})

		for r in rows:
			key = transect_key(r)
			bm = float(r["biomass"]) if r["biomass"] else 0
			tlf = r["TrophicLevelF"]
			if _NRSI_UTL in str(tlf):
				transects[key]["UTL"] += bm
			elif _NRSI_LTL in str(tlf):
				transects[key]["LTL"] += bm
			else:
				transects[key]["CTL"] += bm

		# Group NRSI values by reef
		reef_nrsi_vals: dict[tuple, list[float]] = defaultdict(list)
		for key, levels in transects.items():
			yr, reg, reef, hab, trans = key
			nrsi_val = _compute_nrsi(levels["UTL"], levels["LTL"], levels["CTL"])
			if nrsi_val is not None:
				reef_nrsi_vals[(reg, reef)].append(nrsi_val)

		# Bootstrap per reef
		rng = np.random.default_rng(42)
		results = []
		for (reg, reef), values in sorted(reef_nrsi_vals.items()):
			arr = np.array(values)
			if len(arr) < 2:
				results.append({
					"region": reg,
					"reef": reef,
					"mean_nrsi": round(float(np.mean(arr)), 4),
					"ci_lower": None,
					"ci_upper": None,
					"n_transects": len(arr),
					"warning": "Too few transects for bootstrap",
				})
				continue

			boot_means = []
			for _ in range(n_boot):
				sample = rng.choice(arr, size=len(arr), replace=True)
				boot_means.append(float(np.mean(sample)))

			boot_arr = np.array(boot_means)
			results.append({
				"region": reg,
				"reef": reef,
				"mean_nrsi": round(float(np.mean(arr)), 4),
				"boot_mean": round(float(np.mean(boot_arr)), 4),
				"ci_lower": round(float(np.percentile(boot_arr, 2.5)), 4),
				"ci_upper": round(float(np.percentile(boot_arr, 97.5)), 4),
				"boot_std": round(float(np.std(boot_arr)), 4),
				"n_transects": len(arr),
			})

		return json.dumps({
			"data": results,
			"meta": {
				"parameters": {"region": region, "year": year, "n_boot": n_boot},
				"row_count": len(results),
				"method": f"Bootstrap ({n_boot} iterations), 95% CI",
				"description": "NRSI with bootstrap confidence intervals",
			},
		})

	@mcp.tool()
	def nrsi_regional_summary(year: int | None = None) -> str:
		"""Regional NRSI comparison with Kruskal-Wallis test.

		Computes mean NRSI per region and tests for significant differences.

		Args:
			year: Filter by year
		"""
		conditions = ["Biomass IS NOT NULL", "TrophicLevelF IS NOT NULL"]
		params = []
		if year:
			conditions.append("Year = %s")
			params.append(year)

		where = "WHERE " + " AND ".join(conditions)

		sql = (
			"SELECT Year, Region, Reef, Habitat, Transect, TrophicLevelF, "
			"SUM(Biomass) AS biomass "
			f"FROM ltem_historical_database {where} "
			"GROUP BY Year, Region, Reef, Habitat, Transect, TrophicLevelF"
		)
		rows = execute_select(sql, params=tuple(params) if params else None, max_rows=50000)

		transect_key = lambda r: (r["Year"], r["Region"], r["Reef"], r["Habitat"], r["Transect"])
		transects: dict[tuple, dict[str, float]] = defaultdict(lambda: {"UTL": 0, "LTL": 0, "CTL": 0})

		for r in rows:
			key = transect_key(r)
			bm = float(r["biomass"]) if r["biomass"] else 0
			tlf = r["TrophicLevelF"]
			if _NRSI_UTL in str(tlf):
				transects[key]["UTL"] += bm
			elif _NRSI_LTL in str(tlf):
				transects[key]["LTL"] += bm
			else:
				transects[key]["CTL"] += bm

		# Group by region
		region_nrsi: dict[str, list[float]] = defaultdict(list)
		for key, levels in transects.items():
			yr, reg, reef, hab, trans = key
			nrsi_val = _compute_nrsi(levels["UTL"], levels["LTL"], levels["CTL"])
			if nrsi_val is not None:
				region_nrsi[reg].append(nrsi_val)

		summary = []
		for reg in sorted(region_nrsi.keys()):
			arr = np.array(region_nrsi[reg])
			summary.append({
				"region": reg,
				"mean_nrsi": round(float(np.mean(arr)), 4),
				"median_nrsi": round(float(np.median(arr)), 4),
				"std_nrsi": round(float(np.std(arr, ddof=1)), 4) if len(arr) > 1 else 0,
				"n_transects": len(arr),
			})

		# Kruskal-Wallis test
		kw_result = None
		groups = [np.array(v) for v in region_nrsi.values() if len(v) >= 2]
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
				"parameters": {"year": year},
				"row_count": len(summary),
				"kruskal_wallis": kw_result,
				"description": "Regional NRSI comparison",
			},
		})

	# -----------------------------------------------------------------------
	# Functional group tools
	# -----------------------------------------------------------------------

	@mcp.tool()
	def functional_group_biomass(
		region: str | None = None,
		year: int | None = None,
	) -> str:
		"""Biomass by functional group with Spanish labels.

		Uses the Functional_groups column from the historical database.

		Args:
			region: Filter by region
			year: Filter by year
		"""
		conditions = ["Biomass IS NOT NULL", "Functional_groups IS NOT NULL"]
		params = []
		if region:
			conditions.append("Region = %s")
			params.append(region)
		if year:
			conditions.append("Year = %s")
			params.append(year)

		where = "WHERE " + " AND ".join(conditions)

		sql = (
			"SELECT Functional_groups, "
			"SUM(Biomass) AS total_biomass, "
			"AVG(Biomass) AS mean_biomass, "
			"COUNT(*) AS n_observations, "
			"COUNT(DISTINCT Species) AS n_species "
			f"FROM ltem_historical_database {where} "
			"GROUP BY Functional_groups "
			"ORDER BY total_biomass DESC"
		)
		try:
			rows = execute_select(sql, params=tuple(params) if params else None)
		except Exception as e:
			if "Unknown column" in str(e) or "Functional_groups" in str(e):
				return json.dumps({
					"data": [],
					"meta": {
						"warnings": ["Functional_groups column not found in database"],
						"row_count": 0,
					},
				})
			raise

		rows = _serialize_rows(rows)

		total = sum(r["total_biomass"] for r in rows if r.get("total_biomass"))
		for r in rows:
			r["proportion"] = (
				round(r["total_biomass"] / total, 4)
				if total and r.get("total_biomass") else 0
			)
			# Add Spanish label
			fg = r.get("Functional_groups", "")
			r["label_es"] = _FUNCTIONAL_LABELS.get(fg, fg)

		return json.dumps({
			"data": rows,
			"meta": {
				"parameters": {"region": region, "year": year},
				"row_count": len(rows),
				"total_biomass": total,
				"description": "Biomass by functional group",
			},
		})

	@mcp.tool()
	def functional_group_temporal(region: str | None = None) -> str:
		"""Annual biomass trajectory per functional group.

		Args:
			region: Filter by region
		"""
		conditions = ["Biomass IS NOT NULL", "Functional_groups IS NOT NULL"]
		params = []
		if region:
			conditions.append("Region = %s")
			params.append(region)

		where = "WHERE " + " AND ".join(conditions)

		# Average transect biomass per year x functional group
		sql = (
			"SELECT Year, Functional_groups, "
			"AVG(transect_bm) AS mean_biomass "
			"FROM ("
			"  SELECT Year, Region, Reef, Habitat, Transect, Functional_groups, "
			"  SUM(Biomass) AS transect_bm "
			f"  FROM ltem_historical_database {where} "
			"  GROUP BY Year, Region, Reef, Habitat, Transect, Functional_groups"
			") sub "
			"GROUP BY Year, Functional_groups "
			"ORDER BY Year, Functional_groups"
		)
		try:
			rows = execute_select(sql, params=tuple(params) if params else None)
		except Exception as e:
			if "Unknown column" in str(e) or "Functional_groups" in str(e):
				return json.dumps({
					"data": [],
					"meta": {
						"warnings": ["Functional_groups column not found in database"],
						"row_count": 0,
					},
				})
			raise

		rows = _serialize_rows(rows)

		for r in rows:
			fg = r.get("Functional_groups", "")
			r["label_es"] = _FUNCTIONAL_LABELS.get(fg, fg)
			if r.get("mean_biomass") is not None:
				r["mean_biomass"] = round(r["mean_biomass"], 4)

		return json.dumps({
			"data": rows,
			"meta": {
				"parameters": {"region": region},
				"row_count": len(rows),
				"description": "Annual biomass trajectory per functional group",
			},
		})

	@mcp.tool()
	def functional_group_by_region(year: int | None = None) -> str:
		"""Proportional functional group composition per region.

		Args:
			year: Filter by year
		"""
		conditions = ["Biomass IS NOT NULL", "Functional_groups IS NOT NULL"]
		params = []
		if year:
			conditions.append("Year = %s")
			params.append(year)

		where = "WHERE " + " AND ".join(conditions)

		sql = (
			"SELECT Region, Functional_groups, "
			"SUM(Biomass) AS total_biomass "
			f"FROM ltem_historical_database {where} "
			"GROUP BY Region, Functional_groups "
			"ORDER BY Region, total_biomass DESC"
		)
		try:
			rows = execute_select(sql, params=tuple(params) if params else None)
		except Exception as e:
			if "Unknown column" in str(e) or "Functional_groups" in str(e):
				return json.dumps({
					"data": [],
					"meta": {
						"warnings": ["Functional_groups column not found in database"],
						"row_count": 0,
					},
				})
			raise

		rows = _serialize_rows(rows)

		# Compute proportions per region
		region_totals: dict[str, float] = defaultdict(float)
		for r in rows:
			if r.get("total_biomass"):
				region_totals[r["Region"]] += r["total_biomass"]

		for r in rows:
			reg = r["Region"]
			rt = region_totals.get(reg, 0)
			r["proportion"] = (
				round(r["total_biomass"] / rt, 4)
				if rt and r.get("total_biomass") else 0
			)
			fg = r.get("Functional_groups", "")
			r["label_es"] = _FUNCTIONAL_LABELS.get(fg, fg)

		return json.dumps({
			"data": rows,
			"meta": {
				"parameters": {"year": year},
				"row_count": len(rows),
				"description": "Proportional functional group composition per region",
			},
		})
