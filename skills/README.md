# Skills Directory

Agent-agnostic analytical skills for the LTEM MCP Server. Any AI agent (Claude Code, ChatGPT, Cursor, Copilot, etc.) can read these files to understand how to perform ecological analyses using the MCP tools.

## Structure

```
skills/
├── README.md                          # This file
├── ltem-fish-community/
│   └── SKILL.md                       # Fish community structure analysis
├── ltem-biomass-productivity/
│   └── SKILL.md                       # Biomass and productivity analysis
├── ltem-mpa-effectiveness/
│   └── SKILL.md                       # Marine Protected Area effectiveness
├── ltem-temporal-trends/
│   └── SKILL.md                       # Temporal trend detection
├── ltem-nrsi-index/
│   ├── SKILL.md                       # Normalized Reef State Index
│   └── references/
│       └── nrsi_methodology.md        # NRSI formula and interpretation
├── ltem-invertebrate-community/
│   ├── SKILL.md                       # Invertebrate community analysis
│   └── references/
│       └── invertebrate_taxa.md       # Taxa hierarchy and indicator species
├── ltem-functional-groups/
│   └── SKILL.md                       # Functional group analysis
├── ltem-environmental-drivers/
│   └── SKILL.md                       # Environmental driver correlations
├── ltem-data-quality/
│   └── SKILL.md                       # Data quality assessment
├── ltem-survey-numeralia/
│   └── SKILL.md                       # Survey effort and numeralia
└── ltem-bleaching-assessment/
    └── SKILL.md                       # Coral bleaching assessment
```

## SKILL.md Format

Each skill file follows this format:

```yaml
---
name: skill-name
description: One-line description of what the skill does.
---

# Skill Title

## Purpose
What questions this skill helps answer.

## MCP Tools Available
Table of tools with parameters and purpose.

## Core Workflow
Numbered steps to perform the analysis.

## Aggregation Rules
How data is aggregated internally.

## Interpretation Guide
Reference ranges and thresholds for key metrics.

## Success Criteria
What a complete analysis should include.
```

## How Agents Should Use Skills

1. **Read the SKILL.md** for the relevant analysis domain
2. **Follow the Core Workflow** steps in order, calling the listed MCP tools
3. **Use the Interpretation Guide** to contextualize numeric results
4. **Check Success Criteria** to ensure the analysis is complete
5. **Read reference files** (in `references/` subdirectories) for deeper methodology context

## Adding New Skills

To add a skill for a new analysis domain:

1. Create a directory: `skills/your-skill-name/`
2. Write `SKILL.md` following the format above
3. Optionally add `references/` subdirectory for methodology docs
4. Update `docs/skills-reference.md` with the new skill entry
