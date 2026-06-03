"""LTEM Database MCP Server — FastMCP entry point.

Creates the MCP server instance, registers static resources, core tools,
and auto-discovers all tool modules in the tools/ directory.
"""

import importlib
import json
import logging
import pkgutil
from pathlib import Path

from fastmcp import FastMCP

from mcp_server.db import test_connection
from mcp_server.prompts import discover_prompts
from mcp_server.schema import build_schema_snapshot, describe_table, discover_tables

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Create the MCP server instance
# ---------------------------------------------------------------------------

mcp = FastMCP("LTEM Database")

# ---------------------------------------------------------------------------
# MCP Resources (static + dynamic)
# ---------------------------------------------------------------------------

@mcp.resource("ltem://schema")
def schema_resource() -> str:
	"""Full database schema: tables, columns, types, row counts."""
	return json.dumps(build_schema_snapshot(), indent=2)


@mcp.resource("ltem://regions")
def regions_resource() -> str:
	"""LTEM survey regions with descriptions."""
	regions = [
		{"name": "Alto Golfo", "description": "Upper Gulf of California, Vaquita refuge"},
		{"name": "Bahia Banderas", "description": "Bahia de Banderas, Pacific coast"},
		{"name": "Cabo Pulmo", "description": "Fully protected national marine park, recovery benchmark"},
		{"name": "Corredor", "description": "Corridor region, Baja California Sur"},
		{"name": "Huatulco", "description": "Huatulco National Park, Oaxaca coast"},
		{"name": "Islas Marias", "description": "Islas Marias Biosphere Reserve"},
		{"name": "Ixtapa", "description": "Ixtapa-Zihuatanejo reefs, Pacific coast"},
		{"name": "La Paz", "description": "Bay of La Paz and nearby islands, mixed protection"},
		{"name": "La Ventana", "description": "La Ventana, southern Baja California Sur"},
		{"name": "Loreto", "description": "Loreto Bay National Park, partially protected"},
		{"name": "Los Cabos", "description": "Los Cabos corridor reefs"},
		{"name": "Revillagigedo", "description": "Revillagigedo Archipelago National Park, oceanic islands"},
		{"name": "San Basilio", "description": "San Basilio coastal area"},
		{"name": "Santa Rosalia", "description": "Santa Rosalia, Gulf of California coast"},
	]
	return json.dumps(regions, indent=2)


@mcp.resource("ltem://sampling-protocol")
def sampling_protocol_resource() -> str:
	"""LTEM sampling design and protocol summary."""
	protocol = {
		"method": "Underwater visual census (UVC)",
		"transect_dimensions": "50m x 5m belt transects",
		"replicates": 4,
		"depth_levels": ["Shallow (5-8m)", "Deep (10-15m)"],
		"data_recorded": [
			"Species identification",
			"Individual count (Quantity)",
			"Estimated total length (Size, cm)",
			"Calculated biomass (Biomass, g/m\u00b2)",
		],
		"frequency": "Annual surveys (typically summer months)",
		"coverage": "Multiple regions across Gulf of California / Baja California Sur",
	}
	return json.dumps(protocol, indent=2)


@mcp.resource("ltem://protection-categories")
def protection_categories_resource() -> str:
	"""Protection status definitions used in LTEM analyses."""
	categories = {
		"Cabo Pulmo": {
			"level": "Fully Protected",
			"description": "No-take zone since 1995, strong enforcement, full recovery trajectory",
		},
		"Weak / Paper Park": {
			"level": "Weakly Protected",
			"description": "Designated as protected but limited or no enforcement",
		},
		"Unprotected": {
			"level": "Open Access",
			"description": "No formal protection, open to fishing activities",
		},
	}
	return json.dumps(categories, indent=2)


@mcp.resource("ltem://trophic-groups")
def trophic_groups_resource() -> str:
	"""Trophic group definitions and cutoff values."""
	groups = {
		"Herbivoro": {"description": "Algae and plant feeders (herbivores)"},
		"Carnivoro": {"description": "Invertebrate and small fish feeders (carnivores)"},
		"Piscivoro": {"description": "Fish-eating predators (piscivores)"},
		"Zooplanctivoro": {"description": "Zooplankton feeders (zooplanktivores)"},
	}
	# Note: TrophicGroup labels in the database are in Spanish
	return json.dumps(groups, indent=2)


