---
name: ltem-invertebrate-community
description: Analyze macroinvertebrate communities from the LTEM database (Label='INV'). Covers taxonomic composition, warm/cold coral ratios, latitudinal gradients, temporal trends, and key indicator taxa. Use for invertebrate ecology and coral community questions.
---

# LTEM Invertebrate Community Analysis

## Purpose

This skill guides the analysis of macroinvertebrate communities using the LTEM MCP server:
- Summarize invertebrate abundance and richness by taxonomic group
- Inventory invertebrate species with distribution data
- Analyze warm coral (Scleractinia) vs cold coral (Holaxonia) ratios
- Examine latitudinal gradients across climate periods
- Detect temporal trends in invertebrate populations
- Assess coral bleaching coverage

## Dataset Reference

**Source:** `ltem_historical_database` table, filtered to `Label = 'INV'`
**Key taxonomic columns:** `Taxa2` (class-level, e.g. Asteroidea), `Taxa3` (order-level, e.g. Scleractinia), `Phylum`

### Key Indicator Taxa

| Taxa | Taxa2 | Taxa3 | Ecological Role |
|------|-------|-------|----------------|
| Sea stars | Asteroidea | — | Keystone predators (e.g. crown-of-thorns) |
| Sea urchins | Echinoidea | — | Herbivores controlling algal cover |
| Warm corals | — | Scleractinia | Hard coral reef builders |
| Cold corals | — | Holaxonia | Gorgonian soft corals (cold-water affinity) |

### Climate Periods

| Period | Years | Context |
|--------|-------|---------|
| Historical | 1998-2013 | Pre-warming baseline |
| Warming | 2014-2024 | Marine heatwave era |
| Current | 2025+ | Most recent data |

## MCP Tools Available

| Tool | Parameters | Purpose |
|------|-----------|---------|
| `invertebrate_summary` | `region?`, `year?` | Abundance/richness by Taxa2 and Taxa3 |
| `invertebrate_species_list` | `region?`, `year?`, `taxa2?` | Species inventory with distribution |
| `coral_warm_cold_ratio` | `region?`, `year?` | Scleractinia vs Holaxonia ratio per reef |
| `invertebrate_latitudinal_gradient` | `period?` | Abundance by latitude degree with Spearman correlation |
| `invertebrate_temporal_trends` | `region?`, `taxa2?` | Annual trends with Mann-Kendall test |
| `bleaching_assessment` | `region?`, `year?` | Bleaching coverage by reef and year |

## Core Workflow

1. **Taxonomic overview** — Call `invertebrate_summary` to see which taxa groups dominate. Check proportions of Asteroidea, Echinoidea, Scleractinia, Holaxonia
2. **Species inventory** — Call `invertebrate_species_list` filtered by taxa2 of interest to see species-level detail
3. **Coral balance** — Call `coral_warm_cold_ratio` to assess warm/cold coral proportions per reef. Rising warm:cold ratio may indicate warming
4. **Latitudinal patterns** — Call `invertebrate_latitudinal_gradient` for each climate period to see how spatial patterns have shifted over time
5. **Temporal trends** — Call `invertebrate_temporal_trends` for target taxa2 groups to detect population increases or declines
6. **Bleaching status** — Call `bleaching_assessment` to check current bleaching severity across reefs
7. **Synthesize** — Link invertebrate community patterns to environmental drivers (warming, protection status)

## Aggregation Rules

- Invertebrate data is filtered by `Label = 'INV'` (separate survey protocol from fish)
- Abundance is SUM'd per transect, then averaged per reef for comparisons
- Latitudinal gradient uses the `Degree` column (rounded latitude)
- Mann-Kendall uses reef-averaged annual means

## Interpretation Guide

| Pattern | Interpretation |
|---------|---------------|
| Warm:Cold coral ratio increasing | Possible warming signal |
| Echinoidea declining | Reduced herbivory, potential algal phase shift |
| Asteroidea increasing | Watch for crown-of-thorns outbreaks |
| Bleaching > 30% | High severity, potential coral mortality |
| Latitudinal gradient shifting | Tropicalization or range shifts |

## Success Criteria

A complete invertebrate analysis includes:
- Taxonomic summary showing dominant groups
- Warm/cold coral ratios for at least one region
- Latitudinal gradient across at least two climate periods
- Temporal trend for at least one key taxa group
- Bleaching assessment if coral questions are involved
- Ecological interpretation linking patterns to climate or protection
