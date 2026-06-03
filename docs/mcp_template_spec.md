# MCP Template Specification

**Purpose:** Define the canonical repository structure and non-negotiable rules for MCP servers

**Version:** 1.0.0  
**Last Updated:** February 16, 2026

---

## Canonical Structure

```
mcp-name/
│
├── mcp_server/              # Core server infrastructure (DO NOT MODIFY STRUCTURE)
│   ├── server.py            # FastMCP server + resources
│   ├── config.py            # Pydantic settings
│   ├── db.py                # Database connection + execute_select
│   ├── security.py          # Table whitelist + query validation
│   ├── schema.py            # Schema discovery
│   └── __main__.py          # Entry point
│
├── tools/                   # MCP tools (DOMAIN-SPECIFIC, REPLACE ALL)
│   ├── __init__.py          # Auto-discovery (KEEP)
│   ├── data_access.py       # Basic queries (KEEP AS TEMPLATE)
│   └── your_domain.py       # Your tools (ADD)
│
├── skills/                  # Analysis workflows (DOMAIN-SPECIFIC, REPLACE ALL)
│   ├── README.md            # Skills overview (UPDATE)
│   ├── registry.py          # Skills catalog (REQUIRED)
│   ├── contracts/           # Parameter schemas (REQUIRED)
│   │   └── *.schema.json
│   ├── healthcheck/         # Minimal validation (REQUIRED)
│   │   └── SKILL.md
│   ├── example-workflow/    # Orchestration demo (REQUIRED)
│   │   └── SKILL.md
│   └── your-skill/          # Your skills (ADD)
│       └── SKILL.md
│
├── resources/               # Read-only assets (DOMAIN-SPECIFIC)
│   └── data_dictionary.md   # Schema documentation (UPDATE)
│
├── metadata/                # Metadata for discoverability (REQUIRED)
│   ├── template.json        # Human-edited metadata (UPDATE)
│   ├── manifest.json        # Auto-generated (DO NOT EDIT)
│   ├── schema/              # JSON Schema definitions (KEEP)
│   │   └── metadata.schema.json
│   └── README.md            # Usage guide (KEEP)
│
├── docs/                    # Documentation (UPDATE ALL)
│   ├── infrastructure.md    # Hosting + routing (UPDATE FOR YOUR SETUP)
│   ├── mcp_template_spec.md # This file (KEEP)
│   ├── skills_architecture.md # Tools vs skills (KEEP)
│   ├── metadata_schema.md   # Metadata layers (KEEP)
│   ├── deployment_workflow.md # CI/CD (UPDATE FOR YOUR SETUP)
│   ├── api_examples.md      # curl examples (UPDATE)
│   ├── troubleshooting.md   # Common issues (UPDATE)
│   └── user-guides/         # MCP development tutorials (KEEP)
│
├── tests/                   # Test suite (UPDATE)
│   ├── test_smoke.py        # Basic connectivity (UPDATE)
│   ├── test_tools.py        # Tool tests (ADD)
│   ├── test_security.py     # Security tests (KEEP)
│   └── test_e2e.py          # End-to-end (REQUIRED)
│
├── scripts/                 # Utility scripts (KEEP + ADD)
│   ├── deploy.sh            # Deployment script (UPDATE)
│   ├── validate_tools.py    # Tool validation (KEEP)
│   └── generate_metadata_manifest.py # Metadata generation (KEEP)
│
├── Dockerfile               # Container definition (USUALLY NO CHANGES)
├── docker-compose.yml       # Compose setup (UPDATE CONTAINER NAME)
├── pyproject.toml           # Package definition (UPDATE)
├── .env.example             # Environment template (UPDATE)
├── .gitignore               # Git ignore (KEEP)
├── README.md                # Main documentation (REWRITE)
├── DEPLOYMENT.md            # Deployment guide (UPDATE)
├── TEMPLATE.md              # Template usage guide (KEEP)
├── CHANGELOG.md             # Version history (START FRESH)
└── LICENSE                  # License file (UPDATE)
```

---

## Hard Rules

### Rule 1: tools/ MUST Contain Only Stateless Functions

**✅ CORRECT:**
```python
# tools/analysis.py
def calculate_summary(region: str | None = None) -> str:
    """Stateless function - no global state."""
    sql = "SELECT * FROM table WHERE region = %s"
    rows = execute_select(sql, params=(region,))
    return json.dumps({"data": rows})
```

