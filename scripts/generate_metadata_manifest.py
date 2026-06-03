"""Generate metadata manifest from template.

This script reads metadata/template.json and generates metadata/manifest.json
with additional computed fields and validation.

Usage:
    python scripts/generate_metadata_manifest.py
"""

import json
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def count_tools():
    """Count registered MCP tools."""
    tools_dir = PROJECT_ROOT / "tools"
    if not tools_dir.exists():
        return 0
    
    # Count Python files (excluding __init__.py and __pycache__)
    tool_files = [
        f for f in tools_dir.glob("*.py")
        if f.name not in ["__init__.py", "__pycache__"]
    ]
    return len(tool_files)


def count_skills():
    """Count available skills."""
    skills_dir = PROJECT_ROOT / "skills"
    if not skills_dir.exists():
        return 0
    
    # Count directories with SKILL.md files
    skill_dirs = [
        d for d in skills_dir.iterdir()
        if d.is_dir() and (d / "SKILL.md").exists()
    ]
    return len(skill_dirs)


def list_skills():
    """List all skill IDs."""
    skills_dir = PROJECT_ROOT / "skills"
    if not skills_dir.exists():
        return []
    
    skill_dirs = [
        d.name for d in skills_dir.iterdir()
        if d.is_dir() and (d / "SKILL.md").exists()
    ]
    return sorted(skill_dirs)


def generate_manifest():
    """Generate manifest.json from template.json."""
    template_path = PROJECT_ROOT / "metadata" / "template.json"
    manifest_path = PROJECT_ROOT / "metadata" / "manifest.json"
    
    if not template_path.exists():
        print(f"Error: {template_path} not found")
        sys.exit(1)
    
    # Load template
    with open(template_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    # Update computed fields
    tools_count = count_tools()
    skills_count = count_skills()
    skills_list = list_skills()
    
    if "endpoints" in manifest:
        if "tools" in manifest["endpoints"]:
            manifest["endpoints"]["tools"]["count"] = tools_count
        
        if "skills" in manifest["endpoints"]:
            manifest["endpoints"]["skills"]["count"] = skills_count
            manifest["endpoints"]["skills"]["available"] = skills_list
    
    # Update generation timestamp
    manifest["generated"] = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "generator": "generate_metadata_manifest.py",
        "version": "1.0.0"
    }
    
    # Write manifest
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Generated manifest: {manifest_path}")
    print(f"  Tools: {tools_count}")
    print(f"  Skills: {skills_count}")
    print(f"  Skills list: {', '.join(skills_list[:5])}{'...' if len(skills_list) > 5 else ''}")
    
    return manifest


def main():
    """Main entry point."""
    print("Generating metadata manifest...")
    manifest = generate_manifest()
    print("\n✓ Manifest generation complete!")


if __name__ == "__main__":
    main()
