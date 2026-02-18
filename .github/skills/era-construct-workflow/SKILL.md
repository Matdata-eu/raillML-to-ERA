---
name: era-construct-workflow
description: Complete workflow for adding new ERA infrastructure elements to the railML-to-ERA conversion project. Use when implementing new element mappings from planning through testing.
---

# ERA CONSTRUCT Implementation Workflow

End-to-end process for implementing railML to ERA infrastructure element mappings.

## Complete Workflow

### Phase 1: Requirements Analysis

1. **Identify Target Element**
   - Determine ERA class (e.g., `era:Bridge`, `era:Tunnel`)
   - Find railML source element (e.g., `railml:overCrossing`)

2. **Check Class Hierarchy (CRITICAL)**
   - Use `era-mcp-query` skill to query class hierarchy:
     ```sparql
     PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
     PREFIX owl: <http://www.w3.org/2002/07/owl#>
     PREFIX era: <http://data.europa.eu/949/>
     SELECT ?superClass WHERE {
       era:YourClass rdfs:subClassOf* ?superClass .
       # Filter out deprecated classes
       FILTER NOT EXISTS { ?superClass owl:deprecated "true"^^xsd:boolean }
     }
     ```
   - **Decision**:
     - ✅ IF subclass of `era:InfrastructureElement` → use `era:netReference` positioning patterns
     - ❌ IF NOT subclass → functional resource pattern (referenced FROM other elements)
   - **For functional resources**: Find linking property via:
     ```sparql
     PREFIX owl: <http://www.w3.org/2002/07/owl#>
     SELECT ?property ?domain WHERE {
       ?property rdfs:range era:YourClass .
       OPTIONAL { ?property rdfs:domain ?domain . }
       # Filter out deprecated properties
       FILTER NOT EXISTS { ?property owl:deprecated "true"^^xsd:boolean }
     }
     ```
   
3. **Query SHACL Requirements**
   - Use `era-shacl-analysis` skill
   - Identify REQUIRED properties (minCount=1)
   - Note important properties (maxCount=1)
   - Document datatypes and node kinds
   - Check if `era:netReference` appears (confirms InfrastructureElement)

4. **Explore Source Data**
   - Use `era-mcp-query` skill on `one-eyed-graph`
   - Count available instances
   - Examine attribute structure
   - Identify potential mappings
   - **For functional resources**: Find shared netElements with referencing elements

### Phase 2: Documentation

Update `02-construct/construct-instructions.md`:

```markdown
### 3.N TargetElement

**ERA Class**: `era:TargetClass`  
**railML Source**: `railml:sourceElement`

**Properties** (SHACL Analysis):
- `era:requiredProperty1` — Description (Type, REQUIRED)
- `era:optionalProperty2` — Description (Type, maxCount=1)

**URI Pattern**:
```
http://data.europa.eu/949/functionalInfrastructure/elementType/{railml-id}
```

**Positioning Pattern**: NetLinearReference | NetPointReference | NetAreaReference

**SHACL Requirements**:
- REQUIRED: property1, property2
- Important: property3, property4

**Workshop Simplifications**:
- Property without source: use dummy value X
```

### Phase 3: SPARQL Implementation

1. **Create SPARQL File**
   - Location: `02-construct/03-functional-infrastructure/NN-element-name.sparql`
   - Follow `railml-sparql-construct` skill patterns
   
2. **Implement Structure**
   - Add standard prefixes
   - Write comprehensive header comment
   - Implement CONSTRUCT clause with all required properties
   - Implement WHERE clause with source extraction
   - Add positioning pattern (Linear/Point/Area Reference)

3. **Handle Edge Cases**
   - Micro-topology filtering (if applicable)
   - Optional property extraction with OPTIONAL blocks
   - Conditional mappings for enumerations
   - Fallback/dummy values for missing data

### Phase 4: Validation

1. **Syntax Check**
   - Review SPARQL syntax
   - Verify all BIND variables used
   - Check FILTER expressions

2. **SHACL Compliance**
   - Cross-check implemented properties against SHACL requirements
   - Verify all REQUIRED properties included
   - Confirm datatypes match SHACL constraints