**❌ WRONG:**
```python
# tools/analysis.py
CACHE = {}  # ❌ Global state

def calculate_summary(region: str | None = None) -> str:
    if region in CACHE:  # ❌ Stateful behavior
        return CACHE[region]
    # ...
```

**Rationale:** Tools must be pure functions for predictability and testability.

---

### Rule 2: skills/ MUST Have Named Entrypoints

**Required Files:**
- `skills/registry.py` - Catalog of all skills
- `skills/contracts/` - Parameter schemas for each skill
- At least 2 example skills: `healthcheck/` and `example-workflow/`

**✅ CORRECT:**
```python
# skills/registry.py
SKILLS_REGISTRY = {
    "healthcheck": {
        "name": "Health Check",
        "description": "Minimal validation",
        "version": "1.0.0",
        "inputs_schema": "skills/contracts/healthcheck.schema.json",
        "outputs_schema": "skills/contracts/healthcheck.schema.json"
    },
    "your-analysis": {
        "name": "Your Analysis",
        "description": "Domain-specific workflow",
        "version": "1.0.0",
        "inputs_schema": "skills/contracts/your_analysis.schema.json",
        "outputs_schema": "skills/contracts/your_analysis.schema.json"
    }
}
```

**❌ WRONG:**
```python
# No registry.py file
# Skills scattered without catalog
# No schema definitions
```

**Rationale:** Skills must be discoverable and have clear contracts.

---

### Rule 3: resources/ MUST Be Safe to Expose

**✅ SAFE:**
- Database schema documentation
- Data dictionaries
- Example queries
- Methodology guides
- Public metadata

**❌ UNSAFE:**
- API keys
- Database credentials
- Internal IP addresses
- User data
- Proprietary algorithms

**Enforcement:**
```python
# All resources exposed via MCP resources
@mcp.resource("domain://schema/tables")
def get_schema() -> str:
    # Only return public information
    return schema_documentation
```

**Rationale:** Resources are read-only and publicly accessible via MCP protocol.

---

### Rule 4: metadata/ MUST Include Required Files

**Required:**
1. `metadata/template.json` - Human-edited metadata
2. `metadata/manifest.json` - Auto-generated from template
3. `metadata/schema/` - JSON Schema definitions
4. `metadata/README.md` - Usage documentation

**Validation:**
```bash
# Validate template against schema
python -m jsonschema -i metadata/template.json metadata/schema/metadata.schema.json
```

**Update Process:**
1. Edit `metadata/template.json`
2. Run `python scripts/generate_metadata_manifest.py`
3. Commit both `template.json` and `manifest.json`

**Rationale:** Metadata enables CRAN-style discoverability and documentation.

---

## README.md Requirements

Every MCP repository MUST include a README.md with:

### 1. What It Is
```markdown
# Your Domain MCP Server

Brief description of what data/analysis this MCP provides.
```

### 2. How to Run Locally
```markdown
## Quick Start

\`\`\`bash
# 1. Clone and setup
git clone https://github.com/your-org/your-mcp.git
cd your-mcp

# 2. Configure
cp .env.example .env
# Edit .env with your database credentials

# 3. Run
docker compose up
\`\`\`
```

### 3. How to Deploy
```markdown
## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment instructions.
```

### 4. How to Call It
```markdown
## Usage

### List Tools
\`\`\`bash
curl http://localhost:8000/mcp \\
  -H "Content-Type: application/json" \\
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
\`\`\`

### Call a Tool
\`\`\`bash
curl http://localhost:8000/mcp \\
  -H "Content-Type: application/json" \\
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"your_tool","arguments":{}}}'
\`\`\`
```

### 5. Auth Expectations
```markdown
## Authentication

- **Phase 0:** Basic Auth at reverse proxy (Caddy)
- **Phase 2:** OAuth/JWT (planned)

No authentication required when running locally.
```

---

## DEPLOYMENT.md Requirements

Every MCP repository MUST include a DEPLOYMENT.md with **executable instructions**:

### ✅ CORRECT (Executable):
```markdown
## Deploy to Production

1. SSH to server:
   \`\`\`bash
   ssh user@server.com
   \`\`\`

2. Navigate to project:
   \`\`\`bash
   cd /opt/your-mcp
   \`\`\`

3. Pull latest code:
   \`\`\`bash
   git pull origin main
   \`\`\`

4. Rebuild container:
   \`\`\`bash
   docker compose build
   \`\`\`

5. Restart service:
   \`\`\`bash
   docker compose up -d
   \`\`\`

6. Verify:
   \`\`\`bash
   docker compose ps
   docker compose logs --tail=50
   \`\`\`
```

