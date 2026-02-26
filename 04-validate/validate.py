import time
from maplib import Model
import polars as pl
import rdflib
from rdflib import Graph
import urllib.request
import requests
from pathlib import Path
from datetime import datetime

# Define paths
data_file = Path("../03-post-process/output/era-graph-enriched.ttl")
download_dir = Path("downloads")
download_dir.mkdir(exist_ok=True)
shape_fixes_dir = Path("shape-fixes")

# URLs for ERA SHACL shapes
era_rinf_shapes_url = "https://gitlab.com/era-europa-eu/public/interoperable-data-programme/era-ontology/era-ontology/-/raw/72a053c51b87aab657f133dc175369e1337d1943/era-shacl/ERA-RINF-shapes.ttl?inline=false"

# URLs for ERA ontology and SKOS data
era_ontology_url = "https://gitlab.com/era-europa-eu/public/interoperable-data-programme/era-ontology/era-ontology/-/raw/main/ontology.ttl"
era_skos_api_url = "https://gitlab.com/api/v4/projects/era-europa-eu%2Fpublic%2Finteroperable-data-programme%2Fera-ontology%2Fera-ontology/repository/tree?path=era-skos&ref=main"
era_skos_base_url = "https://gitlab.com/era-europa-eu/public/interoperable-data-programme/era-ontology/era-ontology/-/raw/main/era-skos/"

# Download SHACL shapes
era_rinf_shapes_file = download_dir / "ERA-RINF-shapes.ttl"

# Initialize mapping and load data
m = Model()
print(f"\nLoading data from {data_file}...")

# Load main data file
print("  Loading main data...")
m.read(data_file, format='turtle')

# Fetch ReferenceBorderPoint triples from the ERA endpoint and add to the data graph
era_sparql_endpoint = "https://data-interop.era.europa.eu/api/sparql"
reference_border_points_file = download_dir / "reference-border-points.ttl"

if reference_border_points_file.exists():
    print(f"\nReferenceBorderPoint data already exists at {reference_border_points_file}")
else:
    print("\nFetching ReferenceBorderPoint data from ERA endpoint...")
    rbp_construct_query = """
PREFIX gsp: <http://www.opengis.net/ont/geosparql#>
PREFIX era: <http://data.europa.eu/949/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

CONSTRUCT {
  ?s ?p ?o .
  ?o ?pp ?oo .
}
WHERE {
  ?s a era:ReferenceBorderPoint ;
     ?p ?o .
  OPTIONAL {
    ?o ?pp ?oo .
  }
}
"""
    try:
        response = requests.get(
            era_sparql_endpoint,
            params={"query": rbp_construct_query},
            headers={"Accept": "text/turtle"},
            timeout=60,
        )
        response.raise_for_status()
        reference_border_points_file.write_bytes(response.content)
        print(f"  ✓ Saved ReferenceBorderPoint data to {reference_border_points_file}")
    except Exception as e:
        print(f"  ⚠️  Warning: Failed to fetch ReferenceBorderPoint data: {e}")
        print("     Validation of era:referenceBorderPoint may be incomplete")
        reference_border_points_file = None

if reference_border_points_file and reference_border_points_file.exists():
    print("  Loading ReferenceBorderPoint data into data graph...")
    try:
        m.read(str(reference_border_points_file), format="turtle")
        print("  ✓ Loaded ReferenceBorderPoint data")
    except Exception as e:
        print(f"  ⚠️  Warning: Failed to load ReferenceBorderPoint data: {e}")

if era_rinf_shapes_file.exists():
    print(f"\nERA RINF SHACL shapes already exists at {era_rinf_shapes_file}")
else:
    print("Downloading ERA RINF SHACL shapes...")
    urllib.request.urlretrieve(era_rinf_shapes_url, era_rinf_shapes_file)
    print(f"Downloaded to {era_rinf_shapes_file}")

# Download ERA ontology
era_ontology_file = download_dir / "era-ontology.ttl"
if era_ontology_file.exists():
    print(f"\nERA ontology already exists at {era_ontology_file}")
else:
    print("\nDownloading ERA ontology...")
    urllib.request.urlretrieve(era_ontology_url, era_ontology_file)
    print(f"Downloaded to {era_ontology_file}")

# Download ERA SKOS files
print("\nDownloading ERA SKOS files...")
skos_files = []
try:
    # GitLab API uses pagination - fetch all pages
    page = 1
    per_page = 100  # Maximum allowed by GitLab API
    all_items = []
    
    while True:
        paginated_url = f"{era_skos_api_url}&per_page={per_page}&page={page}"
        print(f"  Fetching page {page} from GitLab API...")
        response = requests.get(paginated_url, timeout=30)
        response.raise_for_status()
        items = response.json()
        
        if not items:  # No more items
            break
        
        all_items.extend(items)
        page += 1
    
    print(f"  Found {len(all_items)} items in era-skos directory")
    
    # Download all .ttl files
    for item in all_items:
        if item['type'] == 'blob' and item['name'].endswith('.ttl'):
            file_name = item['name']
            file_url = era_skos_base_url + file_name
            local_file = download_dir / f"skos-{file_name}"
            
            if local_file.exists():
                print(f"  {file_name} already exists, skipping download")
                skos_files.append(local_file)
            else:
                print(f"  Downloading {file_name}...")
                urllib.request.urlretrieve(file_url, local_file)
                skos_files.append(local_file)
    
    print(f"Downloaded {len(skos_files)} SKOS file(s)")
