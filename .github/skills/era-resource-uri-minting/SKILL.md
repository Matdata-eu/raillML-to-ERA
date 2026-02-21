---
name: era-resource-uri-minting
description: Mint correct URIs for ERA resource instances. Use when writing any BIND(IRI(...)) expression, choosing an ontology module path, or deciding whether to use the ERA namespace or a data provider namespace.
---

# ERA Resource URI Minting

## URI structure

`http://data.europa.eu/949/[ontology-module]/{class-name}/{data-id}`

- `[ontology-module]` — optional; official values: `topology`, `trackside`, `onboard`, `body`
- `{class-name}` — lowerCamelCase singular (e.g., `operationalPoint`, `sectionOfLine`)
- `{data-id}` — alphanumeric; only `-` and `_` as separators; **no** spaces, `/`, `.`, `(`, `)`, `#`, or `%20`

Valid: `http://data.europa.eu/949/topology/linearElement/26489401-SVN`  
Invalid: `http://data.europa.eu/949/operationalPoints/ATAh%20H1K` (encoded space)

---

## Common ERA URI patterns

The official `[ontology-module]` values are `topology`, `trackside`, `onboard`, `body`. Some
implementations use alternative module names (e.g., `infrastructureElement` instead of
`trackside`) — this is acceptable provided URIs are consistent within the dataset.

### Topology module
| Class | Pattern |
|-------|---------|
| LinearElement | `topology/netElements/{id}` |
| NetRelation | `topology/netRelations/{id}` |
| NetLinearReference | `topology/netLinearReferences/{elementId}_{order}` |
| NetPointReference | `topology/netPointReferences/{elementId}_{order}_{start\|end}` |
| TopologicalCoordinate | `topology/topologicalCoordinates/{elementId}_{order}_{start\|end}` |
| rdf:List node | `topology/netLinearReferences/{elementId}_{order}_{nodeOrder}` |

### Infrastructure Element module
| Class | Pattern |
|-------|---------|
| Track | `infrastructureElement/tracks/{id}` |
| OperationalPoint | `infrastructureElement/operationalPoints/{id}` |
| SectionOfLine | `infrastructureElement/sectionsOfLine/{id}` |
| Signal | `infrastructureElement/signals/{id}` |
| Switch | `infrastructureElement/switches/{id}` |
| LevelCrossing | `infrastructureElement/levelCrossings/{id}` |
| ContactLineSystem | `infrastructureElement/contactLineSystems/{id}` |
| ETCS | `infrastructureElement/etcs/{id}` |
| PlatformEdge | `infrastructureElement/platformEdges/{id}` |

### Geometry
- Net element geometry: `http://data.europa.eu/949/geometry/netElement_{id}`
- Enriched geometry: `http://data.europa.eu/949/geometry/{geomType}/{sha256hash8}` (deterministic; SHA-256 of WKT, first 8 chars)

---

## SPARQL BIND pattern

```sparql
BIND(IRI(CONCAT("http://data.europa.eu/949/infrastructureElement/tracks/", ?trackId)) AS ?eraTrack)
```

For composite keys, use `_` as separator:
```sparql
BIND(IRI(CONCAT("http://data.europa.eu/949/topology/netLinearReferences/", str(?trackId), "_", str(?order))) AS ?netLinearRef)
```

---

## Data provider namespace

ERA allows data providers to mint URIs in **their own namespace** instead of `http://data.europa.eu/949/`. The provider choices their own template.

**Requirement: own-namespace URIs MUST be dereferenceable** — an HTTP GET on the URI must return a valid response. This is a Linked Data requirement; non-resolvable URIs are not acceptable.

Dereferenceable URIs SHOULD support **content negotiation**:

| `Accept` header | Expected response |
|-----------------|-------------------|
| `text/html` | Human-readable HTML page describing the resource |
| `text/turtle` or `application/rdf+xml` or `application/ld+json` | RDF description of the resource |

```http
GET https://data.mycompany.eu/_infrastructure_tracks_TRK-001
Accept: text/turtle

→ 200 OK  (or 303 See Other redirect to a document URI)
Content-Type: text/turtle

<https://data.mycompany.eu/_infrastructure_tracks_TRK-001>
    a era:Track ;
    era:trackId "TRK-001" .
```

Use own-namespace URIs when:
- Data is not to be merged into the official ERA Knowledge Graph
- The data provider manages their own URI lifecycle and can guarantee HTTP resolution

Own-namespace IDs follow the same `{data-id}` character restrictions (no spaces, `.`, `(`, `)`, `#`).

## Opinion

The personal opinion of the author is that:
- the data provider should mint their own URIs in their own namespace
- the URI template uses a domain that produces a limited amount of PREFIX declarations. That would mean no /ontology-module/class-name/ path segments, but instead a flatter structure like `http://data.mycompany.eu/_ontology-module_class-name_id`.