3. **Pattern Consistency**
   - Compare with similar existing files
   - Follow project URI patterns
   - Use consistent naming conventions

4. **Test Execution** (if possible)
   - Run via `run-era-construct.py` script
   - Check output RDF syntax
   - Verify expected instance count

### Phase 5: Integration

1. **Update Documentation**
   - Ensure `construct-instructions.md` is current
   - Add any workshop notes or caveats

2. **Verify File Numbering**
   - Files numbered sequentially (01, 02, 03...)
   - Logical ordering (common → topology → functional → linear)

3. **Check References**
   - URIs referenced by this file exist (e.g., OperationalPoints for SectionOfLine)
   - Dependencies documented

## Quick Reference: File Locations

```
advanced-example/
├── 02-construct/
│   ├── construct-instructions.md       # Update documentation here
│   ├── run-era-construct.py           # Execution script
│   └── 03-functional-infrastructure/
│       ├── NN-new-element.sparql      # Create new file here
│       └── ...existing files...
```

## Common Patterns by Element Type

### Infrastructure Elements (subclass of era:InfrastructureElement)

These classes have `era:netReference` property and use positioning patterns:

#### Linear Infrastructure (Track-like)
- ✅ Use: NetLinearReference with start/end LinearReference
- Examples: Track, Bridge, SpeedSection

#### Point Infrastructure (Location-based)
- ✅ Use: NetPointReference with single LinearReference
- Examples: Signal, Switch, LevelCrossing

#### Dual-Point Infrastructure (Start/End points)
- ✅ Use: Two separate NetPointReference instances
- Example: Tunnel (start and end points)

#### Aggregate Infrastructure (Contains other elements)
- ✅ Use: Property references to contained elements
- Example: SectionOfLine (hasPart links to Tracks)

### Functional Resources (NOT subclass of era:InfrastructureElement)

These classes do NOT have `era:netReference` and are referenced FROM infrastructure elements:

#### Referenced from Track
- ❌ Do NOT use NetReference positioning patterns
- ✅ Use: Link from Track via shared netElements
- ✅ Pattern: `?track era:linkingProperty ?functionalResource`
- Examples:
  - ContactLineSystem (via `era:contactLineSystem`)
  - TrainDetectionSystem (via `era:trainDetection`)
  - LoadingGaugeProfile (via `era:gaugingProfile`)
  - TrackGaugeProfile (via `era:wheelSetGauge`)

#### Linking Implementation Pattern

```sparql
CONSTRUCT {
  ?functionalResource a era:FunctionalResourceClass ;
                      era:property ?value .
  
  ?track era:linkingProperty ?functionalResource .
}
WHERE {
  # Get railML functional element
  ?railmlFunctionalElement a railml:functionalElement ;
                           xyz:id ?functionalId ;
                           fx:linearLocation/fx:associatedNetElement/xyz:netElementRef ?sharedNetElement .
  
  # Get railML track sharing the same netElement
  ?railmlTrack a railml:track ;
               xyz:id ?trackId ;
               fx:linearLocation/fx:associatedNetElement/xyz:netElementRef ?sharedNetElement .
  
  # Mint URIs
  BIND (IRI(CONCAT("http://data.europa.eu/949/functionalInfrastructure/functionalResources/", ?functionalId)) AS ?functionalResource)
  BIND (IRI(CONCAT("http://data.europa.eu/949/functionalInfrastructure/tracks/", ?trackId)) AS ?track)
}
```

## Troubleshooting

- **Missing Source Data**: Add dummy values with comment explaining workshop simplification
- **Complex Enumerations**: Use nested IF/BIND for multi-option mappings
- **Multiple NetElements**: Use subqueries or UNION to handle multiple segments
- **Uncertain Datatypes**: Check SHACL shape or query similar ERA instances

## Success Criteria

✓ All SHACL REQUIRED properties implemented  
✓ Documentation updated in construct-instructions.md  
✓ SPARQL file follows project patterns  
✓ URI patterns consistent with existing elements  
✓ No syntax errors  
✓ Appropriate dummy values documented
