---
name: era-mcp-query
description: Execute SPARQL queries against ERA ontology and railML source data using MCP servers. Use when querying ERA definitions, exploring railML structure, or analyzing source data for CONSTRUCT query development.
---

# ERA/railML MCP SPARQL Queries

Execute SPARQL queries against two MCP server endpoints for ERA ontology exploration and railML data analysis.

## Available MCP Servers

### 1. ERA Ontology Server

- **Server**: `explorer-era-ontology`
- **Tool**: `mcp_explorer-era-_sparql_query`
- **Endpoint**: `http://localhost:8082/jena-fuseki/era-ontology/sparql`
- **Contents**: ERA ontology OWL/SHACL definitions (v4.1.0)
- **Use For**: 
  - SHACL constraint queries
  - Property domain/range lookups
  - Class hierarchy exploration
  - SKOS concept scheme browsing

**⚠️ CRITICAL**: Always filter out deprecated elements when querying the ERA ontology:
```sparql
FILTER NOT EXISTS { ?property owl:deprecated "true"^^xsd:boolean }
FILTER NOT EXISTS { ?class owl:deprecated "true"^^xsd:boolean }
```

### 2. railML Source Data Server

- **Server**: `explorer-one-eyed-graph`
- **Tool**: `mcp_explorer-one-_sparql_query`
- **Endpoint**: `http://localhost:8082/jena-fuseki/advanced-example-one-eyed/sparql`
- **Contents**: Converted railML 3.2 sample data (One-Eyed infrastructure)
- **Use For**:
  - Exploring railML structure
  - Counting available instances
  - Extracting sample values
  - Testing CONSTRUCT query patterns

## Common Query Patterns

### Count railML Instances

```sparql
PREFIX railml: <https://www.railml.org/schemas/3.2#>

SELECT ?type (COUNT(*) AS ?count)
WHERE {
  ?element a ?type .
  FILTER(STRSTARTS(STR(?type), STR(railml:)))
}
GROUP BY ?type
ORDER BY DESC(?count)
```

### Explore railML Element Structure

```sparql
PREFIX railml: <https://www.railml.org/schemas/3.2#>
PREFIX xyz: <http://sparql.xyz/facade-x/data/>

SELECT DISTINCT ?property ?value
WHERE {
  ?element a railml:YourElementType .
  ?element ?property ?value .
}
LIMIT 100
```

### Find ERA Property Domain/Range

```sparql
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX era: <http://data.europa.eu/949/>

SELECT ?property ?domain ?range
WHERE {
  ?property rdfs:domain ?domain ;
            rdfs:range ?range .
  FILTER(CONTAINS(STR(?property), "propertyName"))
  
  # Filter out deprecated properties
  FILTER NOT EXISTS { ?property owl:deprecated "true"^^xsd:boolean }
}
```

### Check Class Hierarchy (InfrastructureElement)

**CRITICAL**: Determine if target class is a subclass of `era:InfrastructureElement` before using positioning patterns.

```sparql
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX era: <http://data.europa.eu/949/>

SELECT ?class ?superClass
WHERE {
  era:YourClass rdfs:subClassOf* ?superClass .
  
  # Filter out deprecated classes
  FILTER NOT EXISTS { ?superClass owl:deprecated "true"^^xsd:boolean }
}
```

**If `era:InfrastructureElement` appears in results**:
- ✅ Class has `era:netReference` property
- ✅ Use NetLinearReference, NetPointReference, or NetAreaReference patterns

**If `era:InfrastructureElement` does NOT appear**:
- ❌ Class is a "functional resource" (does NOT have `era:netReference`)
- Find which properties reference this class:

```sparql
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX era: <http://data.europa.eu/949/>

SELECT ?property ?domain
WHERE {
  ?property rdfs:range era:YourFunctionalResourceClass .
  OPTIONAL { ?property rdfs:domain ?domain . }
  
  # Filter out deprecated properties
  FILTER NOT EXISTS { ?property owl:deprecated "true"^^xsd:boolean }
}
```

Then check SHACL to confirm which classes have the linking property:

```sparql
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX era: <http://data.europa.eu/949/>

SELECT ?targetClass
WHERE {
  ?shape sh:targetClass ?targetClass .
  ?shape sh:property ?propShape .
  ?propShape sh:path era:yourLinkingProperty .
}
```

## Best Practices

1. **ALWAYS Filter Deprecated**: Include `FILTER NOT EXISTS { ?property owl:deprecated "true"^^xsd:boolean }` in all ERA ontology queries
2. **Use Correct Server**: ERA definitions → era-ontology, railML data → one-eyed-graph
3. **Limit Results**: Add LIMIT clause for exploratory queries
4. **Prefix Filters**: Use `FILTER(STRSTARTS(STR(?var), "namespace"))` to filter by namespace
5. **Sample Before Construct**: Query railML structure before writing CONSTRUCT queries
6. **Check Availability**: Verify elements exist in source data before mapping

## Example Workflows

### 1. Implementing New Infrastructure Element

```
1. Query era-ontology for SHACL requirements
2. Query one-eyed-graph to count railML instances
3. Explore railML element structure
4. Draft CONSTRUCT query
5. Test pattern with sample data
```

### 2. Finding Missing Properties

```
1. Query era-ontology for all class properties
2. Check current SPARQL file property list
3. Identify gaps
4. Query railML data for potential source attributes
```

## Troubleshooting

- **Empty Results**: Check if query sent to correct MCP server
- **Syntax Errors**: Verify all PREFIX declarations included
- **Large Results**: Use LIMIT and OFFSET for pagination
- **Namespace Issues**: Ensure correct namespace URIs (trailing # or /)
