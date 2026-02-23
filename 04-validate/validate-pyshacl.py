import time
import pyshacl
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
output_dir = Path("output-pyshacl")
output_dir.mkdir(exist_ok=True)

# URLs for ERA SHACL shapes
era_rinf_shapes_url = "https://gitlab.com/era-europa-eu/public/interoperable-data-programme/era-ontology/era-ontology/-/raw/72a053c51b87aab657f133dc175369e1337d1943/era-shacl/ERA-RINF-shapes.ttl?inline=false"

# URLs for ERA ontology and SKOS data
era_ontology_url = "https://gitlab.com/era-europa-eu/public/interoperable-data-programme/era-ontology/era-ontology/-/raw/main/ontology.ttl"
era_skos_api_url = "https://gitlab.com/api/v4/projects/era-europa-eu%2Fpublic%2Finteroperable-data-programme%2Fera-ontology%2Fera-ontology/repository/tree?path=era-skos&ref=main"
era_skos_base_url = "https://gitlab.com/era-europa-eu/public/interoperable-data-programme/era-ontology/era-ontology/-/raw/main/era-skos/"

# Download SHACL shapes
era_rinf_shapes_file = download_dir / "ERA-RINF-shapes.ttl"

# Load main data file into rdflib graph
print(f"\nLoading data from {data_file}...")
data_graph = Graph()
print("  Loading main data...")
data_graph.parse(str(data_file), format='turtle')
print(f"  Loaded {len(data_graph)} triples")

if era_rinf_shapes_file.exists():
    print(f"ERA RINF SHACL shapes already exists at {era_rinf_shapes_file}")
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


# Build ontology graph (ontology + SKOS) for pyshacl inference
ont_graph = Graph()
print("  Loading ERA ontology...")
try:
    ont_graph.parse(str(era_ontology_file), format="turtle")
    print(f"    ✓ Loaded ontology ({len(ont_graph)} triples)")
except Exception as e:
    print(f"    ⚠️  Warning: Failed to load ontology: {e}")

# Load SKOS files into ontology graph
if skos_files:
    print(f"  Loading {len(skos_files)} SKOS files into ontology graph...")
    for skos_file in skos_files:
        print(f"    ... Loading {skos_file.name}")
        try:
            ont_graph.parse(str(skos_file), format="turtle")
        except Exception as e:
            print(f"    ⚠️  Warning: Failed to load {skos_file.name}: {e}")
    print(f"  Ontology graph: {len(ont_graph)} triples total")

print("Data loaded successfully")
print(f"  Data graph: {len(data_graph)} triples")

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

print("\nRunning SHACL validation with pyshacl...")
_t0 = time.perf_counter()
conforms, results_graph, results_text = pyshacl.validate(
    data_graph,
    shacl_graph=shapes_graph,
    ont_graph=ont_graph,
    inference='rdfs',
    abort_on_first=False,
    advanced=True,
    debug=False,
)
_t1 = time.perf_counter()
print(f"Validation completed in {_t1 - _t0:.1f}s")

# Write validation report
print("Writing validation report...")
results_graph.serialize(destination=str(output_dir / "validation-report.ttl"), format="turtle")
print(f"Validation report saved to {output_dir / 'validation-report.ttl'}")

with open(output_dir / "validation-report.txt", 'w', encoding='utf-8') as f:
    f.write(results_text)
print(f"Validation text report saved to {output_dir / 'validation-report.txt'}")

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

rows = list(results_graph.query(query))

print("\n=== VALIDATION SUMMARY ===")
if conforms:
    print("[OK] No validation violations found!")
    summary_status = "✅ PASSED"
    summary_message = "No validation violations found!"
else:
    print(f"[VIOLATIONS] Found {len(rows)} types of violations:")
    summary_status = "❌ FAILED"
    summary_message = f"Found {len(rows)} types of violations"

# Write summary to markdown file
summary_file = output_dir / "validation-summary.md"
print(f"\nWriting validation summary to {summary_file}...")

with open(summary_file, 'w', encoding='utf-8') as f:
    f.write("# SHACL Validation Summary\n\n")
    f.write(f"**Status:** {summary_status}\n\n")
    f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    if conforms:
        f.write(summary_message + "\n\n")
        f.write("All ERA ontology constraints are satisfied.\n")
    else:
        f.write(f"{summary_message}\n\n")
        f.write("## Violation Details\n\n")
        f.write("| Level | Property Path | Constraint Component | Violations | Message | Example Node |\n")
        f.write("|-------|---------------|---------------------|------------|---------|-------------|\n")

        for row in rows:
            level = row.level
            path = row.path
            constraint = row.sourceConstraintComponent
            count = row.violation_count
            message = row.message
            example = row.example

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