---
name: ltem-environmental-drivers
description: Analyze relationships between fish biomass and environmental variables (SST, Chl-a) using the LTEM database. Covers Spearman correlations, SST-biomass regression, chlorophyll-productivity models, and latitudinal gradients. Use for climate-fish and environmental driver questions.
---

# LTEM Environmental Drivers Analysis

## Purpose

This skill guides the analysis of environmental drivers of fish community patterns:
- Quantify correlations between biomass and SST/chlorophyll-a
- Model SST-biomass relationships (linear and quadratic fits)
- Analyze chlorophyll-productivity scaling (log-log regression)
- Examine latitudinal gradients as a proxy for environmental gradients
- Identify optimal environmental conditions for fish biomass

## Dataset Reference

**Source:** `ltem_historical_database` table via MCP server
**Environmental columns:** `SST` (sea surface temperature, degrees C), `Chla` (chlorophyll-a, mg/m3)
**Note:** Environmental columns may not be available for all regions/years. Tools handle missing data gracefully.

## MCP Tools Available

| Tool | Parameters | Purpose |
|------|-----------|---------|
| `environmental_correlations` | `region?` | Spearman rho between transect biomass and SST/Chl-a |
| `sst_biomass_relationship` | `region?` | Linear + quadratic regression of biomass vs SST |
| `chl_productivity_relationship` | `region?` | Log-log regression of Chl-a vs biomass |
| `latitudinal_gradient` | — | Biomass, abundance, and richness by reef latitude |

## Core Workflow

1. **Screen correlations** — Call `environmental_correlations` (all regions, then per region) to identify which environmental variables show significant associations with biomass
2. **SST-biomass model** — Call `sst_biomass_relationship` to fit both linear and quadratic models. Compare R2 values to determine if the relationship is linear or hump-shaped
3. **Optimal SST** — If quadratic R2 > linear R2, the `optimal_sst` value indicates the temperature maximizing fish biomass
4. **Chl-productivity scaling** — Call `chl_productivity_relationship` for the log-log regression. The slope indicates how productivity scales with primary production
5. **Latitudinal gradient** — Call `latitudinal_gradient` to see spatial patterns. Latitude integrates multiple environmental gradients (temperature, productivity, upwelling)
6. **Regional drill-down** — Re-run tools filtered by specific regions to compare environmental relationships across sites

## Aggregation Rules

- Environmental correlations use transect-level biomass (SUM) paired with environmental values
- SST/Chl-a regression uses region-year averages to avoid pseudoreplication
- Latitudinal gradient averages biomass per reef (grouped by latitude)
- Minimum 5 data pairs required for any correlation or regression

## Interpretation Guide

| Analysis | Key Result | Interpretation |
|----------|-----------|---------------|
| Spearman rho (SST) | Positive, p < 0.05 | Warmer waters support higher biomass |
| Spearman rho (SST) | Negative, p < 0.05 | Thermal stress reducing biomass |
| Quadratic R2 > Linear R2 | Hump-shaped | Optimal SST exists; extremes are detrimental |
| Optimal SST ~25-28C | Typical for Gulf of California | Matches known thermal preferences |
| Log-log slope ~1 | Linear scaling | Biomass proportional to primary production |
| Log-log slope > 1 | Super-linear | Biomass amplifies primary production signal |
| Latitude-biomass negative rho | Higher biomass in south | Tropical affinity of reef fish assemblages |

## Success Criteria

A complete environmental analysis includes:
- Spearman correlations for both SST and Chl-a
- SST-biomass regression with model comparison (linear vs quadratic)
- Chlorophyll-productivity log-log relationship
- Latitudinal gradient with correlation statistic
- Ecological narrative linking environmental patterns to fish community drivers
