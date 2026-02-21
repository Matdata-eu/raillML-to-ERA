"""
SHACL-on-SHACL validation of ERA-RINF-shapes.ttl using pyshacl.

Validates the ERA RINF SHACL shapes file against the SHACL meta-shapes
(i.e., checks that the shapes file is itself a valid SHACL document).
"""

from pathlib import Path
from rdflib import Graph
import sys

try:
    from pyshacl import validate
except ImportError:
    print("pyshacl is not installed. Install it with: pip install pyshacl")
    sys.exit(1)

data_file = Path("ERA-RINF-shapes.ttl")

if not data_file.exists():
    print(f"ERROR: Shapes file not found: {data_file}")
    sys.exit(1)

data_graph = Graph()
data_graph.parse(str(data_file), format="turtle")

shaclValidation = Graph()
shaclValidation.parse("https://www.w3.org/ns/shacl-shacl")

print(f"Running SHACL-on-SHACL validation on {data_file}...")

conforms, results_graph, results_text = validate(
    data_graph=data_graph,
    shacl_graph=shaclValidation
)

print(results_text)

if conforms:
    print("✓ The data file conforms to the SHACL-SHACL.")
    sys.exit(0)
else:
    print("✗ The data file does NOT conform to the SHACL-SHACL.")
    sys.exit(1)
