---
name: era-topology-relations
description: Determine spatial relationships between ERA infrastructure elements using network topology overlap matching. Use when inferring any relationship based on network position (containment, proximity, etc.) in post-processing or CONSTRUCT queries.
---

# Topology-Based Relationship Mapping

Determine spatial relationships between ERA infrastructure elements by analyzing network reference overlap using micro-level topology.

## Core Principle

Elements have spatial relationships when their **network references overlap** on the micro-level topology (LinearElement graph):

> **Point elements** (KilometerPost, stoppingPoint OperationalPoints, Signals, Switches, …) are positioned via a `NetPointReference` giving a single (netElement, offset) pair. They relate to a linear element when that offset falls within the linear element's effective window on the same net element.

> **Linear elements** (RunningTrack, Siding, …) are positioned via a `NetLinearReference` that spans a **sequence of net elements** with a declared start and end offset. They overlap when their effective windows on a shared net element intersect. Attention must be paid to intermediate net elements that are fully included (0 → length) vs. boundary elements that use the declared offsets.

> **Area elements** (OperationalPoints, SectionOfLine, …) use a `NetAreaReference` that aggregates multiple `NetLinearReference` instances; consider them as being a list of linear elements for matching purposes.

## Topology Structure

### NetPointReference (Point Elements)

```sparql
?pointElement era:netReference ?netPointRef .
?netPointRef a era:NetPointReference ;
             era:hasTopoCoordinate ?topoCoord .
?topoCoord era:onLinearElement ?linearElement ;
           era:offsetFromOrigin ?offset .
```

### NetLinearReference (Linear Elements)

A `NetLinearReference` covers **one or more** net elements via an ordered rdf:list (`era:hasSequence`). The declared start/end coordinates only bound the **first and last** elements; intermediate elements are fully included.

```sparql
?linearElem era:netReference ?netLinRef .
?netLinRef a era:NetLinearReference ;
           era:hasSequence ?sequenceList ;
           era:startsAt/era:hasTopoCoordinate ?startCoord ;
           era:endsAt/era:hasTopoCoordinate ?endCoord .

# Traverse the sequence to reach every covered net element
?sequenceList rdf:rest*/rdf:first ?netElement .
?netElement era:lengthOfNetLinearElement ?netElementLength .

# Declared boundary positions
?startCoord era:onLinearElement ?firstNetElement ;
            era:offsetFromOrigin ?startOffset .
?endCoord   era:onLinearElement ?lastNetElement ;
            era:offsetFromOrigin ?endOffset .

# Effective window on this specific net element:
#   - first element: starts at declared startOffset
#   - last element:  ends at declared endOffset
#   - intermediate:  spans the full element (0 → length)
BIND (IF(?netElement = ?firstNetElement, ?startOffset, 0) AS ?effectiveStart)
BIND (IF(?netElement = ?lastNetElement,  ?endOffset, ?netElementLength) AS ?effectiveEnd)
```

### NetAreaReference (Aggregate Elements)

Some elements use a `NetAreaReference` whose `era:includes` list contains one or more `NetLinearReference` instances. Unwrap it first:

```sparql
  ?masterPart era:netReference ?masterNetAreaRef .
  ?masterNetAreaRef a era:NetAreaReference ;
                    era:includes ?includeList .
  ?includeList rdf:rest*/rdf:first ?masterNetLinRef .
```

In case of an element that can have both a LinearNetReferenc or an AreaReference, use `UNION` to handle both cases at once.

```sparql
{
  ?masterPart era:netReference ?masterNetLinRef .
  ?masterNetLinRef a era:NetLinearReference .
}
UNION
{
  ?masterPart era:netReference ?masterNetAreaRef .
  ?masterNetAreaRef a era:NetAreaReference ;
                    era:includes ?includeList .
  ?includeList rdf:rest*/rdf:first ?masterNetLinRef .
}
```

After unwrapping, apply the `NetLinearReference` pattern above.

## Matching Patterns

### Pattern 1: Point → Linear (point-in-extent)

**Rule**: A point element relates to a linear element when the point's offset falls within the linear element's effective window on the same net element.

Used by: `infer-part-relations-point.sparql` (KilometerPost → RunningTrack/Siding)  
and: `infer-part-relations-op-stopping-point.sparql` (stoppingPoint OP → RunningTrack/Siding)

