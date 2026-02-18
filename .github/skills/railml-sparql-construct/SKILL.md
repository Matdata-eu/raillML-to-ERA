---
name: railml-sparql-construct
description: Create SPARQL CONSTRUCT queries to transform railML 3.2 XML to ERA ontology RDF following project conventions. Use when implementing new infrastructure element mappings or updating existing CONSTRUCT queries.
---

# railML to ERA SPARQL CONSTRUCT Implementation

Create SPARQL CONSTRUCT queries following established project patterns for transforming railML 3.2 XML data to ERA ontology RDF.

## File Location Pattern

`advanced-example/02-construct/03-functional-infrastructure/NN-element-name.sparql`

## Standard Prefixes

```sparql
PREFIX era: <http://data.europa.eu/949/>
PREFIX country: <http://data.europa.eu/949/countries/>
PREFIX gsp: <http://www.opengis.net/ont/geosparql#>
PREFIX railml: <https://www.railml.org/schemas/3.2#>
PREFIX xyz: <http://sparql.xyz/facade-x/data/>
PREFIX fx: <http://sparql.xyz/facade-x/ns/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
```

## Query Structure Template

```sparql
# Phase 3.N — Element Name (functional infrastructure)
# Maps railml:SourceElement → era:TargetClass
#
# Source: N railML instances
# 
# Target properties:
#   - era:property1 — description (type, cardinality)
#   - era:property2 — description
#
# URI Pattern:
#   http://data.europa.eu/949/functionalInfrastructure/elementType/{id}

CONSTRUCT {
  # Main resource and type
  ?eraElement a era:TargetClass ;
              rdfs:label ?label ;
              era:property1 ?value1 ;
              era:property2 ?value2 .
}
WHERE {
  # Get railML source elements
  ?railmlElement a railml:SourceElement ;
                 xyz:id ?elementId .
  
  # Mint ERA URI
  BIND (IRI(CONCAT("http://data.europa.eu/949/functionalInfrastructure/elementType/", ?elementId)) AS ?eraElement)
  
  # Extract properties
  # ...
}
```

## Class Hierarchy Check: InfrastructureElement

**CRITICAL STEP**: Before applying any positioning pattern, verify if the target ERA class is a subclass of `era:InfrastructureElement`.

### Check Subclass Relationship (MCP Query)

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

**Decision Tree**:

1. **IF class is subclass of `era:InfrastructureElement`**:
   - ✅ Use `era:netReference` property
   - ✅ Create NetLinearReference, NetPointReference, or NetAreaReference
   - Examples: Track, Bridge, Signal, Switch, OperationalPoint, PlatformEdge

2. **IF class is NOT subclass of `era:InfrastructureElement`**:
   - ❌ Do NOT use `era:netReference` property
   - ✅ Class is a "functional resource" referenced FROM infrastructure elements
   - ✅ Find which InfrastructureElement classes reference this resource
   - ✅ Create linking via shared netElements in railML data
   - Examples: ContactLineSystem, TrainDetectionSystem, LoadingGaugeProfile, TrackGaugeProfile

### Discovery of Linking Property (for non-InfrastructureElements)

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

Then check SHACL shapes to confirm which classes have this property:

```sparql
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX era: <http://data.europa.eu/949/>

SELECT ?targetClass ?property
WHERE {
  ?shape sh:targetClass ?targetClass .
  ?shape sh:property ?propShape .
  ?propShape sh:path ?property .
  FILTER(?property = era:yourLinkingProperty)
}
```

## Common Positioning Patterns (for InfrastructureElements only)

### Linear Extent (NetLinearReference)

Used for: Track, Bridge, SpeedSection

```sparql
?netLinearRef a era:NetLinearReference ;
              era:startOfNetLinearReference ?startRef ;
              era:endOfNetLinearReference ?endRef .

?startRef a era:LinearReference ;
          era:atNetElement ?netElement ;
          era:atPosition ?startPos .

?endRef a era:LinearReference ;
        era:atNetElement ?netElement ;
        era:atPosition ?endPos .
```

### Point Position (NetPointReference)

Used for: Signal, Switch, LevelCrossing, Tunnel endpoints

```sparql
?netPointRef a era:NetPointReference ;
             era:at era:NetPoint ;
             era:atPosition ?position .

?position a era:LinearReference ;
          era:atNetElement ?netElement ;
          era:atPosition ?intrinsicCoord .
```

## SKOS Concept Mapping

Map railML enumerations to ERA SKOS concepts:

```sparql
# Define mapping (outside WHERE)
BIND (IF(?railmlValue = "option1",
         IRI("http://data.europa.eu/949/concepts/category/10"),
         IF(?railmlValue = "option2",
            IRI("http://data.europa.eu/949/concepts/category/20"),
            IRI("http://data.europa.eu/949/concepts/category/99")
         )
     ) AS ?eraConcept)
```

## Workshop Simplifications

- **Infrastructure Manager**: Hardcode to `<http://data.europa.eu/949/organisations/0076_IM>`
- **Country**: Use `country:NOR`
- **Dummy Values**: Use conservative/safe defaults for required properties without railML source
- **Micro-topology**: Filter with `FILTER NOT EXISTS { ?element fx:topology ?topology }`

## Common Patterns by Element Type

### Infrastructure Elements (subclass of era:InfrastructureElement)

These classes have `era:netReference` property and use positioning patterns:

- **Linear Infrastructure**: NetLinearReference with start/end LinearReference
  - Examples: Track, Bridge, SpeedSection
- **Point Infrastructure**: NetPointReference with single LinearReference
  - Examples: Signal, Switch, LevelCrossing
- **Dual-Point Infrastructure**: Two separate NetPointReference instances
  - Example: Tunnel (start and end points)
- **Aggregate Infrastructure**: Property references to contained elements
  - Example: SectionOfLine (hasPart links to Tracks)

### Functional Resources (NOT subclass of era:InfrastructureElement)

These classes do NOT have `era:netReference` and are referenced FROM infrastructure elements:

- **ContactLineSystem**: Referenced via `era:contactLineSystem` from Track
- **TrainDetectionSystem**: Referenced via `era:trainDetection` from Track
- **LoadingGaugeProfile**: Referenced via `era:gaugingProfile` from Track
- **TrackGaugeProfile**: Referenced via `era:wheelSetGauge` from Track

**Implementation**: Link from Track via shared netElements (see functional resource linking pattern above)

## Key Considerations

1. **Filter Deprecated**: Always exclude deprecated properties/classes with `FILTER NOT EXISTS { ?x owl:deprecated "true"^^xsd:boolean }`
2. **Class Hierarchy First**: Always check if class is subclass of InfrastructureElement before using positioning patterns
3. **SHACL Compliance**: Check required properties with era-shacl-analysis skill
4. **URI Uniqueness**: Use railML `xyz:id` attributes for ERA URI minting
5. **Datatype Casting**: Explicit `xsd:` types for literals
6. **Optional Properties**: Use OPTIONAL blocks for non-required railML attributes
7. **Label**: Always include `rdfs:label` for human readability

## Validation

After creating SPARQL file:
1. Check syntax with Jena ARQ or SPARQL.anything
2. Verify SHACL required properties are included
3. Review against similar existing files in project
4. Test against source data if available