### ❌ WRONG (Narrative):
```markdown
## Deployment

The deployment process involves connecting to the server,
pulling the latest code, rebuilding the Docker image, and
restarting the service. You should verify that everything
is working correctly after deployment.
```

**Rationale:** DEPLOYMENT.md must be copy-paste executable, not a narrative description.

---

## File Modification Guidelines

### KEEP (Infrastructure)
- `mcp_server/` - All files
- `Dockerfile` - Usually no changes
- `tests/test_security.py` - Security tests
- `scripts/validate_tools.py` - Tool validation
- `scripts/generate_metadata_manifest.py` - Metadata generation
- `docs/mcp_template_spec.md` - This file
- `docs/skills_architecture.md` - Tools vs skills
- `docs/metadata_schema.md` - Metadata layers
- `docs/user-guides/` - MCP development tutorials
- `TEMPLATE.md` - Template usage guide

### UPDATE (Configuration)
- `mcp_server/server.py` - Line 24: Change server name
- `mcp_server/config.py` - Lines 77-81: Rename env var prefix
- `mcp_server/security.py` - Lines 6-10: Update ALLOWED_TABLES
- `docker-compose.yml` - Container name
- `pyproject.toml` - Name, version, description
- `.env.example` - Variable names and defaults
- `metadata/template.json` - All fields

### REPLACE (Domain-Specific)
- `tools/*.py` - All except `__init__.py` and `data_access.py`
- `skills/*/` - All except `registry.py`, `contracts/`, `healthcheck/`, `example-workflow/`
- `resources/` - All content
- `README.md` - Complete rewrite
- `CHANGELOG.md` - Start fresh with v1.0.0

### ADD (Your Content)
- `tools/your_domain.py` - Your tools
- `skills/your-skill/` - Your skills
- `tests/test_tools.py` - Your tool tests
- `docs/api_examples.md` - Your examples

---

## Validation Checklist

Before committing your MCP template:

### Structure
- [ ] `mcp_server/` unchanged
- [ ] `tools/__init__.py` exists
- [ ] `skills/registry.py` exists
- [ ] `skills/contracts/` exists
- [ ] `metadata/template.json` exists
- [ ] `metadata/manifest.json` generated

### Documentation
- [ ] `README.md` includes all 5 required sections
- [ ] `DEPLOYMENT.md` has executable instructions
- [ ] `docs/infrastructure.md` updated for your setup
- [ ] `docs/api_examples.md` has curl examples

### Metadata
- [ ] `metadata/template.json` validated against schema
- [ ] `metadata/manifest.json` generated successfully
- [ ] Metadata exposed as MCP resource

### Skills
- [ ] `skills/registry.py` lists all skills
- [ ] `skills/contracts/` has schemas for all skills
- [ ] `skills/healthcheck/` exists
- [ ] `skills/example-workflow/` exists

### Testing
- [ ] `tests/test_smoke.py` updated for your database
- [ ] `tests/test_e2e.py` exists and passes
- [ ] All tests pass: `pytest tests/ -v`

### Security
- [ ] `.env` in `.gitignore`
- [ ] No secrets in code
- [ ] `ALLOWED_TABLES` configured
- [ ] Read-only database user created

---

## Common Mistakes

### Mistake 1: Modifying mcp_server/ Structure
**Problem:** Changing file organization in `mcp_server/`  
**Fix:** Keep `mcp_server/` structure unchanged. Only update content.

### Mistake 2: No Skills Registry
**Problem:** Skills scattered without `registry.py`  
**Fix:** Create `skills/registry.py` and catalog all skills.

### Mistake 3: Hardcoded Secrets
**Problem:** Database credentials in code  
**Fix:** Use `.env` file and environment variables.

### Mistake 4: Narrative DEPLOYMENT.md
**Problem:** Deployment guide is descriptive, not executable  
**Fix:** Write step-by-step bash commands.

### Mistake 5: Missing Metadata
**Problem:** No `metadata/` directory  
**Fix:** Create metadata infrastructure and expose via MCP resources.

---

## Version History

- **1.0.0** (2026-02-16) - Initial specification
  - Canonical structure defined
  - Hard rules established
  - Documentation requirements specified

---

## See Also

- [docs/skills_architecture.md](skills_architecture.md) - Tools vs Skills semantics
- [docs/metadata_schema.md](metadata_schema.md) - Metadata layers
- [docs/infrastructure.md](infrastructure.md) - Hosting + routing
- [TEMPLATE.md](../TEMPLATE.md) - Template usage guide