except Exception as e:
    print(f"  ⚠️  Warning: Failed to download SKOS files: {e}")
    print("     Validation may be incomplete")


# Load ERA ontology into data graph
print("  Loading ERA ontology...")
try:
    m.read(str(era_ontology_file), format="turtle")
    print(f"    ✓ Loaded ontology")
except Exception as e:
    print(f"    ⚠️  Warning: Failed to load ontology: {e}")

# Load SKOS files into data graph
if skos_files:
    print(f"  Merging {len(skos_files)} SKOS files...")
    merged_skos_file = download_dir / "merged-skos.ttl"
    skos_graph = rdflib.Graph()
    for skos_file in skos_files:
        print(f"    ... Merging {skos_file.name}")
        try:
            skos_graph.parse(str(skos_file), format="turtle")
        except Exception as e:
            print(f"    ⚠️  Warning: Failed to merge {skos_file.name}: {e}")
    skos_graph.serialize(destination=str(merged_skos_file), format="turtle")
    print(f"  Loading merged SKOS file ({len(skos_graph)} triples)...")
    try:
        m.read(str(merged_skos_file), format="turtle")
        print(f"  ✓ Loaded merged SKOS file")
    except Exception as e:
        print(f"  ⚠️  Warning: Failed to load merged SKOS file: {e}")

print("Data loaded successfully")
print(f"  Total triples in data graph")

# Filter SHACL shapes to remove unsupported GeoSPARQL constraints
print("Filtering SHACL shapes to remove unsupported GeoSPARQL functions...")
filtered_shapes_file = download_dir / "filtered-shapes.ttl"

# Load shapes into rdflib
shapes_graph = rdflib.Graph()
shapes_graph.parse(str(era_rinf_shapes_file), format="turtle")

# Identify and remove SPARQL constraints that use unimplemented GeoSPARQL functions
SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")
unimplemented_functions = [
    "http://www.opengis.net/def/function/geosparql/distance",
    "http://www.opengis.net/def/function/geosparql/sfContains",
    "http://www.opengis.net/def/function/geosparql/sfWithin",
    # Prefix forms as they appear in Turtle files
    "geof:distance",
    "geof:sfContains",
    "geof:sfWithin",
]

removed_count = 0
for constraint in shapes_graph.subjects(rdflib.RDF.type, SH.SPARQLConstraint):
    for select_query in shapes_graph.objects(constraint, SH.select):
        query_text = str(select_query)
        if any(func in query_text for func in unimplemented_functions):
            # Remove this constraint component
            for triple in shapes_graph.triples((constraint, None, None)):
                shapes_graph.remove(triple)
            # Also remove references to this constraint
            for s, p, o in list(shapes_graph.triples((None, None, constraint))):
                shapes_graph.remove((s, p, o))
            removed_count += 1
            print(f"  Removed SPARQL constraint using GeoSPARQL function")
            break

print(f"Removed {removed_count} constraint(s) with unimplemented GeoSPARQL functions")

# Apply shape fixes from queries in shape-fixes directory
if shape_fixes_dir.exists():
    fix_files = sorted(shape_fixes_dir.glob("*.sparql"))
    if fix_files:
        print(f"\nApplying {len(fix_files)} shape fix(es)...")
        for fix_file in fix_files:
            print(f"  Applying fix: {fix_file.name}")
            fix_query = fix_file.read_text(encoding='utf-8')
            shapes_graph.update(fix_query)
        print("Shape fixes applied successfully")
    else:
        print("\nNo shape fixes found in shape-fixes directory")
else:
    print("\nShape-fixes directory not found, skipping fixes")

# Save filtered shapes
shapes_graph.serialize(destination=str(filtered_shapes_file), format="turtle")
print(f"Filtered shapes saved to {filtered_shapes_file}")

# Load SHACL shapes into a specific graph
shape_graph_uri = "https://data.europa.eu/949/era-shacl-shapes"
print(f"Loading filtered SHACL shapes into graph {shape_graph_uri}...")
m.read(str(filtered_shapes_file), graph=shape_graph_uri)

df_count = m.query("SELECT (count(?s) as ?count) WHERE { ?s ?p ?o }")
print("Total triples count: " + str(df_count["count"][0]))

print("\nRunning SHACL validation...")
print("NOTE: SHACL validation requires a valid maplib license from https://www.data-treehouse.com/\n")

