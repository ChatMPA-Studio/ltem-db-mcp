# Documentation Requirements

**Purpose:** Define minimum documentation standards for MCP server templates

**Version:** 1.0.0  
**Last Updated:** February 16, 2026

---

## Overview

Every MCP server repository MUST include comprehensive documentation. This ensures:

1. **Discoverability** - Users can find and understand your MCP
2. **Usability** - Developers can deploy and use your MCP
3. **Maintainability** - Future developers can modify and extend your MCP
4. **Reproducibility** - Deployments are consistent and reliable

---

## Required Documentation Files

### 1. README.md (Root Level)

**Purpose:** First point of contact for users

**Required Sections:**

#### A. Project Overview
```markdown
# Your MCP Server Name

Brief description (1-2 sentences) of what this MCP provides.

**Data Source:** [e.g., MySQL database with ecological monitoring data]  
**Tools:** [e.g., 59 query and analysis tools]  
**Skills:** [e.g., 11 structured analysis workflows]
```

#### B. Quick Start
```markdown
## Quick Start

\`\`\`bash
# 1. Clone repository
git clone https://github.com/your-org/your-mcp.git
cd your-mcp

# 2. Configure environment
cp .env.example .env
# Edit .env with your database credentials

# 3. Run with Docker
docker compose up

# 4. Test
curl http://localhost:8000/mcp \\
  -H "Content-Type: application/json" \\
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}'
\`\`\`
```

#### C. Features
```markdown
## Features

- ✅ 59 MCP tools for database queries
- ✅ 11 structured analysis skills
- ✅ Statistical analysis (scipy/numpy)
- ✅ Docker deployment ready
- ✅ Comprehensive test suite
- ✅ Production-ready security
```

#### D. Documentation Links
```markdown
## Documentation

- [Deployment Guide](DEPLOYMENT.md) - Production deployment
- [API Examples](docs/api_examples.md) - curl examples
- [Skills Reference](docs/skills-reference.md) - Analysis workflows
- [Troubleshooting](docs/troubleshooting.md) - Common issues
```

#### E. Requirements
```markdown
## Requirements

- Python 3.10+
- Docker + Docker Compose
- MySQL 8.0+ database
- (Optional) Caddy for reverse proxy
```

#### F. License
```markdown
## License

MIT License - see [LICENSE](LICENSE) file
```

**Validation:**
- [ ] All 6 sections present
- [ ] Quick Start is copy-paste executable
- [ ] Links to other docs work
- [ ] License file exists

---

### 2. DEPLOYMENT.md (Root Level)

**Purpose:** Executable deployment instructions

**Required Sections:**

#### A. Prerequisites
```markdown
## Prerequisites

- Server with Ubuntu 24.04 LTS
- Docker and Docker Compose installed
- MySQL database accessible from server
- (Optional) Domain name for HTTPS
```

#### B. Step-by-Step Deployment
```markdown
## Deployment Steps

### 1. Clone Repository

\`\`\`bash
ssh user@server.com
cd /opt
git clone https://github.com/your-org/your-mcp.git
cd your-mcp
\`\`\`

### 2. Configure Environment

\`\`\`bash
cp .env.example .env
nano .env
# Update database credentials
\`\`\`

### 3. Build and Start

\`\`\`bash
docker compose build
docker compose up -d
\`\`\`

### 4. Verify

\`\`\`bash
docker compose ps
docker compose logs --tail=50
curl http://localhost:8000/health
\`\`\`
```

#### C. Reverse Proxy Setup (Optional)
```markdown
## Reverse Proxy (Caddy)

\`\`\`bash
# Install Caddy
sudo apt install caddy

# Configure Caddyfile
sudo nano /etc/caddy/Caddyfile
# Add handle block for your MCP

# Reload
sudo systemctl reload caddy
\`\`\`
```

