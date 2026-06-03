---
name: example-workflow
description: Demonstrates tool orchestration with validation and interpretation
version: 1.0.0
---

# Example Workflow Skill

## Purpose

Demonstrate multi-step analysis workflow with:
- Input validation
- Tool orchestration
- Result interpretation
- Structured output

**Use cases:**
- Template for creating new skills
- Learning tool orchestration patterns
- Testing skill infrastructure

## Inputs

```json
{
  "region": "La Paz"
}
```

**Validation:**
- `region` must be one of the valid LTEM regions
- See `skills/contracts/example_workflow.schema.json` for full schema

## Workflow

### Step 1: Validate Input

**Check:** Region parameter provided  
**Check:** Region exists in valid regions list

```python
valid_regions = ["Cabo Pulmo", "La Paz", "Loreto", ...]
if region not in valid_regions:
    raise ValueError(f"Invalid region: {region}")
```

### Step 2: Get Regions List

**Tool:** `get_regions`  
**Parameters:** None  
**Purpose:** Verify region exists in database

```json
{
  "regions": ["Cabo Pulmo", "La Paz", "Loreto", ...]
}
```

### Step 3: Get Summary Statistics

**Tool:** `get_summary` (or similar data access tool)  
**Parameters:** `{"region": "La Paz"}`  
**Purpose:** Retrieve basic statistics for the region

```json
{
  "data": {
    "mean_biomass": 125.5,
    "std_biomass": 45.2,
    "n_observations": 1500
  }
}
```

### Step 4: Interpret Results

**Analysis:**
- If `mean_biomass` > 100: "High biomass region"
- If `mean_biomass` 50-100: "Moderate biomass region"
- If `mean_biomass` < 50: "Low biomass region"

**Context:**
- Compare to regional averages
- Note sample size adequacy (n > 100)
- Flag data quality issues

### Step 5: Generate Output

**Structure:**
```json
{
  "region": "La Paz",
  "summary": {
    "mean_biomass": 125.5,
    "std_biomass": 45.2,
    "n_observations": 1500
  },
  "interpretation": "High biomass region",
  "context": {
    "sample_size": "adequate",
    "data_quality": "good"
  },
  "tools_called": ["get_regions", "get_summary"],
  "execution_time": "1.2s",
  "timestamp": "2026-02-16T18:00:00Z"
}
```

## Success Criteria

✅ **Pass if:**
- Input validation succeeds
- All tools return valid data
- Interpretation is generated
- Output matches schema

❌ **Fail if:**
- Invalid region provided
- Tool calls fail
- No data returned
- Timeout (>30 seconds)

## Output Schema

See `skills/contracts/example_workflow.schema.json` for complete output schema.

**Key fields:**
- `region` (string) - Input region
- `summary` (object) - Statistical summary
- `interpretation` (string) - Human-readable interpretation
- `context` (object) - Additional context
- `tools_called` (array) - List of tools used
- `execution_time` (string) - Total execution time

## Error Handling

**Invalid region:**
```json
{
  "error": "Invalid region: InvalidName",
  "valid_regions": ["Cabo Pulmo", "La Paz", ...]
}
```

**Tool failure:**
```json
{
  "error": "Tool call failed: get_summary",
  "details": "Database connection timeout"
}
```

**No data:**
```json
{
  "error": "No data available for region: La Paz",
  "suggestion": "Try a different region or year range"
}
```

## Usage

**Via MCP client:**
```python
result = client.call_skill("example-workflow", {
    "region": "La Paz"
})
print(result["interpretation"])
```

**Via curl:**
```bash
curl http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "skills/call",
    "params": {
      "name": "example-workflow",
      "arguments": {
        "region": "La Paz"
      }
    }
  }'
```

## Customization Guide

To create your own skill based on this example:

### 1. Copy this directory
```bash
cp -r skills/example-workflow skills/my-analysis
```

### 2. Update SKILL.md
- Change name and description
- Define your workflow steps
- Update tool calls
- Define interpretation logic

### 3. Create contract schema
```bash
cp skills/contracts/example_workflow.schema.json \
   skills/contracts/my_analysis.schema.json
# Edit to match your inputs/outputs
```

### 4. Register in registry.py
```python
"my-analysis": {
    "name": "My Analysis",
    "description": "...",
    "version": "1.0.0",
    "inputs_schema": "skills/contracts/my_analysis.schema.json",
    "outputs_schema": "skills/contracts/my_analysis.schema.json",
    "tools_required": ["tool1", "tool2"]
}
```

### 5. Test
```bash
pytest tests/test_skills.py::test_my_analysis -v
```

## Best Practices

1. **Validate inputs early** - Fail fast on invalid inputs
2. **Document tool calls** - List all tools used
3. **Provide interpretation** - Don't just return raw data
4. **Handle errors gracefully** - Return structured error messages
5. **Include provenance** - Track what ran and when
6. **Keep it focused** - One skill = one analysis workflow

## See Also

- [skills/registry.py](../registry.py) - Skills catalog
- [docs/skills_architecture.md](../../docs/skills_architecture.md) - Skills design principles
- [docs/api_examples.md](../../docs/api_examples.md) - API usage examples
