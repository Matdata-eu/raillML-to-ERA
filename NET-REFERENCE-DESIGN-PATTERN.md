# ERA NetLinearReference Design Pattern: Multiple References vs. Sequence Lists

## Overview

This document explains the design decision for representing linear infrastructure elements that span multiple micro-topology segments in the ERA ontology conversion. We use a pattern that creates **multiple NetLinearReference instances** (one per segment) rather than a single NetLinearReference with a sequence list containing multiple LinearElements.

## Context

In railML 3.2, linear infrastructure elements (tracks, speed sections, electrification sections, platform edges, tunnels, bridges, etc.) can span multiple netElements. When converting to ERA ontology, we need to represent these multi-segment extents in the target graph.

The ERA ontology provides the `era:hasSequence` property on NetLinearReference, which has range `rdf:List` to represent ordered sequences of LinearElements that form a linear extent.

## The Design Question

**Given**: A track spanning 3 micro-level LinearElements (ne_147, ne_148, ne_149)

**Option 1 (ERA Standard Pattern)**: Single NetLinearReference with multi-element sequence list
```turtle
tracks/trc1 a era:Track ;
  era:netReference netLinearRef/trc1 .

netLinearRef/trc1 a era:NetLinearReference ;
  era:startsAt netPointRef/trc1_start ;
  era:endsAt netPointRef/trc1_end ;
  era:hasSequence (
    netElements/ne_147
    netElements/ne_148
    netElements/ne_149
  ) . # RDF List with 3 elements
```

**Option 2 (Our Implementation)**: Multiple NetLinearReferences with single-element sequence lists
```turtle
tracks/trc1 a era:Track ;
  era:netReference netLinearRef/trc1_segment_1 ;
  era:netReference netLinearRef/trc1_segment_2 ;
  era:netReference netLinearRef/trc1_segment_3 .

netLinearRef/trc1_segment_1 a era:NetLinearReference ;
  era:startsAt netPointRef/trc1_seg1_start ;
  era:endsAt netPointRef/trc1_seg1_end ;
  era:hasSequence (netElements/ne_147) . # Single-element list

netLinearRef/trc1_segment_2 a era:NetLinearReference ;
  era:startsAt netPointRef/trc1_seg2_start ;
  era:endsAt netPointRef/trc1_seg2_end ;
  era:hasSequence (netElements/ne_148) . # Single-element list

netLinearRef/trc1_segment_3 a era:NetLinearReference ;
  era:startsAt netPointRef/trc1_seg3_start ;
  era:endsAt netPointRef/trc1_seg3_end ;
  era:hasSequence (netElements/ne_149) . # Single-element list
```

## Our Choice: Multiple NetLinearReferences (Option 2)

We chose **Option 2** - creating multiple NetLinearReference instances, one per segment, each with a single-element `rdf:List` for `era:hasSequence`.

### Rationale

#### 1. **SPARQL CONSTRUCT Simplification**

Creating multi-element RDF Lists in SPARQL CONSTRUCT is extremely complex and brittle. The RDF List structure requires:
- A head node (`rdf:first` → first element, `rdf:rest` → next node)
- Intermediate nodes for each element
- Proper ordering via sequence numbers
- Termination with `rdf:nil`

**Challenge**: In SPARQL, you cannot easily create an ordered list of variable length within a single CONSTRUCT query:

```sparql
# This is VERY difficult in SPARQL CONSTRUCT:
?list rdf:first ?element1 ;
      rdf:rest [
        rdf:first ?element2 ;
        rdf:rest [
          rdf:first ?element3 ;
          rdf:rest rdf:nil
        ]
      ] .
```

The number of segments varies per track (1-14 segments in our dataset), making this pattern impractical.

**Our solution**: Each segment becomes a separate CONSTRUCT iteration, creating its own NetLinearReference with a simple single-element list:

```sparql
CONSTRUCT {
  ?track era:netReference ?netLinearRef .
  
  ?netLinearRef a era:NetLinearReference ;
                era:hasSequence ?sequenceList ;
                era:startsAt ?startPointRef ;
                era:endsAt ?endPointRef .
  
  # Single-element RDF List (trivial to construct)
  ?sequenceList rdf:first ?linearElement ;
                rdf:rest rdf:nil .
}
WHERE {
  ?track fx:linearLocation/fx:associatedNetElement ?segment .
  ?segment xyz:netElementRef ?netElementRef ;
           xyz:posBegin ?posBegin ;
           xyz:posEnd ?posEnd ;
           xyz:sequence ?sequence .
  # ... each segment creates one NetLinearReference
}
```