@mcp.resource("ltem://metadata/manifest")
def metadata_manifest_resource() -> str:
	"""Full metadata manifest (auto-generated from template.json)."""
	manifest_path = Path(__file__).parent.parent / "metadata" / "manifest.json"
	if manifest_path.exists():
		return manifest_path.read_text(encoding="utf-8")
	return json.dumps({"error": "Manifest not found. Run: python scripts/generate_metadata_manifest.py"})


@mcp.resource("ltem://metadata/package")
def metadata_package_resource() -> str:
	"""Package metadata: name, version, description, license, runtime."""
	manifest_path = Path(__file__).parent.parent / "metadata" / "manifest.json"
	if manifest_path.exists():
		manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
		return json.dumps(manifest.get("package", {}), indent=2)
	return json.dumps({"error": "Manifest not found"})


@mcp.resource("ltem://metadata/dataset")
def metadata_dataset_resource() -> str:
	"""Dataset metadata: title, description, coverage, publisher (DCAT-like)."""
	manifest_path = Path(__file__).parent.parent / "metadata" / "manifest.json"
	if manifest_path.exists():
		manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
		return json.dumps(manifest.get("dataset", {}), indent=2)
	return json.dumps({"error": "Manifest not found"})


@mcp.resource("ltem://metadata/schema")
def metadata_schema_resource() -> str:
	"""Schema metadata: database structure, entities, fields."""
	manifest_path = Path(__file__).parent.parent / "metadata" / "manifest.json"
	if manifest_path.exists():
		manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
		return json.dumps(manifest.get("schema", {}), indent=2)
	return json.dumps({"error": "Manifest not found"})


@mcp.resource("ltem://metadata/endpoints")
def metadata_endpoints_resource() -> str:
	"""Endpoints metadata: tools, skills, resources counts and lists."""
	manifest_path = Path(__file__).parent.parent / "metadata" / "manifest.json"
	if manifest_path.exists():
		manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
		return json.dumps(manifest.get("endpoints", {}), indent=2)
	return json.dumps({"error": "Manifest not found"})


# ---------------------------------------------------------------------------
# Core tools (schema discovery, health check)
# ---------------------------------------------------------------------------

@mcp.tool()
def health_check() -> str:
	"""Verify database connectivity and return server info."""
	try:
		info = test_connection()
		return json.dumps({"status": "ok", **info})
	except Exception as e:
		return json.dumps({"status": "error", "error": str(e)})


@mcp.tool()
def list_tables() -> str:
	"""List all tables available in the ecological_monitoring database."""
	try:
		tables = discover_tables()
		return json.dumps({"tables": tables, "count": len(tables)})
	except Exception as e:
		return json.dumps({"error": str(e)})


@mcp.tool()
def describe_table_tool(table: str) -> str:
	"""Describe columns and types for a specific table.

	Args:
		table: Table name (e.g., 'ltem_historical_database')
	"""
	try:
		columns = describe_table(table)
		return json.dumps({
			"table": table,
			"columns": columns,
			"column_count": len(columns),
		})
	except Exception as e:
		return json.dumps({"error": str(e)})


@mcp.tool()
def schema_snapshot() -> str:
	"""Full schema snapshot with all tables, columns, types, and row counts."""
	try:
		snapshot = build_schema_snapshot()
		return json.dumps(snapshot, indent=2)
	except Exception as e:
		return json.dumps({"error": str(e)})


# ---------------------------------------------------------------------------
# Auto-discover and register tool modules from tools/ directory
# ---------------------------------------------------------------------------

def _discover_tools() -> None:
	"""Import every module in the tools/ package and call its register(mcp) function."""
	tools_dir = Path(__file__).resolve().parent.parent / "tools"
	if not tools_dir.is_dir():
		logger.warning("tools/ directory not found at %s", tools_dir)
		return

	# pkgutil finds all sub-modules in the tools package
	import tools as tools_pkg
	for importer, module_name, is_pkg in pkgutil.iter_modules(tools_pkg.__path__):
		if module_name.startswith("_"):
			continue
		try:
			mod = importlib.import_module(f"tools.{module_name}")
			if hasattr(mod, "register"):
				mod.register(mcp)
				logger.info("Registered tools from tools.%s", module_name)
			else:
				logger.debug("Skipped tools.%s (no register function)", module_name)
		except Exception:
			logger.exception("Failed to load tools.%s", module_name)


_discover_tools()
discover_prompts(mcp)
