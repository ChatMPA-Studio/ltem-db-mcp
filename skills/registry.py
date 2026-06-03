"""Skills registry for LTEM MCP server.

This module catalogs all available analysis skills with their metadata,
input/output contracts, and tool dependencies.

Skills are structured workflows that orchestrate multiple tools to perform
complex analyses. Each skill has:
- Unique ID (kebab-case)
- Name and description
- Version (semantic versioning)
- Input/output JSON schemas
- List of required tools
- Estimated execution time
"""

from typing import Dict, List, Optional

# ---------------------------------------------------------------------------
# Skills Registry
# ---------------------------------------------------------------------------

SKILLS_REGISTRY: Dict[str, Dict] = {
    "healthcheck": {
        "name": "Health Check",
        "description": "Minimal validation - calls basic tools to verify server health",
        "version": "1.0.0",
        "inputs_schema": "skills/contracts/healthcheck.schema.json",
        "outputs_schema": "skills/contracts/healthcheck.schema.json",
        "estimated_duration": "5 seconds",
        "tools_required": ["get_regions", "list_tables"],
        "tags": ["validation", "diagnostic"]
    },
    "example-workflow": {
        "name": "Example Workflow",
        "description": "Demonstrates tool orchestration with validation and interpretation",
        "version": "1.0.0",
        "inputs_schema": "skills/contracts/example_workflow.schema.json",
        "outputs_schema": "skills/contracts/example_workflow.schema.json",
        "estimated_duration": "30 seconds",
        "tools_required": ["get_regions", "get_summary"],
        "tags": ["example", "tutorial"]
    },
    "ltem-mpa-effectiveness": {
        "name": "MPA Effectiveness Analysis",
        "description": "Compare biomass, abundance, and richness across protection levels using statistical tests",
        "version": "1.0.0",
        "inputs_schema": "skills/contracts/mpa_effectiveness.schema.json",
        "outputs_schema": "skills/contracts/mpa_effectiveness.schema.json",
        "estimated_duration": "60 seconds",
        "tools_required": [
            "biomass_by_protection",
            "compare_protection_levels",
            "compare_all_metrics"
        ],
        "tags": ["mpa", "comparative", "statistical"]
    },
    "ltem-temporal-trends": {
        "name": "Temporal Trends Analysis",
        "description": "Analyze biomass and abundance trends over time using Mann-Kendall test and Sen's slope",
        "version": "1.0.0",
        "inputs_schema": "skills/contracts/temporal_trends.schema.json",
        "outputs_schema": "skills/contracts/temporal_trends.schema.json",
        "estimated_duration": "45 seconds",
        "tools_required": [
            "annual_time_series",
            "trend_analysis",
            "moving_window"
        ],
        "tags": ["temporal", "trends", "statistical"]
    },
    "ltem-fish-community": {
        "name": "Fish Community Analysis",
        "description": "Analyze species composition, diversity indices, and community structure",
        "version": "1.0.0",
        "inputs_schema": "skills/contracts/fish_community.schema.json",
        "outputs_schema": "skills/contracts/fish_community.schema.json",
        "estimated_duration": "50 seconds",
        "tools_required": [
            "species_composition",
            "calculate_diversity",
            "community_comparison"
        ],
        "tags": ["community", "diversity", "species"]
    },
    "ltem-data-quality": {
        "name": "Data Quality Assessment",
        "description": "Assess survey effort, data completeness, and identify quality issues",
        "version": "1.0.0",
        "inputs_schema": "skills/contracts/data_quality.schema.json",
        "outputs_schema": "skills/contracts/data_quality.schema.json",
        "estimated_duration": "40 seconds",
        "tools_required": [
            "survey_effort_summary",
            "get_observations"
        ],
        "tags": ["quality", "validation", "survey"]
    },
    "ltem-nrsi-index": {
        "name": "NRSI Index Calculation",
        "description": "Calculate Natural Reef State Index (NRSI) components and overall score",
        "version": "1.0.0",
        "inputs_schema": "skills/contracts/nrsi_index.schema.json",
        "outputs_schema": "skills/contracts/nrsi_index.schema.json",
        "estimated_duration": "55 seconds",
        "tools_required": [
            "size_structure",
            "trophic_structure",
            "biomass_by_region"
        ],
        "tags": ["nrsi", "index", "ecosystem"]
    },
    "ltem-environmental-drivers": {
        "name": "Environmental Drivers Analysis",
        "description": "Analyze correlations between biomass and environmental variables (SST, Chl-a)",
        "version": "1.0.0",
        "inputs_schema": "skills/contracts/environmental_drivers.schema.json",
        "outputs_schema": "skills/contracts/environmental_drivers.schema.json",
        "estimated_duration": "50 seconds",
        "tools_required": [
            "environmental_correlations",
            "sst_biomass_relationship",
            "chl_productivity_relationship"
        ],
        "tags": ["environmental", "correlation", "drivers"]
    },
    "ltem-functional-groups": {
        "name": "Functional Groups Analysis",
        "description": "Analyze trophic/functional group composition and biomass distribution",
        "version": "1.0.0",
        "inputs_schema": "skills/contracts/functional_groups.schema.json",
        "outputs_schema": "skills/contracts/functional_groups.schema.json",
        "estimated_duration": "45 seconds",
        "tools_required": [
            "trophic_biomass",
            "trophic_structure",
            "trophic_comparison"
        ],
        "tags": ["trophic", "functional", "groups"]
    },
    "ltem-invertebrate-community": {
        "name": "Invertebrate Community Analysis",
        "description": "Analyze invertebrate abundance, diversity, and community patterns",
        "version": "1.0.0",
        "inputs_schema": "skills/contracts/invertebrate_community.schema.json",
        "outputs_schema": "skills/contracts/invertebrate_community.schema.json",
        "estimated_duration": "40 seconds",
        "tools_required": [
            "get_observations"
        ],
        "tags": ["invertebrates", "community", "diversity"]
    },
    "ltem-biomass-productivity": {
        "name": "Biomass-Productivity Relationship",
        "description": "Analyze relationship between biomass and primary productivity (Chl-a)",
        "version": "1.0.0",
        "inputs_schema": "skills/contracts/biomass_productivity.schema.json",
        "outputs_schema": "skills/contracts/biomass_productivity.schema.json",
        "estimated_duration": "45 seconds",
        "tools_required": [
            "chl_productivity_relationship",
            "biomass_by_region"
        ],
        "tags": ["biomass", "productivity", "chlorophyll"]
    },
    "ltem-bleaching-assessment": {
        "name": "Bleaching Impact Assessment",
        "description": "Assess coral bleaching impacts on fish communities using BACI analysis",
        "version": "1.0.0",
        "inputs_schema": "skills/contracts/bleaching_assessment.schema.json",
        "outputs_schema": "skills/contracts/bleaching_assessment.schema.json",
        "estimated_duration": "60 seconds",
        "tools_required": [
            "baci_analysis",
            "annual_time_series"
        ],
        "tags": ["bleaching", "impact", "baci"]
    },
    "ltem-survey-numeralia": {
        "name": "Survey Numeralia Summary",
        "description": "Generate comprehensive survey statistics and metadata",
        "version": "1.0.0",
        "inputs_schema": "skills/contracts/survey_numeralia.schema.json",
        "outputs_schema": "skills/contracts/survey_numeralia.schema.json",
        "estimated_duration": "35 seconds",
        "tools_required": [
            "survey_effort_summary",
            "get_regions",
            "get_reefs"
        ],
        "tags": ["survey", "metadata", "summary"]
    }
}


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def list_skills() -> List[Dict]:
    """List all available skills with metadata.
    
    Returns:
        List of skill dictionaries with id and metadata
    """
    return [
        {"id": skill_id, **skill_info}
        for skill_id, skill_info in SKILLS_REGISTRY.items()
    ]


def get_skill(skill_id: str) -> Optional[Dict]:
    """Get skill metadata by ID.
    
    Args:
        skill_id: Skill identifier (kebab-case)
        
    Returns:
        Skill metadata dictionary or None if not found
    """
    return SKILLS_REGISTRY.get(skill_id)


def list_skills_by_tag(tag: str) -> List[Dict]:
    """List skills filtered by tag.
    
    Args:
        tag: Tag to filter by (e.g., 'statistical', 'mpa', 'temporal')
        
    Returns:
        List of matching skill dictionaries
    """
    return [
        {"id": skill_id, **skill_info}
        for skill_id, skill_info in SKILLS_REGISTRY.items()
        if tag in skill_info.get("tags", [])
    ]


def get_skill_count() -> int:
    """Get total number of registered skills.
    
    Returns:
        Count of skills in registry
    """
    return len(SKILLS_REGISTRY)


def validate_skill_exists(skill_id: str) -> bool:
    """Check if a skill exists in the registry.
    
    Args:
        skill_id: Skill identifier to check
        
    Returns:
        True if skill exists, False otherwise
    """
    return skill_id in SKILLS_REGISTRY
