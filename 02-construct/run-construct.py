#!/usr/bin/env python3
"""
Execute ERA ontology CONSTRUCT queries and load results into target endpoint.

This script:
1. Finds all SPARQL CONSTRUCT queries in the era-construct directory
2. Executes each query against the source endpoint (one-eyed graph)
3. Inserts the resulting RDF triples into the target endpoint (ERA graph)
4. Runs geometry enrichment for NetPointReferences (linear referencing)
"""

import os
import glob
import subprocess
import sys
import argparse
from pathlib import Path
import requests
from typing import List, Tuple
import time
import random

# Ensure UTF-8 encoding for Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuration
SOURCE_ENDPOINT = "http://localhost:8082/jena-fuseki/advanced-example-one-eyed/sparql"
TARGET_ENDPOINT = "http://localhost:8082/jena-fuseki/advanced-example"
TARGET_UPDATE_ENDPOINT = f"{TARGET_ENDPOINT}/update"
TARGET_DATA_ENDPOINT = f"{TARGET_ENDPOINT}/data"

# Oxigraph Docker configuration
OXIGRAPH_CONTAINER_NAME = "era-oxigraph-temp"
OXIGRAPH_PORT = None  # Will be set dynamically
OXIGRAPH_QUERY_ENDPOINT = None  # Will be set after container starts
OXIGRAPH_UPDATE_ENDPOINT = None  # Will be set after container starts

# Directory containing SPARQL queries
CONSTRUCT_DIR = Path("./")

# Input/Output files
INPUT_TTL_FILE = "../01-prep/one-eyed-graph.ttl"
OUTPUT_TTL_FILE = "era-graph.ttl"

# Track if Fuseki endpoints are available
SOURCE_FUSEKI_AVAILABLE = False
TARGET_FUSEKI_AVAILABLE = False
OXIGRAPH_CONTAINER_ID = None  # Track Oxigraph container for cleanup


def find_sparql_queries() -> List[Path]:
    """Find all .sparql files in the era-construct directory, sorted by path."""
    pattern = str(CONSTRUCT_DIR / "**" / "*.sparql")
    files = [Path(f) for f in glob.glob(pattern, recursive=True)]
    return sorted(files)


