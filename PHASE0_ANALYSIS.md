# Phase 0 Template Completion - Gap Analysis & Implementation Plan

**Date:** February 16, 2026  
**Repository:** ltem-db-mcp  
**Goal:** Finalize MCP package template for GitHub commit and droplet deployment

---

## 1. Current Repository Structure Analysis

### ✅ What We Have (Quality Improvements)

```
ltem-db-mcp/
├── mcp_server/                    # Core server infrastructure
│   ├── server.py                  # FastMCP server with resources
│   ├── config.py                  # Pydantic settings
│   ├── db.py                      # Database connection + execute_select
│   ├── security.py                # Table whitelist + query validation
│   ├── schema.py                  # Schema discovery
│   └── __main__.py                # Entry point
│
├── tools/                         # ✅ At root level (11 modules)
│   ├── __init__.py                # Auto-discovery
│   ├── data_access.py             # Basic queries
│   ├── biomass.py                 # Domain-specific
│   └── ... (8 more LTEM tools)
│
├── skills/                        # ✅ At root level (11 skills)
│   ├── README.md                  # Skills overview
│   ├── ltem-mpa-effectiveness/
│   │   └── SKILL.md               # Structured workflow
│   └── ... (10 more LTEM skills)
│
├── resources/                     # ✅ At root level
│   └── data_dictionary.md
│
├── docs/                          # ✅ Comprehensive documentation
│   ├── user-guides/               # ✅ 8 MCP dev tutorials + HTML
│   ├── TOOL_INVENTORY.md
│   ├── VALIDATION_REPORT.md
│   ├── skills-reference.md
│   └── ltem-scripts/              # R analysis scripts
│
├── tests/                         # ✅ Test infrastructure
│   ├── test_smoke.py
│   └── ... (5 more test files)
│
├── scripts/                       # ✅ Utility scripts
│   ├── deploy.sh
│   ├── validate_tools.py
│   └── generate_tutorial_docs.py
│
├── TEMPLATE.md                    # ✅ Template usage guide
├── DEPLOYMENT.md                  # ✅ Deployment instructions
├── README.md                      # ✅ Comprehensive README
├── CHANGELOG.md                   # ✅ Version history
├── Dockerfile                     # ✅ Production-ready
├── docker-compose.yml             # ✅ Compose setup
├── pyproject.toml                 # ✅ Package definition
└── .env.example                   # ✅ Environment template
```

### ❌ What's Missing (ChatGPT Phase 0 Requirements)

#### 1. Metadata Infrastructure
- ❌ `metadata/` directory (root level)
- ❌ `metadata/template.json`
- ❌ `metadata/schema/` (JSON Schema definitions)
- ❌ `metadata/manifest.json` (generated)

#### 2. Documentation Files
- ❌ `docs/infrastructure.md` (hosting + routing + auth)
- ❌ `docs/mcp_template_spec.md` (canonical structure)
- ❌ `docs/skills_architecture.md` (tools vs skills contract)
- ❌ `docs/metadata_schema.md` (metadata layers)
- ❌ `docs/deployment_workflow.md` (CI/CD rules)
- ❌ `docs/api_examples.md` (curl examples)
- ❌ `docs/troubleshooting.md` (common issues)
- ❌ `docs/documentation_requirements.md` (template checklist)

#### 3. Skills Infrastructure
- ❌ `skills/registry.py` (skills registry)
- ❌ `skills/contracts/` (parameter schemas)
- ❌ Example skills: `healthcheck`, `example_workflow`

#### 4. End-to-End Test
- ❌ `tests/test_e2e.py` (initialize + tool + skill + metadata)

---

## 2. Structure Decision: Keep Current Layout

**Decision:** ✅ **Keep tools/, skills/, resources/ at root level**

**Rationale:**
1. **Current structure works** - Auto-discovery functioning correctly
2. **Separation of concerns** - Clear distinction between:
   - `mcp_server/` = infrastructure (server, config, db, security)
   - `tools/` = domain-specific MCP tools
   - `skills/` = domain-specific workflows
   - `resources/` = domain-specific assets
3. **Template clarity** - Easier for users to identify what to replace
4. **No breaking changes** - Server already deployed and working

**ChatGPT structure adjustment:**
- Original suggestion: `mcp_server/tools/`, `mcp_server/skills/`
- Our implementation: `tools/`, `skills/` at root
- **Both are valid** - We'll document our choice in `mcp_template_spec.md`

---

## 3. Phase 0 Implementation Plan

