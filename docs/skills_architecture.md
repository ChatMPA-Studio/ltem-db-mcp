# Skills Architecture

**Purpose:** Define clean semantics for Tools vs Skills to prevent MCP servers from becoming tangled script servers

**Core Principle:** **"Tools are atoms; Skills are molecules"**

**Version:** 1.0.0  
**Last Updated:** February 16, 2026

---

## The Golden Rule

> **Tools stay tiny and reusable. Skills are the only place where "business logic" lives.**

If you enforce only one thing in Phase 0, enforce this rule.

---

## Definitions

### Tools = Atomic, Callable Units

**What they are:**
- Single-responsibility functions
- Exposed over MCP protocol
- Stateless (no hidden global state)
- Return JSON
- Composable building blocks

**What they do:**
- Query database
- Calculate statistics
- Transform data
- Validate inputs
- Return structured results

**What they DON'T do:**
- Multi-step workflows
- Complex orchestration
- Business logic
- Decision trees
- State management

**Example:**
```python
@mcp.tool()
def get_biomass_summary(region: str | None = None) -> str:
    """Get biomass summary statistics.
    
    Single responsibility: Query and summarize biomass data.
    No workflow logic, no orchestration.
    """
    sql = """
        SELECT 
            AVG(biomass) as mean_biomass,
            STDDEV(biomass) as std_biomass,
            COUNT(*) as n_observations
        FROM ltem_historical_database
        WHERE region = %s OR %s IS NULL
    """
    rows = execute_select(sql, params=(region, region))
    return json.dumps({"data": rows})
```

---

### Skills = Structured Workflows

**What they are:**
- Multi-step analysis workflows
- Orchestration of multiple tools
- Validation + execution + interpretation
- Produce stable output contracts
- Return provenance (what ran, with what parameters)

**What they do:**
- Validate inputs
- Call tools in sequence/branching
- Manage intermediate artifacts
- Aggregate results
- Provide interpretation
- Document methodology

**What they DON'T do:**
- Duplicate tool functionality
- Direct database access (use tools instead)
- Expose low-level implementation details

**Example:**
```markdown
# skills/mpa-effectiveness/SKILL.md

## Purpose
Compare biomass across protection levels using statistical tests.

## Workflow

### Step 1: Validate Inputs
- Check region exists
- Verify data availability
- Confirm sample sizes (n ≥ 30)

### Step 2: Get Data
**Tool:** `get_biomass_by_protection`
**Parameters:** `{"region": "La Paz"}`

### Step 3: Statistical Analysis
**Tool:** `compare_groups`
**Parameters:** `{"value_column": "biomass", "group_column": "protection"}`

### Step 4: Interpret Results
- If p < 0.05: "Significant difference exists"
- If p ≥ 0.05: "No significant difference"
- Calculate effect size (MPA biomass / Unprotected biomass)

### Step 5: Return Results
**Output Schema:** `skills/contracts/mpa_effectiveness.schema.json`
```

---

## Non-Negotiable Requirements

### Requirement 1: Every MCP Ships With

#### A. `skills/registry.py`

Lists all available skills with metadata:

```python
"""Skills registry for MCP server."""

from typing import Dict, List

SKILLS_REGISTRY: Dict[str, Dict] = {
    "healthcheck": {
        "name": "Health Check",
        "description": "Minimal validation - calls basic tools to verify server health",
        "version": "1.0.0",
        "inputs_schema": "skills/contracts/healthcheck.schema.json",
        "outputs_schema": "skills/contracts/healthcheck.schema.json",
        "estimated_duration": "5 seconds",
        "tools_required": ["get_regions", "get_summary"]
    },
    "example-workflow": {
        "name": "Example Workflow",
        "description": "Demonstrates tool orchestration with validation and interpretation",
        "version": "1.0.0",
        "inputs_schema": "skills/contracts/example_workflow.schema.json",
        "outputs_schema": "skills/contracts/example_workflow.schema.json",
        "estimated_duration": "30 seconds",
        "tools_required": ["get_summary", "correlation_analysis"]
    },
    "mpa-effectiveness": {
        "name": "MPA Effectiveness Analysis",
        "description": "Compare biomass across protection levels with statistical tests",
        "version": "1.0.0",
        "inputs_schema": "skills/contracts/mpa_effectiveness.schema.json",
        "outputs_schema": "skills/contracts/mpa_effectiveness.schema.json",
        "estimated_duration": "60 seconds",
        "tools_required": ["get_biomass_by_protection", "compare_groups"]
    }
}

def list_skills() -> List[Dict]:
    """List all available skills."""
    return [
        {"id": skill_id, **skill_info}
        for skill_id, skill_info in SKILLS_REGISTRY.items()
    ]

def get_skill(skill_id: str) -> Dict | None:
    """Get skill metadata by ID."""
    return SKILLS_REGISTRY.get(skill_id)
```

#### B. `skills/contracts/`

