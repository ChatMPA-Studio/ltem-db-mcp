# Tutorial 05: Analysis Skills

**Time:** 50 minutes  
**Difficulty:** Intermediate

## Learning Objectives

- Understand the difference between tools and skills
- Create multi-step analysis workflows
- Document analysis procedures
- Provide interpretation guidance

## Prerequisites

- Completed [Tutorial 04: Statistical Tools](quick-04-statistical-tools.md)
- Understanding of your domain analysis workflows

## What are Analysis Skills?

**Skills are molecules; Tools are atoms.**

- **Tools** = Single-purpose functions (query data, calculate correlation)
- **Skills** = Multi-step workflows that orchestrate tools

Example skill: "MPA Effectiveness Analysis"
1. Get regions data (tool)
2. Calculate biomass by protection level (tool)
3. Run statistical comparison (tool)
4. Interpret results (guidance)

## Step 1: Create Skills Directory Structure

```bash
mkdir -p skills/mpa-effectiveness
mkdir -p skills/contracts
```

## Step 2: Create Your First Skill

Create `skills/mpa-effectiveness/SKILL.md`:

```markdown
---
name: mpa-effectiveness
description: Compare ecological metrics across marine protected areas
version: 1.0.0
---

# MPA Effectiveness Analysis

## Purpose

Evaluate the effectiveness of marine protected areas by comparing biomass, abundance, and species richness across different protection levels.

## Use Cases

- Assess MPA performance
- Compare protected vs unprotected sites
- Support conservation policy decisions

## Workflow

### Step 1: Get Available Regions

**Tool:** `get_regions`  
**Parameters:** None  
**Purpose:** Identify which regions have data

```json
{
  "regions": ["Region A", "Region B", "Region C"]
}
```

### Step 2: Get Biomass by Protection Level

**Tool:** `biomass_by_protection`  
**Parameters:** `{"region": "Region A"}`  
**Purpose:** Calculate mean biomass for each protection category

```json
{
  "data": [
    {"protection": "Fully Protected", "mean_biomass": 250.5, "n": 45},
    {"protection": "Partially Protected", "mean_biomass": 150.2, "n": 38},
    {"protection": "Unprotected", "mean_biomass": 85.3, "n": 52}
  ]
}
```

### Step 3: Statistical Comparison

**Tool:** `group_comparison`  
**Parameters:** 
```json
{
  "table": "observations",
  "value_column": "biomass",
  "group_column": "protection_level",
  "test": "kruskal"
}
```

**Purpose:** Test if differences are statistically significant

### Step 4: Interpret Results

**Interpretation Guide:**

✅ **Significant difference (p < 0.05):**
- Protection level affects biomass
- Fully protected areas show higher biomass
- MPA is effective

⚠️ **No significant difference (p >= 0.05):**
- Insufficient evidence of protection effect
- May need more data or time
- Consider other factors (enforcement, habitat quality)

## Success Criteria

- Data from at least 3 protection levels
- Minimum 20 observations per group
- Statistical test completed
- Clear interpretation provided

## Estimated Duration

45-60 seconds

## Tools Required

- `get_regions`
- `biomass_by_protection`
- `group_comparison`

## Example Output

```json
{
  "analysis": "mpa-effectiveness",
  "region": "Region A",
  "results": {
    "fully_protected": {"mean": 250.5, "n": 45},
    "partially_protected": {"mean": 150.2, "n": 38},
    "unprotected": {"mean": 85.3, "n": 52}
  },
  "statistics": {
    "test": "Kruskal-Wallis",
    "p_value": 0.001,
    "significant": true
  },
  "interpretation": "Fully protected areas show significantly higher biomass (p < 0.001). MPA is effective."
}
```

## Limitations

- Assumes consistent survey methodology
- Does not account for habitat differences
- Temporal trends not included
- Correlation does not imply causation

## See Also

- [Temporal Trends Skill](../temporal-trends/SKILL.md)
- [Community Analysis Skill](../community-analysis/SKILL.md)
```

## Step 3: Register Skill in Registry

Create/update `skills/registry.py`:

