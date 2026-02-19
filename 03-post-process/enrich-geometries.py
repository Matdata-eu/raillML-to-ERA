#!/usr/bin/env python3
"""
Enrich network reference geometries using linear referencing.

This script runs AFTER all CONSTRUCT queries have been executed.
It adds gsp:hasGeometry triples to network reference resources that don't already have geometries:

1. NetPointReference → POINT geometry:
   - Finding all NetPointReferences with TopologicalCoordinates (without existing geometries)
   - Getting the LinearElement's LINESTRING geometry
   - Using Shapely's linear referencing to interpolate POINT at offsetFromOrigin
   - Inserting gsp:hasGeometry → gsp:Geometry → gsp:asWKT triples

2. NetLinearReference → LINESTRING geometry:
   - Finding all NetLinearReferences with startsAt/endsAt points (without existing geometries)
   - Interpolating start and end points from their TopologicalCoordinates
   - Creating LINESTRING from start to end point
   - Inserting gsp:hasGeometry → gsp:Geometry → gsp:asWKT triples

3. NetAreaReference → MULTILINESTRING geometry:
   - Finding all NetAreaReferences with included NetLinearReferences (without existing geometries)
   - Collecting all constituent NetLinearReference linestrings
   - Creating MULTILINESTRING from all included linestrings
   - Inserting gsp:hasGeometry → gsp:Geometry → gsp:asWKT triples

Dependencies:
    pip install shapely requests
"""

import requests
import sys
import subprocess
import time
import random

# Ensure UTF-8 encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from shapely.wkt import loads as wkt_loads
from shapely.geometry import Point, LineString, MultiLineString
from shapely import wkt
from typing import Dict, Tuple, Optional, List, Set, Union

# Configuration
SOURCE_ENDPOINT = "http://localhost:8082/jena-fuseki/advanced-example/sparql"
TARGET_ENDPOINT = "http://localhost:8082/jena-fuseki/advanced-example"
TARGET_QUERY_ENDPOINT = f"{TARGET_ENDPOINT}/sparql"
TARGET_UPDATE_ENDPOINT = f"{TARGET_ENDPOINT}/update"
TARGET_DATA_ENDPOINT = f"{TARGET_ENDPOINT}/data"

# Oxigraph Docker configuration
OXIGRAPH_CONTAINER_NAME = "era-geometry-oxigraph-temp"
OXIGRAPH_PORT = None
OXIGRAPH_QUERY_ENDPOINT = None
OXIGRAPH_UPDATE_ENDPOINT = None
OXIGRAPH_STORE_ENDPOINT = None

# Input/Output files
INPUT_TTL_FILE = "../02-construct/output/era-graph.ttl"
OUTPUT_TTL_FILE = "output/era-graph-enriched.ttl"

# Fuseki availability
FUSEKI_AVAILABLE = False
OXIGRAPH_CONTAINER_ID = None


def start_oxigraph_container() -> bool:
    """Start Oxigraph Docker container."""
    global OXIGRAPH_CONTAINER_ID, OXIGRAPH_PORT, OXIGRAPH_QUERY_ENDPOINT, OXIGRAPH_UPDATE_ENDPOINT, OXIGRAPH_STORE_ENDPOINT
    
    try:
        OXIGRAPH_PORT = random.randint(17978, 18078)
        print(f"  Starting Oxigraph Docker container on port {OXIGRAPH_PORT}...")
        
        result = subprocess.run(
            [
                'docker', 'run', '-d',
                '--name', OXIGRAPH_CONTAINER_NAME,
                '-p', f'{OXIGRAPH_PORT}:7878',
                'oxigraph/oxigraph', 'serve'
            ],
            capture_output=True,
            text=True,
            check=True
        )
        
        OXIGRAPH_CONTAINER_ID = result.stdout.strip()
        OXIGRAPH_QUERY_ENDPOINT = f"http://localhost:{OXIGRAPH_PORT}/query"
        OXIGRAPH_UPDATE_ENDPOINT = f"http://localhost:{OXIGRAPH_PORT}/update"
        OXIGRAPH_STORE_ENDPOINT = f"http://localhost:{OXIGRAPH_PORT}/store"
        
        print("  Waiting for Oxigraph to be ready...")
        for i in range(30):
            time.sleep(1)
            try:
                response = requests.post(
                    OXIGRAPH_QUERY_ENDPOINT,
                    data={'query': 'ASK { }'},
                    timeout=2
                )
                if response.status_code == 200:
                    print(f"  ✓ Oxigraph container started (ID: {OXIGRAPH_CONTAINER_ID[:12]})")
                    return True
            except Exception:
                continue
        
        print("  ❌ Oxigraph container did not become ready in time")
        stop_oxigraph_container()
        return False
        
    except Exception as e:
        print(f"  ❌ Failed to start Oxigraph container: {e}")
        return False


