"""Temporal trend analysis tools — time series, Mann-Kendall, change points."""

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


def _mann_kendall(x):
	"""Mann-Kendall trend test.

	Returns: (tau, p_value, trend_direction)
	"""
	n = len(x)
	if n < 4:
		return None, None, "insufficient data"

	s = 0
	for i in range(n - 1):
		for j in range(i + 1, n):
			diff = x[j] - x[i]
			if diff > 0:
				s += 1
			elif diff < 0:
				s -= 1

	# Variance
	var_s = n * (n - 1) * (2 * n + 5) / 18

	# Z statistic
	if s > 0:
		z = (s - 1) / var_s**0.5
	elif s < 0:
		z = (s + 1) / var_s**0.5
	else:
		z = 0

	p_value = 2 * (1 - sp_stats.norm.cdf(abs(z)))
	tau = 2 * s / (n * (n - 1))

	if p_value < 0.05:
		trend = "increasing" if tau > 0 else "decreasing"
	else:
		trend = "no significant trend"

	return round(float(tau), 4), round(float(p_value), 6), trend


def _sens_slope(x, y):
	"""Sen's slope estimator.

	Returns median of all pairwise slopes.
	"""
	n = len(x)
	if n < 2:
		return None

	slopes = []
	for i in range(n):
		for j in range(i + 1, n):
			if x[j] != x[i]:
				slopes.append((y[j] - y[i]) / (x[j] - x[i]))

	return round(float(np.median(slopes)), 4) if slopes else None


