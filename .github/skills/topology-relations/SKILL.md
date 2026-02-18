---
name: topology-relations
description: Determine spatial relationships between ERA infrastructure elements using network topology overlap matching. Use when inferring any relationship based on network position (containment, proximity, etc.) in post-processing or CONSTRUCT queries.
---

# Topology-Based Relationship Mapping

Determine spatial relationships between ERA infrastructure elements by analyzing network reference overlap using micro-level topology.

## Core Principle

Elements have spatial relationships when their **network references overlap** on the micro-level topology (LinearElement graph):

> **Linear elements** (tracks, electrification sections, tunnels, bridges) overlap with other elements when their `NetLinearReference` extents **partly or completely intersect**.
>
> **Point elements** (signals, switches, level crossings) relate to linear/aggregate elements when their `NetPointReference` position **falls within** the element's extent or shares the same micro-topology.

## Topology Structure

### NetPointReference (Point Elements)
```sparql
?pointElement era:netReference ?netPointRef .
?netPointRef a era:NetPointReference ;
             era:atPosition ?position .
?position era:atNetElement ?linearElement ;
          era:atPosition ?offset .
```

### NetLinearReference (Linear Elements)
```sparql
?linearElement era:netReference ?netLinearRef .
?netLinearRef era:startOfNetLinearReference ?startRef ;
              era:endOfNetLinearReference ?endRef .
?startRef era:atNetElement ?microNetElement ;
          era:atPosition ?startOffset .
?endRef era:atNetElement ?microNetElement ;
        era:atPosition ?endOffset .
```

## Matching Patterns

### Pattern 1: Point → Linear Element

**Rule**: Point element relates to linear element if positioned on same `LinearElement` within extent range.

```sparql
# Example: Signal → Track
?signal era:netReference ?signalNetRef .
?signalNetRef era:atPosition ?signalPos .
?signalPos era:atNetElement ?sharedLinearElement ;
           era:atPosition ?signalOffset .

?track era:netReference ?trackNetRef .
?trackNetRef era:startOfNetLinearReference/era:atNetElement ?sharedLinearElement ;
             era:startOfNetLinearReference/era:atPosition ?trackStartOffset ;
             era:endOfNetLinearReference/era:atPosition ?trackEndOffset .

# Check if signal offset is within track range
BIND (IF(?trackStartOffset < ?trackEndOffset, 
         ?trackStartOffset, ?trackEndOffset) AS ?minOffset)
BIND (IF(?trackStartOffset < ?trackEndOffset, 
         ?trackEndOffset, ?trackStartOffset) AS ?maxOffset)

FILTER (?signalOffset >= ?minOffset && ?signalOffset <= ?maxOffset)
```

**Applies to**:
- Signal, Switch, LevelCrossing, TrainDetectionElement → Track
- ETCSLevel, PlatformEdge → Track

### Pattern 2: Linear → Linear Element (Overlap)

**Rule**: Linear element A overlaps with linear element B if their extents intersect on the same `LinearElement`.

```sparql
# Example: Track → ElectrificationSection, SpeedSection
?child era:netReference ?childNetRef .
?childNetRef era:startOfNetLinearReference/era:atNetElement ?sharedLinearElement ;
             era:startOfNetLinearReference/era:atPosition ?childStart ;
             era:endOfNetLinearReference/era:atPosition ?childEnd .

?parent era:netReference ?parentNetRef .
?parentNetRef era:startOfNetLinearReference/era:atNetElement ?sharedLinearElement ;
              era:startOfNetLinearReference/era:atPosition ?parentStart ;
              era:endOfNetLinearReference/era:atPosition ?parentEnd .

# Check for overlap (any intersection, partial or complete)
BIND (IF(?childStart < ?childEnd, ?childStart, ?childEnd) AS ?childMin)
BIND (IF(?childStart < ?childEnd, ?childEnd, ?childStart) AS ?childMax)
BIND (IF(?parentStart < ?parentEnd, ?parentStart, ?parentEnd) AS ?parentMin)
BIND (IF(?parentStart < ?parentEnd, ?parentEnd, ?parentStart) AS ?parentMax)

# Overlap condition: NOT (childMax < parentMin OR childMin > parentMax)
FILTER (?childMax >= ?parentMin && ?childMin <= ?parentMax)
```

