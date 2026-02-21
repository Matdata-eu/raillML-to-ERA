---
name: era-wkt-geometry-enrichment
description: Compute GeoSPARQL WKT geometries for ERA network reference resources (NetPointReference, NetLinearReference, NetAreaReference) by interpolating against LinearElement LINESTRING geometries using Shapely linear referencing. Use when needing to calculate gsp:hasGeometry / gsp:asWKT triples to the graph after topology coordinates and topology is present.
---

# WKT Geometry Enrichment

Compute GeoSPARQL `gsp:hasGeometry` / `gsp:asWKT` triples for ERA network reference resources by interpolating against LinearElement LINESTRING geometries using Shapely linear referencing.

## Overview

ERA infrastructure elements carry topology coordinates (`era:offsetFromOrigin`) but **no WKT
geometry** after SPARQL CONSTRUCT queries. A post-processing step fills this gap in four passes
run in dependency order:

```
1. NetPointReference  → POINT   (interpolate offset on LinearElement)
2. NetLinearReference → LINESTRING (concatenate segments)
3. NetAreaReference   → MULTILINESTRING (union of included NetLinearReference geometries)
4. Subject geometry   → combined WKT on the era:netReference subject itself
```

## Shapely instead of GeoSPARQL functions

This SKILL describes the use of python Shapely instead of GeoSPARQL functions for geometry processing. This is because GeoSPARQL currently doesn't support linear referencing functions like `ST_LineInterpolatePoint` or `ST_LineSubstring` that are needed to compute the geometries from the topology coordinates. Other libraries similar to Shapely could also be used instead. 

Ideally the W3C GeoSPARQL standard would be extended in the future to include linear referencing functions and SPARQL engines should implement them.

## Source Data Requirements

Each `era:LinearElement` must already carry a LINESTRING:

```turtle
topology:ne_126 a era:LinearElement ;
    era:lengthOfNetLinearElement 500.0 ;
    gsp:hasGeometry [ gsp:asWKT "LINESTRING(3.01 53.00, 3.02 53.01)"^^gsp:wktLiteral ] .
```

These geometries must be present in the graph before enrichment runs. If a LinearElement lacks a geometry the interpolation for any NetReference on that element is silently skipped.

Note: LinearElement can have a geographic geometry (with a real CRS) or a non-geographic geometry (e.g., schematic coordinates).

## Pass 1 — NetPointReference → POINT

**Input**: `era:NetPointReference` → `era:hasTopoCoordinate` → `era:TopologicalCoordinate`
with `era:onLinearElement` and `era:offsetFromOrigin`.

**Algorithm**:
1. Resolve the `era:LinearElement` LINESTRING and `era:lengthOfNetLinearElement`.
2. Compute normalised fraction: `frac = clamp(offset / length, 0.0, 1.0)`.
3. Call `LineString.interpolate(frac, normalized=True)` → Shapely `Point`.
4. Write `gsp:hasGeometry` triples with a deterministic URI derived from SHA-256 of the WKT.

```python
frac = max(0.0, min(1.0, offset / le_len))
point = le_geom.interpolate(frac, normalized=True)
```

**Applies to**: Signals, Switches, LevelCrossings, TrainDetectionSystems, KilometricPosts, stoppingPoint OperationalPoints — any resource with one or more `NetPointReference`.

## Pass 2 — NetLinearReference → LINESTRING

**Input**: `era:NetLinearReference` with:
- `era:hasSequence` → rdf:List of `era:LinearElement` (in order)
- `era:startsAt` → `era:NetPointReference` → `era:hasTopoCoordinate` → `era:offsetFromOrigin` (start offset on **first** element)
- `era:endsAt` → `era:NetPointReference` → `era:hasTopoCoordinate` → `era:offsetFromOrigin` (end offset on **last** element)

**Algorithm**:
For each element in the ordered sequence:

| Position | Start fraction | End fraction |
|----------|----------------|-------------|
| First only (single-element) | `startOffset / length` | `endOffset / length` |
| First (multi-element) | `startOffset / length` | `1.0` |
| Intermediate | `0.0` | `1.0` |
| Last (multi-element) | `0.0` | `endOffset / length` |

Each segment is sliced with Shapely `substring(geom, s, e, normalized=True)`.

**Orientation fix**: Before appending each segment's coordinate list, check if the
first coordinate of the new segment is closer to the **last** accumulated coordinate
than to the first. If so, reverse the segment. This handles LinearElements stored in
the opposite direction to traversal order.

**Duplicate junction removal**: When two consecutive segments share an endpoint,
drop the duplicate coordinate at the join.

```python
d_fwd = dist(prev, coords[0])
d_rev = dist(prev, coords[-1])
if d_rev < d_fwd:
    coords = coords[::-1]
if coords[0] ≈ all_coords[-1]:
    coords = coords[1:]
```

**Applies to**: RunningTrack, Siding, PlatformEdge, OperationalPoint (linear),
SectionOfLine, SpeedSection, Bridge, Tunnel — any resource with `NetLinearReference`.

## Pass 3 — NetAreaReference → MULTILINESTRING

**Input**: `era:NetAreaReference` with `era:includes` → rdf:List of `era:NetLinearReference`.

By the time Pass 3 runs, each included `NetLinearReference` already has a LINESTRING
geometry from Pass 2.

**Algorithm**: Collect all LINESTRING geometries from included NetLinearReferences
and wrap them in a Shapely `MultiLineString`.

**Applies to**: Bridges (multi-segment), Tunnels, OperationalPoints, SectionOfLine.

## Pass 4 — Subject Geometry

Adds a combined geometry directly to the infrastructure subject (e.g., `era:Signal`,
`era:RunningTrack`) by collecting all geometries from its `era:netReference` resources.

**Combination rules**:

| All geometry types | Combined result |
|--------------------|-----------------|
| All POINT | `MultiPoint` |
| All LineString / MultiLineString | `MultiLineString` (flattened) |
| Mixed | `GeometryCollection` |
| Single | use as-is |

## Geometry URI Pattern

URIs are deterministic (SHA-256 of WKT, first 8 hex chars):

```
http://data.europa.eu/949/geometry/{geom_type}/{hash8}
```

Example: `http://data.europa.eu/949/geometry/point/a3f8b12c`

This means identical WKT strings always produce the same URI (idempotent re-runs).

## Common Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `0 NetPointReference geometries` | LinearElements have no geometry in the graph | Ensure LinearElement geometries are populated before enrichment |
| LINESTRING with only 1 coordinate | All segments degenerated to Points (zero-length slices) | Check `offsetFromOrigin` / `lengthOfNetLinearElement` units match (both in metres) |
| Disconnected LINESTRING segments | Orientation flip not detected (large coordinate gap) | Check LinearElement LINESTRING direction matches sequence traversal |
| NetAreaReference has 0 lines | Included NetLinearReferences have no geometry yet (Pass 2 failed) | Check Pass 2 output count |
| Subject gets no geometry | All `era:netReference` resources lack geometry | Passes 1–3 must complete first |

## Datatype Note

WKT literals must use the `gsp:wktLiteral` datatype:

```python
Literal(wkt_str, datatype=GSP.wktLiteral)
# → "LINESTRING(...)"^^<http://www.opengis.net/ont/geosparql#wktLiteral>
```

GeoSPARQL CRS prefixes (e.g., `<http://www.opengis.net/def/crs/OGC/1.3/CRS84>`) are stripped
before parsing with Shapely and are **not** re-added in the output — coordinates are WGS84
lon/lat implicitly.
