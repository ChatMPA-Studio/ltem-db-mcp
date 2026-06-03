"""End-to-end tests for Phase 0 template completion.

These tests validate that all required Phase 0 components are present
and functional before deployment.
"""

import json
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Test Metadata Infrastructure
# ---------------------------------------------------------------------------

def test_metadata_directory_exists():
    """Verify metadata directory structure exists."""
    metadata_dir = Path("metadata")
    assert metadata_dir.exists(), "metadata/ directory not found"
    assert metadata_dir.is_dir(), "metadata/ is not a directory"


def test_metadata_template_exists():
    """Verify metadata/template.json exists and is valid JSON."""
    template_path = Path("metadata/template.json")
    assert template_path.exists(), "metadata/template.json not found"

    with open(template_path, 'r', encoding='utf-8') as f:
        template = json.load(f)

    # Verify required top-level keys
    assert "package" in template, "Missing 'package' in template.json"
    assert "dataset" in template, "Missing 'dataset' in template.json"
    assert "schema" in template, "Missing 'schema' in template.json"
    assert "endpoints" in template, "Missing 'endpoints' in template.json"


def test_metadata_manifest_exists():
    """Verify metadata/manifest.json exists and is valid JSON."""
    manifest_path = Path("metadata/manifest.json")
    assert manifest_path.exists(), "metadata/manifest.json not found"

    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    # Verify generated field exists
    assert "generated" in manifest, "Missing 'generated' in manifest.json"


def test_metadata_schema_exists():
    """Verify JSON Schema definition exists."""
    schema_path = Path("metadata/schema/metadata.schema.json")
    assert schema_path.exists(), "metadata/schema/metadata.schema.json not found"

    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = json.load(f)

    assert "$schema" in schema, "Invalid JSON Schema format"


def test_metadata_readme_exists():
    """Verify metadata README exists."""
    readme_path = Path("metadata/README.md")
    assert readme_path.exists(), "metadata/README.md not found"


# ---------------------------------------------------------------------------
# Test Skills Infrastructure
# ---------------------------------------------------------------------------

def test_skills_registry_exists():
    """Verify skills/registry.py exists and is importable."""
    registry_path = Path("skills/registry.py")
    assert registry_path.exists(), "skills/registry.py not found"

    # Test import
    from skills.registry import SKILLS_REGISTRY, list_skills, get_skill

    assert isinstance(SKILLS_REGISTRY, dict), "SKILLS_REGISTRY is not a dict"
    assert len(SKILLS_REGISTRY) >= 2, "Registry must have at least 2 skills (healthcheck + example)"


def test_skills_registry_structure():
    """Verify skills registry has correct structure."""
    from skills.registry import SKILLS_REGISTRY

    # Check healthcheck skill exists
    assert "healthcheck" in SKILLS_REGISTRY, "healthcheck skill not in registry"

    # Check example-workflow skill exists
    assert "example-workflow" in SKILLS_REGISTRY, "example-workflow skill not in registry"

    # Verify skill structure
    for skill_id, skill_info in SKILLS_REGISTRY.items():
        assert "name" in skill_info, f"Skill {skill_id} missing 'name'"
        assert "description" in skill_info, f"Skill {skill_id} missing 'description'"
        assert "version" in skill_info, f"Skill {skill_id} missing 'version'"
        assert "inputs_schema" in skill_info, f"Skill {skill_id} missing 'inputs_schema'"
        assert "outputs_schema" in skill_info, f"Skill {skill_id} missing 'outputs_schema'"
        assert "tools_required" in skill_info, f"Skill {skill_id} missing 'tools_required'"


def test_skills_contracts_directory_exists():
    """Verify skills/contracts/ directory exists."""
    contracts_dir = Path("skills/contracts")
    assert contracts_dir.exists(), "skills/contracts/ directory not found"
    assert contracts_dir.is_dir(), "skills/contracts/ is not a directory"


def test_skills_contracts_exist():
    """Verify contract schemas exist for all registered skills."""
    from skills.registry import SKILLS_REGISTRY

    for skill_id, skill_info in SKILLS_REGISTRY.items():
        schema_path = Path(skill_info["inputs_schema"])
        assert schema_path.exists(), f"Contract schema not found for {skill_id}: {schema_path}"

        # Verify it's valid JSON
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)

        assert "$schema" in schema, f"Invalid JSON Schema for {skill_id}"


def test_healthcheck_skill_exists():
    """Verify healthcheck skill directory and SKILL.md exist."""
    healthcheck_dir = Path("skills/healthcheck")
    assert healthcheck_dir.exists(), "skills/healthcheck/ directory not found"

    skill_md = healthcheck_dir / "SKILL.md"
    assert skill_md.exists(), "skills/healthcheck/SKILL.md not found"


def test_example_workflow_skill_exists():
    """Verify example-workflow skill directory and SKILL.md exist."""
    example_dir = Path("skills/example-workflow")
    assert example_dir.exists(), "skills/example-workflow/ directory not found"

    skill_md = example_dir / "SKILL.md"
    assert skill_md.exists(), "skills/example-workflow/SKILL.md not found"


# ---------------------------------------------------------------------------
# Test Documentation
# ---------------------------------------------------------------------------

def test_core_documentation_exists():
    """Verify all 8 core documentation files exist."""
    required_docs = [
        "docs/infrastructure.md",
        "docs/mcp_template_spec.md",
        "docs/skills_architecture.md",
        "docs/metadata_schema.md",
        "docs/deployment_workflow.md",
        "docs/api_examples.md",
        "docs/troubleshooting.md",
        "docs/documentation_requirements.md",
    ]

    for doc_path in required_docs:
        path = Path(doc_path)
        assert path.exists(), f"Required documentation not found: {doc_path}"


