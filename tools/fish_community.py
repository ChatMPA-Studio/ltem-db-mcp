"""Fish community analysis tools — diversity, composition, trophic/size structure."""

import json
import math
from collections import defaultdict

from fastmcp import FastMCP
from mcp_server.db import execute_select


def _safe_float(v):
	"""Convert Decimal/numeric to float, None stays None."""
	if v is None:
		return None
	if hasattr(v, 'as_integer_ratio'):
		return float(v)
	return v


def _serialize_rows(rows: list[dict]) -> list[dict]:
	"""Convert all Decimal values in rows to float for JSON."""
	return [
		{k: _safe_float(v) for k, v in row.items()}
		for row in rows
	]


def register(mcp: FastMCP) -> None:
	"""Register fish community tools with the MCP server."""

	@mcp.tool()
	def calculate_diversity(
		region: str | None = None,
		reef: str | None = None,
		year: int | None = None,
		depth: str | None = None,
	) -> str:
		"""Calculate diversity indices (Shannon, Simpson, Pielou) per survey unit.

		Computes indices at the transect level, then summarizes.

		Args:
			region: Filter by region
			reef: Filter by reef name
			year: Filter by year
			depth: Filter by habitat/depth (e.g., 'Shallow', 'Deep')
		"""
		conditions = []
		params = []
		if region:
			conditions.append("Region = %s")
			params.append(region)
		if reef:
			conditions.append("Reef = %s")
			params.append(reef)
		if year:
			conditions.append("Year = %s")
			params.append(year)
		if depth:
			conditions.append("Depth2 = %s")
			params.append(depth)

		where = "WHERE " + " AND ".join(conditions) if conditions else ""

		# Get species abundances per transect-survey unit
		sql = (
			"SELECT Year, Region, Reef, Transect, Species, "
			"SUM(Quantity) AS abundance "
			"FROM ltem_historical_database "
			f"{where} "
			"GROUP BY Year, Region, Reef, Transect, Species"
		)
		rows = execute_select(sql, params=tuple(params) if params else None)

		# Group by survey unit (Year-Region-Reef-Transect)
		surveys: dict[str, dict[str, float]] = defaultdict(dict)
		survey_meta: dict[str, dict] = {}
		for r in rows:
			key = f"{r['Year']}-{r['Region']}-{r['Reef']}-{r['Transect']}"
			abundance = float(r['abundance']) if r['abundance'] else 0
			surveys[key][r['Species']] = abundance
			survey_meta[key] = {
				"Year": r['Year'],
				"Region": r['Region'],
				"Reef": r['Reef'],
				"Transect": r['Transect'],
			}

		# Calculate indices per survey
		results = []
		for key, species_counts in surveys.items():
			total = sum(species_counts.values())
			if total == 0:
				continue

			richness = len(species_counts)
			proportions = [n / total for n in species_counts.values()]

			# Shannon H'
			shannon = -sum(p * math.log(p) for p in proportions if p > 0)

			# Simpson D (1 - sum(p^2))
			simpson = 1 - sum(p ** 2 for p in proportions)

			# Pielou J = H' / ln(S)
			pielou = shannon / math.log(richness) if richness > 1 else 0

			results.append({
				**survey_meta[key],
				"species_richness": richness,
				"total_abundance": total,
				"shannon_h": round(shannon, 4),
				"simpson_d": round(simpson, 4),
				"pielou_j": round(pielou, 4),
			})

		return json.dumps({
			"data": results,
			"meta": {
				"parameters": {
					"region": region, "reef": reef, "year": year, "depth": depth,
				},
				"row_count": len(results),
				"aggregation": "Diversity indices per transect survey unit",
			},
		})

	@mcp.tool()
	def species_composition(
		group_by: str = "Region",
		top_n: int = 15,
	) -> str:
		"""Top N species by relative abundance, grouped by region or other factor.

		Args:
			group_by: Group by 'Region', 'MPA', 'Year', or 'Habitat'
			top_n: Number of top species to return per group (default 15)
		"""
		allowed = {"Region", "MPA", "Year", "Habitat"}
		if group_by not in allowed:
			return json.dumps({"error": f"group_by must be one of: {', '.join(sorted(allowed))}"})

		safe_top = min(max(1, top_n), 50)

		sql = (
			f"SELECT {group_by}, Species, SUM(Quantity) AS total_abundance "
			"FROM ltem_historical_database "
			f"GROUP BY {group_by}, Species "
			f"ORDER BY {group_by}, total_abundance DESC"
		)
		rows = execute_select(sql)

		# Group and take top N per group
		groups: dict[str, list] = defaultdict(list)
		for r in rows:
			groups[str(r[group_by])].append({
				"species": r["Species"],
				"abundance": _safe_float(r["total_abundance"]),
			})

		result = {}
		for grp, species_list in groups.items():
			total = sum(s["abundance"] for s in species_list if s["abundance"])
			top = species_list[:safe_top]
			for s in top:
				s["relative_abundance"] = round(s["abundance"] / total, 4) if total else 0
			result[grp] = {
				"top_species": top,
				"total_species": len(species_list),
				"total_abundance": total,
			}

		return json.dumps({
			"data": result,
			"meta": {
				"parameters": {"group_by": group_by, "top_n": safe_top},
				"row_count": len(result),
				"aggregation": f"Top {safe_top} species by abundance per {group_by}",
			},
		})

	@mcp.tool()
	def trophic_structure(
		region: str | None = None,
		year: int | None = None,
	) -> str:
		"""Biomass proportions by trophic group.

		Uses the pre-computed TrophicGroup column in the historical database.

		Args:
			region: Filter by region
			year: Filter by year
		"""
		conditions = ["TrophicGroup IS NOT NULL"]
		params = []
		if region:
			conditions.append("Region = %s")
			params.append(region)
		if year:
			conditions.append("Year = %s")
			params.append(year)

		where = "WHERE " + " AND ".join(conditions)

		sql = (
			"SELECT TrophicGroup AS trophic_group, "
			"SUM(Biomass) AS total_biomass, "
			"SUM(Quantity) AS total_abundance, "
			"COUNT(DISTINCT Species) AS species_count "
			f"FROM ltem_historical_database {where} "
			"GROUP BY TrophicGroup "
			"ORDER BY total_biomass DESC"
		)
		rows = execute_select(sql, params=tuple(params) if params else None)
		rows = _serialize_rows(rows)

		# Calculate proportions
		grand_total = sum(r["total_biomass"] for r in rows if r["total_biomass"])
		for r in rows:
			r["biomass_proportion"] = (
				round(r["total_biomass"] / grand_total, 4)
				if grand_total and r["total_biomass"] else 0
			)

		warnings = []
		null_biomass = sum(1 for r in rows if r.get("trophic_group") == "Unknown")
		if null_biomass:
			warnings.append("Some species lack trophic level data")

		return json.dumps({
			"data": rows,
			"meta": {
				"parameters": {"region": region, "year": year},
				"row_count": len(rows),
				"aggregation": "Biomass by trophic group",
				"warnings": warnings,
			},
		})

	@mcp.tool()
	def size_structure(
		region: str | None = None,
		year: int | None = None,
	) -> str:
		"""Abundance distribution by size class.

		Size classes: 0-10, 10-20, 20-30, 30-40, 40-50, 50+ cm.

		Args:
			region: Filter by region
			year: Filter by year
		"""
		conditions = ["Size IS NOT NULL"]
		params = []
		if region:
			conditions.append("Region = %s")
			params.append(region)
		if year:
			conditions.append("Year = %s")
			params.append(year)

		where = "WHERE " + " AND ".join(conditions)

		sql = (
			"SELECT "
			"CASE "
			"  WHEN Size < 10 THEN '0-10' "
			"  WHEN Size >= 10 AND Size < 20 THEN '10-20' "
			"  WHEN Size >= 20 AND Size < 30 THEN '20-30' "
			"  WHEN Size >= 30 AND Size < 40 THEN '30-40' "
			"  WHEN Size >= 40 AND Size < 50 THEN '40-50' "
			"  WHEN Size >= 50 THEN '50+' "
			"END AS size_class, "
			"SUM(Quantity) AS abundance, "
			"COUNT(DISTINCT Species) AS species_count "
			f"FROM ltem_historical_database {where} "
			"GROUP BY size_class "
			"ORDER BY size_class"
		)
		rows = execute_select(sql, params=tuple(params) if params else None)
		rows = _serialize_rows(rows)

		total = sum(r["abundance"] for r in rows if r["abundance"])
		for r in rows:
			r["proportion"] = (
				round(r["abundance"] / total, 4) if total and r["abundance"] else 0
			)

		return json.dumps({
			"data": rows,
			"meta": {
				"parameters": {"region": region, "year": year},
				"row_count": len(rows),
				"aggregation": "Abundance by size class (cm)",
			},
		})

	@mcp.tool()
	def community_comparison(group_by: str = "Region") -> str:
		"""Bray-Curtis dissimilarity matrix between groups.

		Computes pairwise Bray-Curtis dissimilarity based on species abundance.

		Args:
			group_by: Compare across 'Region', 'MPA', or 'Habitat'
		"""
		allowed = {"Region", "MPA", "Habitat"}
		if group_by not in allowed:
			return json.dumps({"error": f"group_by must be one of: {', '.join(sorted(allowed))}"})

		sql = (
			f"SELECT {group_by} AS grp, Species, SUM(Quantity) AS abundance "
			"FROM ltem_historical_database "
			f"GROUP BY {group_by}, Species"
		)
		rows = execute_select(sql)

		# Build abundance vectors per group
		groups: dict[str, dict[str, float]] = defaultdict(dict)
		all_species = set()
		for r in rows:
			grp = str(r["grp"])
			sp = r["Species"]
			groups[grp][sp] = float(r["abundance"]) if r["abundance"] else 0
			all_species.add(sp)

		group_names = sorted(groups.keys())

		# Compute Bray-Curtis pairwise
		matrix = {}
		for i, g1 in enumerate(group_names):
			for g2 in group_names[i + 1:]:
				# BC = sum|a_i - b_i| / sum(a_i + b_i)
				numerator = 0
				denominator = 0
				for sp in all_species:
					a = groups[g1].get(sp, 0)
					b = groups[g2].get(sp, 0)
					numerator += abs(a - b)
					denominator += a + b
				bc = round(numerator / denominator, 4) if denominator > 0 else 0
				matrix[f"{g1} vs {g2}"] = bc

		return json.dumps({
			"data": {
				"groups": group_names,
				"dissimilarity_matrix": matrix,
				"total_species": len(all_species),
			},
			"meta": {
				"parameters": {"group_by": group_by},
				"row_count": len(matrix),
				"aggregation": "Bray-Curtis dissimilarity",
			},
		})