#### 2. **Individual Segment Positioning**

Each segment has its own:
- **Topological extent**: Start and end positions on the specific LinearElement
- **LRS coordinates**: KilometricPost references and offsets for start and end points
- **Sequence number**: Ordering within the parent element

With multiple NetLinearReferences, each segment maintains complete positioning independence:

```turtle
netLinearRef/trc1_segment_1 a era:NetLinearReference ;
  era:startsAt [
    era:hasTopoCoordinate [
      era:onLinearElement netElements/ne_147 ;
      era:offsetFromOrigin 0.0
    ] ;
    era:hasLrsCoordinate [
      era:kmPost kilometricPosts/km_km_3 ;
      era:offsetFromKilometricPost 245.0
    ]
  ] ;
  era:endsAt [
    era:hasTopoCoordinate [
      era:onLinearElement netElements/ne_147 ;
      era:offsetFromOrigin 400.0
    ] ;
    era:hasLrsCoordinate [
      era:kmPost kilometricPosts/km_km_3 ;
      era:offsetFromKilometricPost 645.0
    ]
  ] ;
  era:hasSequence (netElements/ne_147) .

netLinearRef/trc1_segment_2 a era:NetLinearReference ;
  era:startsAt [
    era:hasTopoCoordinate [
      era:onLinearElement netElements/ne_148 ;
      era:offsetFromOrigin 0.0
    ] ;
    era:hasLrsCoordinate [
      era:kmPost kilometricPosts/km_km_3 ;
      era:offsetFromKilometricPost 645.0
    ]
  ] ;
  era:endsAt [
    era:hasTopoCoordinate [
      era:onLinearElement netElements/ne_148 ;
      era:offsetFromOrigin 250.0
    ] ;
    era:hasLrsCoordinate [
      era:kmPost kilometricPosts/km_km_3 ;
      era:offsetFromKilometricPost 895.0
    ]
  ] ;
  era:hasSequence (netElements/ne_148) .
```

Each segment is a **complete, self-contained positioning unit** with full dual-coordinate representation.

#### 3. **Query Simplification**

Querying for infrastructure at specific positions is simpler:

```sparql
# Find tracks overlapping a specific LinearElement
SELECT ?track WHERE {
  ?track era:netReference ?netLinearRef .
  ?netLinearRef era:hasSequence/(rdf:rest*/rdf:first) ?linearElement .
  FILTER(?linearElement = netElements/ne_147)
}
```

With our pattern, the RDF List traversal is trivial (single-element list), while with multi-element lists, the `rdf:rest*` path expression must traverse variable-length chains.

#### 4. **Compatibility with ERA Ontology**

The ERA ontology does **not mandate** multi-element lists in `era:hasSequence`. The cardinality is open:
- `era:netReference` has `minCount: 1` (at least one reference required)
- `era:hasSequence` accepts `rdf:List` with **no constraint on list length**

Our pattern is fully compliant:
- ✅ Each NetLinearReference has a valid `era:hasSequence` → single-element `rdf:List`
- ✅ The infrastructure element has multiple `era:netReference` links (allowed by ontology)
- ✅ Each NetLinearReference provides complete start/end positioning

#### 5. **Practical Dataset Statistics**

In our advanced example dataset:
- 36 tracks create **54 NetLinearReference instances** (avg 1.5 per track)
- Range: 1-14 segments per linear element
- Speed sections: **31 sections** create **multiple NetLinearReferences each**
- Electrification sections: **16 sections** spanning multiple segments

**Total effort saved**: Avoiding complex multi-element RDF List construction for ~100+ segment instances across all linear infrastructure types.

## Design Principles

### Our Pattern (Multiple NetLinearReferences)

**When to use**:
- ✅ Converting multi-segment linear infrastructure from source data
- ✅ SPARQL CONSTRUCT generation (avoids complex list building)
- ✅ Need independent positioning per segment
- ✅ Source data provides per-segment extents and LRS coordinates

