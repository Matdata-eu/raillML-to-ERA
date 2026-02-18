# SHACL Validation

This folder contains scripts for validating the generated ERA ontology graph against official ERA SHACL shapes.

## Overview

The validation process verifies that the transformed railML data complies with the ERA ontology constraints defined in SHACL shapes.

## Requirements

### maplib License

SHACL validation is performed using [maplib](https://www.data-treehouse.com/), a high-performance knowledge graph library that **requires a license** for SHACL validation features.

**For licensing information and documentation, visit: https://www.data-treehouse.com/**

⚠️ **Note**: The free version of maplib allows loading and querying knowledge graphs, but SHACL validation requires a paid license. The validation script will load the data successfully but will display a license message when attempting validation.

## Validation Script

### `validate.py`

Performs SHACL validation on the enriched ERA graph.

**Input:**
- `../03-post-process/era-graph-enriched.ttl` - The enriched ERA ontology graph

**SHACL Shapes (downloaded automatically):**
- [ERA-RINF-shapes.ttl](https://gitlab.com/era-europa-eu/public/interoperable-data-programme/era-ontology/era-ontology/-/blob/main/era-shacl/ERA-RINF-shapes.ttl)
- [SKOS-shapes.ttl](https://gitlab.com/era-europa-eu/public/interoperable-data-programme/era-ontology/era-ontology/-/blob/main/era-shacl/SKOS-shapes.ttl)

**Output:**
- `validation-report.ttl` - Detailed SHACL validation report (only with valid license)
- Console output with validation summary

**Usage:**
```powershell
python validate.py
```

The script will:
1. Download the latest ERA SHACL shapes from the official repository
2. Preprocess and load the enriched ERA graph (using rdflib to handle format compatibility)
3. Load SHACL shapes into a named graph
4. Perform SHACL validation (requires valid license)
5. Generate a detailed validation report
6. Display a summary of any constraint violations

### Technical Notes

**Data Preprocessing:**
The script uses `rdflib` to preprocess the Turtle file and convert it to N-Triples format before loading into maplib. This workaround ensures compatibility with maplib's parser and handles any encoding or format quirks in the source file.

**Data Quality Warnings:**
You may see warnings about integer conversion (e.g., `'120.0'` being stored as `xsd:integer`). These are data quality issues in the source graph where decimal values are incorrectly typed as integers, but they don't prevent validation from running.

## Validation Report

The validation report (`validation-report.ttl`) contains SHACL validation results showing:
- Constraint violations
- Affected nodes
- Constraint paths
- Violation messages
- Examples of non-conforming data

A summary is also printed to the console, grouping violations by path, message, and constraint component.
