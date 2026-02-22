# railML® to ERA Ontology Conversion

## Overview

Pipeline for converting [railML 3.2](https://www.railml.org/en/example-data) infrastructure data to the [ERA ontology](https://data-interop.era.europa.eu/) (RINF-compatible RDF).

> ⚠️ Built around the **advanced example v14** of railML® in preparation for a Workshop at ERA. Scripts are reusable but assumptions are hardcoded — use with caution for other inputs.

> ⚠️ The `advanced-example.xml` source file is not included due to railML® licensing. See [01-prep/README.md](01-prep/README.md).

## Pipeline

```
railML XML
  ↓ [01-prep]         SPARQL Anything → one-eyed-graph.ttl
  ↓ [02-construct]    SPARQL CONSTRUCT → era-graph.ttl
  ↓ [03-post-process] Geometry enrichment → era-graph-enriched.ttl
  ↓ [04-validate]     SHACL validation → validation-report.ttl
  ↓ [upload-to-rinf]  Upload to https://jena.matdata.eu/rinf
```

A separate standalone script in [06-create-topology](06-create-topology/) builds ERA topology from Belgian open rail segment data (Infrabel).

## Steps

| Step | Folder | Purpose | Output |
|---|---|---|---|
| 1 | [01-prep](01-prep/) | Convert railML XML → raw RDF via SPARQL Anything | `one-eyed-graph.ttl` |
| 2 | [02-construct](02-construct/) | SPARQL CONSTRUCT queries → ERA ontology | `era-graph.ttl` |
| 3 | [03-post-process](03-post-process/) | Geometry enrichment, data fixes | `era-graph-enriched.ttl` |
| 4 | [04-validate](04-validate/) | SHACL validation against ERA shapes (requires maplib license) | `validation-report.ttl` |
| 5 | [05-shacl-shacl](05-shacl-shacl/) | Validate the SHACL shapes themselves | — |
| 6 | [06-create-topology](06-create-topology/) | Build ERA topology from Infrabel open data | `topology.ttl` |

## Quick Start

### Prerequisites
- Docker (for SPARQL Anything in step 1)
- Python 3.10+ with virtual environment
- Apache Jena Fuseki (optional, recommended)

```powershell
pip install -r requirements.txt
```

### Run

```powershell
cd 01-prep        ; .\run-prep.ps1
cd ..\02-construct; .\run-construct.ps1
cd ..\03-post-process; .\run-post-process.ps1
cd ..\04-validate ; python validate.py
```

To upload to the remote Fuseki instance:

```powershell
.\upload-to-rinf.ps1
```

## Fuseki Integration

Steps 01–03 read/write named graphs in a local Fuseki instance and fall back to local files when unavailable.

| Step | Dataset |
|---|---|
| 01 | `advanced-example-one-eyed/` |
| 02 | reads `one-eyed/`, writes `advanced-example/` |
| 03 | updates `advanced-example/` |