**Properties**:
- One `era:NetLinearReference` per micro-topology segment
- Each NetLinearReference has `era:hasSequence` → single-element `rdf:List`
- Infrastructure element has multiple `era:netReference` properties (one per segment)
- Complete dual positioning (topology + LRS) at segment level

**Advantages**:
- ✅ Trivial SPARQL CONSTRUCT implementation
- ✅ Self-contained segment positioning
- ✅ No list ordering complexity
- ✅ Easier to query individual segments
- ✅ Natural mapping from railML associatedNetElement pattern

**Disadvantages**:
- ❌ More NetLinearReference resources (one per segment vs. one per element)
- ❌ Requires aggregation to reconstruct total element extent
- ❌ `era:hasSequence` always contains single-element lists

### ERA Standard Pattern (Single NetLinearReference with Multi-Element List)

**When to use**:
- ✅ Manual RDF creation (not SPARQL CONSTRUCT)
- ✅ Representing continuous extent as single logical unit
- ✅ Source data provides complete sequence upfront
- ✅ Emphasis on minimal resource count

**Properties**:
- One `era:NetLinearReference` per infrastructure element
- `era:hasSequence` → multi-element `rdf:List` with all LinearElements in order
- Single start point (first element start) and end point (last element end)

**Advantages**:
- ✅ Single NetLinearReference resource per element
- ✅ Complete sequence visible in one structure
- ✅ Clearer representation of "total extent"

**Disadvantages**:
- ❌ Complex RDF List construction in SPARQL
- ❌ Difficult to represent per-segment LRS coordinates
- ❌ Variable-length list traversal in queries
- ❌ Start/end points only represent extent boundaries, not intermediate segments

## Complete Examples

### Example 1: Track "trc1" Spanning 3 Segments

**railML Source**:
```xml
<track id="trc1" type="mainTrack">
  <linearLocation>
    <associatedNetElement netElementRef="ne_147" 
                          posBegin="0.0" posEnd="400.0" 
                          sequence="1">
      <linearCoordinateBegin measure="3245.0" positioningSystemRef="km"/>
      <linearCoordinateEnd measure="3645.0" positioningSystemRef="km"/>
    </associatedNetElement>
    <associatedNetElement netElementRef="ne_148" 
                          posBegin="0.0" posEnd="250.0" 
                          sequence="2">
      <linearCoordinateBegin measure="3645.0" positioningSystemRef="km"/>
      <linearCoordinateEnd measure="3895.0" positioningSystemRef="km"/>
    </associatedNetElement>
    <associatedNetElement netElementRef="ne_149" 
                          posBegin="0.0" posEnd="150.0" 
                          sequence="3">
      <linearCoordinateBegin measure="3895.0" positioningSystemRef="km"/>
      <linearCoordinateEnd measure="4045.0" positioningSystemRef="km"/>
    </associatedNetElement>
  </linearLocation>
</track>
```

