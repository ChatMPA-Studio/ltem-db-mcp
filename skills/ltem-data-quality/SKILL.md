---
name: ltem-data-quality
description: Assess data quality in the LTEM database. Covers outlier detection (MAD and quantile methods), sample size adequacy, PEC/INV transect matching, and field completeness. Use before running analyses to validate data quality.
---

# LTEM Data Quality Assessment

## Purpose

This skill guides data quality assessment before running ecological analyses:
- Detect outliers in Size and Quantity per species (MAD and quantile methods)
- Classify sample sizes as sufficient, limited, or insufficient
- Audit PEC/INV transect matching to identify coverage gaps
- Report missing data percentages across fields and years
- Identify species and regions requiring data cleaning

## Dataset Reference

**Source:** `ltem_historical_database` table via MCP server
**Key fields checked:** Size, Biomass, Quantity, TrophicGroup, Label, Habitat, MPA, Latitude, Longitude

## MCP Tools Available

| Tool | Parameters | Purpose |
|------|-----------|---------|
| `detect_outliers_mad` | `region?`, `year?`, `z_threshold=3.5` | MAD-based outlier detection per species (robust to extremes) |
| `detect_outliers_quantile` | `region?`, `year?`, `ci=0.95` | Quantile-based outlier bounds per species |
| `sample_size_assessment` | `group_by` (Region/Reef/Year) | Sample size classification (<10/10-30/>=30 transects) |
| `transect_coverage_audit` | `year?`, `region?` | PEC vs INV transect matching |
| `data_completeness_report` | `region?` | NULL percentages by field per year |

## Core Workflow

1. **Check completeness** — Call `data_completeness_report` to see NULL rates across fields and years. High NULL rates in Biomass or TrophicGroup will affect downstream analyses
2. **Assess sample sizes** — Call `sample_size_assessment` grouped by Region to identify areas with insufficient replication (< 10 transects)
3. **Detect outliers (MAD)** — Call `detect_outliers_mad` for the target region. MAD method is robust to outliers (recommended for ecological data). Default z=3.5 per Iglewicz & Hoaglin (1993)
4. **Cross-check with quantile** — Call `detect_outliers_quantile` with ci=0.95 to see quantile-based bounds. Compare results with MAD method
5. **Audit transect matching** — Call `transect_coverage_audit` to check if PEC (fish) and INV (invertebrate) surveys are conducted on the same transects. Low match rate suggests systematic coverage gaps
6. **Document findings** — Note species with high outlier rates, regions with insufficient data, and years with completeness issues

## Aggregation Rules

- Outlier detection operates on individual observation-level data (Size and Quantity per species)
- Sample size assessment counts unique transect units per grouping factor
- Transect matching identifies unique Year-Reef-Habitat-Transect combinations
- Completeness checks count NULLs at the observation level per year

## Interpretation Guide

| Check | Flag | Action |
|-------|------|--------|
| NULL rate > 50% for a field | Data gap | Avoid using that field in analyses |
| Sample size < 10 transects | Insufficient | Use non-parametric tests only, flag in results |
| Sample size 10-30 | Limited | Parametric tests acceptable but note limitation |
| MAD outlier rate > 5% for a species | High variability | Review species identification, check for data entry errors |
| PEC-INV match rate < 80% | Coverage gap | Note when combining fish and invertebrate analyses |
| Outlier detected in both MAD and quantile | Likely true outlier | Prioritize for manual review |

## Success Criteria

A complete data quality assessment includes:
- Completeness report showing NULL rates across years
- Sample size classification for target regions
- Outlier detection results (at least MAD method)
- Transect matching audit (if using both PEC and INV data)
- List of data quality flags and recommended actions
