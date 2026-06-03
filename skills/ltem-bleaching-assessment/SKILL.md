---
name: ltem-bleaching-assessment
description: Assess coral bleaching patterns using the LTEM database. Combines bleaching coverage data with warm/cold coral ratios and invertebrate community data. Use for coral health and climate impact questions.
---

# LTEM Bleaching Assessment

## Purpose

This skill guides the assessment of coral bleaching and climate impacts using the LTEM MCP server:
- Quantify bleaching coverage by reef and year
- Classify bleaching severity
- Analyze warm vs cold coral balance as a climate indicator
- Track invertebrate community changes related to thermal stress
- Detect temporal trends in bleaching and coral community shifts

## Dataset Reference

**Source:** `ltem_historical_database` table via MCP server
**Bleaching column:** `bleaching_coverage` — percentage of coral showing bleaching
**Coral taxa:** Scleractinia (warm/hard corals), Holaxonia (cold/gorgonian corals)

### Bleaching Severity Scale

| Category | Coverage | Expected Impact |
|----------|---------|-----------------|
| None | 0% | Normal conditions |
| Low | <10% | Minor stress, likely recovery |
| Moderate | 10-30% | Significant stress, partial mortality possible |
| High | 30-60% | Severe stress, mortality likely |
| Severe | >60% | Mass bleaching, widespread mortality |

## MCP Tools Available

| Tool | Parameters | Purpose |
|------|-----------|---------|
| `bleaching_assessment` | `region?`, `year?` | Bleaching coverage with severity classification per reef |
| `coral_warm_cold_ratio` | `region?`, `year?` | Scleractinia vs Holaxonia balance per reef |
| `invertebrate_summary` | `region?`, `year?` | Overall invertebrate community context |
| `invertebrate_temporal_trends` | `region?`, `taxa2?` | Long-term trends in coral-associated invertebrates |

## Core Workflow

1. **Bleaching overview** — Call `bleaching_assessment` to see current bleaching coverage across reefs. Note severity classifications. If bleaching_coverage column is unavailable, the tool returns a warning
2. **Coral community balance** — Call `coral_warm_cold_ratio` to assess warm vs cold coral proportions. Rising warm:cold ratio may indicate warming effects
3. **Temporal bleaching trends** — Call `bleaching_assessment` for multiple years to track whether bleaching frequency or severity is increasing
4. **Invertebrate context** — Call `invertebrate_summary` to see the broader invertebrate community surrounding the corals
5. **Long-term coral trends** — Call `invertebrate_temporal_trends` with taxa2='Scleractinia' or specific coral groups to detect population changes
6. **Regional comparison** — Compare bleaching severity and coral ratios across regions to identify hotspots

## Aggregation Rules

- Bleaching coverage is averaged per reef (across transects)
- Warm/cold ratio computed from transect-level abundance averages per reef
- Invertebrate trends use reef-averaged annual means for Mann-Kendall
- Severity classification uses mean bleaching coverage per reef-year

## Interpretation Guide

| Pattern | Interpretation |
|---------|---------------|
| Bleaching > 30% at multiple reefs | Regional thermal stress event |
| Warm:cold ratio increasing over time | Tropicalization / warming signal |
| Warm:cold ratio > 2 in historically cold areas | Possible range expansion of warm corals |
| Scleractinia declining + bleaching increasing | Climate-driven coral loss |
| Holaxonia stable while Scleractinia declines | Cold corals more resilient to warming |
| Bleaching severity higher at shallow sites | Depth-dependent thermal vulnerability |

**Link to known events:**
- 2014-2016: Global coral bleaching event (El Nino)
- 2023-2024: Record marine heatwaves in Gulf of California
- High bleaching years should correlate with SST anomalies

## Success Criteria

A complete bleaching assessment includes:
- Bleaching coverage data with severity classification
- Warm/cold coral ratio for target reefs
- Temporal comparison showing bleaching trends
- Regional comparison identifying bleaching hotspots
- Ecological narrative linking bleaching to climate events and coral community shifts