**Our Implementation (Multiple NetLinearReferences)**:
```turtle
@prefix era: <http://data.europa.eu/949/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

# Track resource
tracks/trc1 a era:RunningTrack ;
  era:trackId "trc1" ;
  era:netReference netLinearRef/trc1_segment_1 ,
                   netLinearRef/trc1_segment_2 ,
                   netLinearRef/trc1_segment_3 .

# ===== SEGMENT 1: ne_147 =====
netLinearRef/trc1_segment_1 a era:NetLinearReference ;
  era:hasSequence (netElements/ne_147) ; # Single-element list
  era:startsAt netPointRef/trc1_seg1_start ;
  era:endsAt netPointRef/trc1_seg1_end .

netPointRef/trc1_seg1_start a era:NetPointReference ;
  era:hasTopoCoordinate [
    a era:TopologicalCoordinate ;
    era:onLinearElement netElements/ne_147 ;
    era:offsetFromOrigin 0.0
  ] ;
  era:hasLrsCoordinate [
    a era:LinearPositioningSystemCoordinate ;
    era:kmPost kilometricPosts/km_km_3 ;
    era:offsetFromKilometricPost 245.0
  ] .

netPointRef/trc1_seg1_end a era:NetPointReference ;
  era:hasTopoCoordinate [
    a era:TopologicalCoordinate ;
    era:onLinearElement netElements/ne_147 ;
    era:offsetFromOrigin 400.0
  ] ;
  era:hasLrsCoordinate [
    a era:LinearPositioningSystemCoordinate ;
    era:kmPost kilometricPosts/km_km_3 ;
    era:offsetFromKilometricPost 645.0
  ] .

# ===== SEGMENT 2: ne_148 =====
netLinearRef/trc1_segment_2 a era:NetLinearReference ;
  era:hasSequence (netElements/ne_148) ; # Single-element list
  era:startsAt netPointRef/trc1_seg2_start ;
  era:endsAt netPointRef/trc1_seg2_end .

netPointRef/trc1_seg2_start a era:NetPointReference ;
  era:hasTopoCoordinate [
    a era:TopologicalCoordinate ;
    era:onLinearElement netElements/ne_148 ;
    era:offsetFromOrigin 0.0
  ] ;
  era:hasLrsCoordinate [
    a era:LinearPositioningSystemCoordinate ;
    era:kmPost kilometricPosts/km_km_3 ;
    era:offsetFromKilometricPost 645.0
  ] .

netPointRef/trc1_seg2_end a era:NetPointReference ;
  era:hasTopoCoordinate [
    a era:TopologicalCoordinate ;
    era:onLinearElement netElements/ne_148 ;
    era:offsetFromOrigin 250.0
  ] ;
  era:hasLrsCoordinate [
    a era:LinearPositioningSystemCoordinate ;
    era:kmPost kilometricPosts/km_km_3 ;
    era:offsetFromKilometricPost 895.0
  ] .

# ===== SEGMENT 3: ne_149 =====
netLinearRef/trc1_segment_3 a era:NetLinearReference ;
  era:hasSequence (netElements/ne_149) ; # Single-element list
  era:startsAt netPointRef/trc1_seg3_start ;
  era:endsAt netPointRef/trc1_seg3_end .

netPointRef/trc1_seg3_start a era:NetPointReference ;
  era:hasTopoCoordinate [
    a era:TopologicalCoordinate ;
    era:onLinearElement netElements/ne_149 ;
    era:offsetFromOrigin 0.0
  ] ;
  era:hasLrsCoordinate [
    a era:LinearPositioningSystemCoordinate ;
    era:kmPost kilometricPosts/km_km_3 ;
    era:offsetFromKilometricPost 895.0
  ] .

netPointRef/trc1_seg3_end a era:NetPointReference ;
  era:hasTopoCoordinate [
    a era:TopologicalCoordinate ;
    era:onLinearElement netElements/ne_149 ;
    era:offsetFromOrigin 150.0
  ] ;
  era:hasLrsCoordinate [
    a era:LinearPositioningSystemCoordinate ;
    era:kmPost kilometricPosts/km_km_4 ;
    era:offsetFromKilometricPost 45.0
  ] .

# Shared KilometricPost resources
kilometricPosts/km_km_3 a era:KilometricPost ;
  era:hasLRS linearPositioningSystems/km ;
  era:kilometer 3 .

kilometricPosts/km_km_4 a era:KilometricPost ;
  era:hasLRS linearPositioningSystems/km ;
  era:kilometer 4 .

linearPositioningSystems/km a era:LinearPositioningSystem .
```

**ERA Standard Pattern Alternative (Single NetLinearReference)**:
```turtle
@prefix era: <http://data.europa.eu/949/> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

# Track resource
tracks/trc1 a era:RunningTrack ;
  era:trackId "trc1" ;
  era:netReference netLinearRef/trc1 . # Single reference

# Single NetLinearReference with multi-element sequence
netLinearRef/trc1 a era:NetLinearReference ;
  era:hasSequence _:list1 ; # Multi-element list
  era:startsAt netPointRef/trc1_start ; # Overall start
  era:endsAt netPointRef/trc1_end . # Overall end

# RDF List structure (3 elements)
_:list1 rdf:first netElements/ne_147 ;
        rdf:rest _:list2 .

_:list2 rdf:first netElements/ne_148 ;
        rdf:rest _:list3 .

_:list3 rdf:first netElements/ne_149 ;
        rdf:rest rdf:nil .

# Overall start point (first segment start)
netPointRef/trc1_start a era:NetPointReference ;
  era:hasTopoCoordinate [
    a era:TopologicalCoordinate ;
    era:onLinearElement netElements/ne_147 ;
    era:offsetFromOrigin 0.0
  ] ;
  era:hasLrsCoordinate [
    a era:LinearPositioningSystemCoordinate ;
    era:kmPost kilometricPosts/km_km_3 ;
    era:offsetFromKilometricPost 245.0
  ] .

# Overall end point (last segment end)
netPointRef/trc1_end a era:NetPointReference ;
  era:hasTopoCoordinate [
    a era:TopologicalCoordinate ;
    era:onLinearElement netElements/ne_149 ;
    era:offsetFromOrigin 150.0
  ] ;
  era:hasLrsCoordinate [
    a era:LinearPositioningSystemCoordinate ;
    era:kmPost kilometricPosts/km_km_4 ;
    era:offsetFromKilometricPost 45.0
  ] .

# ⚠️ NOTE: Intermediate segment positions (ne_148 start/end) are LOST
# This pattern only captures the overall extent boundaries
```