def stop_oxigraph_container() -> None:
    """Stop and remove Oxigraph Docker container."""
    global OXIGRAPH_CONTAINER_ID
    
    if OXIGRAPH_CONTAINER_ID:
        try:
            print(f"\n🧹 Cleaning up Oxigraph container...")
            subprocess.run(['docker', 'stop', OXIGRAPH_CONTAINER_NAME], 
                         capture_output=True, timeout=10)
            subprocess.run(['docker', 'rm', OXIGRAPH_CONTAINER_NAME], 
                         capture_output=True, timeout=10)
            print("  ✓ Container removed")
        except Exception as e:
            print(f"  ⚠️  Warning: Failed to clean up container: {e}")
        finally:
            OXIGRAPH_CONTAINER_ID = None


def load_data_to_oxigraph() -> bool:
    """Load source TTL file into Oxigraph container."""
    try:
        print(f"  Loading data from {INPUT_TTL_FILE} into Oxigraph...")
        
        with open(INPUT_TTL_FILE, 'rb') as f:
            ttl_data = f.read()
        
        response = requests.post(
            OXIGRAPH_STORE_ENDPOINT,
            data=ttl_data,
            headers={'Content-Type': 'application/x-turtle'},
            timeout=120
        )
        
        if response.status_code in [200, 201, 204]:
            print(f"  ✓ Data loaded into Oxigraph")
            return True
        else:
            print(f"  ❌ Failed to load data: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ Failed to load data into Oxigraph: {e}")
        return False


def check_fuseki_availability() -> bool:
    """Check if Fuseki endpoint is available."""
    try:
        response = requests.post(
            TARGET_QUERY_ENDPOINT,
            data={'query': 'ASK { }'},
            timeout=5
        )
        return response.status_code == 200
    except Exception:
        return False


def get_active_endpoint() -> Optional[str]:
    """Get the active SPARQL query endpoint (Fuseki or Oxigraph)."""
    if FUSEKI_AVAILABLE:
        return TARGET_QUERY_ENDPOINT
    elif OXIGRAPH_CONTAINER_ID:
        return OXIGRAPH_QUERY_ENDPOINT
    else:
        return None


def query_net_point_references() -> List[Dict]:
    """
    Query for all NetPointReferences with their TopologicalCoordinates.
    Only returns those that don't already have gsp:hasGeometry.
    
    Returns list of dictionaries with keys:
        - netPointRef: URI string
        - topoCoord: URI string
        - linearElement: URI string
        - offset: float value
    """
    query = """
    PREFIX era: <http://data.europa.eu/949/>
    PREFIX gsp: <http://www.opengis.net/ont/geosparql#>
    
    SELECT ?netPointRef ?topoCoord ?linearElement ?offset
    WHERE {
        ?netPointRef a era:NetPointReference ;
                     era:hasTopoCoordinate ?topoCoord .
        ?topoCoord era:onLinearElement ?linearElement ;
                   era:offsetFromOrigin ?offset .
        FILTER NOT EXISTS { ?netPointRef gsp:hasGeometry ?existing }
    }
    """
    
    endpoint = get_active_endpoint()
    if not endpoint:
        raise RuntimeError("No SPARQL endpoint available")
    
    response = requests.post(
        endpoint,
        data={'query': query},
        headers={'Accept': 'application/sparql-results+json'},
        timeout=60
    )
    response.raise_for_status()
    
    results = response.json()
    
    records = []
    for binding in results['results']['bindings']:
        records.append({
            'netPointRef': binding['netPointRef']['value'],
            'topoCoord': binding['topoCoord']['value'],
            'linearElement': binding['linearElement']['value'],
            'offset': float(binding['offset']['value'])
        })
    
    return records


