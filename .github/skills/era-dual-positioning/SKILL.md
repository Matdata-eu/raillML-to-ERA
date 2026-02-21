---
name: era-dual-positioning
description: Implement the ERA dual positioning model — TopologicalCoordinate (micro-topology offset) plus LinearPositioningSystemCoordinate (KilometricPost + offset) — for infrastructure elements. Use when writing or debugging any SPARQL CONSTRUCT query that positions an element on the network, or when understanding why an element is missing LRS or topology coordinates.
---

# ERA Dual Positioning Model

The model supports **two complementary positioning references**:

| Reference type | Purpose | Based on |
|----------------|---------|---------|
| `era:TopologicalCoordinate` | Micro-topology position | `era:LinearElement` + `era:offsetFromOrigin` |
| `era:LinearPositioningSystemCoordinate` | Linear referencing position | `era:KilometricPost` + `era:offsetFromKilometricPost` |

Both hang off an `era:NetPointReference` (for point elements) or are attached to the
`era:startsAt` / `era:endsAt` `NetPointReference` nodes of a `era:NetLinearReference`
(for linear elements).

## Complete Object Graph

```
InfrastructureElement
  └─ era:netReference ──▶ NetPointReference         (or startsAt/endsAt of NetLinearReference)
        ├─ era:hasTopoCoordinate ──▶ TopologicalCoordinate
        │       ├─ era:onLinearElement ──▶ LinearElement   (micro-level)
        │       └─ era:offsetFromOrigin ──▶ xsd:double     (metres from element origin)
        └─ era:hasLrsCoordinate ──▶ LinearPositioningSystemCoordinate
                ├─ era:kmPost ──▶ KilometricPost            (shared)
                │       ├─ era:hasLRS ──▶ LinearPositioningSystem
                │       └─ era:kilometer ──▶ xsd:double     (rounded km number)
                └─ era:offsetFromKilometricPost ──▶ xsd:double  (metres within that km)
```

## SPARQL CONSTRUCT Template (point element)

```sparql
PREFIX era: <http://data.europa.eu/949/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX xyz: <http://sparql.xyz/facade-x/data/>
PREFIX fx:  <http://sparql.xyz/facade-x/ns/>

CONSTRUCT {
  # --- topological coordinate ---
  ?eraElement era:netReference ?netPointRef .

  ?netPointRef a era:NetPointReference ;
               era:appliesToDirection ?orientation ;
               era:hasTopoCoordinate ?topoCoord .

  ?topoCoord a era:TopologicalCoordinate ;
             era:onLinearElement ?linearElement ;
             era:offsetFromOrigin ?posDouble .

  # --- LRS coordinate (OPTIONAL block; only emitted when linearCoordinate present) ---
  ?netPointRef era:hasLrsCoordinate ?lrsCoord .

  ?lrsCoord a era:LinearPositioningSystemCoordinate ;
            era:kmPost ?kmPost ;
            era:offsetFromKilometricPost ?kmOffset .

  ?kmPost a era:KilometricPost ;
          era:hasLRS ?eraLPS ;
          era:kilometer ?kmNumber .
}
WHERE {
  ...
}
```

## SPARQL CONSTRUCT Template (linear element — startsAt / endsAt)

For RunningTrack, Siding, PlatformEdge etc., each `NetLinearReference` has a `startsAt` and `endsAt` NetPointReference. Apply the dual coordinate pattern to both:

```sparql
CONSTRUCT {
  ?netLinRef a era:NetLinearReference ;
             era:hasSequence ?sequenceHead ;
             era:startsAt ?startRef ;
             era:endsAt   ?endRef .

  # Start NetPointReference + coordinates
  ?startRef a era:NetPointReference ;
            era:hasTopoCoordinate ?startTopoCoord ;
            era:hasLrsCoordinate  ?startLrsCoord .       # OPTIONAL

  ?startTopoCoord a era:TopologicalCoordinate ;
                  era:onLinearElement ?firstLinearElement ;
                  era:offsetFromOrigin ?startOffset .

  # (lrsCoord triples for start …)

  # End NetPointReference + coordinates
  ?endRef a era:NetPointReference ;
          era:hasTopoCoordinate ?endTopoCoord ;
          era:hasLrsCoordinate  ?endLrsCoord .           # OPTIONAL

  ?endTopoCoord a era:TopologicalCoordinate ;
                era:onLinearElement ?lastLinearElement ;
                era:offsetFromOrigin ?endOffset .

  # (lrsCoord triples for end …)
  ...
}
```

## KilometricPost Sharing

KilometricPost URIs could be minted from `{posSystemRef}_km_{roundedKm}` — the **same URI** is emitted by every element at that kilometer on the same system. SPARQL CONSTRUCT will naturally merge duplicate triples, so no deduplication is needed.
