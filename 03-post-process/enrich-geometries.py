#!/usr/bin/env python3
"""Enrich ERA network reference geometries using linear referencing.

Computes GeoSPARQL geometries for:
- NetPointReference  -> POINT (interpolated on LinearElement)
- NetLinearReference -> LINESTRING (concatenated from sequence of LinearElements)
- NetAreaReference   -> MULTILINESTRING (combined from included NetLinearReferences)
- Subjects of era:netReference -> combined WKT from all referenced geometries
"""

import hashlib
import os

import requests
from rdflib import Graph, Namespace, URIRef, Literal, RDF
from shapely import wkt as shapely_wkt
from shapely.geometry import GeometryCollection, LineString, MultiLineString, MultiPoint, Point
from shapely.ops import substring

# Namespaces
ERA = Namespace("http://data.europa.eu/949/")
GSP = Namespace("http://www.opengis.net/ont/geosparql#")

# Configuration
FUSEKI_URL = "http://localhost:8082/jena-fuseki/advanced-example"
FUSEKI_QUERY = f"{FUSEKI_URL}/query"
FUSEKI_DATA = f"{FUSEKI_URL}/data"
INPUT_TTL = "../02-construct/output/era-graph.ttl"
OUTPUT_TTL = "output/era-graph-enriched.ttl"


def geometry_uri(geom_type: str, wkt_str: str) -> URIRef:
    """Create a deterministic geometry URI from type and WKT."""
    h = hashlib.sha256(wkt_str.encode()).hexdigest()[:8]
    return URIRef(f"https://data.matdata.eu/_geometry_{geom_type}_{h}")


def parse_wkt(wkt_str: str):
    """Parse a WKT string, stripping any GeoSPARQL CRS prefix."""
    s = str(wkt_str).strip()
    if s.startswith("<"):
        s = s[s.index(">") + 1 :].strip()
    return shapely_wkt.loads(s)


def add_geometry(graph: Graph, new_triples: Graph, subject: URIRef, geom_type: str, wkt_str: str):
    """Add gsp:hasGeometry triples to both the main graph and the new-triples graph."""
    uri = geometry_uri(geom_type, wkt_str)
    wkt_lit = Literal(wkt_str, datatype=GSP.wktLiteral)
    for g in (graph, new_triples):
        g.add((subject, GSP.hasGeometry, uri))
        g.add((uri, RDF.type, GSP.Geometry))
        g.add((uri, GSP.asWKT, wkt_lit))


def get_le_geometry(graph: Graph, le: URIRef):
    """Return a LinearElement's (Shapely geometry, length_in_meters) or (None, None)."""
    length = None
    for o in graph.objects(le, ERA.lengthOfNetLinearElement):
        length = float(o)
        break

    geom = None
    for g in graph.objects(le, GSP.hasGeometry):
        for w in graph.objects(g, GSP.asWKT):
            geom = parse_wkt(w)
            break
        if geom:
            break

    return geom, length


def rdf_list_items(graph: Graph, head) -> list:
    """Traverse an RDF list and return all items in order."""
    items = []
    node = head
    while node and node != RDF.nil:
        first = next(graph.objects(node, RDF.first), None)
        if first is not None:
            items.append(first)
        node = next(graph.objects(node, RDF.rest), None)
    return items


# ---------------------------------------------------------------------------
# NetPointReference -> POINT
# ---------------------------------------------------------------------------

def enrich_points(graph: Graph, new_triples: Graph) -> int:
    """Interpolate POINT geometries for NetPointReferences without geometry."""
    count = 0
    for ref in graph.subjects(RDF.type, ERA.NetPointReference):
        if any(graph.objects(ref, GSP.hasGeometry)):
            continue

        tc = next(graph.objects(ref, ERA.hasTopoCoordinate), None)
        if not tc:
            continue

        le = next(graph.objects(tc, ERA.onLinearElement), None)
        offset_lit = next(graph.objects(tc, ERA.offsetFromOrigin), None)
        if not le or offset_lit is None:
            continue

        offset = float(offset_lit)
        le_geom, le_len = get_le_geometry(graph, le)
        if not le_geom or not le_len:
            continue

        frac = max(0.0, min(1.0, offset / le_len))
        point = le_geom.interpolate(frac, normalized=True)
        add_geometry(graph, new_triples, ref, "point", point.wkt)
        count += 1

    return count