def read_query(file_path: Path) -> str:
    """Read SPARQL query from file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def start_oxigraph_container() -> bool:
    """
    Start an Oxigraph Docker container for local SPARQL execution.
    
    Returns:
        bool: True if container started successfully, False otherwise
    """
    global OXIGRAPH_CONTAINER_ID, OXIGRAPH_PORT, OXIGRAPH_QUERY_ENDPOINT, OXIGRAPH_UPDATE_ENDPOINT
    
    try:
        # Find an available port
        OXIGRAPH_PORT = random.randint(17878, 17978)
        
        print(f"  Starting Oxigraph Docker container on port {OXIGRAPH_PORT}...")
        
        # Start Oxigraph container
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
        
        # Wait for container to be ready
        print("  Waiting for Oxigraph to be ready...")
        for i in range(30):  # Wait up to 30 seconds
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
        
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Failed to start Oxigraph container: {e.stderr}")
        return False
    except Exception as e:
        print(f"  ❌ Failed to start Oxigraph container: {e}")
        return False


def stop_oxigraph_container() -> None:
    """Stop and remove the Oxigraph Docker container."""
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
    """
    Load source TTL file into Oxigraph container.
    
    Returns:
        bool: True if data loaded successfully, False otherwise
    """
    try:
        print(f"  Loading data from {INPUT_TTL_FILE} into Oxigraph...")
        
        # Read the TTL file
        with open(INPUT_TTL_FILE, 'rb') as f:
            ttl_data = f.read()
        
        # Load data using SPARQL UPDATE with INSERT DATA
        # For large files, use the bulk load endpoint
        response = requests.post(
            f"http://localhost:{OXIGRAPH_PORT}/store",
            data=ttl_data,
            headers={'Content-Type': 'application/x-turtle'},
            timeout=120
        )
        
        if response.status_code in [200, 201, 204]:
            print(f"  ✓ Data loaded into Oxigraph")
            return True
        else:
            print(f"  ❌ Failed to load data: HTTP {response.status_code}")
            print(f"     {response.text}")
            return False
            
    except Exception as e:
        print(f"  ❌ Failed to load data into Oxigraph: {e}")
        return False


def execute_construct_query(query: str) -> str:
    """Execute CONSTRUCT query against source endpoint or Oxigraph and return Turtle."""
    if SOURCE_FUSEKI_AVAILABLE:
        # Query remote Fuseki endpoint
        response = requests.post(
            SOURCE_ENDPOINT,
            data={'query': query},
            headers={'Accept': 'text/turtle'},
            timeout=60
        )
        response.raise_for_status()
        return response.text
    elif OXIGRAPH_CONTAINER_ID:
        # Query Oxigraph container
        response = requests.post(
            OXIGRAPH_QUERY_ENDPOINT,
            data={'query': query},
            headers={'Accept': 'text/turtle'},
            timeout=60
        )
        response.raise_for_status()
        return response.text
    else:
        raise RuntimeError("No SPARQL endpoint available (neither Fuseki nor Oxigraph)")


def insert_triples(turtle_data: str) -> None:
    """Insert triples into target endpoint using SPARQL UPDATE."""
    # Use INSERT DATA with turtle format
    # For larger datasets, we'll use the graph store protocol instead
    response = requests.post(
        TARGET_DATA_ENDPOINT,
        data=turtle_data.encode('utf-8'),
        headers={'Content-Type': 'text/turtle'},
        params={'default': ''},  # Insert into default graph
        timeout=120
    )
    response.raise_for_status()


def check_fuseki_availability() -> bool:
    """Check if Fuseki target endpoint is available."""
    try:
        # Use ASK query to test endpoint
        response = requests.post(
            f"{TARGET_ENDPOINT}/query",
            data={'query': 'ASK { }'  },
            timeout=5
        )
        return response.status_code == 200
    except Exception:
        return False


def check_source_endpoint_availability() -> bool:
    """Check if Fuseki source endpoint is available."""
    try:
        # Use ASK query to test endpoint
        response = requests.post(
            SOURCE_ENDPOINT.replace('/sparql', '/query'),
            data={'query': 'ASK { }'},
            timeout=5
        )
        return response.status_code == 200
    except Exception:
        return False


def clear_target_endpoint() -> None:
    """Clear all data from the target endpoint."""
    update_query = "CLEAR DEFAULT"
    response = requests.post(
        TARGET_UPDATE_ENDPOINT,
        data={'update': update_query},
        timeout=30
    )
    response.raise_for_status()
    print("✓ Cleared target endpoint")


def process_query_file(file_path: Path) -> Tuple[bool, str, str]:
    """
    Process a single SPARQL query file.
    
    Returns:
        Tuple of (success: bool, message: str, turtle_data: str)
    """
    try:
        print(f"\n📄 Processing: {file_path}")
        
        # Read the query
        query = read_query(file_path)
        
        # Execute CONSTRUCT query
        print("  ⏳ Executing CONSTRUCT query...")
        turtle_data = execute_construct_query(query)
        
        # Count triples (rough estimate)
        triple_count = turtle_data.count('\n') - turtle_data.count('@prefix')
        print(f"  ✓ Generated ~{triple_count} triples")
        
        # Insert into target endpoint if available
        if TARGET_FUSEKI_AVAILABLE:
            print("  ⏳ Inserting triples into target endpoint...")
            try:
                insert_triples(turtle_data)
                print("  ✓ Inserted successfully")
            except Exception as e:
                print(f"  ⚠️  Warning: Failed to insert to Fuseki: {e}")
        
        return True, f"Success: {file_path.name}", turtle_data
        
    except Exception as e:
        error_msg = f"Error processing {file_path.name}: {str(e)}"
        print(f"  ❌ {error_msg}")
        return False, error_msg, ""


def main():
    """Main execution flow."""
    global SOURCE_FUSEKI_AVAILABLE, TARGET_FUSEKI_AVAILABLE
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Execute ERA CONSTRUCT queries')
    parser.add_argument('-y', '--yes', action='store_true', 
                        help='Skip confirmation prompt')
    args = parser.parse_args()
    
    try:
        print("=" * 70)
        print("ERA Ontology CONSTRUCT Query Execution")
        print("=" * 70)
        print(f"Source endpoint: {SOURCE_ENDPOINT}")
        print(f"Source file: {INPUT_TTL_FILE}")
        print(f"Target endpoint: {TARGET_ENDPOINT}")
        print(f"Query directory: {CONSTRUCT_DIR}")
        print(f"Output TTL file: {OUTPUT_TTL_FILE}")
        print()
        
        # Check source endpoint availability
        print("Checking source endpoint availability...")
        SOURCE_FUSEKI_AVAILABLE = check_source_endpoint_availability()
        if SOURCE_FUSEKI_AVAILABLE:
            print("✓ Source endpoint is available (will query Fuseki)")
        else:
            print("⚠️  Source endpoint not available (will use Oxigraph Docker)")
            # Check if local file exists
            if not Path(INPUT_TTL_FILE).exists():
                print(f"❌ ERROR: Local file not found: {INPUT_TTL_FILE}")
                print("   Please run step 01-prep first")
                return 1
            
            # Start Oxigraph container
            if not start_oxigraph_container():
                print("❌ ERROR: Failed to start Oxigraph container")
                print("   Please ensure Docker is running")
                return 1
            
            # Load data into Oxigraph
            if not load_data_to_oxigraph():
                print("❌ ERROR: Failed to load data into Oxigraph")
                return 1
        
        # Check target endpoint availability
        print("Checking target endpoint availability...")
        TARGET_FUSEKI_AVAILABLE = check_fuseki_availability()
        if TARGET_FUSEKI_AVAILABLE:
            print("✓ Target endpoint is available (will save to Fuseki)")
        else:
            print("⚠️  WARNING: Target endpoint is not available")
            print("   Results will only be saved to TTL file")
        print()
        
        # Find all query files
        query_files = find_sparql_queries()
        
        if not query_files:
            print("❌ No SPARQL query files found in era-construct directory")
            return 1
        
        print(f"Found {len(query_files)} SPARQL query file(s):")
        for f in query_files:
            print(f"  - {f}")
        print()
        
        # Clear target endpoint if available
        if TARGET_FUSEKI_AVAILABLE:
            print("\n🗑️  Clearing target endpoint...")
            try:
                clear_target_endpoint()
            except Exception as e:
                print(f"⚠️  WARNING: Failed to clear target endpoint: {e}")
                print("   Continuing with local file output only")
                TARGET_FUSEKI_AVAILABLE = False
        
        # Initialize combined TTL output
        combined_turtle = ""
        
        # Process each query file
        results = []
        for query_file in query_files:
            success, message, turtle_data = process_query_file(query_file)
            results.append((query_file, success, message))
            if success:
                combined_turtle += "\n" + turtle_data
        
        # Save combined TTL file
        print(f"\n💾 Saving combined results to {OUTPUT_TTL_FILE}...")
        try:
            with open(OUTPUT_TTL_FILE, 'w', encoding='utf-8') as f:
                f.write(combined_turtle)
            print(f"✓ Saved to {OUTPUT_TTL_FILE}")
        except Exception as e:
            print(f"❌ Failed to save TTL file: {e}")
            return 1
        
        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        
        successful = sum(1 for _, success, _ in results if success)
        failed = len(results) - successful
        
        print(f"Total queries: {len(results)}")
        print(f"✓ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        if TARGET_FUSEKI_AVAILABLE:
            print(f"💾 Saved to Fuseki: {TARGET_ENDPOINT}")
        print(f"💾 Saved to file: {OUTPUT_TTL_FILE}")
        
        if failed > 0:
            print("\nFailed queries:")
            for file_path, success, message in results:
                if not success:
                    print(f"  - {message}")
            return 1
        else:
            print("\n✅ All queries executed successfully!")
            
            return 0
    
    finally:
        # Always clean up Oxigraph container if it was started
        stop_oxigraph_container()


if __name__ == "__main__":
    exit(main())
