#!/usr/bin/env python3
"""
Create ERA topology (LinearElements + NetRelations) from Belgian rail segment CSV.

Phase 1 — Filter CSV to bounding box → filtered.ttl   (gsp:Geometry only)
Phase 2 — Load filtered.ttl, detect T/X-intersections, split lines
Phase 3 — Create era:LinearElement + era:NetRelation  → topology.ttl

Bounding box (WGS84):
    SW: 50.88022° N  4.44651° E
    NE: 50.92776° N  4.50473° E
"""

import csv
import json
import math
import sys
from itertools import combinations, count
from pathlib import Path

import pyproj
from pyproj import Transformer
from shapely.geometry import LineString, MultiLineString, Point, box
from shapely.ops import substring
from shapely import wkt as shapely_wkt
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, XSD

# ─── Paths ──────────────────────────────────────────────────────────────────
HERE         = Path(__file__).parent
CSV_FILE     = HERE / "geografische-positie-van-alle-spoorsegmenten.csv"
FILTERED_TTL = HERE / "filtered.ttl"
TOPOLOGY_TTL = HERE / "topology.ttl"

# ─── Namespaces ─────────────────────────────────────────────────────────────
ERA  = Namespace("http://data.europa.eu/949/")
GSP  = Namespace("http://www.opengis.net/ont/geosparql#")
DATA = Namespace("https://data.matdata.eu/")

ERA_NAV_BOTH = URIRef("http://data.europa.eu/949/concepts/navigabilities/Both")
ERA_NAV_NONE = URIRef("http://data.europa.eu/949/concepts/navigabilities/None")

# ─── Configuration ──────────────────────────────────────────────────────────
BBOX_MIN_LAT =  50.88022
BBOX_MAX_LAT =  50.92776
BBOX_MIN_LON =   4.44651
BBOX_MAX_LON =   4.50473

# UTM zone 31N — metric CRS suitable for Belgium
CRS_WGS84  = pyproj.CRS("EPSG:4326")
CRS_METRIC = pyproj.CRS("EPSG:32631")
TO_METRIC   = Transformer.from_crs(CRS_WGS84, CRS_METRIC, always_xy=True)
FROM_METRIC = Transformer.from_crs(CRS_METRIC, CRS_WGS84, always_xy=True)

SNAP_TOL      = 0.5   # metres — endpoint / near-intersection tolerance
AZ_LEN        = 5.0   # metres — sub-linestring length for azimuth calculation
MIN_SEG_M     = 0.1   # metres — discard segments shorter than this after splitting
MIN_SPLIT_EXT = 3.0   # metres — line must extend ≥ this beyond split point to warrant a split


# ═══════════════════════════════════════════════════════════════════════════
# Coordinate helpers
# ═══════════════════════════════════════════════════════════════════════════

def to_utm(line_wgs84: LineString) -> LineString:
    """Project a WGS84 LineString (lon, lat) to UTM 31N (metres)."""
    coords = [TO_METRIC.transform(lon, lat) for lon, lat in line_wgs84.coords]
    return LineString(coords)


def from_utm(line_utm: LineString) -> LineString:
    """Project a UTM 31N LineString back to WGS84 (lon, lat)."""
    coords = [FROM_METRIC.transform(x, y) for x, y in line_utm.coords]
    return LineString(coords)


def wkt_literal(line_wgs84: LineString) -> str:
    """Return a bare WKT string for a WGS84 LineString (lon lat, ...)."""
    coord_str = ", ".join(f"{lon} {lat}" for lon, lat in line_wgs84.coords)
    return f"LINESTRING ({coord_str})"


# ═══════════════════════════════════════════════════════════════════════════
# Phase 1 — Filter CSV → filtered.ttl
# ═══════════════════════════════════════════════════════════════════════════

