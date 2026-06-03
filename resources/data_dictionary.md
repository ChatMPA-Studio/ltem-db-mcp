# LTEM Database — Data Dictionary

## Overview

The Long-Term Ecological Monitoring (LTEM) database tracks reef fish communities
across the Gulf of California and Mexican Pacific coast since 1998. Data is
collected via underwater visual census (UVC) along 50m x 5m belt transects.

## Tables

### ltem_historical_database

The main observations table. Each row represents one species observation on one transect.

| Column         | Type          | Description                                      |
|----------------|---------------|--------------------------------------------------|
| Year           | INT           | Survey year (1998–present)                       |
| Month          | INT           | Survey month (1–12)                              |
| Region         | VARCHAR(100)  | Geographic region name                           |
| IDReef         | VARCHAR(50)   | Unique reef/site identifier                      |
| Reef           | VARCHAR(100)  | Reef site name                                   |
| Habitat        | VARCHAR(50)   | Depth category: "Shallow" or "Deep"              |
| Transect       | INT           | Transect replicate number (1–4)                  |
| Species        | VARCHAR(200)  | Scientific species name                          |
| Quantity       | INT           | Number of individuals observed                   |
| Size           | DECIMAL(10,2) | Estimated total length in centimeters            |
| Biomass        | DECIMAL(15,6) | Calculated biomass in grams per square meter     |
| MPA            | VARCHAR(100)  | Marine Protected Area classification             |
| TrophicGroup   | VARCHAR(50)   | Trophic group (Herbivoro, Carnivoro, etc.)       |
| Latitude       | DECIMAL(10,6) | Site latitude (decimal degrees)                  |
| Longitude      | DECIMAL(10,6) | Site longitude (decimal degrees)                 |
| Day            | INT           | Survey day of month (1–31)                       |
| Label          | VARCHAR(10)   | Survey type: "PEC" (fish) or "INV" (invertebrates) |
| IDSpecies      | VARCHAR(50)   | Unique species identifier code                   |
| Taxa2          | VARCHAR(100)  | Taxonomic class/order (e.g. Asteroidea, Echinoidea) |
| Taxa3          | VARCHAR(100)  | Taxonomic order/suborder (e.g. Scleractinia, Holaxonia) |
| Phylum         | VARCHAR(100)  | Taxonomic phylum (e.g. Echinodermata, Cnidaria)  |
| TrophicLevelF  | VARCHAR(20)   | Categorical trophic level range (e.g. "2-2.5", "4-4.5") |
| TrophicLevel   | DECIMAL(5,2)  | Numeric trophic level value                      |
| Functional_groups | VARCHAR(50) | Functional group code (e.g. GenPred_solitary, Plank) |
| Depth2         | VARCHAR(20)   | Simplified depth category: "Shallow" or "Deep"   |
| Degree         | INT           | Rounded latitude (for latitudinal gradient analysis) |
| Area           | DECIMAL(10,2) | Transect area in square meters                   |
| A_ord          | DECIMAL(15,8) | Length-weight parameter a (allometric coefficient) |
| B_pen          | DECIMAL(10,6) | Length-weight parameter b (allometric exponent)   |
| SST            | DECIMAL(8,4)  | Sea surface temperature (degrees Celsius)        |
| Chla           | DECIMAL(10,6) | Chlorophyll-a concentration (mg/m3)              |
| bleaching_coverage | DECIMAL(8,4) | Coral bleaching coverage percentage             |
| Protection_status | VARCHAR(50) | Protection status classification                 |
| Protection_level | VARCHAR(50)  | Protection enforcement level                     |

### ltem_monitoring_species

Reference table of all species recorded across LTEM surveys.

| Column         | Type          | Description                                      |
|----------------|---------------|--------------------------------------------------|
| Species        | VARCHAR(200)  | Scientific species name                          |
| CommonName     | VARCHAR(200)  | Common name (where available)                    |
| Family         | VARCHAR(100)  | Taxonomic family                                 |
| TrophicGroup   | VARCHAR(50)   | Assigned trophic group                           |

### ltem_monitoring_reefs

Reference table of all surveyed reef sites.

| Column         | Type          | Description                                      |
|----------------|---------------|--------------------------------------------------|
| IDReef         | VARCHAR(50)   | Unique reef identifier                           |
| Reef           | VARCHAR(100)  | Reef name                                        |
| Region         | VARCHAR(100)  | Geographic region                                |
| MPA            | VARCHAR(100)  | Marine Protected Area classification             |
| Latitude       | DECIMAL(10,6) | Latitude (decimal degrees)                       |
| Longitude      | DECIMAL(10,6) | Longitude (decimal degrees)                      |

## Key Dimensions

- **Regions**: 14 regions from Alto Golfo to Revillagigedo
- **Time span**: 1998–present (annual surveys, typically summer)
- **Protection levels**: Cabo Pulmo (fully protected), Weak/Paper Park, Unprotected
- **Trophic groups**: Herbivoro, Carnivoro, Piscivoro, Zooplanctivoro
- **Depth categories**: Shallow (5–8m), Deep (10–15m)

## Units

- **Biomass**: grams per square meter (g/m²)
- **Size**: total length in centimeters (cm)
- **Quantity**: count of individuals per transect observation
- **Coordinates**: decimal degrees (WGS84)