def query_net_linear_references() -> List[Dict]:
    """
    Query for all NetLinearReferences with their start and end points.
    Only returns those that don't already have gsp:hasGeometry.
    
    Returns list of dictionaries with keys:
        - netLinearRef: URI string
        - startLinearElement: URI string
        - startOffset: float value
        - endLinearElement: URI string
        - endOffset: float value
    """
    query = """
    PREFIX era: <http://data.europa.eu/949/>
    PREFIX gsp: <http://www.opengis.net/ont/geosparql#>
    
    SELECT ?netLinearRef ?startLinearElement ?startOffset ?endLinearElement ?endOffset
    WHERE {
        ?netLinearRef a era:NetLinearReference ;
                      era:startsAt ?startRef ;
                      era:endsAt ?endRef .
        
        ?startRef era:hasTopoCoordinate ?startTopoCoord .
        ?startTopoCoord era:onLinearElement ?startLinearElement ;
                        era:offsetFromOrigin ?startOffset .
        
        ?endRef era:hasTopoCoordinate ?endTopoCoord .
        ?endTopoCoord era:onLinearElement ?endLinearElement ;
                      era:offsetFromOrigin ?endOffset .
        
        FILTER NOT EXISTS { ?netLinearRef gsp:hasGeometry ?existing }
    }
    """
    
    endpoint = get_active_endpoint()
    if not endpoint:
        raise RuntimeError("No SPARQL endpoint available")
    
    response = requests.post(
        endpoint,
        data={'query': query},
        headers={'Accept': 'application/sparql-results+json'},
        timeout=60
    )
    response.raise_for_status()
    
    results = response.json()
    
    records = []
    for binding in results['results']['bindings']:
        records.append({
            'netLinearRef': binding['netLinearRef']['value'],
            'startLinearElement': binding['startLinearElement']['value'],
            'startOffset': float(binding['startOffset']['value']),
            'endLinearElement': binding['endLinearElement']['value'],
            'endOffset': float(binding['endOffset']['value'])
        })
    
    return records


def query_net_area_references() -> List[Dict]:
    """
    Query for all NetAreaReferences with their included NetLinearReferences.
    Only returns those that don't already have gsp:hasGeometry.
    
    Returns list of dictionaries with keys:
        - netAreaRef: URI string
        - netLinearRefs: list of URI strings
    """
    query = """
    PREFIX era: <http://data.europa.eu/949/>
    PREFIX gsp: <http://www.opengis.net/ont/geosparql#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    
    SELECT ?netAreaRef (GROUP_CONCAT(?netLinearRef; separator="|") AS ?netLinearRefs)
    WHERE {
        ?netAreaRef a era:NetAreaReference ;
                    era:includes ?includesList .
        
        ?includesList rdf:rest* ?listNode .
        ?listNode rdf:first ?netLinearRef .
        
        FILTER NOT EXISTS { ?netAreaRef gsp:hasGeometry ?existing }
    }
    GROUP BY ?netAreaRef
    """
    
    endpoint = get_active_endpoint()
    if not endpoint:
        raise RuntimeError("No SPARQL endpoint available")
    
    response = requests.post(
        endpoint,
        data={'query': query},
        headers={'Accept': 'application/sparql-results+json'},
        timeout=60
    )
    response.raise_for_status()
    
    results = response.json()
    
    records = []
    for binding in results['results']['bindings']:
        linear_refs_str = binding.get('netLinearRefs', {}).get('value', '')
        linear_refs = [ref.strip() for ref in linear_refs_str.split('|') if ref.strip()]
        
        records.append({
            'netAreaRef': binding['netAreaRef']['value'],
            'netLinearRefs': linear_refs
        })
    
    return records


def query_linear_element_geometries() -> Dict[str, str]:
    """
    Query for all LinearElement geometries.
    
    Returns:
        Dictionary mapping LinearElement URI → WKT string
    """
    query = """
    PREFIX era: <http://data.europa.eu/949/>
    PREFIX gsp: <http://www.opengis.net/ont/geosparql#>
    
    SELECT ?linearElement ?wkt
    WHERE {
        ?linearElement a era:LinearElement ;
                       gsp:hasGeometry/gsp:asWKT ?wkt .
    }
    """
    
    endpoint = get_active_endpoint()
    if not endpoint:
        raise RuntimeError("No SPARQL endpoint available")
    
    response = requests.post(
        endpoint,
        data={'query': query},
        headers={'Accept': 'application/sparql-results+json'},
        timeout=60
    )
    response.raise_for_status()
    
    results = response.json()
    
    geometries = {}
    for binding in results['results']['bindings']:
        linear_element = binding['linearElement']['value']
        wkt = binding['wkt']['value']
        geometries[linear_element] = wkt
    
    return geometries


