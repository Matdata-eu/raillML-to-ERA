---
name: era-functional-resources
description: Implement ERA functional resources — classes such as ContactLineSystem, ETCS, TrainDetectionSystem that are NOT subclasses of InfrastructureElement and therefore carry no era:netReference. Instead they are referenced FROM tracks via properties like era:contactLineSystem, era:etcs, era:trainDetectionSystem. Use when adding a new functional resource type or debugging why a resource unexpectedly lacks netReference or geometry.
---

# ERA Functional Resources

Some ERA classes represent **functional characteristics** of the railway rather than
physical infrastructure placed at a specific position. These are called **functional
resources** and follow a different linking pattern from `era:InfrastructureElement`.

## What Makes a Class a Functional Resource?

Run the following check first:

```sparql
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX era: <http://data.europa.eu/949/>
SELECT ?superClass WHERE {
  era:YourClass rdfs:subClassOf* ?superClass .
}
```

| Result                                             | Pattern                                                             |
| -------------------------------------------------- | ------------------------------------------------------------------- |
| Chain includes `era:InfrastructureElement`         | ✅ Use `era:netReference` — the standard positioned element pattern |
| Chain does NOT include `era:InfrastructureElement` | ❌ Functional resource — do NOT add `era:netReference`              |

## Functional Resource Classes in ERA ontology

All classes below are confirmed non-`InfrastructureElement` subclasses with SHACL-defined links from `era:RunningTrack` or `era:Siding`.

| ERA Class                               | Linking property                             | Domain class       |
| --------------------------------------- | -------------------------------------------- | ------------------ |
| `era:ContactLineSystem`                 | `era:contactLineSystem`                      | `era:RunningTrack` |
| `era:ETCS`                              | `era:etcs`                                   | `era:RunningTrack` |
| `era:LinesideDistanceIndication`        | `era:linesideDistanceIndication`             | `era:RunningTrack` |
| `era:PhaseInfo`                         | `era:trackPhaseInfo`                         | `era:RunningTrack` |
| `era:RaisedPantographsDistanceAndSpeed` | `era:trackRaisedPantographsDistanceAndSpeed` | `era:RunningTrack` |
| `era:SystemSeparationInfo`              | `era:trackSystemSeparationInfo`              | `era:RunningTrack` |
| `era:TrainDetectionSystem`              | `era:trainDetectionSystem`                   | `era:RunningTrack` |
| `era:Document`                          | `era:*Document` (many)                       | `era:RunningTrack` |
| `era:MinimumVerticalRadius`             | `era:minimumVerticalRadius`                  | `era:Siding`       |

## How to Find the Linking Property (MCP Discovery)

1. **Query properties whose range is the functional resource class**:

```sparql
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl:  <http://www.w3.org/2002/07/owl#>
PREFIX era:  <http://data.europa.eu/949/>
SELECT ?property ?domain WHERE {
  ?property rdfs:range era:YourClass .
  OPTIONAL { ?property rdfs:domain ?domain }
  FILTER NOT EXISTS { ?property owl:deprecated "true"^^xsd:boolean }
}
```

2. **Inspect SHACL shapes** to confirm the domain class (use `era-shacl-analysis` skill):

```sparql
PREFIX sh:   <http://www.w3.org/ns/shacl#>
PREFIX era:  <http://data.europa.eu/949/>
SELECT ?targetClass ?property WHERE {
  ?shape sh:targetClass ?targetClass ;
         sh:property/sh:path ?property .
  FILTER (?property = era:yourLinkingProperty)
}
```

The SHACL target class tells you which ERA class carries the link (typically `era:RunningTrack`
or `era:Track`).

## Linking through topology relations

In the case that the source system (such as railML®) also has topological positions for the functional resource intead of a direct link with the era:Track, use the SKILL topology-relations to create the link between both.

## A single Track instance but multiple functional resources?

In the case that 1 track shares multiple functional resources, it is unclear on how to proceed. Multiple options exist:

1. split the track into multiple tracks with non overlapping topology locations so that each has only 1 set of functional resources (this violates the principle of having only 1 entity per real-world object).

2. aggregate the functional resources into a single resource (e.g., one ContactLineSystem instance that combines all contact line systems on the track, with aggregated properties giving the most constraint situation, i.e. the 'minimum maximum current')

## Key Rules

1. **Never add `era:netReference` to a functional resource** — it is not a subclass of
`era:InfrastructureElement` and the property is undefined on it. SHACL will flag any
stray `netReference` on these classes.

2. **The functional resource itself has no geometry** — geometry comes from the tracks
that reference it (via `gsp:hasGeometry` on the track's `NetLinearReference`).

3. **1 track to many functional resources of the same class is a problem** — 1 track can span multiple ContactLineSystem instances. Two solutions are possible: (1) split the track into multiple tracks with non-overlapping topology locations, or (2) aggregate the functional resources into a single resource with properties that combine the constraints of all the individual resources (e.g., a ContactLineSystem with `era:maxTrainCurrent` equal to the lowest maxTrainCurrent of all the individual ContactLineSystems on that track).

4. **Many tracks to the same functional resource is not a problem** — if multiple tracks share the same ContactLineSystem, they can all link to the same instance.

5. **Use OPTIONAL for all source-specific properties** — functional attributes like
regenerative braking, current limitation, ETCS version may not be present on every
instance; wrapping in OPTIONAL ensures the resource is still created even when some
properties are absent.

6. **Check for aggregation needs** — some properties (e.g., `era:maxTrainCurrent`) may
have multiple source values per instance. Use a nested `SELECT … MAX(…) GROUP BY …`
sub-query to collapse them before the CONSTRUCT.