def parse_csv_stream():
    """Yield (seg_id: str, line: LineString[WGS84 lon/lat]) from the CSV."""
    csv.field_size_limit(10 * 1024 * 1024)  # 10 MB — accommodate large GeoJSON fields
    bbox_poly = box(BBOX_MIN_LON, BBOX_MIN_LAT, BBOX_MAX_LON, BBOX_MAX_LAT)
    with open(CSV_FILE, encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh, delimiter=";")
        next(reader)  # header
        for row in reader:
            if len(row) < 3:
                continue
            _geo_point, geo_shape_raw, seg_id_raw = row[0], row[1], row[2]
            seg_id = seg_id_raw.strip()
            if not seg_id:
                continue
            try:
                geo_json = json.loads(geo_shape_raw)
                # GeoJSON coordinates: [lon, lat, elevation] — drop elevation
                coords_2d = [(c[0], c[1]) for c in geo_json["coordinates"]]
                if len(coords_2d) < 2:
                    continue
                line = LineString(coords_2d)
            except (json.JSONDecodeError, KeyError, IndexError, ValueError) as exc:
                print(f"  Warning: skip segment {seg_id!r}: {exc}", file=sys.stderr)
                continue

            # Clip to bounding box
            if not line.intersects(bbox_poly):
                continue
            clipped = line.intersection(bbox_poly)
            if clipped.is_empty:
                continue

            if clipped.geom_type == "LineString":
                yield seg_id, clipped
            elif clipped.geom_type == "MultiLineString":
                for k, part in enumerate(clipped.geoms):
                    if not part.is_empty and len(part.coords) >= 2:
                        yield f"{seg_id}_c{k}", part


def build_filtered_ttl():
    """Phase 1: parse CSV, filter to bbox, write gsp:Geometry triples."""
    print("Phase 1: filtering CSV to bounding box …")
    g = Graph()
    g.bind("gsp",  GSP)
    g.bind("rdfs", RDFS)
    g.bind("data", DATA)

    count_segs = 0
    for seg_id, line_wgs84 in parse_csv_stream():
        geom_uri = DATA[f"_geometry_segment_{seg_id}"]
        wkt_str  = wkt_literal(line_wgs84)
        wkt_lit  = Literal(wkt_str, datatype=GSP.wktLiteral)

        g.add((geom_uri, RDF.type,     GSP.Geometry))
        g.add((geom_uri, RDFS.label,   Literal(seg_id)))
        g.add((geom_uri, GSP.asWKT,    wkt_lit))
        count_segs += 1

    g.serialize(destination=str(FILTERED_TTL), format="turtle")
    print(f"  ✓ Wrote {count_segs} geometries to {FILTERED_TTL}")
    return count_segs


# ═══════════════════════════════════════════════════════════════════════════
# Phase 2 — Load filtered.ttl, split at intersections
# ═══════════════════════════════════════════════════════════════════════════

def load_filtered_ttl():
    """
    Load filtered.ttl.
    Returns list of (seg_id: str, line_utm: LineString[UTM 31N]).
    """
    g = Graph()
    g.parse(str(FILTERED_TTL), format="turtle")

    segments = []
    for geom_uri in g.subjects(RDF.type, GSP.Geometry):
        label = g.value(geom_uri, RDFS.label)
        wkt_val = g.value(geom_uri, GSP.asWKT)
        if label is None or wkt_val is None:
            continue
        wkt_str = str(wkt_val)
        if wkt_str.startswith("<"):
            wkt_str = wkt_str[wkt_str.index(">") + 1:].strip()
        line_wgs84 = shapely_wkt.loads(wkt_str)
        if line_wgs84.is_empty or line_wgs84.geom_type != "LineString":
            continue
        line_utm = to_utm(line_wgs84)
        segments.append((str(label), line_utm))

    print(f"  Loaded {len(segments)} geometries from {FILTERED_TTL}")
    return segments


def split_line_at_distances(line: LineString, distances: list[float]) -> list[LineString]:
    """Split a LineString at a list of projected distances (metres). Returns parts."""
    tol = 1e-4  # sub-millimetre — avoid zero-length edge segments
    dists = sorted({d for d in distances if tol < d < line.length - tol})
    if not dists:
        return [line]
    breakpoints = [0.0] + dists + [line.length]
    parts = []
    for a, b in zip(breakpoints, breakpoints[1:]):
        seg = substring(line, a, b)
        if not seg.is_empty and seg.geom_type == "LineString" and seg.length >= MIN_SEG_M:
            parts.append(seg)
    return parts or [line]