# ---------------------------------------------------------------------------
# NetLinearReference -> LINESTRING
# ---------------------------------------------------------------------------

def enrich_lines(graph: Graph, new_triples: Graph) -> int:
    """Build LINESTRING geometries for NetLinearReferences without geometry."""
    count = 0
    for ref in graph.subjects(RDF.type, ERA.NetLinearReference):
        if any(graph.objects(ref, GSP.hasGeometry)):
            continue

        start_ref = next(graph.objects(ref, ERA.startsAt), None)
        end_ref = next(graph.objects(ref, ERA.endsAt), None)
        seq_head = next(graph.objects(ref, ERA.hasSequence), None)
        if not start_ref or not end_ref or not seq_head:
            continue

        # Start topological coordinate
        start_tc = next(graph.objects(start_ref, ERA.hasTopoCoordinate), None)
        if not start_tc:
            continue
        start_offset_lit = next(graph.objects(start_tc, ERA.offsetFromOrigin), None)
        if start_offset_lit is None:
            continue
        start_offset = float(start_offset_lit)

        # End topological coordinate
        end_tc = next(graph.objects(end_ref, ERA.hasTopoCoordinate), None)
        if not end_tc:
            continue
        end_offset_lit = next(graph.objects(end_tc, ERA.offsetFromOrigin), None)
        if end_offset_lit is None:
            continue
        end_offset = float(end_offset_lit)

        elements = rdf_list_items(graph, seq_head)
        if not elements:
            continue

        all_coords = []
        valid = True

        for i, le in enumerate(elements):
            le_geom, le_len = get_le_geometry(graph, le)
            if not le_geom or not le_len:
                valid = False
                break

            is_first = i == 0
            is_last = i == len(elements) - 1

            if is_first and is_last:
                s = max(0.0, min(1.0, start_offset / le_len))
                e = max(0.0, min(1.0, end_offset / le_len))
                seg = substring(le_geom, s, e, normalized=True)
            elif is_first:
                s = max(0.0, min(1.0, start_offset / le_len))
                seg = substring(le_geom, s, 1.0, normalized=True)
            elif is_last:
                e = max(0.0, min(1.0, end_offset / le_len))
                seg = substring(le_geom, 0.0, e, normalized=True)
            else:
                seg = le_geom

            if seg.is_empty or seg.geom_type == "Point":
                continue

            coords = list(seg.coords)

            # Check orientation for connectivity with previous segment
            if all_coords and len(coords) >= 2:
                prev = all_coords[-1]
                d_fwd = (prev[0] - coords[0][0]) ** 2 + (prev[1] - coords[0][1]) ** 2
                d_rev = (prev[0] - coords[-1][0]) ** 2 + (prev[1] - coords[-1][1]) ** 2
                if d_rev < d_fwd:
                    coords = coords[::-1]

            # Remove duplicate junction point
            if all_coords and coords:
                p1, p2 = all_coords[-1], coords[0]
                if abs(p1[0] - p2[0]) < 1e-10 and abs(p1[1] - p2[1]) < 1e-10:
                    coords = coords[1:]

            all_coords.extend(coords)

        if valid and len(all_coords) >= 2:
            add_geometry(graph, new_triples, ref, "linestring", LineString(all_coords).wkt)
            count += 1

    return count


# ---------------------------------------------------------------------------
# NetAreaReference -> MULTILINESTRING
# ---------------------------------------------------------------------------

def enrich_areas(graph: Graph, new_triples: Graph) -> int:
    """Combine included NetLinearReference geometries into MULTILINESTRING."""
    count = 0
    for ref in graph.subjects(RDF.type, ERA.NetAreaReference):
        if any(graph.objects(ref, GSP.hasGeometry)):
            continue

        includes_head = next(graph.objects(ref, ERA.includes), None)
        if not includes_head:
            continue

        included = rdf_list_items(graph, includes_head)
        lines = []
        for inc in included:
            geom_node = next(graph.objects(inc, GSP.hasGeometry), None)
            if not geom_node:
                continue
            wkt_val = next(graph.objects(geom_node, GSP.asWKT), None)
            if not wkt_val:
                continue
            geom = parse_wkt(wkt_val)
            if isinstance(geom, LineString):
                lines.append(geom)

        if lines:
            add_geometry(graph, new_triples, ref, "multilinestring", MultiLineString(lines).wkt)
            count += 1

    return count