**Key Differences**:
- Our pattern: **3 NetLinearReferences**, each with **6 positioning coordinates** (3 segments × 2 endpoints) = **complete per-segment positioning**
- Standard pattern: **1 NetLinearReference** with **2 positioning coordinates** (overall start/end) = **incomplete intermediate positioning**

### Example 2: Speed Section Spanning 14 Segments

In the dataset, speed section `vsp1` spans 14 netElements. 

**Our pattern**:
- Creates **14 NetLinearReferences** (`netLinearRef/vsp1_segment_1` through `netLinearRef/vsp1_segment_14`)
- Each has **complete start/end positioning** with both topology and LRS coordinates
- Total: **28 NetPointReferences** (14 segments × 2 endpoints)
- SPARQL CONSTRUCT: Simple iteration over associatedNetElement entries

**Standard pattern alternative**:
- Would create **1 NetLinearReference** with **14-element RDF List**
- Complex SPARQL: Build linked list structure with proper ordering
- Only **2 NetPointReferences** (overall start/end)
- **Lost information**: 12 intermediate segment boundaries and their LRS coordinates

## SPARQL Implementation Details

### Our Pattern Implementation

```sparql
CONSTRUCT {
  # Infrastructure element
  ?track era:netReference ?netLinearRef .
  
  # NetLinearReference (one per segment iteration)
  ?netLinearRef a era:NetLinearReference ;
                era:hasSequence ?sequenceList ;
                era:startsAt ?startPointRef ;
                era:endsAt ?endPointRef .
  
  # Single-element RDF List (trivial)
  ?sequenceList rdf:first ?linearElement ;
                rdf:rest rdf:nil .
  
  # Start point with dual coordinates
  ?startPointRef a era:NetPointReference ;
                 era:hasTopoCoordinate ?startTopoCoord ;
                 era:hasLrsCoordinate ?startLrsCoord .
  
  ?startTopoCoord a era:TopologicalCoordinate ;
                  era:onLinearElement ?linearElement ;
                  era:offsetFromOrigin ?posBeginDouble .
  
  ?startLrsCoord a era:LinearPositioningSystemCoordinate ;
                 era:kmPost ?startKmPost ;
                 era:offsetFromKilometricPost ?startKmOffset .
  
  # End point with dual coordinates
  ?endPointRef a era:NetPointReference ;
               era:hasTopoCoordinate ?endTopoCoord ;
               era:hasLrsCoordinate ?endLrsCoord .
  
  ?endTopoCoord a era:TopologicalCoordinate ;
                era:onLinearElement ?linearElement ;
                era:offsetFromOrigin ?posEndDouble .
  
  ?endLrsCoord a era:LinearPositioningSystemCoordinate ;
               era:kmPost ?endKmPost ;
               era:offsetFromKilometricPost ?endKmOffset .
  
  # KilometricPost resources (shared)
  ?startKmPost a era:KilometricPost ;
               era:hasLRS ?eraLPS ;
               era:kilometer ?startKmNumber .
  
  ?endKmPost a era:KilometricPost ;
             era:hasLRS ?eraLPS ;
             era:kilometer ?endKmNumber .
}
WHERE {
  # Get infrastructure element
  ?track xyz:id ?trackId .
  BIND (IRI(CONCAT(str(era:), "functionalInfrastructure/tracks/", ?trackId)) AS ?eraTrack)
  
  # Iterate over segments
  ?track fx:linearLocation/fx:associatedNetElement ?segment .
  ?segment xyz:netElementRef ?netElementRef ;
           xyz:posBegin ?posBegin ;
           xyz:posEnd ?posEnd ;
           xyz:sequence ?sequence ;
           fx:linearCoordinateBegin ?startLinCoord ;
           fx:linearCoordinateEnd ?endLinCoord .
  
  # Get LRS positions
  ?startLinCoord xyz:measure ?startMeasure ;
                 xyz:positioningSystemRef ?posSystemRef .
  ?endLinCoord xyz:measure ?endMeasure .
  
  # Mint URIs (one NetLinearReference per segment)
  BIND (IRI(CONCAT(str(era:), "topology/netLinearReferences/", 
                   ?trackId, "_segment_", STR(?sequence))) AS ?netLinearRef)
  BIND (IRI(CONCAT(str(era:), "topology/netElements/", 
                   ?netElementRef)) AS ?linearElement)
  
  # ... additional URI construction for points, coordinates, KilometricPosts ...
}
ORDER BY ?trackId ?sequence
```