### Priority 1: Metadata Infrastructure (CRITICAL)

**Goal:** Enable CRAN-style discoverability

#### Step 1.1: Create metadata directory structure
```bash
metadata/
├── template.json          # Human-edited starter
├── schema/                # JSON Schema definitions
│   ├── package.schema.json
│   ├── dataset.schema.json
│   ├── tool.schema.json
│   └── skill.schema.json
└── manifest.json          # Generated (auto-created)
```

#### Step 1.2: Define metadata/template.json
```json
{
  "package": {
    "name": "ltem-db-mcp",
    "version": "1.2.0",
    "description": "Long-Term Ecological Monitoring Database MCP Server",
    "maintainer": "CBMC",
    "license": "MIT",
    "repository": "https://github.com/your-org/ltem-db-mcp"
  },
  "dataset": {
    "title": "LTEM Historical Database",
    "description": "20+ years of reef fish monitoring data",
    "keywords": ["ecology", "marine", "monitoring", "MPA"],
    "spatial_coverage": "Gulf of California",
    "temporal_coverage": "1999-2024",
    "publisher": "CBMC"
  },
  "endpoints": {
    "tools_count": 59,
    "skills_count": 11,
    "resources_count": 5
  }
}
```

#### Step 1.3: Expose metadata as MCP resource
Add to `mcp_server/server.py`:
```python
@mcp.resource("ltem://metadata/manifest")
def get_metadata_manifest() -> str:
    """Get MCP server metadata manifest."""
    manifest_path = Path(__file__).parent.parent / "metadata" / "manifest.json"
    if manifest_path.exists():
        return manifest_path.read_text()
    return json.dumps({"error": "Manifest not found"})
```

### Priority 2: Skills Infrastructure (CRITICAL)

#### Step 2.1: Create skills/registry.py
```python
"""Skills registry for LTEM MCP server."""

from typing import Dict, List

SKILLS_REGISTRY: Dict[str, Dict] = {
    "ltem-mpa-effectiveness": {
        "name": "MPA Effectiveness Analysis",
        "description": "Compare biomass across protection levels",
        "version": "1.0.0",
        "inputs_schema": "skills/ltem-mpa-effectiveness/inputs.schema.json",
        "outputs_schema": "skills/ltem-mpa-effectiveness/outputs.schema.json"
    },
    # ... register all 11 skills
}

def list_skills() -> List[Dict]:
    """List all available skills."""
    return [
        {"id": skill_id, **skill_info}
        for skill_id, skill_info in SKILLS_REGISTRY.items()
    ]
```

#### Step 2.2: Create skills/contracts/ directory
```bash
skills/contracts/
├── mpa_effectiveness.schema.json
├── temporal_trends.schema.json
└── ... (schemas for all skills)
```

#### Step 2.3: Add example skills
- `skills/healthcheck/` - Minimal tool call validation
- `skills/example-workflow/` - Demonstrates orchestration

### Priority 3: Core Documentation Files (CRITICAL)

#### File 1: docs/infrastructure.md
**Content:**
- Current hosting (DigitalOcean Droplet, Ubuntu 24.04)
- Network model (Caddy → Docker network)
- Routing standard (subpath rules)
- Auth standard (Phase 0: Basic Auth at Caddy)
- Environment variables (secrets management)
- Logs + observability
- AWS migration notes

#### File 2: docs/mcp_template_spec.md
**Content:**
- Canonical structure (with our root-level tools/skills choice)
- Hard rules:
  - tools/ MUST be stateless
  - skills/ MUST have registry
  - resources/ MUST be safe to expose
  - metadata/ MUST include schemas
- README.md requirements
- DEPLOYMENT.md requirements

#### File 3: docs/skills_architecture.md
**Content:**
- **"Tools are atoms; Skills are molecules"**
- Tools = atomic, callable units (single responsibility)
- Skills = structured workflows (validate → call → manage → produce)
- Non-negotiable requirements:
  - skills/registry.py
  - skills/contracts/
  - At least 2 example skills
- Skill types to standardize

#### File 4: docs/metadata_schema.md
**Content:**
- 4 metadata layers:
  1. Package metadata
  2. Dataset metadata (DCAT-like)
  3. Schema metadata
  4. Provenance + analytical metadata
- Exposure via MCP resources
- JSON Schema definitions