try:
    _t0 = time.perf_counter()
    report = m.validate(shape_graph=shape_graph_uri, include_shape_graph=False)
    _t1 = time.perf_counter()
    print(f"Validation completed in {_t1 - _t0:.1f}s")
    validation_model = report.graph()

    # Write validation report
    print("Writing validation report...")
    # Use N-Triples format for more robust serialization (avoid pretty-printing issues)
    validation_model.write("output/validation-report.nt", format="ntriples")
    print("Validation report saved to output/validation-report.nt")
    
    # Convert to Turtle format using rdflib for better readability
    print("Converting to Turtle format using rdflib...")
    g_validation = Graph()
    g_validation.parse("output/validation-report.nt", format="ntriples")
    g_validation.serialize(destination="output/validation-report.ttl", format="turtle")
    print("Validation report saved to output/validation-report.ttl")

    query = """
    PREFIX sh: <http://www.w3.org/ns/shacl#>
    SELECT ?level ?sourceShape (SAMPLE(?path) AS ?path) (SAMPLE(?message) AS ?message) (SAMPLE(?sourceConstraintComponent) AS ?sourceConstraintComponent) (COUNT(?violation) AS ?violation_count) (SAMPLE(?focusNode) AS ?example)
    WHERE {
        ?violation a sh:ValidationResult ;
                    sh:sourceShape ?sourceShape ;
                    sh:focusNode ?focusNode ;
                     .
                     
        OPTIONAL { ?violation sh:resultPath ?path }
        OPTIONAL { ?violation sh:sourceConstraintComponent ?sourceConstraintComponent }
        OPTIONAL { ?violation sh:resultMessage ?message }
        OPTIONAL { ?violation sh:resultSeverity ?level }
    }
    GROUP BY ?level ?sourceShape
    ORDER BY ?level ?sourceShape
    """
    # Get query results
    df = validation_model.query(query)

    print("\n=== VALIDATION SUMMARY ===")
    if len(df) == 0:
        print("[OK] No validation violations found!")
        summary_status = "✅ PASSED"
        summary_message = "No validation violations found!"
    else:
        print(f"[VIOLATIONS] Found {len(df)} types of violations:\n")
        print(df)
        summary_status = "❌ FAILED"
        summary_message = f"Found {len(df)} types of violations"
    
    # Write summary to markdown file
    summary_file = Path("output/validation-summary.md")
    print(f"\nWriting validation summary to {summary_file}...")
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("# SHACL Validation Summary\n\n")
        f.write(f"**Status:** {summary_status}\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        if len(df) == 0:
            f.write(summary_message + "\n\n")
            f.write("All ERA ontology constraints are satisfied.\n")
        else:
            f.write(f"{summary_message}\n\n")
            f.write("## Violation Details\n\n")
            f.write("| Level | Property Path | Constraint Component | Violations | Message | Example Node |\n")
            f.write("|-------|---------------|---------------------|------------|---------|-------------|\n")
            
            for row in df.iter_rows(named=True):
                level = row.get('level', 'N/A')
                path = row.get('path', 'N/A')
                constraint = row.get('sourceConstraintComponent', 'N/A')
                count = row.get('violation_count', 0)
                message = row.get('message', '')
                example = row.get('example', 'N/A')
                
                # Format URIs for readability
                level_str = str(level).replace('http://www.w3.org/ns/shacl#', 'sh:')
                path_str = str(path).replace('http://data.europa.eu/949/', 'era:')
                constraint_str = str(constraint).replace('http://www.w3.org/ns/shacl#', 'sh:')
                example_str = str(example).replace('http://data.europa.eu/949/', 'era:')
                
                # Escape pipe characters in message
                message_str = str(message).replace('|', '\\|') if message else ''
                
                f.write(f"| `{level_str}` | `{path_str}` | `{constraint_str}` | {count} | {message_str} | `{example_str}` |\n")
            
            f.write("\n## Recommendations\n\n")
            f.write("1. Review the violations table above\n")
            f.write("2. Check the full validation report in `validation-report.ttl`\n")
            f.write("3. Update CONSTRUCT queries or add shape fixes as needed\n")
            f.write("4. Re-run the validation after making corrections\n")
    
    print(f"Validation summary saved to {summary_file}")
        
except Exception as e:
    print(f"\n[ERROR] SHACL validation failed: {type(e).__name__}")
    print(f"Details: {str(e)}")
    
    # Check if it's a license issue
    if "license" in str(e).lower():
        print("\n[!] SHACL validation requires a licensed version of maplib.")
        print("    Visit https://www.data-treehouse.com/ to obtain a license.")
        print(f"\n    Data loading was successful ({df_count['count'][0]} triples loaded).")
        print("    Once you have a license, re-run this script to perform validation.")
    # Check if it's an unimplemented function
    elif "not implemented" in str(e).lower() or "function" in str(e).lower():
        print("\n[!] The validation encountered SPARQL constraints using functions")
        print("    that are not yet implemented in maplib.")
        print(f"\n    Data loading was successful ({df_count['count'][0]} triples loaded).")
        print("    Consider updating the SHACL shapes or waiting for maplib updates.")
    else:
        print(f"\n    Data loading was successful ({df_count['count'][0]} triples loaded).")
        print("    Check the error details above for more information.")
    
    raise