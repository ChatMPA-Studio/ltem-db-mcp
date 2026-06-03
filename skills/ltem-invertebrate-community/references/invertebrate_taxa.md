# Invertebrate Taxa Reference

## Taxonomic Hierarchy

The LTEM database uses a three-level taxonomic classification for invertebrates:

```
Phylum > Taxa2 (class-level) > Taxa3 (order/suborder-level)
```

### Key Columns

| Column | Level | Examples |
|--------|-------|---------|
| `Phylum` | Phylum | Echinodermata, Cnidaria, Arthropoda |
| `Taxa2` | Class/Order | Asteroidea, Echinoidea, Holothuroidea |
| `Taxa3` | Order/Suborder | Scleractinia, Holaxonia, Valvatida |

## Key Indicator Taxa

### Echinoderms

| Taxa2 | Common Name | Ecological Role | Key Species |
|-------|-------------|----------------|-------------|
| **Asteroidea** | Sea stars | Keystone predators; control bivalve and coral populations | *Acanthaster planci* (crown-of-thorns), *Phataria unifascialis* |
| **Echinoidea** | Sea urchins | Herbivores; control algal cover on reefs | *Diadema mexicanum*, *Eucidaris thouarsii* |
| Holothuroidea | Sea cucumbers | Detritivores; bioturbation and nutrient cycling | *Isostichopus fuscus* (commercially valuable) |

### Cnidarians (Corals)

| Taxa3 | Type | Thermal Affinity | Ecological Role |
|-------|------|-----------------|----------------|
| **Scleractinia** | Hard corals | Warm water | Primary reef builders; create structural habitat |
| **Holaxonia** | Gorgonians | Cold water | Soft coral gardens; cold-current indicators |

## Warm vs Cold Coral Rationale

The Scleractinia:Holaxonia ratio serves as a **thermal regime indicator** in the Gulf of California:

- **Scleractinia (warm corals)** — Hermatypic (reef-building) corals that thrive in warm tropical/subtropical waters (>22C). Their abundance increases with warming.
- **Holaxonia (cold corals)** — Gorgonian sea fans and sea whips that are more abundant in cooler, nutrient-rich waters associated with upwelling.

### Ecological Interpretation

| Ratio Pattern | Interpretation |
|--------------|---------------|
| Warm:Cold ratio increasing | Warming trend; tropicalization of the reef |
| Warm:Cold ratio > 2 in historically cold areas | Range expansion of warm-water species |
| Warm:Cold ratio decreasing | Cooling (unusual) or warm coral mortality (bleaching) |
| Both declining | General reef degradation (non-thermal stressor) |

## Climate Period Definitions

The LTEM analysis uses three climate periods for invertebrate gradient analysis:

| Period | Years | Rationale |
|--------|-------|-----------|
| **Historical** | 1998-2013 | Pre-warming baseline; includes 1997-98 El Nino recovery |
| **Warming** | 2014-2024 | Marine heatwave era; includes 2014-16 global bleaching event |
| **Current** | 2025+ | Most recent data for comparison with historical baselines |

These periods are defined in `tools/invertebrates.py` as `_PERIOD_RANGES`.

## Latitudinal Gradient Context

The Gulf of California spans ~22N to ~31N latitude, creating a natural environmental gradient:

| Degree | Representative Region | Thermal Character |
|--------|---------------------|-------------------|
| 31 | Alto Golfo | Cool, high productivity, upwelling |
| 27-29 | Santa Rosalia, San Basilio, Loreto | Transitional |
| 24-26 | La Paz, La Ventana, Corredor | Warm tropical |
| 23 | Cabo Pulmo, Los Cabos | Warm, lower Chl-a |

The `Degree` column in the database is the rounded latitude, used for latitudinal gradient analyses.

## Data Filtering

All invertebrate tools filter to `Label = 'INV'` to separate invertebrate survey data from fish surveys (`Label = 'PEC'`). This is critical because:
- INV surveys use different transect protocols from PEC
- Abundance units are not directly comparable between PEC and INV
- Species identifications differ (fish vs invertebrate taxonomic expertise)
