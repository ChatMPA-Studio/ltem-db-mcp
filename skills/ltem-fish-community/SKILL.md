---
name: ltem-fish-community
description: Analyze fish community structure from the LTEM database using MCP tools. Covers diversity indices, species composition, trophic and size structure, and community similarity. Use for community ecology questions about Gulf of California reef fish.
---

# LTEM Fish Community Structure Analysis

## Purpose

This skill guides the analysis of reef fish community structure using the LTEM MCP server. It helps answer questions about:
- Species diversity and evenness across regions, reefs, and years
- Dominant species and community composition patterns
- Trophic group proportions and feeding guild balance
- Size structure and population demographics
- Community similarity (beta diversity) between sites

## Dataset Reference

**Source:** `ltem_historical_database` table via MCP server
**Sampling design:** Region > Reef > Year > Depth > Transect > Species > Size class
**Independent unit:** Transect (50m x 5m belt transect, 4 replicates per depth)

## MCP Tools Available

| Tool | Parameters | Purpose |
|------|-----------|---------|
| `calculate_diversity` | `region?`, `reef?`, `year?`, `depth?` | Shannon H', Simpson D, Pielou J', species richness per survey unit |
| `species_composition` | `group_by` (Region/MPA/Year/Habitat), `top_n=15` | Top N species by relative abundance per group |
| `trophic_structure` | `region?`, `year?` | Biomass proportions by trophic group |
| `size_structure` | `region?`, `year?` | Abundance distribution across size classes (0-10, 10-20, ... 50+ cm) |
| `community_comparison` | `group_by` (Region/MPA/Habitat) | Bray-Curtis dissimilarity matrix between groups |

## Core Workflow

1. **Scope the analysis** — Call `get_regions` to see available regions, then decide on spatial/temporal scope
2. **Calculate diversity indices** — Call `calculate_diversity` with desired filters. Returns Shannon H', Simpson 1-D, Pielou J', and species richness per survey unit
3. **Identify dominant species** — Call `species_composition` grouped by Region (or Year/Habitat) to see which species dominate each community
4. **Evaluate trophic structure** — Call `trophic_structure` to see biomass proportions across trophic groups (Herbivoro, Carnivoro, Piscivoro, Zooplanctivoro)
5. **Examine size structure** — Call `size_structure` to see the abundance distribution across size classes. High proportion of large fish (>40cm) indicates healthy populations
6. **Compare communities** — Call `community_comparison` to get pairwise Bray-Curtis dissimilarity. Values near 0 = similar communities, near 1 = distinct communities
7. **Synthesize** — Combine results into a narrative about community health, diversity patterns, and key differences between sites

## Aggregation Rules

All tools handle hierarchical aggregation internally:
- **Diversity indices** are calculated at the transect level, then summarized
- **Species composition** uses relative abundance pooled across transects within each group
- **Trophic/size structure** sums biomass or counts within transects first, then computes proportions
- **Community comparison** uses species abundance matrices aggregated per group

## Interpretation Guide

| Metric | Low | Medium | High |
|--------|-----|--------|------|
| Shannon H' | <1.5 (low diversity) | 1.5-3.0 | >3.0 (high diversity) |
| Simpson 1-D | <0.5 (dominated by few spp) | 0.5-0.8 | >0.8 (highly diverse) |
| Pielou J' | <0.4 (very uneven) | 0.4-0.7 | >0.7 (even community) |
| Bray-Curtis | <0.3 (similar) | 0.3-0.6 | >0.6 (distinct) |
| Large fish % (>40cm) | <5% (overfished) | 5-15% | >15% (healthy) |

## Success Criteria

A complete fish community analysis includes:
- Diversity indices for the target scope (region, reef, or year)
- Species composition showing top 10-15 dominant species
- Trophic structure proportions
- Size class distribution
- At least one community comparison (between regions or habitats)
- Ecological interpretation of patterns
