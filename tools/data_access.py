"""Data access tools for querying LTEM ecological monitoring data."""

import json
from fastmcp import FastMCP
from mcp_server.db import execute_select


def register(mcp: FastMCP) -> None:
	"""Register data access tools with the MCP server."""

	@mcp.tool()
	def get_regions() -> str:
		"""List all surveyed regions in the LTEM database."""
		rows = execute_select(
			"SELECT DISTINCT Region FROM ltem_historical_database ORDER BY Region"
		)
		regions = [r["Region"] for r in rows if r.get("Region")]
		return json.dumps({
			"data": regions,
			"meta": {"row_count": len(regions)},
		})

	@mcp.tool()
	def get_reefs(region: str | None = None) -> str:
		"""List reefs/sites, optionally filtered by region.

		Args:
			region: Filter by region name (e.g., "La Paz", "Cabo Pulmo")
		"""
		if region:
			rows = execute_select(
				"SELECT DISTINCT IDReef, Reef, Region, MPA "
				"FROM ltem_historical_database "
				"WHERE Region = %s "
				"ORDER BY Reef",
				params=(region,),
			)
		else:
			rows = execute_select(
				"SELECT DISTINCT IDReef, Reef, Region, MPA "
				"FROM ltem_historical_database "
				"ORDER BY Region, Reef"
			)
		return json.dumps({
			"data": rows,
			"meta": {
				"parameters": {"region": region},
				"row_count": len(rows),
			},
		})

	@mcp.tool()
	def get_species_list(
		region: str | None = None,
		year: int | None = None,
		label: str | None = None,
	) -> str:
		"""List species observed in the LTEM surveys.

		Args:
			region: Filter by region name
			year: Filter by survey year
			label: Filter species name (partial match, case-insensitive)
		"""
		conditions = []
		params = []

		if region:
			conditions.append("h.Region = %s")
			params.append(region)
		if year:
			conditions.append("h.Year = %s")
			params.append(year)
		if label:
			conditions.append("h.Species LIKE %s")
			params.append(f"%{label}%")

		where = "WHERE " + " AND ".join(conditions) if conditions else ""

		sql = (
			"SELECT DISTINCT h.IDSpecies, h.Species "
			"FROM ltem_historical_database h "
			f"{where} "
			"ORDER BY h.Species"
		)
		rows = execute_select(sql, params=tuple(params) if params else None)
		return json.dumps({
			"data": rows,
			"meta": {
				"parameters": {"region": region, "year": year, "label": label},
				"row_count": len(rows),
			},
		})

	@mcp.tool()
	def get_observations(
		region: str | None = None,
		reef: str | None = None,
		year: int | None = None,
		species: str | None = None,
		limit: int = 1000,
	) -> str:
		"""Query raw observation data from the LTEM historical database.

		Args:
			region: Filter by region name
			reef: Filter by reef name
			year: Filter by survey year
			species: Filter by species name (exact match)
			limit: Maximum rows to return (default 1000, max 5000)
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
		if species:
			conditions.append("Species = %s")
			params.append(species)

		where = "WHERE " + " AND ".join(conditions) if conditions else ""
		safe_limit = min(max(1, limit), 5000)

		sql = (
			"SELECT Year, Month, Day, Region, Reef, Habitat, MPA, Transect, "
			"Area, IDSpecies, Species, Quantity, Size, Biomass "
			f"FROM ltem_historical_database {where} "
			f"LIMIT {safe_limit}"
		)
		rows = execute_select(sql, params=tuple(params) if params else None)

		# Convert Decimal types to float for JSON serialization
		for row in rows:
			for k, v in row.items():
				if hasattr(v, 'as_integer_ratio'):
					row[k] = float(v)

		return json.dumps({
			"data": rows,
			"meta": {
				"parameters": {
					"region": region,
					"reef": reef,
					"year": year,
					"species": species,
					"limit": safe_limit,
				},
				"row_count": len(rows),
				"warnings": (
					["Result truncated at limit"] if len(rows) == safe_limit else []
				),
			},
		})

	@mcp.tool()
	def get_nrsi_data(
		mpa: str | None = None,
		region: str | None = None,
		reef: str | None = None,
		year: int | None = None,
	) -> str:
		"""Raw biomass per transect × TrophicLevelF, ready for NRSI computation.

		Returns one row per (transect, TrophicLevelF) combination — the unit
		needed to classify UTL/LTL/CTL and compute the Normalized Reef State Index.
		No row cap. Fixed filters: Label='PEC', Biomass IS NOT NULL, TrophicLevelF IS NOT NULL.

		Output columns: time (Year), value (SUM Biomass), TrophicLevelF,
		transect (Year-Region-Reef-Habitat-Depth-Transect), reef, region.

		Args:
			mpa: Filter by MPA status
			region: Filter by region name
			reef: Filter by reef name
			year: Filter by survey year
		"""
		conditions = [
			"Label = 'PEC'",
			"Biomass IS NOT NULL",
			"TrophicLevelF IS NOT NULL",
		]
		params = []

		if mpa:
			conditions.append("MPA = %s")
			params.append(mpa)
		if region:
			conditions.append("Region = %s")
			params.append(region)
		if reef:
			conditions.append("Reef = %s")
			params.append(reef)
		if year:
			conditions.append("Year = %s")
			params.append(year)

		where = "WHERE " + " AND ".join(conditions)

		sql = (
			"SELECT "
			"Year AS time, "
			"SUM(Biomass) AS value, "
			"TrophicLevelF, "
			"CONCAT_WS('-', Year, Region, Reef, Habitat, Depth, Transect) AS transect, "
			"Reef AS reef, "
			"Region AS region "
			f"FROM ltem_historical_database {where} "
			"GROUP BY Year, Region, Reef, Habitat, Depth, Transect, TrophicLevelF "
			"ORDER BY Year, Region, Reef, Transect"
		)

		rows = execute_select(sql, params=tuple(params) if params else None, max_rows=500000)

		for row in rows:
			for k, v in row.items():
				if hasattr(v, 'as_integer_ratio'):
					row[k] = float(v)

		return json.dumps({
			"data": rows,
			"meta": {
				"parameters": {
					"mpa": mpa,
					"region": region,
					"reef": reef,
					"year": year,
				},
				"row_count": len(rows),
				"columns": ["time", "value", "TrophicLevelF", "transect", "reef", "region"],
				"description": "Biomass per transect × TrophicLevelF for NRSI computation",
			},
		})

	@mcp.tool()
	def survey_effort_summary(group_by: str = "Year") -> str:
		"""Summarize survey effort (transect counts, reef counts, species counts).

		Args:
			group_by: Group results by 'Year', 'Region', or 'MPA'
		"""
		allowed_groups = {"Year", "Region", "MPA"}
		if group_by not in allowed_groups:
			return json.dumps({
				"error": f"group_by must be one of: {', '.join(sorted(allowed_groups))}",
			})

		sql = (
			f"SELECT {group_by}, "
			"COUNT(DISTINCT Reef) AS reef_count, "
			"COUNT(DISTINCT CONCAT(Year, '-', Reef, '-', Transect)) AS transect_count, "
			"COUNT(DISTINCT Species) AS species_count, "
			"SUM(Quantity) AS total_individuals "
			f"FROM ltem_historical_database "
			f"GROUP BY {group_by} "
			f"ORDER BY {group_by}"
		)
		rows = execute_select(sql)

		for row in rows:
			for k, v in row.items():
				if hasattr(v, 'as_integer_ratio'):
					row[k] = float(v)

		return json.dumps({
			"data": rows,
			"meta": {
				"parameters": {"group_by": group_by},
				"row_count": len(rows),
				"aggregation": f"Grouped by {group_by}",
			},
		})


	@mcp.tool()
	def get_biomass_data(
		mpa: str | None = None,
		region: str | None = None,
		reef: str | None = None,
		year: int | None = None,
	) -> str:
		"""Reef-year fish biomass ready for ltem-fish-biomass skill computation.

		Returns one row per (Year, Reef, Region) — the aggregation unit needed
		to fit the GAM trend model. Biomass is summed per transect then averaged
		per reef-year. No row cap. Fixed filters: Label='PEC', Biomass IS NOT NULL.

		Output columns: time (Year), reef (Reef), value (mean g/m² per reef-year),
		region (Region), n_transects (number of transects contributing).

		Args:
			mpa: Filter by MPA status
			region: Filter by region name
			reef: Filter by reef name
			year: Filter by survey year
		"""
		conditions = [
			"Label = 'PEC'",
			"Biomass IS NOT NULL",
		]
		params = []

		if mpa:
			conditions.append("MPA = %s")
			params.append(mpa)
		if region:
			conditions.append("Region = %s")
			params.append(region)
		if reef:
			conditions.append("Reef = %s")
			params.append(reef)
		if year:
			conditions.append("Year = %s")
			params.append(year)

		where = "WHERE " + " AND ".join(conditions)

		sql = (
			"SELECT "
			"Year AS time, "
			"Reef AS reef, "
			"Region AS region, "
			"AVG(transect_biomass) AS value, "
			"COUNT(*) AS n_transects "
			"FROM ("
			"  SELECT Year, Region, Reef, Habitat, Depth, Transect, "
			"  SUM(Biomass) AS transect_biomass "
			f"  FROM ltem_historical_database {where} "
			"  GROUP BY Year, Region, Reef, Habitat, Depth, Transect"
			") AS transect_agg "
			"GROUP BY Year, Reef, Region "
			"ORDER BY Year, Region, Reef"
		)

		rows = execute_select(sql, params=tuple(params) if params else None, max_rows=500000)

		for row in rows:
			for k, v in row.items():
				if hasattr(v, "as_integer_ratio"):
					row[k] = float(v)

		return json.dumps({
			"data": rows,
			"meta": {
				"parameters": {
					"mpa": mpa,
					"region": region,
					"reef": reef,
					"year": year,
				},
				"row_count": len(rows),
				"columns": ["time", "reef", "region", "value", "n_transects"],
				"description": "Mean fish biomass (g/m²) per reef-year for GAM trend fitting",
			},
		})

	@mcp.tool()
	def get_invertebrate_data(
		mpa: str | None = None,
		region: str | None = None,
		reef: str | None = None,
		year: int | None = None,
	) -> str:
		"""Reef-year invertebrate abundance by taxon, ready for ltem-invertebrate-abundance skill.

		Returns one row per (Year, Reef, Region, Taxa2) — the aggregation unit
		needed to fit the per-taxon GAM trend model. Abundance is summed per
		transect then averaged per reef-year-taxa. No row cap.
		Fixed filters: Label='INV'.

		Output columns: time (Year), reef (Reef), region (Region),
		taxa (Taxa2), value (mean count per reef-year-taxa), n_transects.

		Args:
			mpa: Filter by MPA status
			region: Filter by region name
			reef: Filter by reef name
			year: Filter by survey year
		"""
		conditions = [
			"Label = 'INV'",
			"Taxa2 IS NOT NULL",
		]
		params = []

		if mpa:
			conditions.append("MPA = %s")
			params.append(mpa)
		if region:
			conditions.append("Region = %s")
			params.append(region)
		if reef:
			conditions.append("Reef = %s")
			params.append(reef)
		if year:
			conditions.append("Year = %s")
			params.append(year)

		where = "WHERE " + " AND ".join(conditions)

		sql = (
			"SELECT "
			"Year AS time, "
			"Reef AS reef, "
			"Region AS region, "
			"Taxa2 AS taxa, "
			"AVG(transect_qty) AS value, "
			"COUNT(*) AS n_transects "
			"FROM ("
			"  SELECT Year, Region, Reef, Habitat, Depth, Transect, Taxa2, "
			"  SUM(Quantity) AS transect_qty "
			f"  FROM ltem_historical_database {where} "
			"  GROUP BY Year, Region, Reef, Habitat, Depth, Transect, Taxa2"
			") AS transect_agg "
			"GROUP BY Year, Reef, Region, Taxa2 "
			"ORDER BY Year, Region, Reef, Taxa2"
		)

		rows = execute_select(sql, params=tuple(params) if params else None, max_rows=500000)

		for row in rows:
			for k, v in row.items():
				if hasattr(v, "as_integer_ratio"):
					row[k] = float(v)

		return json.dumps({
			"data": rows,
			"meta": {
				"parameters": {
					"mpa": mpa,
					"region": region,
					"reef": reef,
					"year": year,
				},
				"row_count": len(rows),
				"columns": ["time", "reef", "region", "taxa", "value", "n_transects"],
				"description": "Mean invertebrate abundance per reef-year-taxon for GAM trend fitting",
			},
		})