```sparql
# --- Master: linear element (RunningTrack / Siding) ---
VALUES ?masterType { era:RunningTrack era:Siding }
?master a ?masterType ;
        era:netReference ?masterNetLinRef .
?masterNetLinRef a era:NetLinearReference ;
                 era:hasSequence ?seq ;
                 era:startsAt/era:hasTopoCoordinate ?masterStartCoord ;
                 era:endsAt/era:hasTopoCoordinate   ?masterEndCoord .
?seq rdf:rest*/rdf:first ?netElement .
?netElement era:lengthOfNetLinearElement ?netElementLength .
?masterStartCoord era:onLinearElement ?firstNetElement ; era:offsetFromOrigin ?masterStartOffset .
?masterEndCoord   era:onLinearElement ?lastNetElement  ; era:offsetFromOrigin ?masterEndOffset .
BIND (IF(?netElement = ?firstNetElement, ?masterStartOffset, 0)               AS ?masterEffStart)
BIND (IF(?netElement = ?lastNetElement,  ?masterEndOffset,   ?netElementLength) AS ?masterEffEnd)

# --- Child: point element ---
?child era:netReference ?childRef .
?childRef a era:NetPointReference ;
          era:hasTopoCoordinate ?childCoord .
?childCoord era:onLinearElement ?netElement ;   # same net element as master
            era:offsetFromOrigin ?childOffset .

FILTER (?childOffset >= ?masterEffStart && ?childOffset <= ?masterEffEnd)
```

**Applies to**: KilometerPost → RunningTrack/Siding; stoppingPoint OP → RunningTrack/Siding

### Pattern 2: Linear → Linear (extent overlap)

**Rule**: A linear child element relates to a linear master element when their effective windows **overlap** on a shared net element (child start or end falls within master window).

Used by: `infer-part-relations-linear.sparql` (RunningTrack/Siding → OperationalPoint/SectionOfLine)

```sparql
# --- Master: aggregate element (OperationalPoint / SectionOfLine) ---
VALUES ?masterType { era:OperationalPoint era:SectionOfLine }
# Unwrap NetAreaReference if necessary (see NetAreaReference section above)
?master a ?masterType ;
        era:netReference ?masterNetLinRef .  # after unwrapping
?masterNetLinRef a era:NetLinearReference ;
                 era:hasSequence ?masterSeq ;
                 era:startsAt/era:hasTopoCoordinate ?masterStartCoord ;
                 era:endsAt/era:hasTopoCoordinate   ?masterEndCoord .
?masterSeq rdf:rest*/rdf:first ?netElement .
?netElement era:lengthOfNetLinearElement ?netElementLength .
?masterStartCoord era:onLinearElement ?firstMasterElement ; era:offsetFromOrigin ?masterStartOffset .
?masterEndCoord   era:onLinearElement ?lastMasterElement  ; era:offsetFromOrigin ?masterEndOffset .
BIND (IF(?netElement = ?firstMasterElement, ?masterStartOffset, 0)               AS ?masterEffStart)
BIND (IF(?netElement = ?lastMasterElement,  ?masterEndOffset,   ?netElementLength) AS ?masterEffEnd)

# --- Child: linear element (RunningTrack / Siding, but not the master's own type) ---
VALUES ?childType { era:RunningTrack era:Siding }
FILTER (?childType != ?masterType)
?child a ?childType ;
       era:netReference ?childNetLinRef .
?childNetLinRef a era:NetLinearReference ;
                era:hasSequence ?childSeq ;
                era:startsAt/era:hasTopoCoordinate ?childStartCoord ;
                era:endsAt/era:hasTopoCoordinate   ?childEndCoord .
?childSeq rdf:rest*/rdf:first ?netElement .   # must share the same net element
?childStartCoord era:onLinearElement ?firstChildElement ; era:offsetFromOrigin ?childStartOffset .
?childEndCoord   era:onLinearElement ?lastChildElement  ; era:offsetFromOrigin ?childEndOffset .
BIND (IF(?netElement = ?firstChildElement, ?childStartOffset, 0)               AS ?childEffStart)
BIND (IF(?netElement = ?lastChildElement,  ?childEndOffset,   ?netElementLength) AS ?childEffEnd)

# Overlap: child start or end falls within master window
FILTER (
  (?childEffStart >= ?masterEffStart && ?childEffStart <= ?masterEffEnd)
  ||
  (?childEffEnd   >= ?masterEffStart && ?childEffEnd   <= ?masterEffEnd)
)
```

## era:hasPart and inverse era:isPartOf

The property `era:hasPart` is used to link a master element to its child elements; `era:isPartOf` is the inverse. After identifying the relationships with the above patterns, insert the triples:

```sparql
PREFIX era: <http://data.europa.eu/949/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

INSERT {
  ?child era:isPartOf ?master .
  ?master era:hasPart ?child .
}
WHERE {
  # ... choose Pattern 1 or Pattern 2 from above ...
}
```

## Common Pitfalls

1. **Intermediate net elements default to full extent** — always apply the `BIND(IF(...))` pattern; do not use the declared start/end offsets for elements that are not first/last.
2. **NetAreaReference unwrapping** — OperationalPoints and SectionOfLines may use `NetAreaReference`; always handle both `NetLinearReference` and `NetAreaReference` with a `UNION`.
3. **Self-containment** — when master and child can be the same type, add `FILTER (?childType != ?masterType)`.
4. **Overlap vs. containment** — the linear-linear pattern checks for *any* overlap (start or end inside master); full containment would additionally require both start and end inside.
5. **stoppingPoint OPs are point-referenced** — they cannot be matched by the linear-linear pattern; use a dedicated query (Pattern 1 with the OP as the point master).

