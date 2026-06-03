---
name: ltem-temporal-trends
description: Analyze temporal trends in fish populations across the 26-year LTEM record. Covers time series construction, trend detection (Mann-Kendall, Sen's slope), change point analysis (Pettitt, CUSUM), seasonal patterns, and regional trajectory comparisons.
---

# LTEM Temporal Trends Analysis

## Purpose

This skill guides temporal analysis of the 26-year LTEM monitoring record:
- Construct annual time series for biomass, abundance, or richness
- Detect monotonic trends using parametric and non-parametric methods
- Identify regime shifts and change points
- Analyze seasonal (monthly) patterns in survey data
- Compare temporal trajectories across regions
- Smooth noisy time series with moving windows

## Dataset Reference

**Source:** `ltem_historical_database` table via MCP server
**Time span:** 1998-present (annual surveys, typically summer months)
**Metrics available:** biomass, abundance (quantity), species richness

## MCP Tools Available

| Tool | Parameters | Purpose |
|------|-----------|---------|
| `annual_time_series` | `region?`, `metric` (biomass/abundance/richness) | Annual mean values with transect counts |
| `trend_analysis` | `region?`, `metric` | Linear regression + Mann-Kendall + Sen's slope |
| `regional_trends` | `metric` | Trend comparison across all regions |
| `change_point_detection` | `region?`, `metric`, `method` (pettitt/cusum) | Detect regime shift years |
| `seasonal_patterns` | `region?` | Monthly aggregation for seasonal signal |
| `moving_window` | `region?`, `metric`, `window=5` | Rolling average smoothing |

## Core Workflow

1. **Build time series** — Call `annual_time_series` for the target region and metric. Check for gaps and sample sizes per year
2. **Test for trends** — Call `trend_analysis` to get linear regression (slope, R2, p-value), Mann-Kendall (tau, Z, p-value), and Sen's slope (robust median trend)
3. **Compare regions** — Call `regional_trends` to see which regions are increasing, decreasing, or stable. Compare slopes and significance
4. **Detect change points** — Call `change_point_detection` with method='pettitt' to find the most likely regime shift year. Use method='cusum' for cumulative deviation visualization
5. **Check seasonality** — Call `seasonal_patterns` to see if there are consistent monthly patterns (important for survey timing interpretation)
6. **Smooth trends** — Call `moving_window` with window=5 to reduce interannual noise and reveal underlying trajectory

## Aggregation Rules

- Annual values are transect-level sums (biomass/abundance) or counts (richness), averaged across all transects per year
- Mann-Kendall test requires at least 4 data points (years)
- Sen's slope uses the median of all pairwise slopes between years
- Moving window uses centered rolling mean

## Interpretation Guide

| Method | Statistic | Interpretation |
|--------|-----------|---------------|
| Linear regression | p < 0.05, slope > 0 | Significant increasing trend |
| Mann-Kendall | p < 0.05, tau > 0 | Non-parametric confirmation of increase |
| Sen's slope | units/year | Robust trend rate (insensitive to outliers) |
| Pettitt test | p < 0.05 | Significant change point at detected year |
| CUSUM | sign change | Regime shift where cumulative deviation reverses |

**Trend direction convention:**
- "increasing" = Mann-Kendall Z > 0 and p < 0.05
- "decreasing" = Mann-Kendall Z < 0 and p < 0.05
- "no_trend" = p >= 0.05

## Success Criteria

A complete temporal analysis includes:
- Annual time series for at least one metric
- Both parametric (linear) and non-parametric (Mann-Kendall) trend tests
- Change point analysis identifying regime shift years
- Regional comparison showing divergent or convergent trajectories
- Ecological narrative connecting trends to known events (El Nino, MPA establishment, etc.)
