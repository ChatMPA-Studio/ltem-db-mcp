---
name: ltem-functional-groups
description: Analyze fish functional group composition and biomass from the LTEM database. Covers functional group biomass breakdown, temporal trajectories, and regional proportional composition. Use for functional ecology and ecosystem role questions.
---

# LTEM Functional Group Analysis

## Purpose

This skill guides the analysis of fish functional group composition using the LTEM MCP server:
- Quantify biomass by functional group with ecological labels
- Track functional group trajectories over time
- Compare proportional composition across regions
- Identify shifts in ecosystem function allocation

## Dataset Reference

**Source:** `ltem_historical_database` table via MCP server
**Key column:** `Functional_groups` — functional classification of fish species

### Functional Groups

| Code | Spanish Label | Ecological Role |
|------|-------------|----------------|
| `GenPred_solitary` | Depredadores solitarios | Large solitary predators (groupers, snappers) |
| `GenPred_schooling` | Depredadores en cardumenes | Schooling predators (jacks, mackerel) |
| `EpiBent_schooling` | Omnivoros en cardumen | Schooling epibenthic omnivores |
| `Crip_schooling` | Herbivoros en cardumen | Schooling herbivores (parrotfish, surgeonfish) |
| `Crip_solitary` | Cripticos solitarios | Small cryptic solitary fish |
| `Plank` | Planctivoros | Planktivores (damselfish, chromis) |
| `Pelagic` | Pelagicos | Pelagic species (typically excluded from reef analyses) |

## MCP Tools Available

| Tool | Parameters | Purpose |
|------|-----------|---------|
| `functional_group_biomass` | `region?`, `year?` | Biomass totals and proportions by functional group |
| `functional_group_temporal` | `region?` | Annual biomass trajectory per functional group |
| `functional_group_by_region` | `year?` | Proportional composition per region |

## Core Workflow

1. **Overall composition** — Call `functional_group_biomass` to see which functional groups dominate total biomass. Note proportions and Spanish labels
2. **Regional comparison** — Call `functional_group_by_region` to compare proportional composition across regions. Protected areas should show higher predator proportions
3. **Temporal trajectories** — Call `functional_group_temporal` for key regions to track how functional group biomass has changed over time
4. **Focused analysis** — Re-call tools with specific region or year filters to drill into patterns of interest
5. **Synthesize** — Assess ecosystem functional balance and identify regions with atypical functional profiles

## Aggregation Rules

- Biomass is SUM'd per transect per functional group, then averaged across transects
- Proportions are computed relative to total biomass within each grouping unit (region or year)
- Pelagic species are typically present in the data but may be excluded from reef-specific analyses
- Tools include Spanish labels (`label_es`) in output for reporting

## Interpretation Guide

| Pattern | Interpretation |
|---------|---------------|
| High GenPred_solitary proportion | Healthy predator population, strong top-down control |
| Declining GenPred_schooling | Loss of schooling predators, possible fishing impact |
| Increasing Plank proportion | Shift toward smaller planktivorous species |
| Crip_schooling dominance | Herbivore-dominated system (can be healthy or overfished) |
| Even distribution across groups | Balanced functional ecosystem |

**Healthy reef indicators:**
- GenPred (solitary + schooling) > 30% of total biomass
- Multiple functional groups present (no single group > 50%)
- Temporal stability (no abrupt shifts between years)

## Success Criteria

A complete functional group analysis includes:
- Biomass breakdown showing all functional groups with proportions
- Regional comparison showing functional composition differences
- Temporal trajectory for at least one region
- Identification of dominant and underrepresented functional groups
- Ecological narrative connecting functional composition to reef health