**Key points**:
- Each `associatedNetElement` entry triggers **one CONSTRUCT iteration**
- Creates **one NetLinearReference** per iteration
- Single-element RDF List: `?sequenceList rdf:first ?linearElement ; rdf:rest rdf:nil`
- No complex list chaining logic required

### Standard Pattern Implementation (Hypothetical)

```sparql
# ⚠️ This is VERY complex and fragile in SPARQL CONSTRUCT
CONSTRUCT {
  ?track era:netReference ?netLinearRef .
  
  ?netLinearRef a era:NetLinearReference ;
                era:hasSequence ?headListNode ;
                era:startsAt ?overallStart ;
                era:endsAt ?overallEnd .
  
  # Build RDF List (requires nested SELECT and UNION for variable-length chains)
  ?listNode rdf:first ?linearElement ;
            rdf:rest ?nextListNode .
  
  # ... complex logic to determine head node, intermediate nodes, tail node ...
}
WHERE {
  # Aggregate all segments for each track
  {
    SELECT ?trackId (GROUP_CONCAT(?netElementRef; separator="|") AS ?segmentRefs)
                     (MIN(?sequence) AS ?firstSeq) (MAX(?sequence) AS ?lastSeq)
    WHERE {
      ?track xyz:id ?trackId ;
             fx:linearLocation/fx:associatedNetElement ?seg .
      ?seg xyz:netElementRef ?netElementRef ;
           xyz:sequence ?sequence .
    }
    GROUP BY ?trackId
  }
  
  # Build list structure (requires complex BIND logic with string parsing)
  # Determine list head, build chain with proper ordering, terminate with rdf:nil
  # ⚠️ SPARQL does not have native list construction - this is VERY difficult
}
```

**Challenges**:
- SPARQL has no native multi-element list construction
- Requires nested SELECTs, string manipulation, and conditional logic
- Ordering must be maintained through sequence numbers
- Variable-length chains (1-14 elements) → cannot use fixed CONSTRUCT pattern
- Error-prone and difficult to debug

## Querying Patterns

### Query 1: Find tracks on a specific LinearElement

**Our pattern**:
```sparql
SELECT ?track WHERE {
  ?track a era:Track ;
         era:netReference ?netLinearRef .
  ?netLinearRef era:hasSequence/(rdf:rest*/rdf:first) netElements/ne_147 .
}
```
Simple traversal: `rdf:rest*` is always empty (single-element list) or requires zero steps.

**Standard pattern**:
```sparql
SELECT ?track WHERE {
  ?track a era:Track ;
         era:netReference ?netLinearRef .
  ?netLinearRef era:hasSequence/(rdf:rest*/rdf:first) netElements/ne_147 .
}
```
Complex traversal: `rdf:rest*` must traverse 0-13 intermediate nodes depending on list length.

### Query 2: Get total extent of a track