# ---------------------------------------------------------------------------
# Subject geometries (combine reference geometries)
# ---------------------------------------------------------------------------

def _geom_type_label(geom) -> str:
    """Map a Shapely geometry to a URI path segment."""
    mapping = {
        "Point": "point",
        "LineString": "linestring",
        "MultiPoint": "multipoint",
        "MultiLineString": "multilinestring",
        "GeometryCollection": "geometrycollection",
    }
    return mapping.get(geom.geom_type, "geometry")


def enrich_subjects(graph: Graph, new_triples: Graph) -> int:
    """Add a combined geometry to subjects of era:netReference that lack one."""
    count = 0
    seen = set()

    for subject in graph.subjects(ERA.netReference, None):
        if subject in seen:
            continue
        seen.add(subject)

        if any(graph.objects(subject, GSP.hasGeometry)):
            continue

        geoms = []
        for ref in graph.objects(subject, ERA.netReference):
            for geom_node in graph.objects(ref, GSP.hasGeometry):
                for wkt_val in graph.objects(geom_node, GSP.asWKT):
                    geoms.append(parse_wkt(wkt_val))

        if not geoms:
            continue

        if len(geoms) == 1:
            combined = geoms[0]
        else:
            types = {g.geom_type for g in geoms}
            if types == {"Point"}:
                combined = MultiPoint(geoms)
            elif types <= {"LineString", "MultiLineString"}:
                lines = []
                for g in geoms:
                    if isinstance(g, LineString):
                        lines.append(g)
                    elif isinstance(g, MultiLineString):
                        lines.extend(g.geoms)
                combined = MultiLineString(lines)
            else:
                combined = GeometryCollection(geoms)

        add_geometry(graph, new_triples, subject, _geom_type_label(combined), combined.wkt)
        count += 1

    return count


# ---------------------------------------------------------------------------
# Fuseki helpers
# ---------------------------------------------------------------------------

def check_fuseki() -> bool:
    try:
        r = requests.post(FUSEKI_QUERY, data={"query": "ASK { }"}, timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def load_graph_from_fuseki() -> Graph:
    g = Graph()
    r = requests.post(
        FUSEKI_QUERY,
        data={"query": "CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }"},
        headers={"Accept": "text/turtle"},
        timeout=120,
    )
    r.raise_for_status()
    g.parse(data=r.text, format="turtle")
    return g


def upload_triples_to_fuseki(new_triples: Graph):
    """POST only the new geometry triples to Fuseki (additive)."""
    ttl = new_triples.serialize(format="turtle")
    r = requests.post(
        FUSEKI_DATA,
        data=ttl.encode("utf-8"),
        headers={"Content-Type": "text/turtle"},
        timeout=120,
    )
    r.raise_for_status()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    fuseki = check_fuseki()

    if fuseki:
        print("  Loading graph from Fuseki...")
        graph = load_graph_from_fuseki()
    else:
        print(f"  Fuseki not available - loading from {INPUT_TTL}")
        graph = Graph()
        graph.parse(INPUT_TTL, format="turtle")

    print(f"  Loaded {len(graph)} triples")

    graph.bind("era", ERA)
    graph.bind("gsp", GSP)

    new_triples = Graph()

    # Enrich in order: points -> lines -> areas -> subjects
    # (areas depend on line geometries, subjects depend on all reference geometries)
    n = enrich_points(graph, new_triples)
    print(f"  + {n} NetPointReference geometries")

    n = enrich_lines(graph, new_triples)
    print(f"  + {n} NetLinearReference geometries")

    n = enrich_areas(graph, new_triples)
    print(f"  + {n} NetAreaReference geometries")

    n = enrich_subjects(graph, new_triples)
    print(f"  + {n} subject geometries (via era:netReference)")

    print(f"  {len(new_triples)} new triples, {len(graph)} total triples")

    if fuseki:
        print("  Uploading new triples to Fuseki...")
        upload_triples_to_fuseki(new_triples)
        print("  ✓ Uploaded to Fuseki")

    os.makedirs(os.path.dirname(OUTPUT_TTL) or ".", exist_ok=True)
    graph.serialize(destination=OUTPUT_TTL, format="turtle")
    print(f"  ✓ Saved to {OUTPUT_TTL}")


if __name__ == "__main__":
    main()
