from maplib import Model
import polars as pl
import rdflib
import urllib.request
from pathlib import Path
from datetime import datetime

# Define paths
data_file = Path("../03-post-process/era-graph-enriched.ttl")
shapes_dir = Path("shapes")
shapes_dir.mkdir(exist_ok=True)

# URLs for ERA SHACL shapes
era_rinf_shapes_url = "https://gitlab.com/era-europa-eu/public/interoperable-data-programme/era-ontology/era-ontology/-/raw/main/era-shacl/ERA-RINF-shapes.ttl"
skos_shapes_url = "https://gitlab.com/era-europa-eu/public/interoperable-data-programme/era-ontology/era-ontology/-/raw/main/era-shacl/SKOS-shapes.ttl"

# Download SHACL shapes
era_rinf_shapes_file = shapes_dir / "ERA-RINF-shapes.ttl"
skos_shapes_file = shapes_dir / "SKOS-shapes.ttl"

print("Downloading ERA RINF SHACL shapes...")
urllib.request.urlretrieve(era_rinf_shapes_url, era_rinf_shapes_file)
print(f"Downloaded to {era_rinf_shapes_file}")

print("Downloading SKOS SHACL shapes...")
urllib.request.urlretrieve(skos_shapes_url, skos_shapes_file)
print(f"Downloaded to {skos_shapes_file}")

# Initialize mapping and load data
m = Model()
print(f"Loading data from {data_file}...")

# Workaround: Use rdflib to parse and re-serialize the turtle file
# This handles any encoding or format quirks that maplib's parser doesn't like
print("Preprocessing TTL file with rdflib...")
g_temp = rdflib.Graph()
g_temp.parse(str(data_file), format="turtle")
temp_nt_file = shapes_dir / "temp_data.nt"
g_temp.serialize(destination=str(temp_nt_file), format="ntriples")
print(f"Converted to N-Triples format at {temp_nt_file}")

# Load the normalized N-Triples file into maplib
m.read(str(temp_nt_file), format="ntriples")
print("Data loaded successfully")

# Clean up temporary file
temp_nt_file.unlink()

# Filter SHACL shapes to remove unsupported GeoSPARQL constraints
print("Filtering SHACL shapes to remove unsupported GeoSPARQL functions...")
filtered_shapes_file = shapes_dir / "filtered-shapes.ttl"

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
    validation_model.write("validation-report.ttl", format="turtle")
    print("Validation report saved to validation-report.ttl")

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
    else:
        print(f"[VIOLATIONS] Found {len(df)} types of violations:\n")
        print(df)
        
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