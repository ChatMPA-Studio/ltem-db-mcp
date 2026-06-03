---
name: ltem-biomass-productivity
description: Analyze fish biomass, productivity, and environmental drivers from the LTEM database. Covers regional biomass patterns, depth comparisons, trophic biomass, SST and chlorophyll relationships, and latitudinal gradients. Use for production ecology and environmental correlation questions.
---

# LTEM Biomass, Productivity & Environmental Analysis

## Purpose

This skill guides the analysis of fish biomass patterns and environmental relationships using the LTEM MCP server:
- Compare biomass across regions and depth categories
- Analyze trophic-level biomass distribution
- Correlate biomass with SST and chlorophyll-a
- Model SST-biomass relationships (linear and quadratic)
- Examine chlorophyll-productivity relationships (log-log)
- Analyze latitudinal gradients in biomass and diversity

## Dataset Reference

**Source:** `ltem_historical_database` table via MCP server
**Biomass units:** grams per square meter (g/m2)
**Environmental variables:** SST (degrees C), Chla (mg/m3) — may not be available for all regions

## MCP Tools Available

| Tool | Parameters | Purpose |
|------|-----------|---------|
| `biomass_by_region` | `year?`, `depth?` | Mean transect biomass per region with Kruskal-Wallis test |
| `biomass_by_depth` | `region?` | Shallow vs Deep biomass comparison with Mann-Whitney U |
| `trophic_biomass` | `region?`, `year?` | Biomass breakdown by trophic group with proportions |
| `environmental_correlations` | `region?` | Spearman correlations between biomass and SST/Chl-a |
| `sst_biomass_relationship` | `region?` | Linear and quadratic regression of biomass vs SST |
| `chl_productivity_relationship` | `region?` | Log-log regression of Chl-a vs biomass |
| `latitudinal_gradient` | — | Biomass trends along the latitudinal gradient |

## Core Workflow

1. **Regional overview** — Call `biomass_by_region` to compare mean biomass across all regions. Check Kruskal-Wallis p-value for significant regional differences
2. **Depth comparison** — Call `biomass_by_depth` for target regions to test shallow vs deep biomass differences
3. **Trophic breakdown** — Call `trophic_biomass` to see how biomass is distributed across trophic groups. High carnivore/piscivore proportion indicates healthy trophic structure
4. **Environmental correlations** — Call `environmental_correlations` for Spearman rho between biomass and SST/Chl-a. Note: may return warnings if environmental columns are missing
5. **SST-biomass model** — Call `sst_biomass_relationship` to fit linear and quadratic models. Quadratic fit may reveal optimal SST for biomass
6. **Chl-a productivity** — Call `chl_productivity_relationship` for log-log regression. Slope indicates productivity scaling
7. **Latitudinal gradient** — Call `latitudinal_gradient` to examine biomass patterns from north (Alto Golfo) to south (Huatulco)

## Aggregation Rules

- **Biomass** is SUM'd within each transect first, then MEAN'd across transects for comparisons
- **Environmental variables** (SST, Chl-a) are averaged per transect unit (they are the same within a transect)
- **Correlations** use transect-level biomass totals paired with environmental values
- Tools handle this hierarchical aggregation internally

## Interpretation Guide

| Result | Interpretation |
|--------|---------------|
| Kruskal-Wallis p < 0.05 | Significant biomass differences between regions |
| Mann-Whitney p < 0.05 | Significant shallow/deep biomass difference |
| Spearman rho > 0.3 (positive) | Moderate positive correlation with environment |
| Quadratic R2 > Linear R2 | Non-linear (hump-shaped) SST-biomass relationship |
| Optimal SST from quadratic | Temperature maximizing fish biomass |
| Log-log slope near 1 | Linear productivity scaling with chlorophyll |
| Negative latitude-biomass rho | Biomass decreases toward higher latitudes |

## Success Criteria

A complete biomass analysis includes:
- Regional biomass comparison with statistical test
- Depth category comparison for at least one region
- Trophic biomass proportions
- Environmental correlations (if SST/Chl-a data available)
- At least one regression model (SST or Chl-a)
- Ecological interpretation linking biomass patterns to environmental drivers
