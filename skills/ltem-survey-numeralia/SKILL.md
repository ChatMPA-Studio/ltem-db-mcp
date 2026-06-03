---
name: ltem-survey-numeralia
description: Generate survey effort summaries (numeralia) from the LTEM database. Covers grand totals, PEC/INV breakdown, regional effort, and identification of consistently monitored reefs. Use for reporting survey scope and sampling effort.
---

# LTEM Survey Numeralia

## Purpose

This skill guides the generation of survey effort summaries for reporting and presentations:
- Grand totals (observations, individuals, species, reefs, transects, area)
- Breakdown by survey type (PEC = fish, INV = invertebrates)
- Regional effort summaries with temporal coverage
- Identification of consistently monitored reefs for balanced panel analyses
- Survey effort by year, region, or MPA status

## Dataset Reference

**Source:** `ltem_historical_database` table via MCP server
**Survey types:** PEC (Peces = fish visual census), INV (Invertebrados = invertebrate surveys)
**Label column:** `Label` — distinguishes PEC from INV observations

## MCP Tools Available

| Tool | Parameters | Purpose |
|------|-----------|---------|
| `numeralia_historical` | — | Grand totals across entire database |
| `numeralia_by_label` | `year?` | Breakdown by PEC/INV survey type |
| `numeralia_by_region` | `year?`, `label?` | Regional effort summary |
| `consistent_reefs` | `min_years=5`, `label?` | Reefs meeting minimum sampling frequency |
| `survey_effort_summary` | `group_by` (Year/Region/MPA) | Reef, transect, species counts by grouping factor |

## Core Workflow

1. **Grand totals** — Call `numeralia_historical` to get overall database scope: total observations, individuals, species, reefs, transects, area, and year range
2. **PEC/INV breakdown** — Call `numeralia_by_label` to see the split between fish and invertebrate surveys. Optionally filter by year for current-year numeralia
3. **Regional effort** — Call `numeralia_by_region` to compare sampling effort across regions. Check which regions have the longest monitoring histories
4. **Survey effort trends** — Call `survey_effort_summary` grouped by Year to see how sampling effort has changed over time
5. **Identify balanced panels** — Call `consistent_reefs` with min_years=5 (or higher) to find reefs suitable for temporal trend analysis. Note coverage percentages
6. **MPA effort** — Call `survey_effort_summary` grouped by MPA to compare effort across protection categories

## Aggregation Rules

- Transect counts use unique Year-Reef-Habitat-Transect combinations
- Species counts use distinct species names per grouping unit
- Consistent reefs are identified via HAVING clause (COUNT DISTINCT Year >= threshold)
- Coverage percentage = (years monitored / total years in dataset) x 100

## Interpretation Guide

| Metric | Typical Value | Context |
|--------|--------------|---------|
| Total observations | >500,000 | 26+ years of monitoring |
| Total species (PEC) | ~300-400 | Gulf of California reef fish richness |
| Total species (INV) | ~100-200 | Macroinvertebrate diversity |
| Consistent reefs (5+ years) | ~30-50 | Suitable for trend analysis |
| Coverage > 80% | Well-monitored reef | Strong temporal data |
| Coverage < 30% | Sporadically visited | Use for spatial analyses only |

## Success Criteria

A complete numeralia report includes:
- Grand database totals (observations, individuals, species, reefs, area)
- PEC/INV breakdown for the entire history and current year
- Regional summary showing effort distribution
- List of consistent reefs with coverage percentages
- Clear presentation suitable for stakeholder reports or DataMares submissions
