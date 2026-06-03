# MCP Server Metadata

This directory contains metadata for the LTEM MCP server, enabling discoverability and documentation.

## Files

- **`template.json`** - Human-edited metadata template (edit this)
- **`manifest.json`** - Auto-generated manifest (do not edit manually)
- **`schema/`** - JSON Schema definitions for validation

## Metadata Layers

### 1. Package Metadata
- MCP server name, version, description
- Maintainer, license, repository
- Runtime requirements, Docker image

### 2. Dataset Metadata (DCAT-like)
- Title, description, keywords
- Spatial/temporal coverage
- Publisher, contact, license

### 3. Schema Metadata
- Database structure (tables, fields, types)
- Primary keys, indexes
- Constraints and relationships

### 4. Provenance & Analytics
- Source systems
- Processing steps
- Statistical methods
- Quality metrics

## Usage

### For Template Users

1. **Copy `template.json`** to your new MCP repository
2. **Edit all fields** to match your domain
3. **Validate** against `schema/metadata.schema.json`
4. **Generate manifest** (see below)

### Generating Manifest

```python
# Run this to generate manifest.json from template.json
python scripts/generate_metadata_manifest.py
```

### Exposing via MCP

Metadata is exposed as MCP resources:

```
ltem://metadata/manifest     # Full manifest
ltem://metadata/package      # Package info only
ltem://metadata/dataset      # Dataset info only
ltem://metadata/schema       # Schema info only
```

## Validation

```bash
# Validate template.json against schema
python -m jsonschema -i metadata/template.json metadata/schema/metadata.schema.json
```

## Best Practices

1. **Keep template.json up to date** - Update when adding tools/skills
2. **Regenerate manifest** after changes
3. **Validate before commit** - Ensure schema compliance
4. **Document changes** in CHANGELOG.md

## Schema Evolution

- **Breaking changes:** Increment major version
- **New fields:** Increment minor version
- **Bug fixes:** Increment patch version

Current schema version: `1.0.0`
