---
name: ltem-nrsi-index
description: Calculate and interpret the Normalized Reef State Index (NRSI) from the LTEM database. NRSI measures reef trophic health using relative biomass of upper, lower, and consumer trophic levels. Use for reef health assessment and trophic balance questions.
---

# LTEM Normalized Reef State Index (NRSI)

## Purpose

This skill guides the calculation and interpretation of the NRSI using the LTEM MCP server:
- Compute NRSI per reef to assess trophic health
- Estimate uncertainty via bootstrap confidence intervals
- Compare NRSI across regions with statistical tests
- Track NRSI changes over time
- Identify reefs with degraded or healthy trophic structure

## Dataset Reference

**Source:** `ltem_historical_database` table via MCP server
**Key column:** `TrophicLevelF` — categorical trophic level ranges (e.g., '2-2.5', '4-4.5')
**Biomass column:** `Biomass` in g/m2

### NRSI Formula

```
UTL = relative biomass of TrophicLevelF containing '4-4.5' (Upper Trophic Level)
LTL = relative biomass of TrophicLevelF containing '2-2.5' (Lower Trophic Level)
CTL = relative biomass of all other trophic levels (Consumer Trophic Level)

Standard:  NRSI = (UTL + LTL - CTL) / (UTL + LTL + CTL)
Conditional: if LTL > UTL + CTL, then NRSI = UTL / (UTL + CTL)
```

The conditional prevents artificially high NRSI when herbivore/detritivore biomass (LTL) dominates the system.

## MCP Tools Available

| Tool | Parameters | Purpose |
|------|-----------|---------|
| `nrsi_by_reef` | `region?`, `year?` | NRSI mean and median per reef (transect-level computation) |
| `nrsi_bootstrapped` | `region?`, `year?`, `n_boot=100` | NRSI with 95% bootstrap CI per reef |
| `nrsi_regional_summary` | `year?` | Regional NRSI comparison with Kruskal-Wallis test |

## Core Workflow

1. **Regional overview** — Call `nrsi_regional_summary` to compare NRSI across all regions. Check Kruskal-Wallis for significant differences
2. **Reef-level detail** — Call `nrsi_by_reef` for a target region to see per-reef NRSI values. Identify reefs with the highest and lowest scores
3. **Uncertainty estimation** — Call `nrsi_bootstrapped` for key reefs to get 95% confidence intervals. Reefs where CI includes 0 have ambiguous trophic state
4. **Temporal comparison** — Call `nrsi_regional_summary` or `nrsi_by_reef` for specific years to track changes over time
5. **Synthesize** — Map NRSI values to reef health categories and identify spatial patterns

## Aggregation Rules

- Biomass is SUM'd per transect for each trophic level category (UTL/LTL/CTL)
- Relative biomass proportions are computed within each transect
- NRSI is computed per transect, then averaged per reef
- Bootstrap resamples transect-level NRSI values within each reef

## Interpretation Guide

| NRSI Range | Category | Ecological Meaning |
|-----------|----------|-------------------|
| 0.5 to 1.0 | Excellent | High apex predator + herbivore biomass, healthy reef |
| 0.0 to 0.5 | Good | Balanced trophic structure |
| -0.5 to 0.0 | Degraded | Mid-level consumers dominate, possible overfishing |
| -1.0 to -0.5 | Severely degraded | Very low top predator biomass, collapsed trophic structure |

**Key patterns to look for:**
- Cabo Pulmo typically shows positive NRSI (recovery of apex predators)
- Unprotected reefs often show negative NRSI (fishing removes top predators)
- NRSI > 0 with narrow bootstrap CI = confident healthy assessment

## Success Criteria

A complete NRSI analysis includes:
- Regional comparison with statistical test
- Per-reef NRSI for at least one region
- Bootstrap confidence intervals for key reefs
- Temporal comparison if multiple years available
- Clear mapping of NRSI values to ecological health categories
