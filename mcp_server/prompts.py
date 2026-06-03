"""Auto-discover skills and register them as MCP prompts.

Reads every skills/<name>/SKILL.md file, parses its YAML frontmatter,
and registers it as an MCP prompt so any remote client can discover
the guided analytical workflows.

If a skill directory contains a references/ subdirectory, all .md files
within it are appended to the prompt body as supplementary context.
"""

import logging
import re
from pathlib import Path

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"

# ---------------------------------------------------------------------------
# YAML frontmatter parser (minimal, avoids pyyaml dependency)
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
	"""Return (metadata_dict, body) from a SKILL.md file."""
	m = _FRONTMATTER_RE.match(text)
	if not m:
		return {}, text

	meta: dict[str, str] = {}
	for line in m.group(1).splitlines():
		if ":" in line:
			key, _, value = line.partition(":")
			meta[key.strip()] = value.strip()

	body = text[m.end():]
	return meta, body


# ---------------------------------------------------------------------------
# Reference file loader
# ---------------------------------------------------------------------------

def _load_references(skill_dir: Path) -> str:
	"""Concatenate all .md files under skill_dir/references/."""
	refs_dir = skill_dir / "references"
	if not refs_dir.is_dir():
		return ""

	parts: list[str] = []
	for ref_file in sorted(refs_dir.glob("*.md")):
		content = ref_file.read_text(encoding="utf-8")
		parts.append(f"\n\n---\n## Reference: {ref_file.stem}\n\n{content}")

	return "".join(parts)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def discover_prompts(mcp: FastMCP) -> None:
	"""Find all skills/*/SKILL.md and register each as an MCP prompt."""
	if not SKILLS_DIR.is_dir():
		logger.warning("skills/ directory not found at %s", SKILLS_DIR)
		return

	count = 0
	for skill_file in sorted(SKILLS_DIR.glob("*/SKILL.md")):
		skill_dir = skill_file.parent
		skill_id = skill_dir.name

		try:
			raw = skill_file.read_text(encoding="utf-8")
			meta, body = _parse_frontmatter(raw)

			name = meta.get("name", skill_id)
			description = meta.get("description", f"Guided workflow: {name}")

			# Append reference materials if present
			refs = _load_references(skill_dir)
			full_body = body.strip() + refs

			# Register as MCP prompt using closure to capture full_body
			_register_prompt(mcp, name, description, full_body)
			count += 1
			logger.info("Registered prompt: %s", name)

		except Exception:
			logger.exception("Failed to register prompt from %s", skill_file)

	logger.info("Registered %d prompts from skills/", count)


def _register_prompt(
	mcp: FastMCP, name: str, description: str, body: str
) -> None:
	"""Register a single skill as an MCP prompt."""

	@mcp.prompt(name=name, description=description)
	def _prompt() -> str:
		return body

	# Override the generic function name for debugging
	_prompt.__name__ = f"prompt_{name.replace('-', '_')}"
	_prompt.__qualname__ = _prompt.__name__