#### D. Rollback Procedure
```markdown
## Rollback

\`\`\`bash
# Checkout previous version
git checkout v1.0.0

# Rebuild and restart
docker compose down
docker compose build
docker compose up -d
\`\`\`
```

**Validation:**
- [ ] Every step has executable bash commands
- [ ] No narrative-only sections
- [ ] Rollback procedure included
- [ ] Verification steps included

---

### 3. docs/api_examples.md

**Purpose:** Provide copy-paste API examples

**Required Sections:**

- Initialize session
- List tools
- Call tool (no parameters)
- Call tool (with parameters)
- List resources
- Read resource
- Error handling examples
- Complete workflow example

**Validation:**
- [ ] All examples use curl
- [ ] Examples are copy-paste ready
- [ ] Expected responses shown
- [ ] Error cases covered

---

### 4. docs/troubleshooting.md

**Purpose:** Help users solve common problems

**Required Sections:**

- Authentication issues (401, 403)
- Routing issues (502, 404)
- Container health issues
- Environment variable issues
- Database connectivity issues
- MCP protocol issues
- Performance issues
- Diagnostic commands

**Validation:**
- [ ] Each issue has symptoms, causes, solutions
- [ ] Solutions include executable commands
- [ ] Diagnostic scripts provided

---

### 5. docs/skills_usage.md (If Skills Present)

**Purpose:** Explain how to use analysis skills

**Required Sections:**

#### A. Skills Overview
```markdown
## Available Skills

| Skill ID | Purpose | Estimated Time |
|----------|---------|----------------|
| mpa-effectiveness | Compare protection levels | 60s |
| temporal-trends | Analyze trends over time | 45s |
```

#### B. Skill Entry Points
```markdown
## How to Use Skills

Skills are documented workflows in the `skills/` directory.

Each skill has a `SKILL.md` file with:
- Purpose and use cases
- Step-by-step workflow
- Tool calls required
- Interpretation guide
- Success criteria
```

#### C. Example Workflow
```markdown
## Example: MPA Effectiveness Analysis

See `skills/mpa-effectiveness/SKILL.md` for complete workflow.

**Summary:**
1. Get regions → `get_regions`
2. Get biomass data → `biomass_by_protection`
3. Statistical test → `compare_protection_levels`
4. Interpret results
```

**Validation:**
- [ ] All skills listed
- [ ] Entry points explained
- [ ] Example workflow provided

---

### 6. .env.example (Root Level)

**Purpose:** Template for environment configuration

**Required Content:**

```bash
# Server Configuration
PORT=8000
MCP_BASE_PATH=/mcp
LOG_LEVEL=INFO

# Database Configuration
MYDB_HOST=your-database-host.com
MYDB_PORT=3306
MYDB_USER=mcp_readonly
MYDB_PASSWORD=your-secure-password
MYDB_NAME=your_database

# Or use DATABASE_URL
# DATABASE_URL=mysql://user:password@host:3306/database

# Docker Configuration (for docker-compose)
HOST_PORT=8001
COMPOSE_PROJECT_NAME=your-mcp
```

**Validation:**
- [ ] All required variables documented
- [ ] Example values provided
- [ ] Comments explain each variable
- [ ] No actual secrets included

---

## Optional but Recommended Documentation

### 7. CHANGELOG.md

**Purpose:** Track version history

**Format:**

```markdown
# Changelog

## [1.2.0] - 2026-02-16

### Added
- New statistical analysis tools
- Skills registry

### Changed
- Updated metadata schema

### Fixed
- Database connection timeout issue

## [1.1.0] - 2026-01-15

### Added
- Docker deployment support
```

---

### 8. CONTRIBUTING.md

**Purpose:** Guide for contributors

**Sections:**
- How to report bugs
- How to suggest features
- How to submit pull requests
- Code style guidelines
- Testing requirements

---

### 9. docs/architecture.md

**Purpose:** Explain system design

**Sections:**
- Component overview
- Data flow
- Security model
- Scalability considerations

---

### 10. docs/development.md

