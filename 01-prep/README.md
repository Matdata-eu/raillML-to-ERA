# Step 01: Preparation

## Overview
Convert railML 3.2 XML data to RDF using SPARQL Anything.

## Important: Source Data Licensing
The railML example file cannot be included in this repository due to licensing restrictions. You need to:

1. Obtain the original `2025-11-03_railML_AdvancedExample_v14_railML3.2.xml` file from railML.org
2. Run the patch script: `python patch-railml.py`
3. This creates `2025-11-03_railML_AdvancedExample_v14_railML3.2_patched.xml` with additional content added

The patch script adds:
- Electrification system definitions and detailed parameters
- Loading gauge specifications
- Track gauge definitions
- Platform height and overcrossing length measurements

## Input
- `2025-11-03_railML_AdvancedExample_v14_railML3.2_patched.xml` - railML infrastructure data (created by patch-railml.py)
- `one-eyed-graph.sparql` - SPARQL query to extract RDF from XML

## Output
- `one-eyed-graph.ttl` - Raw RDF graph extracted from railML XML
- Uploaded to Fuseki: `http://localhost:8082/jena-fuseki/advanced-example-one-eyed/`

## Usage
```powershell
.\run-prep.ps1
```

## Requirements
- Docker (for SPARQL Anything container)
- Apache Jena Fuseki server running on port 8082 (optional)

## Notes
- If Fuseki is unavailable, output is saved locally only
- The one-eyed graph contains railML data in RDF format but not yet mapped to ERA ontology