def interpolate_point_on_linestring(wkt: str, offset: float) -> Optional[Point]:
    """
    Interpolate a point along a LINESTRING at a given offset.
    
    Args:
        wkt: WKT LINESTRING (may include CRS prefix)
        offset: Distance along the line from origin (meters)
    
    Returns:
        Shapely Point at the interpolated position, or None if invalid
    """
    try:
        # Remove CRS prefix if present (e.g., "<http://...> LINESTRING(...)")
        if wkt.startswith('<'):
            wkt = wkt.split('>', 1)[1].strip()
        
        line = wkt_loads(wkt)
        
        # Use Shapely's interpolate function for linear referencing
        # Distance is in the same units as the coordinates
        point = line.interpolate(offset)
        
        return point
        
    except Exception as e:
        print(f"  ⚠️  Warning: Failed to interpolate point: {e}")
        return None


def create_geometry_triple(
    resource_uri: str,
    geometry: Union[Point, LineString, MultiLineString],
    geometry_type: str
) -> str:
    """
    Create geometry triples for a resource in Turtle format.
    
    Returns Turtle string:
        <resourceUri> gsp:hasGeometry <geometry> .
        <geometry> a gsp:Geometry ;
                  gsp:asWKT "..."^^gsp:wktLiteral .
    
    Args:
        resource_uri: Resource URI string (NetPointReference, NetLinearReference, or NetAreaReference)
        geometry: Shapely geometry (Point, LineString, or MultiLineString)
        geometry_type: Type identifier for URI minting ("point", "linestring", "multilinestring")
    
    Returns:
        Turtle string with geometry triples
    """
    wkt_string = geometry.wkt
    # Create a hash-based URI for the geometry to ensure uniqueness
    import hashlib
    geom_hash = hashlib.md5(wkt_string.encode()).hexdigest()[:8]
    geometry_uri = f"http://data.europa.eu/949/geometry/{geometry_type}/{geom_hash}"
    
    turtle = f"""
<{resource_uri}> <http://www.opengis.net/ont/geosparql#hasGeometry> <{geometry_uri}> .
<{geometry_uri}> a <http://www.opengis.net/ont/geosparql#Geometry> ;
    <http://www.opengis.net/ont/geosparql#asWKT> "{wkt_string}"^^<http://www.opengis.net/ont/geosparql#wktLiteral> .
"""
    return turtle


def insert_geometry_triples(turtle_data: str) -> None:
    """Insert geometry triples into target endpoint."""
    if FUSEKI_AVAILABLE:
        response = requests.post(
            TARGET_DATA_ENDPOINT,
            data=turtle_data.encode('utf-8'),
            headers={'Content-Type': 'text/turtle'},
            params={'default': ''},
            timeout=120
        )
        response.raise_for_status()
    elif OXIGRAPH_CONTAINER_ID:
        response = requests.post(
            OXIGRAPH_STORE_ENDPOINT,
            data=turtle_data.encode('utf-8'),
            headers={'Content-Type': 'application/x-turtle'},
            timeout=120
        )
        response.raise_for_status()
    else:
        raise RuntimeError("No endpoint available for inserting triples")


def save_enriched_graph_to_file(turtle_data: str) -> None:
    """Save enriched graph to local file by merging with original."""
    print(f"   Reading original graph from: {INPUT_TTL_FILE}")
    
    with open(INPUT_TTL_FILE, 'r', encoding='utf-8') as f:
        original_turtle = f.read()
    
    # Simple merge: concatenate Turtle documents
    # They will share the same namespace prefixes
    enriched_turtle = original_turtle + "\n\n# Geometry Enrichment\n" + turtle_data
    
    print(f"   Writing enriched graph to: {OUTPUT_TTL_FILE}")
    with open(OUTPUT_TTL_FILE, 'w', encoding='utf-8') as f:
        f.write(enriched_turtle)
    
    print("   ✓ Saved successfully")