**Applies to**:
- Track → SpeedSection, ElectrificationSection, SectionOfLine
- Bridge, Tunnel → SectionOfLine

### Pattern 3: Element → Aggregate Container

**Rule**: Element relates to aggregate container if sharing the same micro `LinearElement`.

```sparql
# Example: Signal → OperationalPoint
?element era:netReference/era:atPosition/era:atNetElement ?linearElement .
?operationalPoint era:netReference/era:atPosition/era:atNetElement ?linearElement .
```

**Note**: OperationalPoints are typically small areas; simple LinearElement matching is sufficient.

## Implementation in Post-Processing

### SPARQL UPDATE Template

```sparql
PREFIX era: <http://data.europa.eu/949/>

INSERT {
  # Define your relationship properties here
  ?elementA era:yourRelationProperty ?elementB .
  # Optionally add inverse property
  ?elementB era:inverseRelationProperty ?elementA .
}
WHERE {
  # Pattern selection (use UNION for multiple patterns)
  {
    # Pattern 1: Point → Linear
    # ... (see above)
  } UNION {
    # Pattern 2: Linear → Linear
    # ... (see above)
  } UNION {
    # Pattern 3: Element → Aggregate
    # ... (see above)
  }
  
  # Idempotency: prevent duplicate relations
  FILTER NOT EXISTS { ?elementA era:yourRelationProperty ?elementB }
}
```

### Execution in run-post-process.ps1

```powershell
# Example: Infer topology-based relations
Write-Host "Inferring topology-based relations..." -ForegroundColor Cyan
$topologyQuery = Get-Content "your-topology-query.sparql" -Raw
$response = Invoke-RestMethod -Uri "$fusekiEndpoint/update" -Method POST `
    -Body $topologyQuery -ContentType "application/sparql-update"
```

## Validation Queries

### Count Relations by Type

```sparql
PREFIX era: <http://data.europa.eu/949/>

SELECT ?elementAType ?elementBType (COUNT(*) AS ?count)
WHERE {
  ?elementA era:yourRelationProperty ?elementB .
  ?elementA a ?elementAType .
  ?elementB a ?elementBType .
}
GROUP BY ?elementAType ?elementBType
ORDER BY DESC(?count)
```

### Find Elements Without Related Elements

```sparql
PREFIX era: <http://data.europa.eu/949/>

SELECT ?elementType (COUNT(?element) AS ?unrelatedCount)
WHERE {
  ?element a ?elementType .
  FILTER (?elementType IN (era:Signal, era:Track, era:Switch))
  FILTER NOT EXISTS { ?element era:yourRelationProperty ?other }
}
GROUP BY ?elementType
```

## Common Applications

- **Containment relations**: `era:isPartOf` / `era:hasPart` for infrastructure hierarchy
- **Spatial associations**: Elements affected by speed limits, electrification systems
- **Operational groupings**: Elements within operational points or sections
- **Conflict detection**: Overlapping protection zones, interlocking areas

## Common Pitfalls

1. **Bidirectional offset handling**: Always use MIN/MAX for start/end offsets (railML allows reverse ranges)
2. **Idempotency**: Use `FILTER NOT EXISTS` to prevent duplicate relations
3. **Type filtering**: Filter element types to avoid unwanted relations (e.g., exclude micro-topology NetElements)
4. **Overlap vs. containment**: Linear overlap requires intersection check, not full containment

## Key Considerations

- **Micro-topology required**: Patterns rely on `LinearElement` (micro-level) from railML source data
- **Transitive relations**: Consider if transitive chains need flattening (e.g., A→B→C implies A→C)
- **Multiple relations**: Elements can relate to multiple other elements (e.g., Track in both SpeedSection and SectionOfLine)
- **Performance**: Use FILTER on element types early to reduce join size
- **Relationship semantics**: Choose appropriate ERA properties based on the spatial relationship meaning
