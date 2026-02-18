# Step 03: Post-Processing

## Overview
Enrich the ERA graph with computed data: temporal information, topology-based part relations, and geometries.

## Input
- Source: `http://localhost:8082/jena-fuseki/advanced-example/` (ERA graph from step 02)
- `add-temporal.sparql` - Add temporal validity data
- `infer-part-relations.sparql` - Infer isPartOf/hasPart relations based on network topology
- `enrich-geometries.py` - Compute NetPointReference geometries using linear referencing

## Output
- `era-graph-enriched.ttl` - Final enriched ERA ontology graph
- Updated in Fuseki: `http://localhost:8082/jena-fuseki/advanced-example/`

## Usage
```powershell
.\run-post-process.ps1
```

## Requirements
- Python 3.8+
- `rdflib`, `shapely`, `requests` libraries (`pip install rdflib shapely requests`)
- Source Fuseki endpoint available (ERA graph)

## Notes
- Part relation inference uses network topology matching:
  - Point elements (signals, switches, etc.) are linked to tracks if their network reference is on the same LinearElement within the track's extent
  - Linear elements (tracks, tunnels, bridges, etc.) are linked to higher elements (SectionsOfLine) when their network references partly or completely overlap
  - Point elements are linked to OperationalPoints if they share the same LinearElement
- Geometry enrichment uses linear referencing to compute POINT geometries for NetPointReferences
- If Fuseki is unavailable, works with local TTL file from step 02
- Temporal data processing is skipped if `add-temporal.sparql` is empty
