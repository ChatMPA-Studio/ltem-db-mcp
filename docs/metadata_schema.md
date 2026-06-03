# Metadata Schema Documentation

**Purpose:** Define the 4-layer metadata model for CRAN-style discoverability

**Version:** 1.0.0  
**Last Updated:** February 16, 2026

---

## Overview

MCP server metadata is split into **4 layers** for scalability and clarity:

1. **Package Metadata** - The MCP server itself
2. **Dataset Metadata** - The data being exposed (DCAT-like)
3. **Schema Metadata** - Database structure and entities
4. **Provenance + Analytical Metadata** - Source systems and processing

---

## Layer 1: Package Metadata

**Purpose:** Describe the MCP server as a software package

### Required Fields

```json
{
  "package": {
    "name": "ltem-db-mcp",
    "version": "1.2.0",
    "description": "Long-Term Ecological Monitoring Database MCP Server",
    "maintainer": {
      "name": "CBMC",
      "email": "contact@cbmc.org",
      "organization": "Community-Based Marine Conservation"
    },
    "license": "MIT",
    "repository": {
      "type": "git",
      "url": "https://github.com/your-org/ltem-db-mcp"
    },
    "homepage": "https://github.com/your-org/ltem-db-mcp",
    "runtime": {
      "python_version": ">=3.10",
      "dependencies": [
        "fastmcp>=0.3.0",
        "pymysql>=1.1.0",
        "pydantic>=2.0.0",
        "scipy>=1.11.0",
        "numpy>=1.24.0"
      ],
      "docker_image": "ltem-mcp:1.2.0",
      "port": 8000,
      "base_path": "/mcp"
    }
  }
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | ✅ | Package name (lowercase, hyphens) |
| `version` | string | ✅ | Semantic version (X.Y.Z) |
| `description` | string | ✅ | One-line summary (10-500 chars) |
| `maintainer` | object | ✅ | Contact information |
| `license` | string | ✅ | SPDX license identifier |
| `repository` | object | ⚠️ | Git repository URL |
| `homepage` | string | ⚠️ | Project homepage |
| `runtime` | object | ⚠️ | Runtime requirements |

**Validation:**
- `name` must match pattern `^[a-z0-9-]+$`
- `version` must match pattern `^\\d+\\.\\d+\\.\\d+$`
- `license` must be valid SPDX identifier

---

## Layer 2: Dataset Metadata (DCAT-like)

**Purpose:** Describe the data being exposed (Dublin Core + DCAT standards)

### Required Fields

```json
{
  "dataset": {
    "title": "LTEM Historical Database",
    "description": "Long-term ecological monitoring data from reef fish surveys...",
    "keywords": [
      "ecology",
      "marine biology",
      "reef fish",
      "monitoring",
      "MPA effectiveness"
    ],
    "spatial_coverage": {
      "description": "Gulf of California, Mexico",
      "regions": ["Cabo Pulmo", "La Paz", "Loreto"],
      "bounding_box": {
        "north": 29.5,
        "south": 23.0,
        "east": -109.0,
        "west": -114.0
      }
    },
    "temporal_coverage": {
      "start": "1999-01-01",
      "end": "2024-12-31",
      "frequency": "annual",
      "total_years": 25
    },
    "publisher": {
      "name": "Community-Based Marine Conservation",
      "url": "https://cbmc.org"
    },
    "contact": {
      "name": "CBMC Data Team",
      "email": "data@cbmc.org"
    },
    "language": "en",
    "update_frequency": "annually",
    "access": "restricted",
    "license": "CC-BY-NC-4.0"
  }
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | ✅ | Dataset title |
| `description` | string | ✅ | Detailed description (≥50 chars) |
| `keywords` | array | ✅ | Search keywords (≥3) |
| `spatial_coverage` | object | ⚠️ | Geographic extent |
| `temporal_coverage` | object | ⚠️ | Time range |
| `publisher` | object | ✅ | Data publisher |
| `contact` | object | ✅ | Contact for questions |
| `language` | string | ⚠️ | ISO 639-1 code (e.g., "en") |
| `update_frequency` | string | ⚠️ | Update cadence |
| `access` | string | ⚠️ | "public" or "restricted" |
| `license` | string | ✅ | Data license |

**DCAT Alignment:**
- `title` → `dcat:title`
- `description` → `dcat:description`
- `keywords` → `dcat:keyword`
- `spatial_coverage` → `dcat:spatial`
- `temporal_coverage` → `dcat:temporal`
- `publisher` → `dct:publisher`

---

## Layer 3: Schema Metadata

**Purpose:** Document database structure and entities

### Database Schema

```json
{
  "schema": {
    "database": {
      "type": "MySQL",
      "version": "8.0",
      "name": "ecological_monitoring",
      "tables": [
        {
          "name": "ltem_historical_database",
          "description": "Main observation table with fish survey data",
          "row_count": 500000,
          "primary_key": ["Year", "Region", "Reef", "Transect", "Species"],
          "indexes": ["idx_year", "idx_region", "idx_species"]
        }
      ]
    }
  }
}
```

### Entity Schema

```json
{
  "schema": {
    "entities": [
      {
        "name": "Observation",
        "description": "Individual fish observation record",
        "fields": [
          {
            "name": "Year",
            "type": "INTEGER",
            "description": "Survey year",
            "required": true
          },
          {
            "name": "Biomass",
            "type": "DECIMAL(10,2)",
            "description": "Biomass in g/m²",
            "required": false,
            "units": "g/m²",
            "constraints": {
              "min": 0,
              "max": 10000
            }
          }
        ]
      }
    ]
  }
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `database.type` | string | ✅ | Database type (MySQL, PostgreSQL, etc.) |
| `database.name` | string | ✅ | Database name |
| `tables` | array | ✅ | List of tables |
| `entities` | array | ✅ | Entity definitions |
| `fields` | array | ✅ | Field definitions with types |

**JSON Schema Support:**
- Each entity can reference a JSON Schema file
- Enables validation and code generation
- Supports complex types and relationships

---

## Layer 4: Provenance + Analytical Metadata

**Purpose:** Document data lineage and analytical methods

### Provenance

```json
{
  "provenance": {
    "source_systems": [
      {
        "name": "LTEM Survey Database",
        "type": "MySQL",
        "description": "Primary data collection system"
      }
    ],
    "extraction": {
      "method": "Direct database connection",
      "frequency": "real-time",
      "last_updated": "2024-12-31"
    },
    "processing": {
      "steps": [
        "Quality control validation",
        "Taxonomic standardization",
        "Biomass calculation (length-weight relationships)",
        "Trophic group assignment",
        "Aggregation to transect level"
      ],
      "methodology": "See docs/METHODOLOGY_COMPLIANCE.md"
    },
    "quality": {
      "completeness": 0.98,
      "accuracy": "Field-validated",
      "consistency": "Standardized protocols since 1999"
    }
  }
}
```

### Analytics

```json
{
  "analytics": {
    "statistical_methods": [
      "Mann-Kendall trend test",
      "Kruskal-Wallis test",
      "Spearman correlation",
      "Bootstrap resampling",
      "BACI analysis"
    ],
    "aggregation_rules": {
      "sample_unit": "transect",
      "hierarchy": "transect → reef → region",
      "method": "SUM at transect level, then MEAN/MEDIAN at higher levels"
    }
  }
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_systems` | array | ⚠️ | Origin of data |
| `extraction` | object | ⚠️ | How data is extracted |
| `processing` | object | ⚠️ | Processing steps |
| `quality` | object | ⚠️ | Quality metrics |
| `statistical_methods` | array | ⚠️ | Available statistical methods |
| `aggregation_rules` | object | ⚠️ | How data is aggregated |

---

## Metadata Storage

### File Locations

```
metadata/
├── template.json          # Human-edited (source of truth)
├── manifest.json          # Auto-generated (do not edit)
├── schema/                # JSON Schema definitions
│   └── metadata.schema.json
└── README.md              # Usage documentation
```

### Generation Workflow

```bash
# 1. Edit template
nano metadata/template.json

# 2. Validate against schema
python -m jsonschema -i metadata/template.json metadata/schema/metadata.schema.json

# 3. Generate manifest
python scripts/generate_metadata_manifest.py

# 4. Commit both files
git add metadata/template.json metadata/manifest.json
git commit -m "Update metadata"
```

---

## Exposure via MCP Resources

Metadata MUST be accessible through MCP resources:

### Resource URIs

```
domain://metadata/manifest       # Full manifest
domain://metadata/package        # Package info only
domain://metadata/dataset        # Dataset info only
domain://metadata/schema         # Schema info only
domain://metadata/provenance     # Provenance info only
```

### Implementation Example

```python
# mcp_server/server.py
from pathlib import Path
import json

@mcp.resource("ltem://metadata/manifest")
def get_metadata_manifest() -> str:
    """Get full metadata manifest."""
    manifest_path = Path(__file__).parent.parent / "metadata" / "manifest.json"
    if manifest_path.exists():
        return manifest_path.read_text()
    return json.dumps({"error": "Manifest not found"})

@mcp.resource("ltem://metadata/package")
def get_package_metadata() -> str:
    """Get package metadata only."""
    manifest_path = Path(__file__).parent.parent / "metadata" / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        return json.dumps(manifest.get("package", {}))
    return json.dumps({"error": "Manifest not found"})
```

---

## Validation Rules

### Template Validation

```bash
# Validate template.json against schema
python -m jsonschema -i metadata/template.json metadata/schema/metadata.schema.json
```

### Required Fields Check

```python
# scripts/validate_metadata.py
import json
from pathlib import Path

def validate_metadata():
    """Validate metadata completeness."""
    template_path = Path("metadata/template.json")
    template = json.loads(template_path.read_text())
    
    # Check required top-level keys
    required_keys = ["package", "dataset", "schema", "endpoints"]
    for key in required_keys:
        assert key in template, f"Missing required key: {key}"
    
    # Check package required fields
    package = template["package"]
    assert "name" in package
    assert "version" in package
    assert "description" in package
    assert "license" in package
    
    print("✓ Metadata validation passed")

if __name__ == "__main__":
    validate_metadata()
```

---

## Best Practices

### 1. Keep Template Up to Date

Update `metadata/template.json` when:
- Adding/removing tools
- Adding/removing skills
- Changing version
- Updating dependencies
- Modifying database schema

### 2. Regenerate Manifest After Changes

```bash
# Always regenerate after editing template
python scripts/generate_metadata_manifest.py
```

### 3. Version Metadata Schema

Track schema changes:
- **Breaking changes:** Increment major version
- **New fields:** Increment minor version
- **Bug fixes:** Increment patch version

### 4. Document Custom Fields

If adding custom fields beyond the standard schema:

```json
{
  "custom": {
    "domain_specific_field": "value",
    "_comment": "Custom fields for domain-specific needs"
  }
}
```

### 5. Validate Before Commit

```bash
# Pre-commit hook
python -m jsonschema -i metadata/template.json metadata/schema/metadata.schema.json
python scripts/generate_metadata_manifest.py
git add metadata/manifest.json
```

---

## Examples

### Minimal Metadata

```json
{
  "package": {
    "name": "my-mcp",
    "version": "1.0.0",
    "description": "My MCP server",
    "license": "MIT"
  },
  "dataset": {
    "title": "My Dataset",
    "description": "Description of my dataset with at least 50 characters for validation.",
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "publisher": {"name": "My Org"},
    "contact": {"email": "contact@example.com"},
    "license": "CC-BY-4.0"
  },
  "schema": {
    "database": {
      "type": "MySQL",
      "name": "my_database",
      "tables": []
    },
    "entities": []
  },
  "endpoints": {
    "tools": {"count": 0},
    "skills": {"count": 0},
    "resources": {"count": 0}
  }
}
```

### Complete Metadata

See `metadata/template.json` in this repository for a complete example.

---

## Future Enhancements (Phase 2)

### Planned Additions

1. **Linked Data Support**
   - RDF/JSON-LD export
   - Schema.org vocabulary
   - DCAT-AP compliance

2. **Versioned Metadata**
   - Track metadata history
   - Link to specific data versions
   - Changelog integration

3. **Automated Discovery**
   - MCP registry integration
   - Search API
   - Metadata harvesting

4. **Quality Metrics**
   - Automated completeness scoring
   - Validation reports
   - Compliance badges

---

## See Also

- [metadata/README.md](../metadata/README.md) - Metadata usage guide
- [docs/mcp_template_spec.md](mcp_template_spec.md) - Repository structure
- [scripts/generate_metadata_manifest.py](../scripts/generate_metadata_manifest.py) - Generation script

---

**Version:** 1.0.0  
**Last Review:** February 16, 2026