def split_at_intersections(segments: list[tuple[str, LineString]]) -> list[tuple[str, LineString]]:
    """
    Iteratively split LineStrings at T-intersections and X-crossings until stable.

    T-intersection: an endpoint of line B lies within SNAP_TOL metres of the
                    interior of line A (not at A's endpoints) → split A.
    X-crossing:     two lines cross geometrically → split both at the crossing.

    Returns a new list of (id, LineString UTM) segments with no internal intersections.
    """
    from shapely.strtree import STRtree

    iteration = 0
    while True:
        iteration += 1
        changed   = False
        new_segs  = []

        lines = [s[1] for s in segments]
        tree  = STRtree(lines)

        for i, (sid, line) in enumerate(segments):
            split_dists = []

            # Query spatially close segments (buffer by tolerance for T-junctions)
            candidates = tree.query(line.buffer(SNAP_TOL * 2))

            for j in candidates:
                if j == i:
                    continue
                _other_id, other = segments[j]

                # T-intersection: endpoint of `other` near the interior of `line`
                for pt in (Point(other.coords[0]), Point(other.coords[-1])):
                    if line.distance(pt) < SNAP_TOL:
                        # Ignore if pt is already near an endpoint of `line`
                        d_start = Point(line.coords[0]).distance(pt)
                        d_end   = Point(line.coords[-1]).distance(pt)
                        if d_start >= SNAP_TOL and d_end >= SNAP_TOL:
                            split_dists.append(line.project(pt))

                # X-crossing: the two lines geometrically cross
                if line.crosses(other):
                    inter = line.intersection(other)
                    if inter.geom_type == "Point":
                        split_dists.append(line.project(inter))
                    elif inter.geom_type == "MultiPoint":
                        for p in inter.geoms:
                            split_dists.append(line.project(p))

            # Only keep split distances where the line extends ≥ MIN_SPLIT_EXT
            # beyond the split point in both directions — avoids creating tiny
            # stubs that would trigger further splits on the next iteration.
            split_dists = [
                d for d in split_dists
                if d >= MIN_SPLIT_EXT and (line.length - d) >= MIN_SPLIT_EXT
            ]

            if split_dists:
                changed = True
                parts = split_line_at_distances(line, split_dists)
                for k, part in enumerate(parts):
                    new_id = f"{sid}_s{k}" if len(parts) > 1 else sid
                    new_segs.append((new_id, part))
            else:
                new_segs.append((sid, line))

        segments = new_segs
        print(f"  Iteration {iteration}: {len(segments)} segments", end="")
        if not changed:
            print(" — stable, no more splits needed")
            break
        print(" — splits applied, continuing …")

    return segments


# ═══════════════════════════════════════════════════════════════════════════
# Phase 3 — Endpoint grouping, azimuth, NetRelations, topology.ttl
# ═══════════════════════════════════════════════════════════════════════════

def angular_diff(a1: float, a2: float) -> float:
    """Minimum angular difference between two azimuths in degrees (result 0–180)."""
    diff = abs(a1 - a2) % 360.0
    return min(diff, 360.0 - diff)


def azimuth_from_endpoint(line_utm: LineString, is_start: bool, length: float = AZ_LEN) -> float:
    """
    Azimuth (0–360°, clockwise from North) of the sub-line extending
    from the given endpoint *into* the line interior.
    """
    line_len = line_utm.length
    if line_len < 1e-6:
        return 0.0
    sub_len = min(length, line_len * 0.9)  # never exceed the line

    if is_start:
        sub = substring(line_utm, 0.0, sub_len)
        p1  = Point(sub.coords[0])
        p2  = Point(sub.coords[-1])
    else:
        sub = substring(line_utm, line_len - sub_len, line_len)
        p1  = Point(sub.coords[-1])   # the endpoint
        p2  = Point(sub.coords[0])    # going into the interior

    dx = p2.x - p1.x
    dy = p2.y - p1.y
    return math.degrees(math.atan2(dx, dy)) % 360.0