**Our pattern**:
```sparql
SELECT ?track ?totalStartKm ?totalEndKm WHERE {
  ?track a era:Track ;
         era:netReference ?netLinearRef .
  ?netLinearRef era:startsAt/era:hasLrsCoordinate ?startLrs ;
                era:endsAt/era:hasLrsCoordinate ?endLrs .
  ?startLrs era:kmPost/era:kilometer ?startKm .
  ?endLrs era:kmPost/era:kilometer ?endKm .
  
  # Aggregate across all segments
  {
    SELECT ?track (MIN(?startKm) AS ?totalStartKm) (MAX(?endKm) AS ?totalEndKm)
    WHERE { ... }
    GROUP BY ?track
  }
}
```
Requires aggregation to reconstruct total extent from segments.

**Standard pattern**:
```sparql
SELECT ?track ?totalStartKm ?totalEndKm WHERE {
  ?track a era:Track ;
         era:netReference ?netLinearRef .
  ?netLinearRef era:startsAt/era:hasLrsCoordinate/era:kmPost/era:kilometer ?totalStartKm ;
                era:endsAt/era:hasLrsCoordinate/era:kmPost/era:kilometer ?totalEndKm .
}
```
Direct access to total extent (simpler query).

### Query 3: Find segment boundaries within a track

**Our pattern**:
```sparql
SELECT ?track ?segmentStart ?segmentEnd WHERE {
  ?track a era:Track ;
         era:netReference ?netLinearRef .
  ?netLinearRef era:startsAt/era:hasTopoCoordinate ?startCoord ;
                era:endsAt/era:hasTopoCoordinate ?endCoord .
  ?startCoord era:onLinearElement ?element ;
              era:offsetFromOrigin ?segmentStart .
  ?endCoord era:offsetFromOrigin ?segmentEnd .
}
```
All segment boundaries available with their precise positions.

**Standard pattern**:
```sparql
# ⚠️ Cannot retrieve intermediate segment boundaries
# Only overall start and end are available
SELECT ?track ?overallStart ?overallEnd WHERE {
  ?track a era:Track ;
         era:netReference ?netLinearRef .
  ?netLinearRef era:startsAt/era:hasTopoCoordinate/era:offsetFromOrigin ?overallStart ;
                era:endsAt/era:hasTopoCoordinate/era:offsetFromOrigin ?overallEnd .
}
```

## Conclusion

We chose the **multiple NetLinearReferences** pattern because:

1. ✅ **SPARQL CONSTRUCT feasibility**: Creating multi-element RDF Lists in SPARQL is extremely complex; single-element lists are trivial
2. ✅ **Complete positioning**: Every segment boundary has dual coordinates (topology + LRS), not just overall extent
3. ✅ **Natural mapping**: Directly corresponds to railML `associatedNetElement` structure
4. ✅ **ERA compliance**: Fully compliant with ERA ontology cardinality and structure requirements
5. ✅ **Query simplicity**: Individual segments are easily accessible without complex list traversal

This pattern is a **pragmatic design choice** that balances:
- Implementation feasibility (SPARQL CONSTRUCT generation)
- Data completeness (per-segment positioning)
- Ontology compliance (valid ERA structure)
- Query usability (reasonable traversal patterns)

While it creates more NetLinearReference resources, it provides complete positioning information for every segment and avoids the complexity of multi-element RDF List construction in SPARQL, making it the optimal choice for this conversion project.

## Implementation Files

The pattern is implemented in:
- [`02-construct/03-functional-infrastructure/01-tracks.sparql`](../02-construct/03-functional-infrastructure/01-tracks.sparql) - Track mapping (54 NetLinearReferences for 36 tracks)
- [`02-construct/03-functional-infrastructure/03-platform-edges.sparql`](../02-construct/03-functional-infrastructure/03-platform-edges.sparql) - Platform edge mapping
- [`02-construct/03-functional-infrastructure/07-speed-sections.sparql`](../02-construct/03-functional-infrastructure/07-speed-sections.sparql) - Speed section mapping
- [`02-construct/03-functional-infrastructure/08-electrification-sections.sparql`](../02-construct/03-functional-infrastructure/08-electrification-sections.sparql) - Electrification section mapping (via track references)
- [`02-construct/03-functional-infrastructure/09-bridges.sparql`](../02-construct/03-functional-infrastructure/09-bridges.sparql) - Bridge mapping
- [`02-construct/03-functional-infrastructure/10-tunnels.sparql`](../02-construct/03-functional-infrastructure/10-tunnels.sparql) - Tunnel mapping