def register(mcp: FastMCP) -> None:
	"""Register temporal trend tools with the MCP server."""

	@mcp.tool()
	def annual_time_series(
		region: str | None = None,
		metric: str = "biomass",
	) -> str:
		"""Annual time series of a given metric.

		Args:
			region: Filter by region
			metric: 'biomass', 'abundance', or 'richness'
		"""
		allowed = {"biomass", "abundance", "richness"}
		if metric not in allowed:
			return json.dumps({"error": f"metric must be one of: {', '.join(sorted(allowed))}"})

		conditions = []
		params = []
		if region:
			conditions.append("Region = %s")
			params.append(region)
		if metric == "biomass":
			conditions.append("Biomass IS NOT NULL")

		where = "WHERE " + " AND ".join(conditions) if conditions else ""

		if metric == "biomass":
			agg = "AVG(transect_biomass) AS value"
			inner = "SUM(Biomass) AS transect_biomass"
		elif metric == "abundance":
			agg = "AVG(transect_abundance) AS value"
			inner = "SUM(Quantity) AS transect_abundance"
		else:
			agg = "AVG(transect_richness) AS value"
			inner = "COUNT(DISTINCT Species) AS transect_richness"

		sql = (
			f"SELECT Year, {agg}, COUNT(*) AS n_transects "
			"FROM ("
			f"  SELECT Year, Reef, Transect, {inner} "
			f"  FROM ltem_historical_database {where} "
			"  GROUP BY Year, Reef, Transect"
			") sub "
			"GROUP BY Year ORDER BY Year"
		)
		rows = execute_select(sql, params=tuple(params) if params else None)
		rows = _serialize_rows(rows)

		return json.dumps({
			"data": rows,
			"meta": {
				"parameters": {"region": region, "metric": metric},
				"row_count": len(rows),
				"aggregation": f"Annual mean transect-level {metric}",
			},
		})

	@mcp.tool()
	def trend_analysis(
		region: str | None = None,
		metric: str = "biomass",
	) -> str:
		"""Linear regression + Mann-Kendall trend test + Sen's slope.

		Args:
			region: Filter by region
			metric: 'biomass', 'abundance', or 'richness'
		"""
		allowed = {"biomass", "abundance", "richness"}
		if metric not in allowed:
			return json.dumps({"error": f"metric must be one of: {', '.join(sorted(allowed))}"})

		conditions = []
		params = []
		if region:
			conditions.append("Region = %s")
			params.append(region)
		if metric == "biomass":
			conditions.append("Biomass IS NOT NULL")

		where = "WHERE " + " AND ".join(conditions) if conditions else ""

		if metric == "biomass":
			inner = "SUM(Biomass) AS transect_val"
		elif metric == "abundance":
			inner = "SUM(Quantity) AS transect_val"
		else:
			inner = "COUNT(DISTINCT Species) AS transect_val"

		sql = (
			"SELECT Year, AVG(transect_val) AS value "
			"FROM ("
			f"  SELECT Year, Reef, Transect, {inner} "
			f"  FROM ltem_historical_database {where} "
			"  GROUP BY Year, Reef, Transect"
			") sub "
			"GROUP BY Year ORDER BY Year"
		)
		rows = execute_select(sql, params=tuple(params) if params else None)

		if len(rows) < 4:
			return json.dumps({
				"data": [],
				"meta": {
					"parameters": {"region": region, "metric": metric},
					"row_count": 0,
					"warnings": [f"Insufficient time points ({len(rows)}) for trend analysis"],
				},
			})

		years = np.array([r["Year"] for r in rows], dtype=float)
		values = np.array([float(r["value"]) for r in rows])

		# Linear regression
		slope, intercept, r_value, p_value, std_err = sp_stats.linregress(years, values)
		linear = {
			"slope": round(float(slope), 4),
			"intercept": round(float(intercept), 4),
			"r_squared": round(float(r_value ** 2), 4),
			"p_value": round(float(p_value), 6),
		}

		# Mann-Kendall
		mk_tau, mk_p, mk_trend = _mann_kendall(values)
		mann_kendall = {
			"tau": mk_tau,
			"p_value": mk_p,
			"trend": mk_trend,
		}

		# Sen's slope
		sens = _sens_slope(years, values)

		return json.dumps({
			"data": {
				"linear_regression": linear,
				"mann_kendall": mann_kendall,
				"sens_slope": sens,
				"year_range": [int(years[0]), int(years[-1])],
				"n_years": len(years),
			},
			"meta": {
				"parameters": {"region": region, "metric": metric},
				"row_count": len(rows),
				"aggregation": f"Trend analysis of annual {metric}",
			},
		})

	@mcp.tool()
	def regional_trends(metric: str = "biomass") -> str:
		"""Trend comparison across all regions.

		Args:
			metric: 'biomass', 'abundance', or 'richness'
		"""
		allowed = {"biomass", "abundance", "richness"}
		if metric not in allowed:
			return json.dumps({"error": f"metric must be one of: {', '.join(sorted(allowed))}"})

		if metric == "biomass":
			inner = "SUM(Biomass) AS transect_val"
			extra_where = "AND Biomass IS NOT NULL"
		elif metric == "abundance":
			inner = "SUM(Quantity) AS transect_val"
			extra_where = ""
		else:
			inner = "COUNT(DISTINCT Species) AS transect_val"
			extra_where = ""

		sql = (
			"SELECT Region, Year, AVG(transect_val) AS value "
			"FROM ("
			f"  SELECT Region, Year, Reef, Transect, {inner} "
			f"  FROM ltem_historical_database WHERE 1=1 {extra_where} "
			"  GROUP BY Region, Year, Reef, Transect"
			") sub "
			"GROUP BY Region, Year ORDER BY Region, Year"
		)
		rows = execute_select(sql)

		# Group by region
		by_region: dict[str, list[tuple[int, float]]] = defaultdict(list)
		for r in rows:
			by_region[str(r["Region"])].append((r["Year"], float(r["value"])))

		results = []
		for region in sorted(by_region.keys()):
			data = by_region[region]
			if len(data) < 4:
				results.append({
					"region": region,
					"n_years": len(data),
					"trend": "insufficient data",
				})
				continue

			years = np.array([d[0] for d in data], dtype=float)
			values = np.array([d[1] for d in data])

			slope, _, r_value, p_value, _ = sp_stats.linregress(years, values)
			mk_tau, mk_p, mk_trend = _mann_kendall(values)

			results.append({
				"region": region,
				"n_years": len(data),
				"year_range": [int(years[0]), int(years[-1])],
				"linear_slope": round(float(slope), 4),
				"r_squared": round(float(r_value ** 2), 4),
				"linear_p": round(float(p_value), 6),
				"mk_tau": mk_tau,
				"mk_p": mk_p,
				"trend": mk_trend,
			})

		return json.dumps({
			"data": results,
			"meta": {
				"parameters": {"metric": metric},
				"row_count": len(results),
				"aggregation": f"Regional {metric} trends",
			},
		})

	@mcp.tool()
	def change_point_detection(
		region: str | None = None,
		metric: str = "biomass",
		method: str = "pettitt",
	) -> str:
		"""Detect change points in annual time series using Pettitt or CUSUM.

		Args:
			region: Filter by region
			metric: 'biomass' or 'abundance'
			method: 'pettitt' or 'cusum'
		"""
		if method not in ("pettitt", "cusum"):
			return json.dumps({"error": "method must be 'pettitt' or 'cusum'"})

		conditions = []
		params = []
		if region:
			conditions.append("Region = %s")
			params.append(region)
		if metric == "biomass":
			conditions.append("Biomass IS NOT NULL")

		where = "WHERE " + " AND ".join(conditions) if conditions else ""

		if metric == "biomass":
			inner = "SUM(Biomass) AS transect_val"
		else:
			inner = "SUM(Quantity) AS transect_val"

		sql = (
			"SELECT Year, AVG(transect_val) AS value "
			"FROM ("
			f"  SELECT Year, Reef, Transect, {inner} "
			f"  FROM ltem_historical_database {where} "
			"  GROUP BY Year, Reef, Transect"
			") sub "
			"GROUP BY Year ORDER BY Year"
		)
		rows = execute_select(sql, params=tuple(params) if params else None)

		if len(rows) < 6:
			return json.dumps({
				"data": [],
				"meta": {
					"warnings": [f"Insufficient time points ({len(rows)}) for change point detection"],
					"row_count": 0,
				},
			})

		years = [r["Year"] for r in rows]
		values = np.array([float(r["value"]) for r in rows])
		n = len(values)

		if method == "pettitt":
			# Pettitt test
			U = np.zeros(n, dtype=float)
			for t in range(n):
				for i in range(n):
					for j in range(i + 1, n):
						if i <= t < j:
							U[t] += np.sign(values[j] - values[i])

			k_idx = int(np.argmax(np.abs(U)))
			k_stat = float(np.abs(U[k_idx]))

			# Approximate p-value
			p_value = 2 * np.exp(-6 * k_stat**2 / (n**3 + n**2))
			p_value = min(float(p_value), 1.0)

			result = {
				"method": "pettitt",
				"change_point_year": years[k_idx],
				"change_point_index": k_idx,
				"test_statistic": round(k_stat, 2),
				"p_value": round(p_value, 6),
				"significant": bool(p_value < 0.05),
				"mean_before": round(float(np.mean(values[:k_idx + 1])), 2),
				"mean_after": round(float(np.mean(values[k_idx + 1:])), 2) if k_idx < n - 1 else None,
			}
		else:
			# CUSUM
			mean_val = np.mean(values)
			cusum = np.cumsum(values - mean_val)
			k_idx = int(np.argmax(np.abs(cusum)))

			result = {
				"method": "cusum",
				"change_point_year": years[k_idx],
				"change_point_index": k_idx,
				"max_cusum": round(float(np.max(np.abs(cusum))), 2),
				"mean_before": round(float(np.mean(values[:k_idx + 1])), 2),
				"mean_after": round(float(np.mean(values[k_idx + 1:])), 2) if k_idx < n - 1 else None,
			}

		return json.dumps({
			"data": result,
			"meta": {
				"parameters": {"region": region, "metric": metric, "method": method},
				"row_count": n,
				"aggregation": f"Change point detection ({method})",
			},
		})

	@mcp.tool()
	def seasonal_patterns(region: str | None = None) -> str:
		"""Monthly aggregation of survey data to detect seasonal patterns.

		Args:
			region: Filter by region
		"""
		conditions = []
		params = []
		if region:
			conditions.append("Region = %s")
			params.append(region)

		where = "WHERE " + " AND ".join(conditions) if conditions else ""

		sql = (
			"SELECT Month, "
			"AVG(Biomass) AS mean_biomass, "
			"AVG(Quantity) AS mean_abundance, "
			"COUNT(DISTINCT CONCAT(Year, '-', Reef, '-', Transect)) AS n_surveys "
			f"FROM ltem_historical_database {where} "
			"GROUP BY Month ORDER BY Month"
		)
		rows = execute_select(sql, params=tuple(params) if params else None)
		rows = _serialize_rows(rows)

		return json.dumps({
			"data": rows,
			"meta": {
				"parameters": {"region": region},
				"row_count": len(rows),
				"aggregation": "Monthly means across all years",
			},
		})

	@mcp.tool()
	def moving_window(
		region: str | None = None,
		metric: str = "biomass",
		window: int = 5,
	) -> str:
		"""Rolling average of annual time series.

		Args:
			region: Filter by region
			metric: 'biomass' or 'abundance'
			window: Window size in years (default 5)
		"""
		conditions = []
		params = []
		if region:
			conditions.append("Region = %s")
			params.append(region)
		if metric == "biomass":
			conditions.append("Biomass IS NOT NULL")

		where = "WHERE " + " AND ".join(conditions) if conditions else ""

		if metric == "biomass":
			inner = "SUM(Biomass) AS transect_val"
		else:
			inner = "SUM(Quantity) AS transect_val"

		sql = (
			"SELECT Year, AVG(transect_val) AS value "
			"FROM ("
			f"  SELECT Year, Reef, Transect, {inner} "
			f"  FROM ltem_historical_database {where} "
			"  GROUP BY Year, Reef, Transect"
			") sub "
			"GROUP BY Year ORDER BY Year"
		)
		rows = execute_select(sql, params=tuple(params) if params else None)

		if len(rows) < window:
			return json.dumps({
				"data": [],
				"meta": {
					"warnings": [f"Insufficient years ({len(rows)}) for window size {window}"],
					"row_count": 0,
				},
			})

		years = [r["Year"] for r in rows]
		values = np.array([float(r["value"]) for r in rows])

		safe_window = min(max(2, window), len(values))

		# Calculate rolling average
		rolling = []
		for i in range(len(values) - safe_window + 1):
			window_vals = values[i:i + safe_window]
			rolling.append({
				"center_year": years[i + safe_window // 2],
				"window_start": years[i],
				"window_end": years[i + safe_window - 1],
				"rolling_mean": round(float(np.mean(window_vals)), 2),
				"rolling_std": round(float(np.std(window_vals, ddof=1)), 2) if safe_window > 1 else 0,
			})

		return json.dumps({
			"data": rolling,
			"meta": {
				"parameters": {"region": region, "metric": metric, "window": safe_window},
				"row_count": len(rolling),
				"aggregation": f"{safe_window}-year rolling average of {metric}",
			},
		})
