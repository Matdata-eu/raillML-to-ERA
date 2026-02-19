from maplib import Model
import polars as pl
import rdflib
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
era_rinf_shapes_url = "https://gitlab.com/era-europa-eu/public/interoperable-data-programme/era-ontology/era-ontology/-/raw/main/era-shacl/ERA-RINF-shapes.ttl"
skos_shapes_url = "https://gitlab.com/era-europa-eu/public/interoperable-data-programme/era-ontology/era-ontology/-/raw/main/era-shacl/SKOS-shapes.ttl"

# URLs for ERA ontology and SKOS data
era_ontology_url = "https://gitlab.com/era-europa-eu/public/interoperable-data-programme/era-ontology/era-ontology/-/raw/main/ontology.ttl"
era_skos_api_url = "https://gitlab.com/api/v4/projects/era-europa-eu%2Fpublic%2Finteroperable-data-programme%2Fera-ontology%2Fera-ontology/repository/tree?path=era-skos&ref=main"
era_skos_base_url = "https://gitlab.com/era-europa-eu/public/interoperable-data-programme/era-ontology/era-ontology/-/raw/main/era-skos/"

# Download SHACL shapes
era_rinf_shapes_file = download_dir / "ERA-RINF-shapes.ttl"
skos_shapes_file = download_dir / "SKOS-shapes.ttl"

if era_rinf_shapes_file.exists():
    print(f"ERA RINF SHACL shapes already exists at {era_rinf_shapes_file}")
else:
    print("Downloading ERA RINF SHACL shapes...")
    urllib.request.urlretrieve(era_rinf_shapes_url, era_rinf_shapes_file)
    print(f"Downloaded to {era_rinf_shapes_file}")

if skos_shapes_file.exists():
    print(f"SKOS SHACL shapes already exists at {skos_shapes_file}")
else:
    print("Downloading SKOS SHACL shapes...")
    urllib.request.urlretrieve(skos_shapes_url, skos_shapes_file)
    print(f"Downloaded to {skos_shapes_file}")

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

# Initialize mapping and load data
m = Model()
print(f"\nLoading data from {data_file}...")

# Workaround: Use rdflib to parse and re-serialize the turtle file
# This handles any encoding or format quirks that maplib's parser doesn't like
print("Preprocessing TTL file with rdflib...")
g_temp = rdflib.Graph()

# Load main data file
print("  Loading main data...")
g_temp.parse(str(data_file), format="turtle")

# Load ERA ontology into data graph
print("  Loading ERA ontology...")
try:
    g_temp.parse(str(era_ontology_file), format="turtle")
    print(f"    ✓ Loaded ontology")
except Exception as e:
    print(f"    ⚠️  Warning: Failed to load ontology: {e}")

# Load SKOS files into data graph
if skos_files:
    print("  Loading SKOS files...")
    for skos_file in skos_files:
        try:
            g_temp.parse(str(skos_file), format="turtle")
            print(f"    ✓ Loaded {skos_file.name}")
        except Exception as e:
            print(f"    ⚠️  Warning: Failed to load {skos_file.name}: {e}")

temp_nt_file = download_dir / "temp_data.nt"
g_temp.serialize(destination=str(temp_nt_file), format="ntriples")
print(f"Converted to N-Triples format at {temp_nt_file}")

# Load the normalized N-Triples file into maplib
m.read(str(temp_nt_file), format="ntriples")
print("Data loaded successfully")
print(f"  Total triples in data graph: {len(g_temp)}")

# Clean up temporary file
temp_nt_file.unlink()

# Filter SHACL shapes to remove unsupported GeoSPARQL constraints
print("Filtering SHACL shapes to remove unsupported GeoSPARQL functions...")
filtered_shapes_file = download_dir / "filtered-shapes.ttl"

# Load shapes into rdflib
shapes_graph = rdflib.Graph()
shapes_graph.parse(str(era_rinf_shapes_file), format="turtle")
shapes_graph.parse(str(skos_shapes_file), format="turtle")

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
    report = m.validate(shape_graph=shape_graph_uri, include_shape_graph=False)
    validation_model = report.graph()

    # Write validation report
    print("Writing validation report...")
    validation_model.write("output/validation-report.ttl", format="turtle")
    print("Validation report saved to output/validation-report.ttl")

    query = """
    PREFIX sh: <http://www.w3.org/ns/shacl#>
    SELECT ?path ?message ?sourceConstraintComponent (COUNT(?violation) AS ?violation_count) (SAMPLE(?focusNode) AS ?example)
    WHERE {
        ?violation a sh:ValidationResult ;
                    sh:resultPath ?path ;
                    sh:focusNode ?focusNode ;
                    sh:sourceConstraintComponent ?sourceConstraintComponent .
        
        OPTIONAL { ?violation sh:resultMessage ?message }
    }
    GROUP BY ?path ?message ?sourceConstraintComponent
    ORDER BY ?path ?message ?sourceConstraintComponent
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
            f.write("| Property Path | Constraint Component | Violations | Message | Example Node |\n")
            f.write("|---------------|---------------------|------------|---------|-------------|\n")
            
            for row in df.iter_rows(named=True):
                path = row.get('path', 'N/A')
                constraint = row.get('sourceConstraintComponent', 'N/A')
                count = row.get('violation_count', 0)
                message = row.get('message', '')
                example = row.get('example', 'N/A')
                
                # Format URIs for readability
                path_str = str(path).replace('http://data.europa.eu/949/', 'era:')
                constraint_str = str(constraint).replace('http://www.w3.org/ns/shacl#', 'sh:')
                example_str = str(example).replace('http://data.europa.eu/949/', 'era:')
                
                # Escape pipe characters in message
                message_str = str(message).replace('|', '\\|') if message else ''
                
                f.write(f"| `{path_str}` | `{constraint_str}` | {count} | {message_str} | `{example_str}` |\n")
            
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