```python
"""Skills registry for analysis workflows."""

from typing import Dict, List, Optional

SKILLS_REGISTRY: Dict[str, Dict] = {
    "mpa-effectiveness": {
        "name": "MPA Effectiveness Analysis",
        "description": "Compare ecological metrics across protection levels",
        "version": "1.0.0",
        "inputs_schema": "skills/contracts/mpa_effectiveness.schema.json",
        "outputs_schema": "skills/contracts/mpa_effectiveness.schema.json",
        "estimated_duration": "60 seconds",
        "tools_required": [
            "get_regions",
            "biomass_by_protection",
            "group_comparison"
        ],
        "tags": ["mpa", "comparative", "statistical"]
    }
}

def list_skills() -> List[Dict]:
    """List all available skills."""
    return [
        {"id": skill_id, **skill_info}
        for skill_id, skill_info in SKILLS_REGISTRY.items()
    ]

def get_skill(skill_id: str) -> Optional[Dict]:
    """Get skill metadata by ID."""
    return SKILLS_REGISTRY.get(skill_id)
```

## Step 4: Create Input/Output Schemas

Create `skills/contracts/mpa_effectiveness.schema.json`:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "MPA Effectiveness Analysis Input",
  "type": "object",
  "properties": {
    "region": {
      "type": ["string", "null"],
      "description": "Region to analyze (null = all regions)"
    },
    "metric": {
      "type": "string",
      "enum": ["biomass", "abundance", "richness"],
      "default": "biomass",
      "description": "Ecological metric to compare"
    }
  }
}
```

## Step 5: Document Skill Architecture

Update `skills/README.md`:

```markdown
# Analysis Skills

Structured workflows that orchestrate multiple tools to perform complex analyses.

## Available Skills

| Skill ID | Purpose | Duration | Tools Used |
|----------|---------|----------|------------|
| mpa-effectiveness | Compare protection levels | 60s | 3 |

## Using Skills

Skills are documented workflows, not executable code. To use a skill:

1. Read the `SKILL.md` file
2. Follow the workflow steps
3. Call the listed tools in order
4. Apply the interpretation guidance

## Creating New Skills

See [Skills Architecture](../docs/skills_architecture.md) for design principles.

### Skill Template

```markdown
---
name: skill-id
description: Brief description
version: 1.0.0
---

# Skill Name

## Purpose
What problem does this solve?

## Workflow
Step-by-step procedure

## Interpretation
How to understand results

## Tools Required
List of tools needed
```
```

## Step 6: Best Practices

### 1. Clear Workflow Steps

Each step should specify:
- Tool to call
- Parameters needed
- Expected output
- Purpose of the step

### 2. Interpretation Guidance

Provide clear guidance:
- What results mean
- When to be concerned
- What actions to take

### 3. Success Criteria

Define what makes a successful analysis:
- Minimum data requirements
- Quality checks
- Expected outcomes

### 4. Document Limitations

Be honest about what the skill cannot do:
- Assumptions made
- Confounding factors
- Alternative approaches

## Common Patterns

### Pattern 1: Comparative Analysis

```
1. Get groups
2. Calculate metric for each group
3. Statistical comparison
4. Interpret differences
```

### Pattern 2: Temporal Analysis

```
1. Get time series data
2. Calculate trend
3. Detect change points
4. Interpret trajectory
```

### Pattern 3: Correlation Analysis

```
1. Get paired variables
2. Calculate correlation
3. Test significance
4. Interpret relationship
```

## Testing Skills

Create `tests/test_skills.py`:

```python
"""Tests for skills infrastructure."""

import pytest
from skills.registry import list_skills, get_skill

def test_skills_registry_exists():
    """Verify skills registry is importable."""
    skills = list_skills()
    assert isinstance(skills, list)

def test_mpa_effectiveness_registered():
    """Verify MPA effectiveness skill is registered."""
    skill = get_skill("mpa-effectiveness")
    assert skill is not None
    assert skill["name"] == "MPA Effectiveness Analysis"

def test_skill_has_required_fields():
    """Verify skill has all required metadata."""
    skill = get_skill("mpa-effectiveness")
    required_fields = [
        "name", "description", "version",
        "tools_required", "estimated_duration"
    ]
    for field in required_fields:
        assert field in skill
```

## Next Steps

✅ You now have structured analysis workflows!

**Next tutorial:** [Security Configuration](quick-06-security-config.md)

Learn how to:
- Implement table whitelists
- Create read-only database users
- Add query validation
- Set row limits and timeouts

## Checklist

- [ ] Created skills directory structure
- [ ] Created first skill with SKILL.md
- [ ] Documented workflow steps
- [ ] Provided interpretation guidance
- [ ] Created skills/registry.py
- [ ] Registered skill in registry
- [ ] Created input/output schemas
- [ ] Updated skills/README.md
- [ ] Tested skills infrastructure
- [ ] Skills follow "molecules not atoms" principle

## Resources

- [Skills Architecture](../skills_architecture.md)
- [MCP Skills Specification](https://spec.modelcontextprotocol.io/)
