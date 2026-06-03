---
name: ltem-mpa-effectiveness
description: Assess Marine Protected Area effectiveness using the LTEM database, focused on Cabo Pulmo National Park. Compares biomass, diversity, trophic structure, and size structure across protection levels. Use for MPA evaluation, conservation impact, and Cabo Pulmo recovery questions.
---

# LTEM MPA Effectiveness Assessment

## Purpose

This skill guides the assessment of Marine Protected Area performance using the LTEM MCP server:
- Compare ecological metrics across protection levels
- Track Cabo Pulmo National Park recovery trajectory (established 1995)
- Analyze trophic structure differences by protection status
- Evaluate size structure as an indicator of fishing pressure
- Conduct Before-After-Control-Impact (BACI) analysis
- Assess spillover effects from Cabo Pulmo to surrounding areas

## Dataset Reference

**Source:** `ltem_historical_database` table via MCP server
**Protection categories:** Cabo Pulmo (strict no-take since 1995), Weak regulations, Unprotected (sin proteccion), Area protegida
**Cabo Pulmo baseline years:** 1998-2000 (earliest monitoring data)

## MCP Tools Available

| Tool | Parameters | Purpose |
|------|-----------|---------|
| `compare_protection_levels` | `metric` (biomass/abundance/richness) | Kruskal-Wallis + pairwise Mann-Whitney across protection levels |
| `cabo_pulmo_recovery` | `baseline_years?` | Annual biomass trajectory with recovery factor vs baseline |
| `compare_all_metrics` | — | Multi-metric comparison (biomass, abundance, richness) with Cabo Pulmo advantage % |
| `trophic_comparison` | — | Trophic group proportions by protection level |
| `size_comparison` | — | Size class proportions by protection level with large fish % |
| `baci_analysis` | `before_years?`, `after_years?` | Before-After-Control-Impact design for Cabo Pulmo |
| `spillover_analysis` | — | Biomass by distance from Cabo Pulmo |

## Core Workflow

1. **Multi-metric overview** — Call `compare_all_metrics` for a comprehensive comparison across protection levels. Note the Cabo Pulmo advantage percentage
2. **Biomass comparison** — Call `compare_protection_levels` with metric='biomass' for detailed statistical tests (Kruskal-Wallis + pairwise)
3. **Recovery trajectory** — Call `cabo_pulmo_recovery` to see the annual biomass trend and recovery factor relative to baseline. Default baseline is 1998-2000
4. **Trophic structure** — Call `trophic_comparison` to compare trophic group proportions. Higher top predator proportion in Cabo Pulmo indicates trophic recovery
5. **Size structure** — Call `size_comparison` to compare size class distributions. Higher large fish (>40cm) percentage in Cabo Pulmo indicates reduced fishing mortality
6. **BACI analysis** — Call `baci_analysis` for the formal Before-After-Control-Impact test. Default compares 1998-2000 (before full enforcement) vs 2018-2020 (after)
7. **Spillover** — Call `spillover_analysis` to test whether biomass declines with distance from Cabo Pulmo boundaries

## Aggregation Rules

- All metrics are computed at the transect level, then averaged per protection level
- Recovery factor = (current year biomass) / (baseline period mean biomass)
- BACI effect = (Impact_after - Impact_before) - (Control_after - Control_before)
- Spillover uses haversine distance from Cabo Pulmo centroid

## Interpretation Guide

| Result | Interpretation |
|--------|---------------|
| Cabo Pulmo advantage > 100% | Biomass more than double unprotected sites |
| Recovery factor > 4 | Cabo Pulmo's documented ~463% recovery |
| Top predator proportion higher in Cabo Pulmo | Trophic cascade recovery |
| Large fish % > 15% in Cabo Pulmo vs < 5% unprotected | Size structure recovery |
| BACI effect positive and significant | Protection effect beyond temporal trends |
| Negative distance-biomass slope in spillover | Evidence of spillover from MPA |

## Success Criteria

A complete MPA assessment includes:
- Multi-metric comparison with statistical significance
- Cabo Pulmo recovery trajectory showing temporal trend
- Trophic and size structure comparison
- BACI analysis with quantified protection effect
- Ecological narrative linking protection to biomass/trophic/size recovery