#### File 5: docs/deployment_workflow.md
**Content:**
- Baseline workflow (Phase 0)
- GitHub = source of truth
- Versioning rules (main, tags vX.Y.Z)
- Manual deploy steps
- Semi-automated deploy (GitHub Actions → GHCR)
- Rollback protocol

#### File 6: docs/api_examples.md
**Content:**
- curl examples for:
  - initialize
  - tools/list
  - tools/call
  - resources/list
  - resources/read
  - SSE usage

#### File 7: docs/troubleshooting.md
**Content:**
- Auth failures
- 502/404 routing issues
- Container health problems
- Environment variables missing
- Database connectivity
- Common error messages

#### File 8: docs/documentation_requirements.md
**Content:**
- Minimum docs checklist
- README.md requirements
- DEPLOYMENT.md requirements
- Skills usage docs
- API examples
- Troubleshooting guide

### Priority 4: End-to-End Test (HIGH)

#### Create tests/test_e2e.py
```python
"""End-to-end test for MCP server."""

def test_full_workflow():
    """Test complete MCP workflow."""
    # 1. Initialize
    # 2. List tools
    # 3. Call a tool
    # 4. List skills (via registry)
    # 5. Fetch metadata resource
    # 6. Verify responses
```

### Priority 5: Template Completeness Validation (HIGH)

#### Create docs/template_complete.md
**Phase 0 Checklist:**
- [ ] Infrastructure doc exists
- [ ] Template spec frozen
- [ ] Skills architecture enforced
- [ ] Metadata schema defined
- [ ] Docker/Compose works with .env only
- [ ] Deployment guide validated
- [ ] E2E test exists and passes

---

## 4. Implementation Order

### Week 1: Core Infrastructure
1. ✅ Create metadata/ directory structure
2. ✅ Write metadata/template.json
3. ✅ Create JSON schemas (metadata/schema/)
4. ✅ Expose metadata as MCP resource
5. ✅ Create skills/registry.py
6. ✅ Create skills/contracts/

### Week 2: Documentation
7. ✅ Write docs/infrastructure.md
8. ✅ Write docs/mcp_template_spec.md
9. ✅ Write docs/skills_architecture.md
10. ✅ Write docs/metadata_schema.md
11. ✅ Write docs/deployment_workflow.md
12. ✅ Write docs/api_examples.md
13. ✅ Write docs/troubleshooting.md
14. ✅ Write docs/documentation_requirements.md

### Week 3: Testing & Validation
15. ✅ Create tests/test_e2e.py
16. ✅ Run all tests
17. ✅ Create docs/template_complete.md
18. ✅ Validate checklist
19. ✅ Update TEMPLATE.md
20. ✅ Update README.md

### Week 4: Deployment
21. ✅ GitHub commit
22. ✅ Droplet deployment
23. ✅ Validation on production
24. ✅ Documentation review

---

## 5. Key Decisions & Rationale

### Decision 1: Keep tools/skills at root level
**Rationale:** Clear separation, easier for template users, no breaking changes

### Decision 2: Add metadata infrastructure
**Rationale:** Required for Phase 0, enables discoverability, aligns with CRAN-style goals

### Decision 3: Formalize skills architecture
**Rationale:** "Tools are atoms; Skills are molecules" - prevents tangled script servers

### Decision 4: Comprehensive documentation
**Rationale:** Template must be self-documenting, reduce support burden

### Decision 5: E2E testing
**Rationale:** Validate full MCP protocol compliance before deployment

---

## 6. Success Criteria

Phase 0 is complete when:

1. ✅ All 8 documentation files exist and are comprehensive
2. ✅ Metadata infrastructure functional (template.json, schemas, manifest)
3. ✅ Skills registry implemented with contracts
4. ✅ E2E test passes
5. ✅ Template completeness checklist validated
6. ✅ Docker deployment works with only .env changes
7. ✅ Deployed to droplet and accessible
8. ✅ All MCP protocol endpoints functional

---

## 7. Timeline Estimate

- **Metadata Infrastructure:** 4-6 hours
- **Skills Infrastructure:** 3-4 hours
- **Documentation (8 files):** 8-12 hours
- **Testing & Validation:** 2-3 hours
- **Deployment & Review:** 2-3 hours

**Total:** 19-28 hours (2.5-3.5 days of focused work)

---

## 8. Next Immediate Actions

1. Create metadata/ directory structure
2. Write metadata/template.json
3. Create JSON schemas
4. Write docs/infrastructure.md
5. Write docs/mcp_template_spec.md

**Start with:** Metadata infrastructure (highest priority for discoverability)
