# Changelog

All notable changes to the LTEM Database MCP Server will be documented in this file.

## [1.2.0] — 2026-02-16

Major expansion with automated report generation, comprehensive validation, and user tutorials.

### Report Generation (4 new tools, 59 total)

- **`generate_mpa_report`** — MPA effectiveness assessment with biomass comparisons, Cabo Pulmo recovery trajectory, BACI analysis
- **`generate_temporal_report`** — Temporal trends analysis with time series plots, Mann-Kendall tests, change point detection
- **`generate_community_report`** — Community structure analysis with diversity indices, species composition, trophic structure
- **`generate_quality_report`** — Data quality audit with outlier detection, sample size assessment, completeness checks

**Features:**
- Publication-ready HTML/PDF reports with embedded Matplotlib visualizations
- Base64-encoded PNG figures for HTML, file references for PDF
- Statistical tables with interpretation guidelines
- Colorblind-safe palettes (viridis, colorbrewer)
- PDF generation via WeasyPrint (optional dependency)

### Validation & Quality Assurance

- **`scripts/validate_tools.py`** — Automated validation script for all 59 tools
- **`docs/VALIDATION_REPORT.md`** — Comprehensive validation report documenting:
  - Tool registration and response structure checks
  - Aggregation hierarchy validation (transect → reef → region)
  - Statistical test appropriateness (non-parametric for ecological data)
  - Edge case handling (NULL values, small samples, missing data)
  - All 11 SKILL.md workflow validations

**Findings:** All 59 tools passed validation with minor warnings for environmental data availability (SST/Chla columns may be NULL).

### User Guides & Tutorials

- **`docs/user-guides/`** — New tutorial directory with framework for 16 tutorials
- **Quick-start tutorials** (5-10 min) — Getting started, MPA effectiveness, temporal trends, community diversity, data quality, NRSI, environmental drivers, report generation
- **Comprehensive tutorials** (20-30 min) — In-depth guides with methodology explanations
- **`docs/user-guides/README.md`** — Tutorial catalog and navigation

### Dependencies

- **matplotlib >= 3.7.0** — Publication-quality static visualizations
- **seaborn >= 0.12.0** — Statistical plot types and color palettes
- **Pillow >= 10.0.0** — Image processing for figure embedding
- **WeasyPrint >= 60.0** — PDF generation (optional)

### Testing

- **`tests/test_report_generator.py`** — 9 test classes, 30+ tests for report generation
  - Base class tests (initialization, sections, tables, figures)
  - Figure embedding tests (Matplotlib → base64 PNG)
  - HTML structure validation
  - PDF generation tests (optional, requires WeasyPrint)
  - Integration tests with real data (marked as slow)

### Documentation Updates

- **README.md** — Updated tool count (34 → 59), added Report Generation section
- **TOOL_INVENTORY.md** — Added Report Generation category with 4 tools
- **pyproject.toml** — Added visualization dependencies to `[project.optional-dependencies]`

---

## [1.1.0] — 2026-02-14

Production deployment and package template release. MCP server now runs via HTTP transport on DigitalOcean with Docker, and serves as a reusable template for future MCP servers.

### New Tool Modules (21 new tools, 55 total)

- **Reporting** (4) — Grand numeralia, per-label/region breakdowns, consistent reef filtering
- **Data Quality** (5) — MAD and quantile outlier detection, sample size assessment, PEC/INV coverage audit, data completeness report
- **Invertebrates** (6) — Invertebrate summary/species list, warm/cold coral ratio, latitudinal gradient by climate period, temporal trends with Mann-Kendall, bleaching assessment
- **Ecosystem Indicators** (6) — NRSI by reef (standard + bootstrap CI), regional NRSI comparison, functional group biomass/temporal/regional analysis

### Analytical Skills (11 skills)

Agent-agnostic skills in `skills/` directory, usable by any AI agent:
- ltem-fish-community, ltem-biomass-productivity, ltem-mpa-effectiveness, ltem-temporal-trends
- ltem-nrsi-index, ltem-invertebrate-community, ltem-functional-groups
- ltem-environmental-drivers, ltem-data-quality, ltem-survey-numeralia, ltem-bleaching-assessment

