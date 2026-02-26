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

### Shape Fixes

Before validation, the script automatically applies SPARQL UPDATE queries from the `shape-fixes/` directory to correct known issues in the downloaded SHACL shapes. This allows us to adapt the official ERA shapes to work correctly with our transformation pipeline without modifying the upstream source.

**Location:** `shape-fixes/*.sparql`

Each `.sparql` file in this directory contains a SPARQL UPDATE query that modifies the SHACL shapes graph. Fixes are applied in alphabetical order after downloading and filtering the shapes but before validation.

**Example Use Cases:**
- Correcting overly restrictive datatype constraints
- Adjusting cardinality constraints to match actual ERA data
- Removing constraints that don't apply to our use case

**Current Fixes:**
- `document-url-iri.sparql` - Changes `era-sh:DocumentUrl` constraint from `sh:datatype xsd:anyURI` to `sh:nodeKind sh:IRI` to accept IRI nodes (not just typed literals)
- `topo-coordinate-0.sparql` - Changes `era-sh:OffsetFromOrigin` datatype from `xsd:positiveInteger` to `xsd:nonNegativeInteger` to allow zero values

To add a new fix, create a `.sparql` file with a SPARQL UPDATE query (DELETE/INSERT) in the `shape-fixes/` directory.

### `validate.py`

Performs SHACL validation on the enriched ERA graph.

## Data Graph Resources

The following resources are loaded into the data graph before validation is executed. All downloads are cached under `downloads/` and only re-fetched when the cached file is absent. To force a refresh, delete the corresponding file from `downloads/`.

| # | Resource | Source | Cached file | Purpose |
|---|----------|--------|-------------|---------|
| 1 | **Enriched ERA graph** | `../03-post-process/output/era-graph-enriched.ttl` | *(not cached — read directly)* | The transformed railML data being validated |
| 2 | **ERA ReferenceBorderPoint instances** | SPARQL CONSTRUCT on `https://data-interop.era.europa.eu/api/sparql` — all `era:ReferenceBorderPoint` triples | `downloads/reference-border-points.ttl` | Required for `era:referenceBorderPoint` constraints (the referenced resources are managed by ERA, not locally) |
| 3 | **ERA OWL ontology** | `https://gitlab.com/era-europa-eu/.../ontology.ttl` (main branch) | `downloads/era-ontology.ttl` | Provides class/property definitions needed for type-checking constraints |
| 4 | **ERA SKOS concept schemes** | All `*.ttl` files under `era-skos/` in the ERA ontology GitLab repository, merged into a single file | `downloads/merged-skos.ttl` (individual files as `downloads/skos-*.ttl`) | Required for SKOS vocabulary constraints (e.g. `era:opType`, `era:trainDetectionSystem` must reference known SKOS concepts) |

**SHACL Shapes (loaded into a named graph, not the data graph):**
- [ERA-RINF-shapes.ttl](https://gitlab.com/era-europa-eu/public/interoperable-data-programme/era-ontology/era-ontology/-/blob/main/era-shacl/ERA-RINF-shapes.ttl) — pinned to a specific commit; cached as `downloads/ERA-RINF-shapes.ttl`

---

**Input:**
- `../03-post-process/output/era-graph-enriched.ttl` - The enriched ERA ontology graph

**SHACL Shapes (downloaded automatically):**
- [ERA-RINF-shapes.ttl](https://gitlab.com/era-europa-eu/public/interoperable-data-programme/era-ontology/era-ontology/-/blob/main/era-shacl/ERA-RINF-shapes.ttl) — includes SKOS concept validation constraints (previously a separate `SKOS-shapes.ttl`, now merged)

**Output:**
- `validation-report.ttl` - Detailed SHACL validation report (only with valid license)
- `validation-summary.md` - Human-readable markdown summary of validation results
- Console output with validation summary

**Usage:**
```powershell
python validate.py
```

The script will:
1. Download the latest ERA SHACL shapes from the official repository
2. Preprocess and load the enriched ERA graph (using rdflib to handle format compatibility)
3. Filter out SHACL constraints with unimplemented GeoSPARQL functions
4. Apply shape fixes from `shape-fixes/*.sparql` to correct known issues
5. Load SHACL shapes into a named graph
6. Perform SHACL validation (requires valid license)
7. Generate a detailed validation report
8. Display and save a summary of any constraint violations

### Technical Notes

**Data Preprocessing:**
The script uses `rdflib` to preprocess the Turtle file and convert it to N-Triples format before loading into maplib. This workaround ensures compatibility with maplib's parser and handles any encoding or format quirks in the source file.

**Data Quality Warnings:**
You may see warnings about integer conversion (e.g., `'120.0'` being stored as `xsd:integer`). These are data quality issues in the source graph where decimal values are incorrectly typed as integers, but they don't prevent validation from running.

## Validation Report

The validation produces two output files:

### `validation-report.ttl`
The detailed SHACL validation report in RDF/Turtle format containing:
- Constraint violations
- Affected nodes
- Constraint paths
- Violation messages
- Examples of non-conforming data

### `validation-summary.md`
A human-readable markdown summary with:
- Overall validation status (✅ PASSED / ❌ FAILED)
- Timestamp of validation run
- Table of violations grouped by property path and constraint type
- Violation counts and example nodes
- Recommendations for addressing violations

A summary is also printed to the console, grouping violations by path, message, and constraint component.