**Purpose:** Guide for local development

**Sections:**
- Setting up development environment
- Running tests
- Adding new tools
- Adding new skills
- Debugging tips

---

## Documentation Quality Standards

### Writing Style

1. **Be concise** - Get to the point quickly
2. **Be specific** - Use exact commands, not descriptions
3. **Be complete** - Include all necessary steps
4. **Be accurate** - Test all examples before committing

### Code Examples

1. **Executable** - All bash examples must be copy-paste ready
2. **Tested** - Verify examples work before documenting
3. **Annotated** - Include comments explaining non-obvious steps
4. **Complete** - Don't skip steps or assume knowledge

### Formatting

1. **Use markdown** - Proper headers, lists, code blocks
2. **Use code fences** - Always specify language (```bash, ```python, etc.)
3. **Use tables** - For structured comparisons
4. **Use links** - Cross-reference related docs

---

## Documentation Checklist

Before releasing your MCP:

### Root Level
- [ ] README.md with all 6 required sections
- [ ] DEPLOYMENT.md with executable steps
- [ ] .env.example with all variables
- [ ] LICENSE file
- [ ] CHANGELOG.md (recommended)

### docs/ Directory
- [ ] api_examples.md with curl examples
- [ ] troubleshooting.md with common issues
- [ ] skills_usage.md (if skills present)
- [ ] infrastructure.md (production setup)
- [ ] mcp_template_spec.md (template structure)
- [ ] skills_architecture.md (tools vs skills)
- [ ] metadata_schema.md (metadata layers)
- [ ] deployment_workflow.md (CI/CD)

### Metadata
- [ ] metadata/template.json complete
- [ ] metadata/manifest.json generated
- [ ] metadata/README.md present

### Skills (if present)
- [ ] Each skill has SKILL.md
- [ ] skills/README.md overview
- [ ] skills/registry.py exists
- [ ] skills/contracts/ has schemas

### Tests
- [ ] tests/README.md (how to run tests)
- [ ] Test examples in documentation

---

## Maintenance

### When to Update Documentation

Update docs when:

1. **Adding features** - Document new tools/skills
2. **Changing API** - Update api_examples.md
3. **Fixing bugs** - Add to troubleshooting.md
4. **Deploying** - Update CHANGELOG.md
5. **Changing config** - Update .env.example

### Documentation Review

Review docs:

- **Before each release** - Ensure accuracy
- **After major changes** - Update affected docs
- **Quarterly** - General review and cleanup

---

## Examples

### Good Documentation

✅ **Executable:**
```markdown
## Deploy to Production

\`\`\`bash
ssh user@server.com
cd /opt/your-mcp
git pull origin main
docker compose build
docker compose up -d
\`\`\`
```

✅ **Complete:**
```markdown
## Prerequisites

- Python 3.10+
- Docker 20.10+
- MySQL 8.0+
- 2GB RAM minimum
```

✅ **Specific:**
```markdown
## Error: Can't connect to database

**Solution:**
\`\`\`bash
# Test connectivity
docker compose exec mcp python -c "from mcp_server.db import get_connection; get_connection()"

# Check .env file
cat .env | grep DB_HOST
\`\`\`
```

### Bad Documentation

❌ **Narrative:**
```markdown
## Deployment

To deploy, you should connect to your server, pull the latest code,
rebuild the Docker image, and restart the service.
```

❌ **Incomplete:**
```markdown
## Prerequisites

- Python
- Docker
- Database
```

❌ **Vague:**
```markdown
## Error: Database connection fails

**Solution:** Fix your database configuration.
```

---

## See Also

- [docs/mcp_template_spec.md](mcp_template_spec.md) - Repository structure
- [docs/skills_architecture.md](skills_architecture.md) - Tools vs Skills
- [TEMPLATE.md](../TEMPLATE.md) - Template usage guide

---

**Version:** 1.0.0  
**Last Review:** February 16, 2026