def group_endpoints_union_find(
    segments: list[tuple[str, LineString]],
    tolerance: float,
) -> list[list[tuple[str, bool, Point]]]:
    """
    Collect all segment endpoints and cluster those within `tolerance` metres.

    Returns list of groups; each group is a list of (seg_id, is_start, point).
    Only groups with ≥ 2 members (actual connection nodes) are returned.
    """
    endpoints: list[tuple[str, bool, Point]] = []
    for sid, line in segments:
        endpoints.append((sid, True,  Point(line.coords[0])))
        endpoints.append((sid, False, Point(line.coords[-1])))

    n = len(endpoints)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    # Build clusters (O(n²) — acceptable for the filtered dataset size)
    for i in range(n):
        for j in range(i + 1, n):
            if endpoints[i][2].distance(endpoints[j][2]) < tolerance:
                union(i, j)

    groups: dict[int, list] = {}
    for i in range(n):
        root = find(i)
        groups.setdefault(root, []).append(endpoints[i])

    return [g for g in groups.values() if len(g) >= 2]


def build_net_relations(
    groups:    list[list[tuple[str, bool, Point]]],
    seg_dict:  dict[str, LineString],
    id_gen,
) -> list[tuple[str, str, bool, str, bool, URIRef, Point]]:
    """
    Create NetRelation tuples from endpoint groups.

    Returns list of (rel_id, seg_id_A, is_start_A, seg_id_B, is_start_B, nav_uri, node_point_utm).

    Navigability rules
    ──────────────────
    • 2 endpoints  → 1 relation, navigability Both
    • 3 endpoints  → 3 relations (all pairs); the pair with the smallest
                     azimuth difference gets navigability None (same-direction
                     branches cannot navigate between each other); others Both
    • 4 endpoints  → 4 relations; the 2 pairs with the smallest azimuth
                     differences are excluded entirely; remaining 4 get Both
    • 5+           → all pairs, navigability Both
    """
    relations = []

    for group in groups:
        n = len(group)
        all_pairs = list(combinations(range(n), 2))
        node_pt   = Point(
            sum(ep[2].x for ep in group) / n,
            sum(ep[2].y for ep in group) / n,
        )

        if n == 2:
            a, b = group[0], group[1]
            relations.append((
                f"rel_{next(id_gen)}",
                a[0], a[1], b[0], b[1],
                ERA_NAV_BOTH, node_pt,
            ))

        elif n == 3:
            az = [azimuth_from_endpoint(seg_dict[g[0]], g[1]) for g in group]
            diffs = sorted(
                (angular_diff(az[i], az[j]), i, j) for i, j in all_pairs
            )
            non_nav = (diffs[0][1], diffs[0][2])  # closest azimuth pair

            for i, j in all_pairs:
                nav = ERA_NAV_NONE if (i, j) == non_nav or (j, i) == non_nav else ERA_NAV_BOTH
                a, b = group[i], group[j]
                relations.append((
                    f"rel_{next(id_gen)}",
                    a[0], a[1], b[0], b[1],
                    nav, node_pt,
                ))

        elif n == 4:
            az = [azimuth_from_endpoint(seg_dict[g[0]], g[1]) for g in group]
            diffs = sorted(
                (angular_diff(az[i], az[j]), i, j) for i, j in all_pairs
            )
            # Exclude the 2 pairs with the smallest azimuth difference
            excluded = {(diffs[0][1], diffs[0][2]), (diffs[1][1], diffs[1][2])}

            for i, j in all_pairs:
                if (i, j) in excluded or (j, i) in excluded:
                    continue
                a, b = group[i], group[j]
                relations.append((
                    f"rel_{next(id_gen)}",
                    a[0], a[1], b[0], b[1],
                    ERA_NAV_BOTH, node_pt,
                ))

        else:  # 5+ — create all pairs
            for i, j in all_pairs:
                a, b = group[i], group[j]
                relations.append((
                    f"rel_{next(id_gen)}",
                    a[0], a[1], b[0], b[1],
                    ERA_NAV_BOTH, node_pt,
                ))

    return relations