JSON Schema definitions for each skill:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "MPA Effectiveness Analysis Input",
  "type": "object",
  "required": ["region"],
  "properties": {
    "region": {
      "type": "string",
      "description": "Region to analyze",
      "enum": ["La Paz", "Cabo Pulmo", "Loreto"]
    },
    "year_range": {
      "type": "object",
      "properties": {
        "start": {"type": "integer", "minimum": 1999},
        "end": {"type": "integer", "maximum": 2024}
      }
    },
    "significance_level": {
      "type": "number",
      "default": 0.05,
      "minimum": 0.01,
      "maximum": 0.1
    }
  }
}
```

#### C. At Least 2 Example Skills

**1. `skills/healthcheck/SKILL.md`** - Minimal validation
```markdown
---
name: healthcheck
description: Minimal validation skill
---

# Health Check Skill

## Purpose
Verify server health by calling basic tools.

## Workflow

### Step 1: List Regions
**Tool:** `get_regions`
**Expected:** Returns list of regions

### Step 2: Get Summary
**Tool:** `get_summary`
**Expected:** Returns summary statistics

## Success Criteria
- Both tools return valid JSON
- No errors raised
- Response time < 5 seconds
```

**2. `skills/example-workflow/SKILL.md`** - Orchestration demo
```markdown
---
name: example-workflow
description: Demonstrates tool orchestration
---

# Example Workflow Skill

## Purpose
Demonstrate multi-step analysis with validation and interpretation.

## Workflow

### Step 1: Validate Input
- Check region parameter exists
- Verify region is valid

### Step 2: Get Summary Statistics
**Tool:** `get_summary`
**Parameters:** `{"region": "<user_input>"}`

### Step 3: Analyze Correlation
**Tool:** `correlation_analysis`
**Parameters:** `{"x_column": "temperature", "y_column": "biomass"}`

### Step 4: Interpret Results
- If correlation > 0.7: "Strong positive relationship"
- If correlation < -0.7: "Strong negative relationship"
- Otherwise: "Weak or no relationship"

## Output
```json
{
  "summary": {...},
  "correlation": {...},
  "interpretation": "Strong positive relationship",
  "tools_called": ["get_summary", "correlation_analysis"],
  "execution_time": "1.2s"
}
```
```

---

### Requirement 2: Skills Must Publish

Every skill MUST provide:

1. **name** - Unique identifier (kebab-case)
2. **description** - One-line summary
3. **inputs_schema** - JSON Schema for inputs
4. **outputs_schema** - JSON Schema for outputs
5. **version** - Semantic version (X.Y.Z)
6. **tools_required** - List of tools this skill calls

**Optional but recommended:**
- **estimated_duration** - Expected execution time
- **tags** - Categorization (e.g., ["statistical", "comparative"])
- **methodology** - Link to detailed methodology docs

---

## Recommended Skill Types

Standardize early around these patterns:

### Type 1: Fetch → Clean → Summarize

**Purpose:** Data retrieval and basic summarization

**Pattern:**
1. Fetch data (tool call)
2. Validate completeness
3. Clean/filter (if needed)
4. Summarize statistics
5. Return structured output

**Example:** `data-quality-audit`

---

### Type 2: Query → Aggregate → Plot-spec

**Purpose:** Analysis with visualization specification

**Pattern:**
1. Query data (tool call)
2. Aggregate by grouping variables
3. Calculate statistics
4. Generate Vega-Lite spec (NOT images)
5. Return spec + data

**Important:** Return plot specifications (Vega-Lite, Plotly JSON), NOT rendered images.

**Example:** `temporal-trends`

---

### Type 3: Validate Dataset → Report QA Flags

**Purpose:** Data quality assessment

**Pattern:**
1. Check completeness (missing values)
2. Check consistency (value ranges)
3. Check integrity (foreign keys)
4. Flag issues
5. Return QA report

**Example:** `data-quality-check`

---

### Type 4: Multi-Tool Orchestration

**Purpose:** Complex analysis requiring multiple tools

**Pattern:**
1. Validate inputs
2. Call tool A → intermediate result
3. Call tool B with result from A
4. Call tool C with results from A + B
5. Aggregate and interpret
6. Return comprehensive output

**Example:** `mpa-effectiveness-analysis`

---

## Anti-Patterns (DON'T DO THIS)

### ❌ Anti-Pattern 1: Tools with Business Logic

**WRONG:**
```python
@mcp.tool()
def analyze_mpa_effectiveness(region: str) -> str:
    """This is actually a skill disguised as a tool!"""
    # Step 1: Get data
    biomass_data = get_biomass(region)
    
    # Step 2: Statistical test
    result = kruskal_wallis(biomass_data)
    
    # Step 3: Interpretation
    if result.p_value < 0.05:
        interpretation = "Significant difference"
    else:
        interpretation = "No significant difference"
    
    # Step 4: Effect size
    effect_size = calculate_effect_size(biomass_data)
    
    # This is a multi-step workflow - should be a skill!
    return json.dumps({...})