### Infrastructure

- **Centralized config** — `mcp_server/config.py` with env var validation and fail-fast startup
- **Tool auto-discovery** — `server.py` uses pkgutil to find all `tools/*.py` modules automatically
- **Docker deployment** — Multi-stage Dockerfile, non-root user, healthcheck, docker-compose with log rotation
- **Deploy script** — `scripts/deploy.sh` with backup, rebuild, health check, and verify
- **Test suite expansion** — 34 smoke tests (pytest), HTTP tool invocation tests, bash/PowerShell smoke scripts
- **HTTP transport** — Streamable HTTP at configurable MCP_BASE_PATH (default `/mcp`)

### Template Guide

- `TEMPLATE.md` — Step-by-step instructions for creating new MCP servers from this repo
- Covers tool creation, skill authoring, security config, Docker deployment, Caddy routing

### Documentation

- `resources/data_dictionary.md` — Full schema documentation (51 columns)
- `docs/TOOL_INVENTORY.md` — Complete catalog of all 55 tools and 5 resources
- `docs/skills-reference.md` — Skill catalog with workflow descriptions
- Reference docs for NRSI methodology and invertebrate taxa

---

## [1.0.0] — 2025-02-09

First stable release. MCP server is fully functional via local stdio transport.

### Purpose

Exposes the CBMC LTEM (Long-Term Ecological Monitoring) database as structured analysis tools via the Model Context Protocol (MCP), enabling Claude and chatMPA Studio to query 26 years of fish survey data from the Gulf of California and Baja California Sur.

### Tool Categories (33 tools, 5 resources)

- **Core** (4) — Database health check, table listing, column description, full schema snapshot
- **Data Access** (5) — Region, reef, species, and observation queries with filtering; survey effort summaries
- **Fish Community** (5) — Shannon/Simpson/Pielou diversity, species composition, trophic structure, size structure, Bray-Curtis dissimilarity
- **Biomass** (7) — Regional biomass comparison (Kruskal-Wallis), depth comparison, trophic biomass, environmental correlations (SST, Chl-a), latitudinal gradient
- **MPA Effectiveness** (7) — Protection level comparison, Cabo Pulmo recovery trajectory, multi-metric comparison, trophic/size by protection, BACI analysis, spillover analysis
- **Temporal Trends** (6) — Annual time series, linear regression + Mann-Kendall trend test, regional trend comparison, Pettitt/CUSUM change point detection, seasonal patterns, rolling averages

### Security Guardrails

- Read-only database user (`mcp_ltem_ro`, SELECT only)
- Credentials via `.env` file, never hardcoded, gitignored
- SQL validation: only SELECT/SHOW/DESCRIBE statements allowed
- Denied keyword list: INSERT, UPDATE, DELETE, ALTER, DROP, CREATE, TRUNCATE, etc.
- Table whitelist: only 3 core LTEM tables accessible
- Auto LIMIT cap at 5,000 rows per query
- Query timeout at 20 seconds
- Parameterized queries throughout

### Known Limitations

- **No SST/Chla columns** in the database — environmental tools return graceful errors
- **IDReef/IDSpecies type mismatch** — text in `ltem_historical_database`, double in reference tables; tools use CAST for joins
- **Biomass sparsity** — some region/year combinations have very few transects
- **MPA column encoding** — Spanish text with mixed UTF-8/Latin-1 artifacts
- **Schema cache** — per-process; restart server to refresh after DB schema changes
- **No visualization** — by design; rendering delegated to Claude/chatMPA Studio
- **Local stdio only** — no HTTP/SSE transport; no Docker or cloud deployment

### Infrastructure

- Python 3.10+ required
- FastMCP 2.x, PyMySQL, pandas, scipy, numpy
- MySQL 8.0 on AWS RDS
- Automated smoke tests (pytest, 23 tests)
- Build report generator (HTML + DOCX)