def test_root_documentation_exists():
    """Verify root-level documentation files exist."""
    required_files = [
        "README.md",
        "DEPLOYMENT.md",
        "TEMPLATE.md",
        ".env.example",
    ]

    for file_path in required_files:
        path = Path(file_path)
        assert path.exists(), f"Required file not found: {file_path}"


# ---------------------------------------------------------------------------
# Test MCP Server
# ---------------------------------------------------------------------------

def test_mcp_server_importable():
    """Verify MCP server module is importable."""
    from mcp_server.server import mcp

    assert mcp is not None, "MCP server instance not found"


def test_metadata_resources_registered():
    """Verify metadata resource functions exist in server.py."""
    from mcp_server import server

    # Check that metadata resource functions are defined
    expected_functions = [
        "metadata_manifest_resource",
        "metadata_package_resource",
        "metadata_dataset_resource",
        "metadata_schema_resource",
        "metadata_endpoints_resource",
    ]

    for func_name in expected_functions:
        assert hasattr(server, func_name), f"Metadata resource function not found: {func_name}"


def test_core_tools_registered():
    """Verify core tool functions exist in server.py."""
    from mcp_server import server

    # Check that core tool functions are defined
    core_tools = ["health_check", "list_tables", "describe_table_tool", "schema_snapshot"]

    for tool_name in core_tools:
        assert hasattr(server, tool_name), f"Core tool function not found: {tool_name}"


# ---------------------------------------------------------------------------
# Test Project Structure
# ---------------------------------------------------------------------------

def test_project_structure():
    """Verify canonical project structure exists."""
    required_dirs = [
        "mcp_server",
        "tools",
        "skills",
        "resources",
        "metadata",
        "docs",
        "tests",
        "scripts",
    ]

    for dir_name in required_dirs:
        path = Path(dir_name)
        assert path.exists(), f"Required directory not found: {dir_name}"
        assert path.is_dir(), f"{dir_name} is not a directory"


def test_docker_files_exist():
    """Verify Docker deployment files exist."""
    required_files = [
        "Dockerfile",
        "docker-compose.yml",
    ]

    for file_name in required_files:
        path = Path(file_name)
        assert path.exists(), f"Required file not found: {file_name}"


def test_python_package_files_exist():
    """Verify Python package files exist."""
    required_files = [
        "pyproject.toml",
        "mcp_server/__init__.py",
        "tools/__init__.py",
    ]

    for file_name in required_files:
        path = Path(file_name)
        assert path.exists(), f"Required file not found: {file_name}"


# ---------------------------------------------------------------------------
# Test Scripts
# ---------------------------------------------------------------------------

def test_metadata_generation_script_exists():
    """Verify metadata generation script exists."""
    script_path = Path("scripts/generate_metadata_manifest.py")
    assert script_path.exists(), "scripts/generate_metadata_manifest.py not found"


# ---------------------------------------------------------------------------
# Integration Tests
# ---------------------------------------------------------------------------

def test_metadata_manifest_is_current():
    """Verify manifest.json is up-to-date with template.json."""
    template_path = Path("metadata/template.json")
    manifest_path = Path("metadata/manifest.json")

    with open(template_path, 'r', encoding='utf-8') as f:
        template = json.load(f)

    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    # Check that manifest has same structure as template (minus generated field)
    assert manifest.get("package") == template.get("package"), "Manifest package differs from template"
    assert manifest.get("dataset") == template.get("dataset"), "Manifest dataset differs from template"


def test_skills_count_matches_registry():
    """Verify skills count in metadata matches registry."""
    from skills.registry import get_skill_count

    manifest_path = Path("metadata/manifest.json")
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)

    registry_count = get_skill_count()
    manifest_count = manifest.get("endpoints", {}).get("skills", {}).get("count", 0)

    assert registry_count == manifest_count, f"Skills count mismatch: registry={registry_count}, manifest={manifest_count}"


# ---------------------------------------------------------------------------
# Phase 0 Completion Gate
# ---------------------------------------------------------------------------

def test_phase0_complete():
    """Master test: Verify all Phase 0 requirements are met.

    This test serves as the gate for Phase 0 completion.
    If this test passes, the template is ready for deployment.
    """
    # Metadata infrastructure
    assert Path("metadata/template.json").exists()
    assert Path("metadata/manifest.json").exists()
    assert Path("metadata/schema/metadata.schema.json").exists()

    # Skills infrastructure
    assert Path("skills/registry.py").exists()
    assert Path("skills/contracts").exists()
    assert Path("skills/healthcheck/SKILL.md").exists()
    assert Path("skills/example-workflow/SKILL.md").exists()

    # Documentation
    assert Path("docs/infrastructure.md").exists()
    assert Path("docs/mcp_template_spec.md").exists()
    assert Path("docs/skills_architecture.md").exists()
    assert Path("docs/metadata_schema.md").exists()
    assert Path("docs/deployment_workflow.md").exists()
    assert Path("docs/api_examples.md").exists()
    assert Path("docs/troubleshooting.md").exists()
    assert Path("docs/documentation_requirements.md").exists()

    # MCP server
    from mcp_server.server import mcp
    from mcp_server import server
    assert mcp is not None

    # Resources registered (check function exists)
    assert hasattr(server, "metadata_manifest_resource")

    # Skills registry functional
    from skills.registry import SKILLS_REGISTRY, list_skills
    assert len(SKILLS_REGISTRY) >= 2
    assert len(list_skills()) >= 2

    print("\n✅ Phase 0 Complete! Template is ready for deployment.")