def main():
    """Main execution flow."""
    global FUSEKI_AVAILABLE
    
    try:
        print("=" * 70)
        print("ERA Geometry Enrichment - Linear Referencing")
        print("=" * 70)
        print(f"Target endpoint: {TARGET_ENDPOINT}")
        print()
        
        # Check Fuseki availability
        print("🔍 Checking Fuseki availability...")
        FUSEKI_AVAILABLE = check_fuseki_availability()
        if FUSEKI_AVAILABLE:
            print("   ✓ Fuseki is available")
        else:
            print("   ⚠️  Fuseki is not available (will use Oxigraph Docker)")
            
            # Check if local file exists
            from pathlib import Path
            if not Path(INPUT_TTL_FILE).exists():
                print(f"   ❌ ERROR: Local file not found: {INPUT_TTL_FILE}")
                print("      Please run step 02-construct first")
                return 1
            
            # Start Oxigraph container
            if not start_oxigraph_container():
                print("   ❌ ERROR: Failed to start Oxigraph container")
                print("      Please ensure Docker is running")
                return 1
            
            # Load data into Oxigraph
            if not load_data_to_oxigraph():
                print("   ❌ ERROR: Failed to load data into Oxigraph")
                return 1
        
        print()
        
        # Step 1: Query for all reference types
        print("📊 Querying NetPointReferences with TopologicalCoordinates...")
        net_point_ref_records = query_net_point_references()
        print(f"   Found {len(net_point_ref_records)} NetPointReferences (without geometries)")
        
        print("\n📊 Querying NetLinearReferences...")
        net_linear_ref_records = query_net_linear_references()
        print(f"   Found {len(net_linear_ref_records)} NetLinearReferences (without geometries)")
        
        print("\n📊 Querying NetAreaReferences...")
        net_area_ref_records = query_net_area_references()
        print(f"   Found {len(net_area_ref_records)} NetAreaReferences (without geometries)")
        
        total_records = len(net_point_ref_records) + len(net_linear_ref_records) + len(net_area_ref_records)
        
        if total_records == 0:
            print("\n✓ No references found without geometries - nothing to enrich")
            return 0
        
        # Step 2: Query for LinearElement geometries
        print("\n📊 Querying LinearElement geometries...")
        linear_element_geometries = query_linear_element_geometries()
        print(f"   Found {len(linear_element_geometries)} LinearElements with geometries")
        
        geometry_triples = []
        successful = 0
        skipped = 0
        
        # Step 3: Process NetPointReferences
        if net_point_ref_records:
            print(f"\n🔧 Enriching {len(net_point_ref_records)} NetPointReferences with POINT geometries...")
            
            for record in net_point_ref_records:
                net_point_ref = record['netPointRef']
                linear_element = record['linearElement']
                offset = record['offset']
                
                # Get LinearElement geometry
                wkt_str = linear_element_geometries.get(linear_element)
                if not wkt_str:
                    print(f"  ⚠️  No geometry for LinearElement {linear_element}")
                    skipped += 1
                    continue
                
                # Interpolate point
                point = interpolate_point_on_linestring(wkt_str, offset)
                
                if not point:
                    skipped += 1
                    continue
                
                # Create geometry triple
                turtle = create_geometry_triple(net_point_ref, point, "point")
                geometry_triples.append(turtle)
                successful += 1
            
            print(f"   ✓ NetPointReferences enriched: {successful}")
        
        # Step 4: Process NetLinearReferences
        if net_linear_ref_records:
            print(f"\n🔧 Enriching {len(net_linear_ref_records)} NetLinearReferences with LINESTRING geometries...")
            
            linear_successful = 0
            linear_skipped = 0
            
            for record in net_linear_ref_records:
                net_linear_ref = record['netLinearRef']
                start_element = record['startLinearElement']
                start_offset = record['startOffset']
                end_element = record['endLinearElement']
                end_offset = record['endOffset']
                
                # Interpolate start point
                start_wkt = linear_element_geometries.get(start_element)
                if not start_wkt:
                    print(f"  ⚠️  No geometry for start LinearElement {start_element}")
                    linear_skipped += 1
                    continue
                
                start_point = interpolate_point_on_linestring(start_wkt, start_offset)
                if not start_point:
                    linear_skipped += 1
                    continue
                
                # Interpolate end point
                end_wkt = linear_element_geometries.get(end_element)
                if not end_wkt:
                    print(f"  ⚠️  No geometry for end LinearElement {end_element}")
                    linear_skipped += 1
                    continue
                
                end_point = interpolate_point_on_linestring(end_wkt, end_offset)
                if not end_point:
                    linear_skipped += 1
                    continue
                
                # Create LineString from start to end
                # For simplicity, use a straight line between the two points
                # Future enhancement: extract the actual segment from the LineString if on same element
                linestring = LineString([(start_point.x, start_point.y), (end_point.x, end_point.y)])
                
                # Create geometry triple
                turtle = create_geometry_triple(net_linear_ref, linestring, "linestring")
                geometry_triples.append(turtle)
                linear_successful += 1
            
            print(f"   ✓ NetLinearReferences enriched: {linear_successful}")
            if linear_skipped > 0:
                print(f"   ⚠️  Skipped: {linear_skipped}")
            
            successful += linear_successful
            skipped += linear_skipped
        
        # Step 5: Process NetAreaReferences
        if net_area_ref_records:
            print(f"\n🔧 Enriching {len(net_area_ref_records)} NetAreaReferences with MULTILINESTRING geometries...")
            
            area_successful = 0
            area_skipped = 0
            
            for record in net_area_ref_records:
                net_area_ref = record['netAreaRef']
                linear_refs = record['netLinearRefs']
                
                if not linear_refs:
                    area_skipped += 1
                    continue
                
                # Collect LineString geometries for each included NetLinearReference
                linestrings = []
                
                for linear_ref in linear_refs:
                    # Find the matching NetLinearReference record
                    found = False
                    for linear_record in net_linear_ref_records:
                        if linear_record['netLinearRef'] == linear_ref:
                            # Reconstruct the geometry
                            start_element = linear_record['startLinearElement']
                            start_offset = linear_record['startOffset']
                            end_element = linear_record['endLinearElement']
                            end_offset = linear_record['endOffset']
                            
                            start_wkt = linear_element_geometries.get(start_element)
                            end_wkt = linear_element_geometries.get(end_element)
                            
                            if start_wkt and end_wkt:
                                start_point = interpolate_point_on_linestring(start_wkt, start_offset)
                                end_point = interpolate_point_on_linestring(end_wkt, end_offset)
                                
                                if start_point and end_point:
                                    linestrings.append(LineString([(start_point.x, start_point.y), 
                                                                  (end_point.x, end_point.y)]))
                                    found = True
                            break
                    
                    if not found:
                        print(f"  ⚠️  Could not create geometry for NetLinearReference {linear_ref}")
                
                if len(linestrings) == 0:
                    area_skipped += 1
                    continue
                
                # Create MultiLineString
                multilinestring = MultiLineString(linestrings)
                
                # Create geometry triple
                turtle = create_geometry_triple(net_area_ref, multilinestring, "multilinestring")
                geometry_triples.append(turtle)
                area_successful += 1
            
            print(f"   ✓ NetAreaReferences enriched: {area_successful}")
            if area_skipped > 0:
                print(f"   ⚠️  Skipped: {area_skipped}")
            
            successful += area_successful
            skipped += area_skipped
        
        print(f"\n   ══════════════════════════════")
        print(f"   Total successfully enriched: {successful}")
        print(f"   Total skipped: {skipped}")
        print(f"   ══════════════════════════════")
        
        # Step 4: Insert geometry triples
        if geometry_triples:
            combined_turtle = "\n".join(geometry_triples)
            triple_count = combined_turtle.count('\n')
            
            action = "Inserting" if FUSEKI_AVAILABLE else "Saving"
            print(f"\n📤 {action} ~{triple_count} geometry triples...")
            
            if FUSEKI_AVAILABLE or OXIGRAPH_CONTAINER_ID:
                insert_geometry_triples(combined_turtle)
                print("   ✓ Inserted successfully")
            
            # Always save to local file when not using Fuseki
            if not FUSEKI_AVAILABLE:
                save_enriched_graph_to_file(combined_turtle)
        
        # Summary
        print("\n" + "=" * 70)
        print("✅ Geometry enrichment complete!")
        print(f"   Total references enriched: {successful}")
        if net_point_ref_records:
            point_enriched = len([t for t in geometry_triples if '"point/' in t])
            print(f"     - NetPointReferences: {point_enriched}")
        if net_linear_ref_records:
            linear_enriched = len([t for t in geometry_triples if '"linestring/' in t])
            print(f"     - NetLinearReferences: {linear_enriched}")
        if net_area_ref_records:
            area_enriched = len([t for t in geometry_triples if '"multilinestring/' in t])
            print(f"     - NetAreaReferences: {area_enriched}")
        print(f"   Geometry triples added: ~{len(geometry_triples) * 2}")
        if FUSEKI_AVAILABLE:
            print(f"   Saved to Fuseki: {TARGET_ENDPOINT}")
        else:
            print(f"   Saved to file: {OUTPUT_TTL_FILE}")
        print("=" * 70)
        
        return 0 if skipped == 0 else 1
    
    finally:
        # Always clean up Oxigraph container if it was started
        stop_oxigraph_container()


if __name__ == "__main__":
    exit(main())
