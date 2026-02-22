# 06 — Create ERA Topology from Belgian Rail Segments

Builds an ERA-compliant RDF topology graph (`topology.ttl`) from an open Belgian rail segment dataset published by Infrabel.

## Input data

**Source:** [Geografische positie van alle spoorsegmenten](https://opendata.infrabel.be/explore/dataset/geografische-positie-van-alle-spoorsegmenten/export/?basemap=jawg.light&location=14,50.88241,4.48204) — Infrabel Open Data

**File:** `geografische-positie-van-alle-spoorsegmenten.csv` (semicolon-delimited)

| Column | Content |
|---|---|
| Geo Point | Centroid (ignored) |
| Geo Shape | GeoJSON `LineString` with `[lon, lat, elevation]` coordinates |
| Id of the segment | Segment identifier used as URI slug |

## How to run

```powershell
cd 06-create-topology
& ..\.venv\Scripts\python.exe create-topology.py
```

The script is idempotent: Phase 1 is skipped when `filtered.ttl` already exists. Delete it to re-run the CSV filter.

## Processing pipeline

### Phase 1 — Filter CSV → `filtered.ttl`

The full CSV is streamed and each segment is clipped to a bounding box around the area of interest (Brussels-East, WGS84):

```
SW: 50.88022° N  4.44651° E
NE: 50.92776° N  4.50473° E
```

Segments outside the box are discarded. Segments that cross the boundary are clipped with Shapely; a `MultiLineString` result (segment re-enters the box) produces one sub-segment per part, suffixed `_c0`, `_c1`, …

The output `filtered.ttl` contains only `gsp:Geometry` triples (one per segment) with a bare WKT `LINESTRING (lon lat, …)` literal. No ERA topology is written yet.

### Phase 2 — Detect intersections and split lines

Segments loaded from `filtered.ttl` are projected into **UTM zone 31N (EPSG:32631)** for metric distance calculations.

The function `split_at_intersections` iterates until no further splits are required:

1. A **spatial index** (Shapely `STRtree`) is built over all current segments.
2. For each segment `A`, nearby candidates are queried using a buffer of `2 × SNAP_TOL` (1 m).
3. Two split triggers are checked:
   - **T-intersection** — an endpoint of segment `B` lies within `SNAP_TOL` (0.5 m) of the interior of `A` (not near `A`'s own endpoints). The projected distance along `A` is recorded as a split point.
   - **X-crossing** — `A` and `B` geometrically cross (`shapely.crosses`). The crossing point(s) are projected onto `A`.
4. A split point is **only applied** when the line extends at least **3 m** beyond the split point in both directions (`MIN_SPLIT_EXT`). This prevents the creation of tiny stub segments near existing endpoints that would themselves trigger further splits on the next iteration, which would otherwise cause infinite looping.
5. Each split segment inherits the parent ID with a `_s0`, `_s1`, … suffix.

Typical convergence: 1–2 iterations.

### Phase 3 — Build ERA topology → `topology.ttl`

#### LinearElements

Each segment becomes an `era:LinearElement` with:
- `era:lengthOfNetLinearElement` — length in metres (rounded to 3 decimal places)
- `gsp:hasGeometry` → a `gsp:Geometry` with `gsp:asWKT` back-projected to WGS84

URIs follow the pattern:
```
https://data.matdata.eu/_netElements_{seg_id}
https://data.matdata.eu/_geometry_netElement_{seg_id}
```

#### NetRelations

Endpoints are clustered with a Union-Find algorithm (tolerance `SNAP_TOL = 0.5 m`). Each cluster of ≥ 2 coincident endpoints is a **connection node**, and every pair within a node becomes a candidate `era:NetRelation`.

**Navigability** is determined by the azimuth of each endpoint into its line interior (measured over the first/last 5 m):

| Node degree | Relations created | Navigability rule |
|---|---|---|
| 2 (simple connection) | 1 | `Both` |
| 3 (switch) | 3 (all pairs) | Pair with the smallest azimuth difference → `None`; others → `Both` |
| 4 (diamond crossing) | 4 (of 6 pairs) | 2 pairs with smallest azimuth differences excluded; remaining 4 → `Both` |

Note: here it would be useful to add additional information concerning the type of switch (turnout, single slip or double slip crossing), or knowing if it is just a simple crossing. In any case, it is assumed that every diamond crossing is a double slip crossing.

NetRelation URIs follow the pattern:
```
https://data.matdata.eu/_netRelations_rel_{n}
```

Each `era:NetRelation` carries `era:elementA`, `era:elementB`, `era:isOnOriginOfElementA`, `era:isOnOriginOfElementB`, and `era:navigability`.

## Output files

| File | Contents |
|---|---|
| `filtered.ttl` | Intermediate — `gsp:Geometry` triples for bbox-filtered segments |
| `topology.ttl` | Final — `era:LinearElement` + `era:NetRelation` RDF graph |

## Dependencies

```
pyproj>=3.0   # CRS transformations (WGS84 ↔ UTM 31N)
shapely>=2.0  # Geometric operations
rdflib>=6.0   # RDF graph serialisation
```

Install into the project venv:

```powershell
pip install pyproj shapely rdflib
```

## Key constants

| Constant | Value | Purpose |
|---|---|---|
| `SNAP_TOL` | 0.5 m | T-intersection detection and endpoint clustering |
| `MIN_SPLIT_EXT` | 3.0 m | Minimum line extension beyond a split point |
| `AZ_LEN` | 5.0 m | Sub-line length used for azimuth calculation |
| `MIN_SEG_M` | 0.1 m | Minimum segment length after splitting |
