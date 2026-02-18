# Step 02: CONSTRUCT Queries

## Overview
Transform railML RDF (one-eyed graph) to ERA ontology using SPARQL CONSTRUCT queries.

## Input
- Source: `http://localhost:8082/jena-fuseki/advanced-example-one-eyed/` (one-eyed graph from step 01)
- SPARQL queries in subdirectories:
  - `01-common/` - Infrastructure managers, positioning systems
  - `02-topology/` - Net elements, net relations
  - `03-functional-infrastructure/` - Tracks, signals, switches, etc.

## Output
- `era-graph.ttl` - Complete ERA ontology graph (all CONSTRUCT queries combined)
- Uploaded to Fuseki: `http://localhost:8082/jena-fuseki/advanced-example/`

## Usage
```powershell
python run-construct.py
```

## Requirements
- Python 3.8+
- `requests` library (`pip install requests`)
- Source Fuseki endpoint available (one-eyed graph)

## Notes
- Queries are executed in alphanumeric order
- Each query's results are combined into a single TTL file
- If Fuseki is unavailable, only local TTL file is created
- Target Fuseki endpoint is cleared before execution
