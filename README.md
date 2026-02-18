# Advanced Example: railML® to ERA Ontology Conversion

## Overview
This example demonstrates a possible pipeline for converting railML 3.2 infrastructure data to the ERA (European Railway Agency) ontology format.

⚠️ This is an pipeline specifically constructed to be used for the [advanced example v14 of railML®](https://www.railml.org/en/example-data) and in preparation of a Workshop at ERA. Most of the scripts will be useful when starting from another railML® file but the result will be different. Certain assumptions have been taken and some values are hardcoded. Use with caution.

⚠️ Due to the applicable license of railML®, the advanced-example.xml file has not been added to this repository. See [01-prep readme](01-prep/README.md) for more information.

The conversion follows a three-step process:
1. **Preparation** - Extract RDF from railML XML
2. **Construction** - Transform to ERA ontology structure
3. **Post-Processing** - Enrich with computed data

## Quick Start

### Prerequisites
- Docker (for SPARQL Anything)
- Python 3.8+ with virtual environment
- Apache Jena Fuseki server (optional, recommended)

### Install Python Dependencies
```powershell
pip install requests rdflib shapely
```

### Run Complete Pipeline
```powershell
# Step 1: Convert railML XML to RDF
cd 01-prep
.\run-prep.ps1

# Step 2: Transform to ERA ontology
cd ..\02-construct
python run-construct.py

# Step 3: Enrich with computed data
cd ..\03-post-process
.\run-post-process.ps1
```

## Pipeline Steps

### [01-prep](01-prep/) - Preparation
Converts railML 3.2 XML to raw RDF using SPARQL Anything.

**Output:** `one-eyed-graph.ttl` (railML data in RDF format)

[📖 Read more](01-prep/README.md)

### [02-construct](02-construct/) - CONSTRUCT Queries
Transforms railML RDF to ERA ontology using SPARQL CONSTRUCT queries organized by domain:
- Common (infrastructure managers, positioning systems)
- Topology (net elements, relations)
- Functional Infrastructure (tracks, signals, switches, platforms, etc.)

**Output:** `era-graph.ttl` (ERA ontology graph)

[📖 Read more](02-construct/README.md)

### [03-post-process](03-post-process/) - Post-Processing
Enriches ERA graph with computed data:
- Temporal validity information
- Point geometries via linear referencing

**Output:** `era-graph-enriched.ttl` (final enriched ERA graph)

[📖 Read more](03-post-process/README.md)

## Data Flow

```
railML XML
    ↓
[01-prep] SPARQL Anything
    ↓
one-eyed-graph.ttl (RDF)
    ↓
[02-construct] SPARQL CONSTRUCT queries
    ↓
era-graph.ttl (ERA ontology)
    ↓
[03-post-process] Enrichment
    ↓
era-graph-enriched.ttl (final)
```

## Fuseki Integration

All steps support Apache Jena Fuseki for data storage and querying:
- **Step 01:** Uploads to `advanced-example-one-eyed/`
- **Step 02:** Reads from `advanced-example-one-eyed/`, writes to `advanced-example/`
- **Step 03:** Updates `advanced-example/` with enriched data

If Fuseki is unavailable, all steps gracefully fall back to local file processing.

## Directory Structure

```
advanced-example/
├── 00-docs/              # Documentation and schemas
├── 01-prep/              # XML → RDF conversion
├── 02-construct/         # RDF → ERA ontology transformation
│   ├── 01-common/
│   ├── 02-topology/
│   └── 03-functional-infrastructure/
└── 03-post-process/      # Data enrichment
```

## Notes

- Each step can run independently if previous outputs are available
- Local TTL files are always created as backup
- CONSTRUCT queries follow ERA ontology SHACL constraints
- Geometry enrichment uses Shapely for linear referencing calculations