def build_topology_ttl(segments: list[tuple[str, LineString]]):
    """Phase 3: build era:LinearElement + era:NetRelation and write topology.ttl."""
    print("Phase 3: building topology …")

    g = Graph()
    g.bind("era",  ERA)
    g.bind("gsp",  GSP)
    g.bind("rdfs", RDFS)
    g.bind("data", DATA)

    seg_dict = dict(segments)  # id → LineString(UTM)
    id_gen   = count(1)

    # ── LinearElements + Geometries ──────────────────────────────────────────
    for sid, line_utm in segments:
        le_uri   = DATA[f"_netElements_{sid}"]
        geom_uri = DATA[f"_geometry_netElement_{sid}"]

        line_wgs84 = from_utm(line_utm)
        wkt_str    = wkt_literal(line_wgs84)
        wkt_lit    = Literal(wkt_str, datatype=GSP.wktLiteral)
        length_m   = round(line_utm.length, 3)

        g.add((le_uri, RDF.type,                    ERA.LinearElement))
        g.add((le_uri, RDFS.label,                  Literal(sid)))
        g.add((le_uri, ERA.lengthOfNetLinearElement, Literal(length_m, datatype=XSD.double)))
        g.add((le_uri, GSP.hasGeometry,             geom_uri))

        g.add((geom_uri, RDF.type,  GSP.Geometry))
        g.add((geom_uri, GSP.asWKT, wkt_lit))

    print(f"  ✓ {len(segments)} LinearElements added")

    # ── Endpoint groups → NetRelations ────────────────────────────────────────
    groups = group_endpoints_union_find(segments, SNAP_TOL)
    print(f"  Found {len(groups)} connection nodes")

    relations = build_net_relations(groups, seg_dict, id_gen)

    for rel_id, sid_a, is_start_a, sid_b, is_start_b, nav, node_pt_utm in relations:
        rel_uri   = DATA[f"_netRelations_{rel_id}"]
        le_a      = DATA[f"_netElements_{sid_a}"]
        le_b      = DATA[f"_netElements_{sid_b}"]
        ngeom_uri = DATA[f"_geometry_netRelation_{rel_id}"]

        lon, lat = FROM_METRIC.transform(node_pt_utm.x, node_pt_utm.y)
        pt_wkt   = Literal(f"POINT ({lon} {lat})", datatype=GSP.wktLiteral)

        g.add((rel_uri, RDF.type,                  ERA.NetRelation))
        g.add((rel_uri, ERA.elementA,               le_a))
        g.add((rel_uri, ERA.elementB,               le_b))
        g.add((rel_uri, ERA.isOnOriginOfElementA,   Literal(is_start_a)))
        g.add((rel_uri, ERA.isOnOriginOfElementB,   Literal(is_start_b)))
        g.add((rel_uri, ERA.navigability,           nav))
        g.add((rel_uri, GSP.hasGeometry,            ngeom_uri))

        g.add((ngeom_uri, RDF.type,  GSP.Geometry))
        g.add((ngeom_uri, GSP.asWKT, pt_wkt))

    print(f"  ✓ {len(relations)} NetRelations added")

    g.serialize(destination=str(TOPOLOGY_TTL), format="turtle")
    print(f"  ✓ Wrote topology to {TOPOLOGY_TTL}")


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def main():
    # Phase 1 ─ build / reuse filtered.ttl
    if FILTERED_TTL.exists():
        print(f"Phase 1: {FILTERED_TTL} already exists — skipping CSV filtering")
    else:
        build_filtered_ttl()

    # Phase 2 ─ load, detect intersections, split
    print("Phase 2: detecting and resolving intersections …")
    segments = load_filtered_ttl()
    segments = split_at_intersections(segments)
    print(f"  ✓ {len(segments)} segments after splitting")

    # Phase 3 ─ build topology RDF
    build_topology_ttl(segments)
    print("Done.")


if __name__ == "__main__":
    main()
