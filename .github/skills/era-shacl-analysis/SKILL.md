---
name: era-shacl-analysis
description: Query ERA ontology SHACL constraints to find required and important properties for infrastructure classes. Use when identifying missing properties, validating ontology compliance, or checking SHACL requirements for ERA infrastructure elements.
---

# ERA SHACL Constraint Analysis

Query the ERA ontology's SHACL shapes to identify required and recommended properties for infrastructure elements.

## When to Use

- Finding required properties (minCount=1) for ERA classes
- Identifying important properties (maxCount=1 indicates single-value constraints)
- Validating SPARQL CONSTRUCT implementations against SHACL requirements
- Checking property datatypes and node kinds

## MCP Endpoint

- **Server**: `explorer-era-ontology`
- **Endpoint**: `http://localhost:8082/jena-fuseki/era-ontology/sparql`
- **Use**: `mcp_explorer-era-_sparql_query` tool with `query` parameter

## Common Query Patterns

### Find Required Properties (minCount=1)

```sparql
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX era: <http://data.europa.eu/949/>

SELECT ?property ?description ?datatype ?nodeKind
WHERE {
  ?shape sh:targetClass era:YourClass .
  ?shape sh:property ?propShape .
  ?propShape sh:path ?property .
  ?propShape sh:minCount ?minCount .
  FILTER(?minCount = 1)
  
  # Filter out deprecated properties
  FILTER NOT EXISTS { ?property owl:deprecated "true"^^xsd:boolean }
  
  OPTIONAL { ?propShape sh:description ?description . }
  OPTIONAL { ?propShape sh:datatype ?datatype . }
  OPTIONAL { ?propShape sh:nodeKind ?nodeKind . }
}
```

### Find Important Single-Value Properties (maxCount=1)

```sparql
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX era: <http://data.europa.eu/949/>

SELECT ?property ?description ?datatype
WHERE {
  ?shape sh:targetClass era:YourClass .
  ?shape sh:property ?propShape .
  ?propShape sh:path ?property .
  ?propShape sh:maxCount ?maxCount .
  FILTER(?maxCount = 1)
  
  # Filter out deprecated properties
  FILTER NOT EXISTS { ?property owl:deprecated "true"^^xsd:boolean }
  
  OPTIONAL { ?propShape sh:description ?description . }
  OPTIONAL { ?propShape sh:datatype ?datatype . }
}
```

### Count Required Properties Across Classes

```sparql
PREFIX sh: <http://www.w3.org/ns/shacl#>

SELECT ?class (COUNT(DISTINCT ?property) AS ?requiredCount)
WHERE {
  ?shape sh:targetClass ?class .
  ?shape sh:property ?propShape .
  ?propShape sh:path ?property .
  ?propShape sh:minCount ?minCount .
  FILTER(?minCount = 1)
}
GROUP BY ?class
ORDER BY DESC(?requiredCount)
```

## Key Infrastructure Classes

### InfrastructureElement Subclasses (have era:netReference)

- `era:Track`, `era:RunningTrack`, `era:Siding`
- `era:OperationalPoint`
- `era:PlatformEdge`
- `era:Switch`
- `era:Signal`
- `era:SectionOfLine`
- `era:Bridge`, `era:Tunnel`, `era:LevelCrossing`

### Functional Resources (NOT InfrastructureElement subclasses, NO era:netReference)

- `era:ContactLineSystem` (referenced via `era:contactLineSystem` from Track)
- `era:TrainDetectionSystem` (referenced via `era:trainDetection` from Track)
- `era:LoadingGaugeProfile` (referenced via `era:gaugingProfile` from Track)
- `era:TrackGaugeProfile` (referenced via `era:wheelSetGauge` from Track)

**IMPORTANT**: Query class hierarchy before assuming positioning patterns.

### Check if Class has netReference Property

```sparql
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX era: <http://data.europa.eu/949/>

SELECT ?shape
WHERE {
  ?shape sh:targetClass era:YourClass .
  ?shape sh:property ?propShape .
  ?propShape sh:path era:netReference .
}
```

**If results found**: Class is InfrastructureElement, use positioning patterns  
**If no results**: Class is functional resource, find linking property instead

## Interpretation

- **minCount=1**: Property is REQUIRED (must appear at least once)
- **maxCount=1**: Single-value constraint (important TSI/RINF properties)
- **nodeKind=IRI**: Property expects URI/SKOS concept reference
- **datatype**: Literal datatype (xsd:string, xsd:integer, xsd:boolean, etc.)

## Critical Filtering

**⚠️ ALWAYS filter out deprecated properties and classes**:

```sparql
FILTER NOT EXISTS { ?property owl:deprecated "true"^^xsd:boolean }
FILTER NOT EXISTS { ?class owl:deprecated "true"^^xsd:boolean }
```

**Examples of deprecated vocabulary to avoid**:
- `era:InfrastructureManager` (class) → use `era:Body` + `era:OrganisationRole` instead
- `era:imCode` (property) → use `era:organisationCode` instead
- `era:elementPart` (property) → use micro topology instead
- `era:NationalRailwayLine` (class) → use `era:SectionOfLine` instead
