#!/usr/bin/env python3
"""Test SHACL validation capability in maplib"""

import os
from pathlib import Path
from maplib import Model

# Create a simple model with minimal data
m = Model()

# Create minimal test data file
test_data = """
@prefix ex: <http://example.org/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

ex:subject ex:predicate "value" .
"""

test_data_file = Path("test_data.ttl")
test_data_file.write_text(test_data)

m.read(str(test_data_file), format="turtle")
test_data_file.unlink()

print("Data loaded successfully")

# Create a minimal SHACL shape file
shape_graph = "http://example.org/shapes"
test_shape = """
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <http://example.org/> .

[] a sh:NodeShape .
"""

test_shape_file = Path("test_shape.ttl")
test_shape_file.write_text(test_shape)

m.read(str(test_shape_file), graph=shape_graph)
test_shape_file.unlink()

print("Shape graph created successfully")

# Check environment variables
print("\nEnvironment variables:")
for key in os.environ:
    if 'maplib' in key.lower() or 'license' in key.lower() or 'treehouse' in key.lower():
        print(f"  {key}={os.environ[key]}")

# Try to get license information
print("\nAttempting validation...")
try:
    report = m.validate(shape_graph=shape_graph, include_shape_graph=False)
    print("✓ Validation successful!")
    print(f"Report type: {type(report)}")
except Exception as e:
    print(f"✗ Validation failed: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    import traceback
    traceback.print_exc()