```

**RIGHT:**
```python
# Tool: Simple, atomic
@mcp.tool()
def get_biomass_by_protection(region: str) -> str:
    """Get biomass data grouped by protection level."""
    sql = "SELECT protection, biomass FROM table WHERE region = %s"
    rows = execute_select(sql, params=(region,))
    return json.dumps({"data": rows})

# Skill: Orchestrates tools
# skills/mpa-effectiveness/SKILL.md
# Calls: get_biomass_by_protection → compare_groups → interpret
```

---

### ❌ Anti-Pattern 2: Skills Accessing Database Directly

**WRONG:**
```markdown
# skills/my-analysis/SKILL.md

## Step 1: Query Database
Execute SQL: `SELECT * FROM table WHERE ...`
```

**RIGHT:**
```markdown
# skills/my-analysis/SKILL.md

## Step 1: Get Data
**Tool:** `get_observations`
**Parameters:** `{"region": "La Paz"}`
```

**Rationale:** Skills orchestrate tools; they don't access infrastructure directly.

---

### ❌ Anti-Pattern 3: No Input/Output Schemas

**WRONG:**
```python
SKILLS_REGISTRY = {
    "my-skill": {
        "name": "My Skill",
        "description": "Does stuff"
        # Missing: inputs_schema, outputs_schema
    }
}
```

**RIGHT:**
```python
SKILLS_REGISTRY = {
    "my-skill": {
        "name": "My Skill",
        "description": "Does stuff",
        "inputs_schema": "skills/contracts/my_skill.schema.json",
        "outputs_schema": "skills/contracts/my_skill.schema.json",
        "version": "1.0.0"
    }
}
```

---

### ❌ Anti-Pattern 4: Skills Without SKILL.md

**WRONG:**
```
skills/
└── my-analysis/
    └── (no SKILL.md file)
```

**RIGHT:**
```
skills/
└── my-analysis/
    └── SKILL.md  # Structured workflow documentation
```

---

## Benefits of This Architecture

### 1. Composability
- Tools can be reused across multiple skills
- New skills can be built from existing tools
- No duplication of query logic

### 2. Testability
- Tools are pure functions → easy to unit test
- Skills are documented workflows → easy to integration test
- Clear contracts via JSON Schema

### 3. Maintainability
- Business logic isolated in skills
- Infrastructure logic isolated in tools
- Changes to workflow don't affect tools

### 4. Discoverability
- `skills/registry.py` provides catalog
- JSON Schemas document contracts
- SKILL.md files explain methodology

### 5. Agent-Agnostic
- Skills work with any AI (Claude, GPT-4, etc.)
- Structured markdown is universally readable
- No vendor lock-in

---

## Migration Guide

### If You Have Existing "Fat Tools"

**Step 1:** Identify multi-step logic in tools
```python
# This tool does too much:
@mcp.tool()
def complex_analysis(...):
    # 50+ lines of workflow logic
```

**Step 2:** Extract atomic operations
```python
# Break into smaller tools:
@mcp.tool()
def get_data(...): ...

@mcp.tool()
def calculate_statistic(...): ...

@mcp.tool()
def compare_groups(...): ...
```

**Step 3:** Create skill to orchestrate
```markdown
# skills/complex-analysis/SKILL.md

## Workflow
1. Call `get_data`
2. Call `calculate_statistic`
3. Call `compare_groups`
4. Interpret results
```

---

## Validation Checklist

Before deploying your MCP:

- [ ] All tools are stateless functions
- [ ] No tool has >50 lines of logic
- [ ] `skills/registry.py` exists and lists all skills
- [ ] `skills/contracts/` has schemas for all skills
- [ ] `skills/healthcheck/` exists
- [ ] `skills/example-workflow/` exists
- [ ] Every skill has SKILL.md file
- [ ] Every skill has input/output schemas
- [ ] No skill accesses database directly
- [ ] All business logic is in skills, not tools

---

## Examples from LTEM MCP

### Good Tool Example
```python
@mcp.tool()
def get_regions() -> str:
    """List all surveyed regions.
    
    Atomic: Single query, single responsibility.
    """
    sql = "SELECT DISTINCT Region FROM ltem_historical_database ORDER BY Region"
    rows = execute_select(sql)
    return json.dumps({"regions": [r['Region'] for r in rows]})
```

### Good Skill Example
```markdown
# skills/ltem-mpa-effectiveness/SKILL.md

## Purpose
Compare biomass across protection levels.

## Workflow

1. **Get regions** → `get_regions`
2. **Get biomass data** → `biomass_by_protection`
3. **Statistical test** → `compare_protection_levels`
4. **Interpret** → Effect size + significance
5. **Return** → Structured JSON with provenance
```

---

## See Also

- [docs/mcp_template_spec.md](mcp_template_spec.md) - Repository structure
- [docs/metadata_schema.md](metadata_schema.md) - Metadata layers
- [skills/README.md](../skills/README.md) - Skills overview

---

**Version:** 1.0.0  
**Last Review:** February 16, 2026
