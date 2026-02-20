# Step 03: Post-Processing

## Overview
Enrich the ERA graph with computed data: temporal information, topology-based relations, geometries, and data quality fixes.

## Processing Steps
1. **SPARQL Updates** (`sparql-update/`): Add temporal data, RDF types, and infer topology-based part relations
2. **Geometry Enrichment**: Compute point geometries using linear referencing
3. **Data Fixes** (`data-fixes/`): Apply corrections for validation issues
4. **Output Finalization**: Export enriched graph from Fuseki

## Input
- ERA graph from step 02 (Fuseki or local file)
- SPARQL update queries in `sparql-update/` and `data-fixes/`

## Output
- `era-graph-enriched.ttl` - Final enriched ERA graph
- Updated in Fuseki: `http://localhost:8082/jena-fuseki/advanced-example/`

## Usage
```powershell
.\run-post-process.ps1
```

## Requirements
- Python 3.8+ with `rdflib`, `shapely`, `requests`
- Fuseki endpoint (optional, falls back to local file)

## Key Features
- **Topology Relations**: Infers `isPartOf`/`hasPart` based on network position overlap
- **Linear Referencing**: Computes point geometries from linear positions
- **Fallback Mode**: Works offline if Fuseki unavailable
