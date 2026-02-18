# ERA Ontology Mapping Plan

- [ERA Ontology Mapping Plan](#era-ontology-mapping-plan)
  - [Overview](#overview)
    - [Source Graph](#source-graph)
    - [Target Graph ontology](#target-graph-ontology)
    - [Key Technical Patterns](#key-technical-patterns)
    - [Organization Model (new n-ary pattern)](#organization-model-new-n-ary-pattern)
  - [Folder Structure](#folder-structure)
  - [Phase 1 — Common / Organization (`01-common/`)](#phase-1--common--organization-01-common)
    - [1.1 Organizations → `era:Body` + `era:OrganisationRole` (`01-infrastructure-managers.sparql`)](#11-organizations--erabody--eraorganisationrole-01-infrastructure-managerssparql)
    - [1.2 Linear Positioning Systems → `era:LinearPositioningSystem` (`02-linear-positioning-systems.sparql`)](#12-linear-positioning-systems--eralinearpositioningsystem-02-linear-positioning-systemssparql)
  - [Phase 2 — Topology (`02-topology/`) — **Micro Level Only**](#phase-2--topology-02-topology--micro-level-only)
    - [2.1 Net Elements → `era:LinearElement` (`01-net-elements.sparql`)](#21-net-elements--eralinearelement-01-net-elementssparql)
    - [2.2 Net Relations → `era:NetRelation` (`02-net-relations.sparql`)](#22-net-relations--eranetrelation-02-net-relationssparql)
  - [Phase 3 — Functional Infrastructure (`03-functional-infrastructure/`)](#phase-3--functional-infrastructure-03-functional-infrastructure)
    - [3.1 Tracks → `era:Track` (`01-tracks.sparql`)](#31-tracks--eratrack-01-trackssparql)
    - [3.2 Operational Points → `era:OperationalPoint` (3 files)](#32-operational-points--eraoperationalpoint-3-files)
      - [3.2.1 Base Properties (`02-operational-points.sparql`)](#321-base-properties-02-operational-pointssparql)
      - [3.2.2 Operational Point Ownership (`02-operational-point-owns.sparql`)](#322-operational-point-ownership-02-operational-point-ownssparql)
      - [3.2.3 NetLinearReference (`02-operational-points-netlinearreference.sparql`)](#323-netlinearreference-02-operational-points-netlinearreferencesparql)
      - [3.2.4 NetPointReference (`02-operational-points-netpointreference.sparql`)](#324-netpointreference-02-operational-points-netpointreferencesparql)
    - [3.3 Platform Edges → `era:PlatformEdge` (`03-platform-edges.sparql`)](#33-platform-edges--eraplatformedge-03-platform-edgessparql)
    - [3.4 Switches → `era:Switch` (`04-switches.sparql`)](#34-switches--eraswitch-04-switchessparql)
    - [3.5 Signals → `era:Signal` (`05-signals.sparql`)](#35-signals--erasignal-05-signalssparql)
    - [3.6 Train Detection Elements → `era:TrainDetectionSystem` (`06-train-detection-elements.sparql`)](#36-train-detection-elements--eratraindetectionsystem-06-train-detection-elementssparql)
    - [3.7 Speed Sections → `era:SpeedSection` (`07-speed-sections.sparql`)](#37-speed-sections--eraspeedsection-07-speed-sectionssparql)
    - [3.8 Electrification Sections → `era:ContactLineSystem` (`08-electrification-sections.sparql`)](#38-electrification-sections--eracontactlinesystem-08-electrification-sectionssparql)
    - [3.9 Bridges → `era:Bridge` (`09-bridges.sparql`)](#39-bridges--erabridge-09-bridgessparql)
    - [3.10 Tunnels → `era:Tunnel` (`10-tunnels.sparql`)](#310-tunnels--eratunnel-10-tunnelssparql)
    - [3.11 Level Crossings → `era:LevelCrossing` (`11-level-crossings.sparql`)](#311-level-crossings--eralevelcrossing-11-level-crossingssparql)
    - [3.12 ETCS → `era:ETCS` (`12-etcs.sparql`)](#312-etcs--eraetcs-12-etcssparql)
    - [3.13 Sections of Line → `era:SectionOfLine` (`11-sections-of-line-*.sparql`)](#313-sections-of-line--erasectionofline-11-sections-of-line-sparql)
  - [Linear Positioning System Architecture (Dual Positioning Model)](#linear-positioning-system-architecture-dual-positioning-model)
    - [Linear Positioning System Resources (`02-linear-positioning-systems.sparql`)](#linear-positioning-system-resources-02-linear-positioning-systemssparql)
    - [KilometricPost Inference Pattern](#kilometricpost-inference-pattern)
    - [LinearPositioningSystemCoordinate Pattern](#linearpositioningsystemcoordinate-pattern)
    - [Dual Positioning Model — Complete Pattern](#dual-positioning-model--complete-pattern)
  - [Implementation Order](#implementation-order)
  - [Cross-Cutting Concerns](#cross-cutting-concerns)


## Overview

Transform the **one-eyed graph** (railML 3.2 XML converted to RDF via SPARQL Anything facade-x) into **ERA ontology-compliant RDF** using SPARQL CONSTRUCT queries.

⚠️ **Workshop Simplification**: For demo purposes, all infrastructure elements are assigned to infrastructure manager `http://data.europa.eu/949/organisations/0076_IM` (Belgian infrastructure manager BN). In production scenarios, infrastructure manager assignments would be determined by organizational unit responsibility or geographic location.

🔧 **Post-Processing Pipeline**: After all SPARQL CONSTRUCT queries execute, the `enrich-geometries.py` script enriches NetPointReference resources (signals, etc.) with spatial geometries using Shapely linear referencing. This adds `gsp:hasGeometry` triples by interpolating POINT positions along LinearElement LINESTRING geometries at the `offsetFromOrigin` positions. The script runs automatically when executing `run-era-construct.py`.

**MCP Discovery Methodology**: Two MCP servers support ontology-driven mapping development:
- "explorer-one-eyed-graph": discovers source instances and schema from railML RDF (one-eyed graph)
- "explorer-era-ontology": discovers classes, properties, SKOS concepts, and SHACL shapes from ERA ontology
  - **Important**: Filter out deprecated elements using `FILTER NOT EXISTS { ?property owl:deprecated "true"^^xsd:boolean }`

**Discovery Process for Each Entity Type**:
1. **Query ObjectProperties** with specific domain (e.g., `era:ContactLineSystem`)
2. **Query DatatypeProperties** with specific domain
3. **Identify required properties** via SHACL `sh:minCount` constraints
4. **Retrieve SKOS concepts** for properties with `skos:Concept` range
5. **Analyze source data** in railML to find available values for properties
6. **Map properties** where source data exists, document others as "available but unmapped"

This approach ensures mappings are ontology-compliant and makes full use of available source data.

### Source Graph
- **Endpoint**: `http://localhost:8082/jena-fuseki/advanced-example-one-eyed/sparql`
- **Namespaces**:
  - railML types: `https://www.railml.org/schemas/3.2#` (e.g., `railml:netElement`, `railml:switchIS`)
  - XML attributes: `http://sparql.xyz/facade-x/data/` (e.g., `xyz:id`, `xyz:ref`, `xyz:pos`)
  - XML child elements: `http://sparql.xyz/facade-x/ns/` (e.g., `fx:spotLocation`, `fx:name`, `fx:elementA`)

### Target Graph ontology
- **Namespace**: `http://data.europa.eu/949/`
- **Ontology endpoint**: `http://localhost:8082/jena-fuseki/era-ontology/sparql`
- **GeoSPARQL**: `http://www.opengis.net/ont/geosparql#` (geometry/spatial features)
- **Countries**: `http://data.europa.eu/949/countries/` (country code namespace)

### Key Technical Patterns
- **URI Minting**: `http://data.europa.eu/949/{category}/{railml_id}` (e.g., `era-topology:ne_001`)
- **Reference Resolution**: Source uses string-based `xyz:ref` values; CONSTRUCT queries must dereference via `xyz:id` lookup to mint proper URI links
- **SKOS Concepts**: Typed values use URIs from ERA concept schemes. **Important**: concept URIs omit the scheme name segment — e.g., `concepts/navigabilities/Both` (not `.../Navigabilities/Both`), `concepts/organisation-roles/IM` (not `.../OrgRoles/IM`)

### Organization Model (new n-ary pattern)
```
era:Body                          # the organization entity
  era:organisationCode "BN"       # 4-char code (was era:imCode)
  era:role → era:OrganisationRole # link to role instance

era:OrganisationRole              # n-ary relationship
  era:hasOrganisationRole → skos:Concept  # e.g. concepts/organisation-roles/IM
  era:roleOf → era:Body           # back-link

# Linking infrastructure to IM:
?element era:infrastructureManager → era:OrganisationRole
```

---

## Folder Structure

```
advanced-example/era-construct/
├── 01-common/
│   ├── 01-infrastructure-managers.sparql
│   └── 02-linear-positioning-systems.sparql
├── 02-topology/
│   ├── 01-net-elements.sparql
│   └── 02-net-relations.sparql
└── 03-functional-infrastructure/
    ├── 01-tracks.sparql
    ├── 02-operational-point-owns.sparql
    ├── 02-operational-points.sparql
    ├── 02-operational-points-netlinearreference.sparql
    ├── 02-operational-points-netpointreference.sparql
    ├── 03-platform-edges.sparql
    ├── 04-switches.sparql
    ├── 05-signals.sparql
    ├── 06-train-detection-elements.sparql
    ├── 07-speed-sections.sparql
    ├── 08-electrification-sections.sparql
    ├── 09-bridges.sparql
    ├── 10-tunnels.sparql
    ├── 11-level-crossings.sparql
    └── 12-sections-of-line.sparql
```

---

## Phase 1 — Common / Organization (`01-common/`)

### 1.1 Organizations → `era:Body` + `era:OrganisationRole` (`01-infrastructure-managers.sparql`)

**Source** (4 instances): `railml:organizationalUnit` with `fx:isInfrastructureManager` child
- `xyz:id` — unique identifier (e.g., `"im01"`, `"oru598"`)
- `xyz:code` — IM code (e.g., `"BN"`)
- `fx:name` → child with `xyz:name`, `xyz:language`

**Target**: Two linked entities per organization:
1. `era:Body` — the organization itself
   - `era:organisationCode` — 4-char code (replaces deprecated `era:imCode`)
   - `rdfs:label` — organization name
2. `era:OrganisationRole` — n-ary role relationship
   - `era:hasOrganisationRole` → `<http://data.europa.eu/949/concepts/organisation-roles/IM>` (SKOS concept)
   - `era:roleOf` → back-link to the `era:Body`

**URI Patterns**:
- Body: `http://data.europa.eu/949/organisations/{id}`
- OrganisationRole: `http://data.europa.eu/949/organisations/{id}/roles/IM`

**⚠ Deprecated vocabulary avoided**: `era:InfrastructureManager` (class), `era:imCode` (property)

---

### 1.2 Linear Positioning Systems → `era:LinearPositioningSystem` (`02-linear-positioning-systems.sparql`)

**Source** (4 instances): `railml:linearPositioningSystem`
- `xyz:id` — unique identifier (e.g., `"LPS_8176"`, `"km"`)

**Target**: `era:LinearPositioningSystem`
- `dct:identifier` — positioning system identifier (`xsd:string`)

**Note**: `era:lineId` will be added later when lines are mapped (Phase 3, Section 3.13).

**📖 See [Linear Positioning System Architecture](#linear-positioning-system-resources-02-linear-positioning-systemssparql)** below for detailed documentation on the dual positioning model and how these resources are referenced by KilometricPost and infrastructure elements.

---

## Phase 2 — Topology (`02-topology/`) — **Micro Level Only**

### 2.1 Net Elements → `era:LinearElement` (`01-net-elements.sparql`)

**Source** (64 instances): `railml:netElement` — **only micro-level elements will be mapped**:
- **54 leaf elements** (micro level): have `xyz:length`, no `fx:elementCollectionUnordered`
  - `xyz:id` — identifier (e.g., `"ne_147"`)
  - `xyz:length` — length in metres (e.g., `"400.0"`)
- **10 parent elements** (meso/macro level): ⚠️ **NOT MAPPED** — have `fx:elementCollectionUnordered` with `fx:elementPart` children
  - These will be **excluded** from the CONSTRUCT query
  - Any references to these elements must be resolved to their constituent micro elements

**Target**: Single `era:NetElement` subclass:
1. **`era:LinearElement`** — for micro-level elements that exist (54 of 143 listed IDs)
   - `era:lengthOfNetLinearElement` → `xsd:double` (only 54 have length attribute)
   - `gsp:hasGeometry` → `gsp:Geometry` node with `gsp:asWKT` (all 54 have LINESTRING geometries)

**URI Pattern**: `http://data.europa.eu/949/topology/netElements/{id}`

**⚠️ Network Registry Structure**: The network registry lists 143 micro-level network resources (both netElements and netRelations). Of these, 54 are netElements and 89 are netRelations. Only netElements should be mapped in this query.

**Geometry Coverage**: All 54 netElements have visualization data via spotElementProjection. Geometry mapping uses nested SELECT with GROUP_CONCAT to create LINESTRING WKT from aggregated coordinate pairs. Coordinates are accessed through: `netElement → associatedPositioningSystem → intrinsicCoordinate@id`, then `spotElementProjection@refersToElement` references the intrinsicCoordinate ID.

**Filter Pattern**: Map only the netElements listed in `networks/network/level[@descriptionLevel="Micro"]/networkResource/@ref` that have `railml:netElement` type (54 elements). NetRelations are mapped separately in 02-net-relations.sparql.

**⚠ Deprecated vocabulary avoided**: `era:elementPart` (property), `era:currentlyValid` (property), `era:NonLinearElement` (class)

---

### 2.2 Net Relations → `era:NetRelation` (`02-net-relations.sparql`)

**Source** (97 instances): `railml:netRelation` with properties:
- `xyz:id` — unique identifier
- `xyz:navigability` — string: `"Both"`, `"AB"`, `"BA"`, `"None"`
- `xyz:positionOnA` — `"0"` (origin) or `"1"` (end)
- `xyz:positionOnB` — `"0"` (origin) or `"1"` (end)
- `fx:elementA` → child with `xyz:ref` string referencing a netElement
- `fx:elementB` → child with `xyz:ref` string referencing a netElement

**Target**: `era:NetRelation`
- `era:elementA` → `era:LinearElement` URI (range: LinearElement)
- `era:elementB` → `era:LinearElement` URI (range: LinearElement)
- `era:isOnOriginOfElementA` → `xsd:boolean` (map: `"0"` = `true`, `"1"` = `false`)
- `era:isOnOriginOfElementB` → `xsd:boolean` (map: `"0"` = `true`, `"1"` = `false`)
- `era:navigability` → `skos:Concept` from scheme `concepts/navigabilities/Navigabilities`

**URI Pattern**: `http://data.europa.eu/949/topology/netRelations/{id}`

**Mapping Notes**:
- **Critical**: Dereference `fx:elementA/xyz:ref` string (e.g., `"ne_147"`) by minting the corresponding ERA URI directly (`era-topology:ne_147`)
- Map `xyz:positionOnA/B`: `"0"` → `true` (at origin/start), `"1"` → `false` (at end)
- Map navigability string to SKOS concept: `http://data.europa.eu/949/concepts/navigabilities/{value}`

---

## Phase 3 — Functional Infrastructure (`03-functional-infrastructure/`)

### 3.1 Tracks → `era:Track` (`01-tracks.sparql`)

**Source** (36 instances): `railml:track` with properties:
- `xyz:id` — unique identifier (e.g., `"trc1"`, `"trc2"`)
- `xyz:type` — track type (`"mainTrack"`, `"secondaryTrack"`, `"connectingTrack"`, `"sidingTrack"`)
- `fx:name` → child with `xyz:name`, `xyz:language`
- `fx:linearLocation` → linear extent positioning
  - `fx:associatedNetElement` (multiple) — track segments
    - `xyz:netElementRef` — which LinearElement this segment is on
    - `xyz:posBegin`, `xyz:posEnd` — start/end positions on that element
    - `xyz:sequence` — ordering of segments
    - `fx:linearCoordinateBegin` → LRS coordinate at segment start
    - `fx:linearCoordinateEnd` → LRS coordinate at segment end
- `fx:length` → child with `xyz:value`, `xyz:type` (e.g., `"physical"`)
- `fx:trackBegin`, `fx:trackEnd` — begin/end references
- `xyz:mainDirection` — direction of travel

**Target**: `era:RunningTrack` or `era:Siding` (subclasses of `era:Track`)

**Subclass Mapping** (based on railML track type):
- `"mainTrack"`, `"secondaryTrack"`, `"connectingTrack"` → `era:RunningTrack` (19 tracks in dataset)
- `"sidingTrack"` → `era:Siding` (3 tracks in dataset)

**Properties** (SHACL-compliant):
- `era:trackId` — string identifier (REQUIRED for `era:RunningTrack`)
- `era:sidingId` — string identifier (REQUIRED for `era:Siding`)
- `rdfs:label` — track name from `fx:name/xyz:name`
- `era:inCountry` → `country:NOR` (Norway country code)
- `era:infrastructureManager` — OrganisationRole (hardcoded to `organisations/0076_IM` for workshop)
- `era:netReference` → `era:NetLinearReference` (one per `associatedNetElement` segment)
- `era:linesideDistanceIndication` → `era:LinesideDistanceIndication` (REQUIRED for `era:RunningTrack`)
- `era:wheelSetGauge` → SKOS Concept for nominal track gauge (hardcoded to `concepts/nominal-track-gauges/30` for standard gauge 1435mm)
- `era:gaugingProfile` → SKOS Concept for loading gauge profile (optional, mapped from railML `loadingGauge` linked via shared `netElementRef`: GA→10, GB→20, GC→30, G1→40, GB1→70, GB2→80)

**LinesideDistanceIndication** (dummy data for RunningTrack):
- `era:linesideDistanceIndicationAppearance` → `<http://data.europa.eu/949/concepts/lineside-distance-indication-appearance/02>` ("Left and right")
- `era:linesideDistanceIndicationFrequency` → `1000` (integer, meters between distance markers)

**Rationale for dummy values**:
- **Appearance**: "Left and right" (02) is most comprehensive default for workshop purposes
- **Frequency**: 1000 meters (1 km) is standard kilometer marker spacing in European rail
- **Production**: These would be sourced from infrastructure documentation or field surveys

**NetLinearReference structure** (linear extent, not point):
- `era:startsAt` → `era:NetPointReference` (segment start point)
- `era:endsAt` → `era:NetPointReference` (segment end point)

**NetPointReference structure** (for segment start/end points):
- `era:hasTopoCoordinate` → `era:TopologicalCoordinate` (topology-based position)
  - `era:onLinearElement` → `era:LinearElement` (from `netElementRef`)
  - `era:offsetFromOrigin` → `xsd:double` (from `posBegin`/`posEnd`)
- `era:hasLrsCoordinate` → `era:LinearPositioningSystemCoordinate` (LRS-based position)
  - `era:kmPost` → `era:KilometricPost` (inferred from measure)
  - `era:offsetFromKilometricPost` → `xsd:double` (measure - km * 1000)

**Linear extent pattern**:
```
Track → era:netReference → NetLinearReference (per segment)
  ├─ era:startsAt → NetPointReference (segment start)
  │   ├─ hasTopoCoordinate → TopologicalCoordinate (posBegin on netElement)
  │   └─ hasLrsCoordinate → LinearPositioningSystemCoordinate (linearCoordinateBegin)
  └─ era:endsAt → NetPointReference (segment end)
      ├─ hasTopoCoordinate → TopologicalCoordinate (posEnd on netElement)
      └─ hasLrsCoordinate → LinearPositioningSystemCoordinate (linearCoordinateEnd)
```

**URI Patterns**:
- Track: `http://data.europa.eu/949/functionalInfrastructure/tracks/{id}`
- LinesideDistanceIndication: `http://data.europa.eu/949/topology/linesideDistanceIndications/{trackId}`
- NetLinearReference: `http://data.europa.eu/949/topology/netLinearReferences/{trackId}_segment_{sequence}`
- NetPointReference (start): `http://data.europa.eu/949/topology/netPointReferences/{trackId}_segment_{sequence}_start`
- NetPointReference (end): `http://data.europa.eu/949/topology/netPointReferences/{trackId}_segment_{sequence}_end`
- TopologicalCoordinate: `http://data.europa.eu/949/topology/topologicalCoordinates/{trackId}_{netElementId}_{position}`
- LinearPositioningSystemCoordinate: `http://data.europa.eu/949/topology/linearPositioningSystemCoordinates/{trackId}_segment_{sequence}_{start_or_end}_{positioningSystemRef}_{measure}`
- KilometricPost: `http://data.europa.eu/949/kilometricPosts/{positioningSystemRef}_km_{kmNumber}` (shared)

**Mapping Notes**:
- **Linear extent vs point position**: Unlike signals (which use `NetPointReference` with single `TopologicalCoordinate`), tracks use `NetLinearReference` with start/end `NetPointReference` pairs
- **Multiple segments**: Tracks spanning multiple `netElements` create multiple `NetLinearReference` instances (54 segments total for 36 tracks, avg 1.5 per track)
- **Dual positioning**: Both segment start and end points have topology-based (`TopologicalCoordinate`) and LRS-based (`LinearPositioningSystemCoordinate`) positions
- **KilometricPost inference**: Same pattern as signals — KilometricPost inferred from LRS measure, shared across all elements using same positioning system
- **Track subclass determination**: Uses `xyz:type` attribute to determine whether track is RunningTrack or Siding
- **SHACL compliance**: All required properties implemented with dummy data where railML source lacks information
- ⚠️ **Workshop simplification**: All tracks assigned to infrastructure manager `organisations/0076_IM` (Belgian IM)

---

### 3.2 Operational Points → `era:OperationalPoint` (3 files)

**Source** (10 instances): `railml:operationalPoint` with properties:
- `xyz:id` — unique identifier
- `fx:name` → child with `xyz:name`, `xyz:language`
- `fx:designator` → child with `xyz:register`, `xyz:entry`
- `fx:spotLocation` → positioning on topology (reference points)
- `fx:areaLocation` → area extent (full operational point extent)
- `fx:gmlLocations` → geographic coordinates
- `fx:opEquipment` → equipment references
- `fx:opOperations` → operational characteristics

**Target**: `era:OperationalPoint` with dual net references

**Implementation Split** (3 separate SPARQL files for clarity):

#### 3.2.1 Base Properties (`02-operational-points.sparql`)
Creates the core `era:OperationalPoint` resource with basic properties (no net references):
- `era:opName` — name string from `fx:name`
- `era:opType` — SKOS concept (operational point type)
- `era:uopid` — unique identifier from `fx:designator/xyz:entry`
- `era:inCountry` → `country:NOR` (Norway country code)
- `gsp:hasGeometry` — POINT geometry from `fx:spotElementProjection`
- `era:infrastructureManager` — OrganisationRole (hardcoded to `organisations/0076_IM`)
- `rdfs:label` — operational point name

**URI Pattern**: `http://data.europa.eu/949/functionalInfrastructure/operationalPoints/{id}`

**Mapping Notes**:
- UOPID format: `CONCAT('NO', ?uopid_suffix)` with register `_railML`
- Infrastructure manager: hardcoded to Belgian IM (0076_IM) for workshop
- Geometry: POINT from spotElementProjection coordinates (WGS84 transformation)

#### 3.2.2 Operational Point Ownership (`02-operational-point-owns.sparql`)
Maps operational point ownership relationships to functional infrastructure via `era:hasPart`:

**Strategy**: Create `era:hasPart` links from operational points to owned infrastructure elements using three ownership patterns:

**Ownership Patterns**:
1. **Platform Edges** — Direct ownership via `ownsInfrastructureElement`
   - OP has `opEquipment` → `ownsInfrastructureElement` → ref to platform edge ID
   - Dereference to confirm element is a `railml:platformEdge`
   
2. **Signals** — Direct ownership via `ownsSignal`
   - OP has `opEquipment` → `ownsSignal` → ref to signal ID
   - Creates `era:hasPart` link to signal URI
   
3. **Tracks/Sidings** — Spatial match via area location intersection
   - OP has `areaLocation` → `associatedNetElement` → meso/macro element refs
   - Expand meso/macro elements to constituent micro elements
   - Find tracks whose `linearLocation` references these micro elements
   - Creates `era:hasPart` links for all spatially contained tracks

**Target**: `era:hasPart` triples linking operational points to owned infrastructure
```turtle
?operationalPoint era:hasPart ?platformEdge .
?operationalPoint era:hasPart ?signal .
?operationalPoint era:hasPart ?track .
```

**URI Patterns**:
- Uses existing URIs from other queries (no new resources created)
- OperationalPoint: `functionalInfrastructure/operationalPoints/{id}`
- PlatformEdge: `functionalInfrastructure/platformEdges/{id}`
- Signal: `functionalInfrastructure/signals/{id}`
- Track: `functionalInfrastructure/tracks/{id}` (both RunningTrack and Siding)

**Mapping Notes**:
- Query uses three UNION blocks (one per ownership pattern)
- Platform edges and signals use direct ownership references from `opEquipment`
- Tracks/sidings use spatial matching through netElement intersection
- Spatial matching: OP's meso/macro elements → micro children → tracks referencing those micros
- All three patterns mint the same OperationalPoint URI for consistency

#### 3.2.3 NetLinearReference (`02-operational-points-netlinearreference.sparql`)
Maps operational points with `areaLocation` (on meso/macro elements) to linear extents:

**Strategy**: Expand meso/macro elements to constituent micro elements, create NetLinearReference (0 to length) for each micro element

**Target**: `era:NetLinearReference` per micro element
- `era:startsAt` → `era:NetPointReference` (position 0)
- `era:endsAt` → `era:NetPointReference` (position = element length)

Each start/end NetPointReference has:
- `era:hasTopoCoordinate` → `era:TopologicalCoordinate` (precisely positioned on micro element)
- `era:hasLrsCoordinate` → `era:LinearPositioningSystemCoordinate` (from track coverage)

**URI Patterns**:
- NetLinearReference: `http://data.europa.eu/949/topology/netLinearReferences/{oppId}_{microElementRef}`
- NetPointReference (start): `http://data.europa.eu/949/topology/netPointReferences/{oppId}_{microElementRef}_start`
- NetPointReference (end): `http://data.europa.eu/949/topology/netPointReferences/{oppId}_{microElementRef}_end`
- TopologicalCoordinate: `http://data.europa.eu/949/topology/topologicalCoordinates/{oppId}_{netElementId}_{position}`
- LinearPositioningSystemCoordinate: `http://data.europa.eu/949/topology/linearPositioningSystemCoordinates/{oppId}_{microElementRef}_{start|end}_{positioningSystemRef}_{measure}`
- KilometricPost: `http://data.europa.eu/949/kilometricPosts/{positioningSystemRef}_km_{kmNumber}` (shared)

**Mapping Notes**:
- ⚠️ **Micro topology conversion**: areaLocation references meso/macro elements → expand to constituent micro elements via `fx:elementCollectionUnordered` → `fx:elementPart`
- LRS coordinates sourced from track's `linearCoordinateBegin`/`linearCoordinateEnd` on `associatedNetElement`
- Every operational point micro element has exactly 1 track reference (verified)
- Represents the full linear extent of the operational point on each micro element

#### 3.2.4 NetPointReference (`02-operational-points-netpointreference.sparql`)
Maps operational points with `spotLocation` (on micro elements) to point references:

**Strategy**: Map spotLocations directly to NetPointReference (similar to signals)

**Target**: `era:NetPointReference` per spotLocation
- `era:hasTopoCoordinate` → `era:TopologicalCoordinate` (positioned on micro element)
- `era:hasLrsCoordinate` → `era:LinearPositioningSystemCoordinate` (if linearCoordinate available)

**URI Patterns**:
- NetPointReference: `http://data.europa.eu/949/topology/netPointReferences/{spotLocationId}`
- TopologicalCoordinate: `http://data.europa.eu/949/topology/topologicalCoordinates/{spotLocId}_{netElementId}_{position}`
- LinearPositioningSystemCoordinate: `http://data.europa.eu/949/topology/linearPositioningSystemCoordinates/{spotLocId}_{positioningSystemRef}_{measure}`
- KilometricPost: `http://data.europa.eu/949/kilometricPosts/{positioningSystemRef}_km_{kmNumber}` (shared)

**Mapping Notes**:
- spotLocations are reference positions for timetable activities
- LRS coordinates from spotLocation's `fx:linearCoordinate` (if present)
- Uses same NetPointReference pattern as signals (Section 3.5)
- ⚠️ **Micro topology only**: `xyz:netElementRef` must resolve to micro-level LinearElements

**Coverage** (in advanced example dataset):
- 4 operational points with areaLocation (creates NetLinearReference)
- All operational points have spotLocations (creates NetPointReference)
- Both reference types coexist (operational points have both linear extent and reference points)

---

### 3.3 Platform Edges → `era:PlatformEdge` (`03-platform-edges.sparql`)

**Source** (13 instances): `railml:platformEdge` with properties:
- `xyz:id` — unique identifier
- `fx:name` → child with `xyz:name` (optional) — platform edge name
- `fx:linearLocation` → child containing positioning
  - `fx:associatedNetElement` — one or more segments
    - `xyz:netElementRef` — reference to `railml:netElement`
    - `xyz:posBegin`, `xyz:posEnd` — topological extent on netElement
    - `xyz:sequence` — segment ordering (optional, defaults to 1)
    - `fx:linearCoordinateBegin`, `fx:linearCoordinateEnd` — LRS coordinates
      - `xyz:measure` — position in meters
      - `xyz:positioningSystemRef` — reference to `railml:linearPositioningSystem`

**Target**: `era:PlatformEdge` with linear extent positioning via `era:NetLinearReference`
- `era:platformId` — identifier string
- `rdfs:label` — platform edge name (optional)
- `era:inCountry` → `country:NOR` (Norway country code)
- `era:infrastructureManager` → `era:OrganisationRole` (hardcoded to `organisations/0076_IM` for workshop)
- `era:netReference` → `era:NetLinearReference` (one per segment)
- `gsp:hasGeometry` → `gsp:Geometry` (LINESTRING from screen visualization coordinates)

**NetLinearReference structure** (linear extent positioning):
- `era:startsAt` → `era:NetPointReference` (start of extent)
- `era:endsAt` → `era:NetPointReference` (end of extent)

Each `era:NetPointReference` (start/end) has:
- `era:hasTopoCoordinate` → `era:TopologicalCoordinate`
  - `era:onLinearElement` → micro-level `era:LinearElement`
  - `era:offsetFromOrigin` — position on element (xsd:double)
- `era:hasLrsCoordinate` → `era:LinearPositioningSystemCoordinate`
  - `era:kmPost` → `era:KilometricPost`
  - `era:offsetFromKilometricPost` — offset in meters (xsd:double)

Each `era:KilometricPost`:
- `era:hasLRS` → `era:LinearPositioningSystem`
- `era:kilometer` — km number (xsd:integer, rounded from measure)

**URI Patterns**:
- PlatformEdge: `functionalInfrastructure/platformEdges/{id}`
- NetLinearReference: `topology/netLinearReferences/{platformEdgeId}_segment_{sequence}`
- NetPointReference (start/end): `topology/netPointReferences/{platformEdgeId}_segment_{sequence}_{start|end}`
- TopologicalCoordinate: `topology/topologicalCoordinates/{platformEdgeId}_{netElementId}_{position}`
- LinearPositioningSystemCoordinate: `topology/linearPositioningSystemCoordinates/{platformEdgeId}_segment_{sequence}_{start|end}_{posSystemRef}_{measure}`
- KilometricPost: `kilometricPosts/{posSystemRef}_km_{kmNumber}`

**Mapping Notes**:
- Platform edges typically span a single netElement, but multi-segment extents are supported
- Follows same dual positioning pattern as tracks (topological + LRS coordinates)
- ⚠️ **Micro topology conversion**: Link to topology via `xyz:netElementRef`, resolving to micro-level LinearElements
- LRS coordinates from `linearCoordinateBegin/End` provide KilometricPost references
- Sequence defaults to "1" if not present in source data

---

### 3.4 Switches → `era:Switch` (`04-switches.sparql`)

**Source** (26 instances): `railml:switchIS` with properties:
- `xyz:id` — unique identifier
- `xyz:type` — switch type: `"ordinarySwitch"` (most common), `"doubleSwitchCrossing"`, `"switchCrossingPart"`
- `fx:name` → child with `xyz:name`, `xyz:language`
- `fx:spotLocation` → positioning with `xyz:netElementRef`, `xyz:pos`, `xyz:applicationDirection`
  - `fx:linearCoordinate` → LRS coordinate (optional)
- `fx:leftBranch`, `fx:rightBranch` — branch definitions
  - `xyz:branchingSpeed` — maximum speed when branching (km/h, optional)
  - `xyz:joiningSpeed` — maximum speed when joining (km/h, optional)
  - `xyz:radius` — curve radius in metres (optional)
  - `xyz:netRelationRef` — reference to the NetRelation this branch connects to

**Target**: Three interconnected resources per switch:

1. **`era:Switch`** — the switch infrastructure element
   - `era:switchId` — identifier string
   - `rdfs:label` — switch name from `fx:name`
   - `era:inCountry` → `country:NOR` (Norway country code)
   - `era:infrastructureManager` → `era:OrganisationRole` (hardcoded to `organisations/0076_IM` for workshop)
   - `era:netReference` → `era:NetPointReference` (topological positioning)

2. **`era:NetPointReference`** — topological point reference
   - `era:appliesToDirection` — SKOS concept from `applicationDirection` (towards topology direction)
   - `era:hasTopoCoordinate` → `era:TopologicalCoordinate` (precise position)
   - `era:hasLrsCoordinate` → `era:LinearPositioningSystemCoordinate` (if linearCoordinate available)
   - `gsp:hasGeometry` → `gsp:Geometry` (POINT geometry - **added by post-processing script**)

3. **`gsp:Geometry`** — spatial geometry for the switch location
   - `gsp:asWKT` — WKT POINT literal (interpolated using Shapely linear referencing)
   - **Not created by SPARQL** - added by `enrich-geometries.py` after all CONSTRUCT queries complete

4. **`era:TopologicalCoordinate`** — precise position on linear element
   - `era:onLinearElement` → `era:LinearElement` (micro-level netElement)
   - `era:offsetFromOrigin` — position in meters (`xsd:double`)

**URI Patterns**:
- Switch: `http://data.europa.eu/949/functionalInfrastructure/switches/{id}`
- NetPointReference: `http://data.europa.eu/949/topology/netPointReferences/{switchId}_on_{netElementId}`
- TopologicalCoordinate: `http://data.europa.eu/949/topology/topologicalCoordinates/{switchId}_{netElementId}_{position}`
- LinearPositioningSystemCoordinate: `http://data.europa.eu/949/topology/linearPositioningSystemCoordinates/{switchId}_{positioningSystemRef}_{measure}` (if LRS available)
- KilometricPost: `http://data.europa.eu/949/kilometricPosts/{positioningSystemRef}_km_{kmNumber}` (shared)
- OrganisationRole: `http://data.europa.eu/949/organisations/0076_IM` (Belgian IM for workshop)

**Positioning Pattern**: `Switch → NetPointReference → TopologicalCoordinate → LinearElement`

This pattern enables:
- Precise spatial queries ("find switches at position X on element Y")
- Distance calculations ("switches within 500m of coordinate")
- Direction-aware switching logic
- Standard ERA infrastructure element positioning model (same as signals)

**Application Direction Mapping**:
- railML `"normal"` → ERA `concepts/orientations/00` (Normal)
- railML `"reverse"` → ERA `concepts/orientations/01` (Opposite)
- railML `"both"` → ERA `concepts/orientations/02` (Both)

**Mapping Notes**:
- Extract position from `fx:spotLocation/xyz:pos` and convert to `xsd:double`
- Map `applicationDirection` to ERA orientation concepts (for `era:appliesToDirection`)
- Extract switch name from `fx:name/xyz:name` (Norwegian language)
- **Geometry enrichment (post-processing)**: 
  - NetPointReference geometries are **NOT** created in SPARQL
  - After all CONSTRUCT queries complete, `enrich-geometries.py` uses Shapely's linear referencing to interpolate POINT positions along LinearElement LINESTRING geometries at the `offsetFromOrigin` position
  - This provides accurate spatial coordinates for each switch position
  - The script is automatically called by `run-era-construct.py` after all SPARQL queries complete
- Infrastructure manager: For this workshop/demo, all switches are assigned to `http://data.europa.eu/949/organisations/0076_IM` (Belgian infrastructure manager BN)
  - In production scenarios, this would be determined by the organizational unit responsible for the switch's location
- ⚠️ **Micro topology only**: `xyz:netElementRef` must resolve to micro-level LinearElements
- **LRS coordinates**: If spotLocation has `fx:linearCoordinate` child, create `era:hasLrsCoordinate` → `era:LinearPositioningSystemCoordinate` with KilometricPost reference (same pattern as signals)
- **Branch properties**: Not currently mapped to ERA properties (no clear ERA equivalents for branchingSpeed, joiningSpeed, radius)
- **NetRelation references**: Not currently mapped (would require complex handling of branch topology relationships)

**Switch Types in Dataset**:
- Ordinary switches: 24 instances (simple point switches)
- Double switch crossings: 1 instance (complex junction)
- Switch crossing parts: 1 instance (component of crossing)

**Template for Other Point Infrastructure**:
This NetPointReference pattern should be used for all point-based infrastructure elements (train detection elements, buffer stops, borders, etc.) that have `fx:spotLocation` in the railML source.

---

### 3.5 Signals → `era:Signal` (`05-signals.sparql`)

**Source** (80 instances): `railml:signalIS` with properties:
- `xyz:id` — unique identifier
- `fx:spotLocation` → positioning with `xyz:netElementRef`, `xyz:pos`, `xyz:applicationDirection`
- `fx:isTrainMovementSignal`, `fx:isSpeedSignal`, etc. — signal function booleans/types
- `fx:typeDesignator` — type designation
- `fx:signalConstruction` → construction details

**Target**: Three interconnected resources per signal:

1. **`era:Signal`** — the signal infrastructure element
   - `era:signalId` — identifier string
   - `era:signalType` — SKOS concept from TJN signal code mapping (e.g., `concepts/signal-types/01`)
   - `era:inCountry` → `country:NOR` (Norway country code)
   - `era:hasOrientation` — SKOS concept from `applicationDirection` (⚠️ refers to KM direction, not topology direction)
   - `era:infrastructureManager` → `era:OrganisationRole` (replaces deprecated `era:imCode`)
   - `era:netReference` → `era:NetPointReference` (topological positioning)

2. **`era:NetPointReference`** — topological point reference
   - `era:appliesToDirection` — SKOS concept from `applicationDirection` (towards topology direction)
   - `era:hasTopoCoordinate` → `era:TopologicalCoordinate` (precise position)
   - `gsp:hasGeometry` → `gsp:Geometry` (POINT geometry - **added by post-processing script**)

3. **`gsp:Geometry`** — spatial geometry for the signal location
   - `gsp:asWKT` — WKT POINT literal (interpolated using Shapely linear referencing)
   - **Not created by SPARQL** - added by `enrich-geometries.py` after all CONSTRUCT queries complete

4. **`era:TopologicalCoordinate`** — precise position on linear element
   - `era:onLinearElement` → `era:LinearElement` (micro-level netElement)
   - `era:offsetFromOrigin` — position in meters (`xsd:double`)

**URI Patterns**:
- Signal: `http://data.europa.eu/949/functionalInfrastructure/signals/{id}`
- NetPointReference: `http://data.europa.eu/949/topology/netPointReferences/{signalId}_on_{netElementId}`
- TopologicalCoordinate: `http://data.europa.eu/949/topology/topologicalCoordinates/{signalId}_{netElementId}_{position}`
- Geometry: `http://data.europa.eu/949/geometry/{lon}/{lat}` (using decimal coordinates)
- OrganisationRole: `http://data.europa.eu/949/organisations/{eraCode}_IM` (e.g., `organisations/0076_IM` for BN)

**Positioning Pattern**: `Signal → NetPointReference → TopologicalCoordinate → LinearElement`

This pattern enables:
- Precise spatial queries ("find signals at position X on element Y")
- Distance calculations ("signals within 500m of coordinate")
- Direction-aware signaling logic
- Standard ERA infrastructure element positioning model

**Application Direction Mapping**:
- railML `"normal"` → ERA `concepts/orientations/00` (Normal)
- railML `"reverse"` → ERA `concepts/orientations/01` (Opposite)
- railML `"both"` → ERA `concepts/orientations/02` (Both)

**Mapping Notes**:
- Extract position from `fx:spotLocation/xyz:pos` and convert to `xsd:double`
- Map `applicationDirection` to ERA orientation concepts (used for both `era:hasOrientation` and `era:appliesToDirection`)
- **Geometry enrichment (post-processing)**: 
  - NetPointReference geometries are **NOT** created in SPARQL (GeoSPARQL lacks linear referencing functions)
  - After all CONSTRUCT queries complete, `enrich-geometries.py` uses Shapely's linear referencing to:
    1. Query all NetPointReferences with TopologicalCoordinates
    2. Get the LinearElement's LINESTRING geometry and offsetFromOrigin
    3. Interpolate the POINT position along the LINESTRING using `shapely.geometry.LineString.interpolate()`
    4. Insert `gsp:hasGeometry` triples back into the RDF graph
  - This provides accurate spatial coordinates for each signal position
  - The script is automatically called by `run-era-construct.py` after all SPARQL queries complete
- Infrastructure manager: For this workshop/demo, all signals are assigned to `http://data.europa.eu/949/organisations/0076_IM` (Belgian infrastructure manager BN)
  - In production scenarios, this would be determined by the organizational unit responsible for the signal's location
  - The URI pattern matches that from `01-infrastructure-managers.sparql`: `organisations/{eraCode}_IM`
- ⚠️ **Micro topology only**: `xyz:netElementRef` must resolve to micro-level LinearElements
- ⚠️ **Deprecated vocabulary avoided**: `era:imCode` (property) → use `era:infrastructureManager` instead

**Signal Type Classification (`era:signalType`)**:

Each signal is classified using the `era:signalType` property, which links to a SKOS concept from the ERA signal types vocabulary (`http://data.europa.eu/949/concepts/signal-types/`).

**Source**: railML `fx:typeDesignator` element with TJN rulebook code
```xml
<signalIS id="sig179">
  <typeDesignator entry="§8-10" rulebook="TJN"/>
  ...
</signalIS>
```

**Mapping Logic**: TJN (Norwegian railway regulations) signal codes are mapped to ERA standardized signal types:

| TJN Code | Norwegian Name | ERA Type | Description |
|----------|----------------|----------|-------------|
| §8-10 | Innkjørhovedsignal | 01 | Home Signal |
| §8-11 | Utkjørhovedsignal | 04 | Exit Signal |
| §8-12 | Indre hovedsignal | 02 | Intermediate/Inner Signal |
| §8-13 | Blokksignal | 06 | Block Signal |
| §8-23 | Dvergsignaler | 12 | Shunting Signal |

**Default Behavior**: Signals with unmapped TJN codes (e.g., E35 ERTMS stop signs, §8-14 distant signals, 68A/B/D speed signs, §8-15 repeaters) default to Type 02 (Intermediate Signal) for conservative classification.

**Implementation**: SPARQL BIND with nested IF statements
```sparql
# Extract typeDesignator with TJN rulebook
OPTIONAL {
  ?signal fx:typeDesignator ?typeDesNode .
  ?typeDesNode xyz:entry ?tjnCode ;
               xyz:rulebook "TJN" .
}

# Map TJN codes to ERA signal type SKOS concepts
BIND (
  IF(?tjnCode = "§8-10", IRI("http://data.europa.eu/949/concepts/signal-types/01"),
  IF(?tjnCode = "§8-11", IRI("http://data.europa.eu/949/concepts/signal-types/04"),
  IF(?tjnCode = "§8-12", IRI("http://data.europa.eu/949/concepts/signal-types/02"),
  IF(?tjnCode = "§8-13", IRI("http://data.europa.eu/949/concepts/signal-types/06"),
  IF(?tjnCode = "§8-23", IRI("http://data.europa.eu/949/concepts/signal-types/12"),
  IRI("http://data.europa.eu/949/concepts/signal-types/02")  # Default
  )))))
  AS ?eraSignalType
)
```

**Reference Documentation**: See `TJN-TO-ERA-SIGNAL-TYPE-MAPPING.md` for comprehensive mapping table with Norwegian regulatory references (Kapittel 8 - Signaler), confidence levels, and production considerations.

**Workshop vs Production**:
- **Workshop**: High-confidence mappings (§8-10, §8-11, §8-12, §8-13, §8-23) are sufficient for demonstration; unmapped codes use conservative Type 02 default
- **Production**: Requires domain expert validation, particularly for:
  - E35 ERTMS stop signs (context-dependent mapping)
  - §8-14 distant signals (may need separate classification)
  - Speed restriction signs (68A/B/D)
  - Combined and repeater signals

**Distribution** (in advanced example dataset):
- Type 01 (Home): 6 signals
- Type 02 (Intermediate): 55 signals (2 mapped + 53 defaults)
- Type 04 (Exit): 6 signals
- Type 06 (Block): 2 signals
- Type 12 (Shunting): 2 signals

**Template for Other Infrastructure Elements**:
This NetPointReference pattern should be used for all point-based infrastructure elements (switches, train detection elements, buffer stops, borders, etc.) that have `fx:spotLocation` in the railML source.

---

### 3.6 Train Detection Elements → `era:TrainDetectionSystem` (`06-train-detection-elements.sparql`)

**Source** (64 instances): `railml:trainDetectionElement` with properties:
- `xyz:id` — unique identifier
- `xyz:type` — detection type (e.g., `"axleCounter"`, `"trackCircuit"`)
- `fx:spotLocation` → positioning
- Additional technical properties

**Target**: `era:TrainDetectionSystem`

**URI Pattern**: `http://data.europa.eu/949/functionalInfrastructure/trainDetectionSystems/{id}`

**Mapping Notes**:
- Map `xyz:type` to ERA train detection system type vocabulary
- ⚠️ **Micro topology conversion**: Resolve spotLocation to micro-level LinearElements only

---

### 3.7 Speed Sections → `era:SpeedSection` (`07-speed-sections.sparql`)

**Source** (31 instances): `railml:speedSection` with properties:
- `xyz:id` — unique identifier
- `fx:linearLocation` → child containing positioning
  - `fx:associatedNetElement` — typically multiple segments per speed section
    - `xyz:netElementRef` — reference to `railml:netElement`
    - `xyz:posBegin`, `xyz:posEnd` — topological extent on netElement
    - `xyz:sequence` — segment ordering (optional, defaults to 1)
    - `fx:linearCoordinateBegin`, `fx:linearCoordinateEnd` — LRS coordinates
      - `xyz:measure` — position in meters
      - `xyz:positioningSystemRef` — reference to `railml:linearPositioningSystem`

**Target**: `era:SpeedSection` with linear extent positioning via `era:NetLinearReference`
- `era:speedSectionId` — identifier string
- `era:inCountry` → `country:NOR` (Norway country code)
- `era:infrastructureManager` → `era:OrganisationRole` (hardcoded to `organisations/0076_IM` for workshop)
- `era:netReference` → `era:NetLinearReference` (one per segment)

**NetLinearReference structure** (linear extent positioning):
- `era:startsAt` → `era:NetPointReference` (start of extent)
- `era:endsAt` → `era:NetPointReference` (end of extent)

Each `era:NetPointReference` (start/end) has:
- `era:hasTopoCoordinate` → `era:TopologicalCoordinate`
  - `era:onLinearElement` → micro-level `era:LinearElement`
  - `era:offsetFromOrigin` — position on element (xsd:double)
- `era:hasLrsCoordinate` → `era:LinearPositioningSystemCoordinate`
  - `era:kmPost` → `era:KilometricPost`
  - `era:offsetFromKilometricPost` — offset in meters (xsd:double)

Each `era:KilometricPost`:
- `era:hasLRS` → `era:LinearPositioningSystem`
- `era:kilometer` — km number (xsd:integer, rounded from measure)

**URI Patterns**:
- SpeedSection: `functionalInfrastructure/speedSections/{id}`
- NetLinearReference: `topology/netLinearReferences/{speedSectionId}_segment_{sequence}`
- NetPointReference (start/end): `topology/netPointReferences/{speedSectionId}_segment_{sequence}_{start|end}`
- TopologicalCoordinate: `topology/topologicalCoordinates/{speedSectionId}_{netElementId}_{position}`
- LinearPositioningSystemCoordinate: `topology/linearPositioningSystemCoordinates/{speedSectionId}_segment_{sequence}_{start|end}_{posSystemRef}_{measure}`
- KilometricPost: `kilometricPosts/{posSystemRef}_km_{kmNumber}`

**Mapping Notes**:
- Speed sections typically span multiple netElements (multi-segment extents)
- Same speed section ID will have multiple netElement references with different LRS coordinates
- Follows same dual positioning pattern as tracks and platform edges (topological + LRS coordinates)
- ⚠️ **Micro topology conversion**: Link to topology via `xyz:netElementRef`, resolving to micro-level LinearElements only
- LRS coordinates from `linearCoordinateBegin/End` provide KilometricPost references
- Sequence defaults to "1" if not present in source data

---

### 3.8 Electrification Sections → `era:ContactLineSystem` (`08-electrification-sections.sparql`)

**Source** (16 instances): `railml:electrificationSection` with properties:
- `xyz:id` — unique identifier (e.g., `"elc8"`, `"elc9"`)
- `xyz:contactLineType` — contact line type (`"overhead"` or `"none"`)
- `fx:hasContactWire` → child element (present for electrified sections with overhead contact line)
- `fx:energyCatenary` → catenary energy supply details
  - `xyz:allowsRegenerativeBraking` — boolean indicating if regenerative braking is permitted
- `fx:energyPantograph` → pantograph energy collection details
- `fx:energyRollingstock` → rolling stock energy consumption details
  - `xyz:requiresPowerLimitation` — boolean indicating if power limitation is required on board
  - `xyz:permittedMaxContactForce`, `xyz:permittedStaticContactForce` — contact force limits
  - `xyz:requiredFireCategory` — fire safety category
  - `xyz:requiresAutomaticDroppingDevice` — automatic pantograph drop requirement
- `fx:etcsElectrification` → ETCS electrification compatibility
- `fx:linearLocation` → linear extent positioning (associatedNetElement references)

**Data Coverage** (discovered via MCP): 
- 7 of 16 sections are electrified (have `fx:hasContactWire`): elc732, elc877, elc8, elc46, elc439, elc440, elc442
- 9 of 16 sections are non-electrified: elc430, elc432-elc438, elc600
- All 7 electrified sections have `allowsRegenerativeBraking` and `requiresPowerLimitation` data

**Target**: `era:ContactLineSystem` (NOT a subclass of InfrastructureElement)

**Discovery Process** (MCP-driven):
1. **Queried ObjectProperties**: Found 3 properties with domain `era:ContactLineSystem`
   - `era:contactLineSystemType` (required via SHACL `sh:minCount 1`)
   - `era:conditionalRegenerativeBrake`
   - `era:conditionsAppliedRegenerativeBraking`
2. **Queried DatatypeProperties**: Found 6 properties with domain `era:ContactLineSystem`
   - `era:conditionsChargingElectricEnergyStorage` (xsd:anyURI)
   - `era:currentLimitationRequired` (xsd:boolean)
   - `era:energySupplySystemTSICompliant` (xsd:boolean)
   - `era:maxTrainCurrent` (xsd:integer)
   - `era:permissionChargingElectricEnergyTractionStandstill` (xsd:boolean)
   - `era:umax2` (xsd:integer)
3. **Queried SKOS concepts**: Retrieved concept schemes for mapped properties
   - `contact-line-systems`: 10=OCL, 20=Third Rail, 30=Fourth Rail, 40=Not electrified
   - `regenerative-braking`: 10=allowed, 20=allowed under conditions, 30=only emergency, 40=conditions+emergency, 50=not allowed
4. **Analyzed railML data**: Identified available source values for 3 properties (others lack source data)

**Mapped Properties** (9 of 10 discovered for ContactLineSystem, plus Track pantograph spacing):
- `era:contactLineSystemType` → SKOS Concept for contact line system type (REQUIRED)
  - **Conditional mapping** based on `fx:hasContactWire` property presence:
    - IF `fx:hasContactWire` present → `concepts/contact-line-systems/10` (Overhead contact line - OCL)
    - IF `fx:hasContactWire` absent → `concepts/contact-line-systems/40` (Not electrified)
- `era:conditionalRegenerativeBrake` → SKOS Concept (permission for regenerative braking)
  - **Mapped from** `fx:energyCatenary/xyz:allowsRegenerativeBraking` (boolean):
    - `"true"` string → `concepts/regenerative-braking/10` (allowed)
    - `"false"` string → `concepts/regenerative-braking/50` (not allowed)
  - **Note**: Boolean-to-SKOS concept conversion — railML uses boolean, ERA uses controlled vocabulary
- `era:currentLimitationRequired` → xsd:boolean (current/power limitation on board required)
  - **Mapped from** `fx:energyRollingstock/xyz:requiresPowerLimitation` (boolean string)
  - **Note**: String-to-boolean datatype conversion
- `era:energySupplySystem` → SKOS Concept (energy supply system voltage and frequency)
  - **Mapped from** `xyz:electrificationSystemRef` → `railml:electrificationSystem` attributes:
    - `xyz:voltage=25000` AND `xyz:frequency=50` → `concepts/energy-supply-systems/AC10` (AC 25kV-50Hz)
    - `xyz:voltage=3000` AND `xyz:frequency=0` → `concepts/energy-supply-systems/DC30` (DC 3kV)
  - **Note**: References shared electrificationSystem definitions in railML common section; voltage in volts, frequency in Hz
- `era:maxCurrentStandstillPantograph` → xsd:integer (maximum current at standstill per pantograph)
  - **Fixed value**: 200 amperes for all electrified sections
  - **Note**: Applied only to sections with `fx:hasContactWire` present
- `era:maxTrainCurrent` → xsd:integer (maximum train current in amperes)
  - **Mapped from** `fx:energyCatenary/fx:maxTrainCurrent/xyz:maxCurrent`
  - **Note**: Takes maximum value if multiple maxTrainCurrent entries exist (different operationTypes/trainTypes)
  - **Data conversion**: String to xsd:integer
- `era:maximumContactWireHeight` → xsd:double (maximum contact wire height in meters)
  - **Mapped from** `fx:hasContactWire/xyz:maxHeight`
  - **Data conversion**: String to xsd:double
- `era:minimumContactWireHeight` → xsd:double (minimum contact wire height in meters)
  - **Mapped from** `fx:hasContactWire/xyz:minHeight`
  - **Data conversion**: String to xsd:double
- `era:tsiPantographHead` → SKOS Concept (TSI compliant pantograph heads)
  - **Mapped from** `fx:energyPantograph/xyz:compliantTSITypes`:
    - `"tsi1950"` → `concepts/compliant-pantograph-heads/10` (1950 mm Type 1)
    - `"tsi2000_2260"` → `concepts/compliant-pantograph-heads/30` (2000 mm – 2260 mm)
  - **Note**: Maps to ERA compliant pantograph head concept scheme
- `era:inCountry` → `country:NOR` (Norway country code)
- `era:infrastructureManager` → `era:OrganisationRole` (hardcoded to `organisations/0076_IM` for workshop)

**Track Pantograph Spacing Properties** (linked via shared netElements):
- `era:trackRaisedPantographsDistanceAndSpeed` → `era:RaisedPantographsDistanceAndSpeed`
  - Links Track to structured pantograph spacing requirements
  - One `RaisedPantographsDistanceAndSpeed` instance per electrification section
  - Instance properties:
    - `era:raisedPantographsNumber` → xsd:integer (number of raised pantographs allowed)
      - **Mapped from** `fx:pantographSpacing/xyz:numberPantographsRaised`
    - `era:raisedPantographsDistance` → xsd:integer (spacing between pantographs in meters)
      - **Mapped from** `fx:pantographSpacing/xyz:spacingPantographsRaised`
  - **Note**: This pattern keeps infrastructure constraints (track + pantograph spacing) separate from contact line system characteristics

**Additional available properties** (from ERA ontology, not mapped in workshop):
- ObjectProperties:
  - `era:conditionsAppliedRegenerativeBraking` → Document (conditions for regenerative braking)
- DatatypeProperties:
  - `era:conditionsChargingElectricEnergyStorage` → xsd:anyURI
  - `era:energySupplySystemTSICompliant` → xsd:boolean (energy supply system TSI compliant)
  - `era:permissionChargingElectricEnergyTractionStandstill` → xsd:boolean
  - `era:umax2` → xsd:integer (Umax2 for French network)

**Note**: 9 of 10 ContactLineSystem properties discovered via MCP are now mapped. The 10th property (`era:conditionsAppliedRegenerativeBraking`) requires Document resource type which is not available in the railML source data.

**Linking to Tracks** (Functional Resource Pattern):  
ContactLineSystem is NOT a subclass of `era:InfrastructureElement` and thus does NOT have `era:netReference`.  
Instead, `era:Track` resources reference ContactLineSystems via `era:contactLineSystem` property.

**Discovery of linking mechanism** (MCP-driven):
1. **Queried properties with ContactLineSystem range**: `?property rdfs:range era:ContactLineSystem`
   - Found `era:contactLineSystem` property with domain as union (blank node)
2. **Queried SHACL shapes**: `sh:path era:contactLineSystem`
   - Found property on `era:CommonCharacteristicsSubset` and `era:RunningTrack`
   - `era:RunningTrack` is subclass of `era:Track` → `era:InfrastructureElement`
3. **Conclusion**: Tracks link TO ContactLineSystems (not the reverse)

**Linking Implementation**:
1. Each `railml:electrificationSection` covers multiple `netElements` (via `linearLocation/associatedNetElement`)
2. Each `railml:track` also covers multiple `netElements`
3. This SPARQL file links Tracks to ContactLineSystems when they share `netElements`
4. Result: `era:Track era:contactLineSystem era:ContactLineSystem` triples

**Architectural Pattern**: Same as TrainDetectionSystem, LoadingGaugeProfile, TrackGaugeProfile
- All are functional resources (NOT InfrastructureElements)
- All are referenced FROM Tracks or other infrastructure elements
- All use shared netElements as the linking basis in railML data

**URI Patterns**:
- ContactLineSystem: `functionalInfrastructure/contactLineSystems/{id}`
- Track: `functionalInfrastructure/tracks/{id}`
- RaisedPantographsDistanceAndSpeed: `functionalInfrastructure/raisedPantographsDistanceAndSpeed/{electrificationSectionId}`

**Mapping Notes**:
- **Architectural Pattern Discovery**: MCP queries revealed ContactLineSystem follows the "functional resource" pattern:
  - NOT a subclass of `era:InfrastructureElement`
  - Does NOT have `era:netReference` property
  - Referenced FROM `era:Track` via `era:contactLineSystem` property
  - Same pattern as TrainDetectionSystem, LoadingGaugeProfile, TrackGaugeProfile
- **Property Discovery**: Systematic MCP discovery found 10 total properties (3 Object, 7 Datatype)
  - 9 of 10 now mapped with available railML source data
  - 1 additional property documented as "available but unmapped" for future enhancement
- **Pantograph Spacing Requirements**: Use `era:trackRaisedPantographsDistanceAndSpeed` on Track (not ContactLineSystem)
  - Links to `era:RaisedPantographsDistanceAndSpeed` instances with number and distance properties
  - Avoids deprecated property and correctly associates spacing constraints with track infrastructure
- **Linking Mechanism**: Shared `netElements` between `railml:track` and `railml:electrificationSection`
  - Each ContactLineSystem resource represents one `railml:electrificationSection`
  - Tracks and electrification sections share netElement references
  - SPARQL WHERE clause joins on shared netElementRef values
  - Same join pattern creates Track → RaisedPantographsDistanceAndSpeed links
- **Data Type Conversions**:
  - Boolean to SKOS Concept: `allowsRegenerativeBraking` ("true"/"false" string) → regenerative-braking concepts
  - String to Boolean: `requiresPowerLimitation` ("true"/"false" string) → xsd:boolean
  - String to Integer: `maxCurrent`, `numberPantographsRaised`, `spacingPantographsRaised` → xsd:integer
  - Voltage+Frequency to SKOS Concept: `electrificationSystemRef` → `electrificationSystem` voltage/frequency → energy-supply-systems concepts
  - String to Double: `maxHeight`, `minHeight` → xsd:double
  - String to SKOS Concept: `compliantTSITypes` ("tsi1950"/"tsi2000_2260") → pantograph head concepts
- **Energy Supply System Mapping**: References shared `electrificationSystem` definitions from railML common section
  - `electrificationSystemRef` → `electrificationSystem` with voltage + frequency attributes
  - 25000V + 50Hz → AC10 concept (AC 25kV-50Hz)
  - 3000V + 0Hz → DC30 concept (DC 3kV)
  - Pattern follows railML best practice: shared infrastructure definitions in common section
- **Conditional Mapping**: `contactLineSystemType` uses OPTIONAL + FILTER EXISTS pattern
  - IF `fx:hasContactWire` child exists → concept 10 (OCL)
  - ELSE → concept 40 (Not electrified)
- **Aggregation Pattern**: `maxTrainCurrent` uses nested SELECT with MAX() aggregation
  - railML allows multiple maxTrainCurrent entries (different operation types/train types)
  - SPARQL takes maximum value across all entries for simplicity
- **Future Enhancement Opportunities**: Additional ERA properties available if source data becomes available:
  - `energySupplySystemTSICompliant` (requires TSI compliance flags)
  - `umax2` (requires voltage data for French network)
  - `conditionsChargingElectricEnergyStorage` (requires URI references)
  - `permissionChargingElectricEnergyTractionStandstill` (requires charging permission flags)
  - `conditionsAppliedRegenerativeBraking` (requires Document resource)
- ⚠️ **Workshop simplification**: All electrification sections assigned to infrastructure manager `organisations/0076_IM` (Belgian IM)

---

### 3.9 Bridges → `era:Bridge` (`09-bridges.sparql`)

**Source** (2-4 instances): `railml:overCrossing` with `xyz:constructionType="bridge"` OR `railml:underCrossing` with properties:
- `xyz:id` — unique identifier (e.g., `"bri586"`, `"bri200"`)
- `xyz:constructionType` — construction type (`"bridge"`)
- `fx:name` → child with `xyz:name`, `xyz:language` (optional) — bridge name
- `fx:areaLocation` → child containing linear extent positioning
  - `fx:associatedNetElement` — one or more segments
    - `xyz:netElementRef` — reference to `railml:netElement`
    - `xyz:posBegin`, `xyz:posEnd` — topological extent on netElement
    - `xyz:sequence` — segment ordering (optional, defaults to 1)
    - `fx:linearCoordinateBegin`, `fx:linearCoordinateEnd` — LRS coordinates (optional)
      - `xyz:measure` — position in meters
      - `xyz:positioningSystemRef` — reference to `railml:linearPositioningSystem`

**Target**: `era:Bridge` with linear extent positioning via `era:NetLinearReference`
- `rdfs:label` — bridge name (langString, optional)
- `era:inCountry` → `country:NOR` (Norway country code, maxCount=1)
- `era:infrastructureManager` → `era:OrganisationRole` (hardcoded to `organisations/0076_IM` for workshop)
- `era:netReference` → `era:NetLinearReference` (one per segment)

**SHACL Required Properties** (with dummy values for workshop):
- `era:existBridgeWindRestriction` → `false` (boolean, maxCount=1) — indicates if wind restrictions exist
- `era:maxbridgeWind` → `0` (integer, maxCount=1) — maximum wind speed (km/h), 0 when no restriction
- `era:existOpeningHoursLimitation` → `false` (boolean, maxCount=1) — indicates if opening hours are limited

**NetLinearReference structure** (linear extent positioning):
- `era:startsAt` → `era:NetPointReference` (start of extent)
- `era:endsAt` → `era:NetPointReference` (end of extent)

Each `era:NetPointReference` (start/end) has:
- `era:hasTopoCoordinate` → `era:TopologicalCoordinate`
  - `era:onLinearElement` → micro-level `era:LinearElement`
  - `era:offsetFromOrigin` — position on element (xsd:double)
- `era:hasLrsCoordinate` → `era:LinearPositioningSystemCoordinate` (if LRS coordinates available)
  - `era:kmPost` → `era:KilometricPost`
  - `era:offsetFromKilometricPost` — offset in meters (xsd:double)

Each `era:KilometricPost`:
- `era:hasLRS` → `era:LinearPositioningSystem`
- `era:kilometer` — km number (xsd:integer, rounded from measure)

**URI Patterns**:
- Bridge: `functionalInfrastructure/bridges/{id}`
- NetLinearReference: `topology/netLinearReferences/{bridgeId}_segment_{sequence}`
- NetPointReference (start/end): `topology/netPointReferences/{bridgeId}_segment_{sequence}_{start|end}`
- TopologicalCoordinate: `topology/topologicalCoordinates/{bridgeId}_{netElementId}_{position}`
- LinearPositioningSystemCoordinate: `topology/linearPositioningSystemCoordinates/{bridgeId}_segment_{sequence}_{start|end}_{posSystemRef}_{measure}`
- KilometricPost: `kilometricPosts/{posSystemRef}_km_{kmNumber}`

**Mapping Notes**:
- railML uses two different elements for bridges:
  - `railml:overCrossing` with `xyz:constructionType="bridge"` — bridge that crosses over the railway
  - `railml:underCrossing` with `xyz:constructionType="bridge"` — bridge that the railway crosses over
- Both types map to `era:Bridge` (difference is perspective, not structure type)
- Follows same dual positioning pattern as tracks and platform edges (topological + LRS coordinates)
- ⚠️ **Micro topology conversion**: Link to topology via `xyz:netElementRef`, resolving to micro-level LinearElements
- LRS coordinates from `linearCoordinateBegin/End` provide KilometricPost references (if available)
- Sequence defaults to "1" if not present in source data
- ⚠️ **Workshop simplification**: 
  - All bridges assigned to infrastructure manager `organisations/0076_IM` (Belgian IM)
  - SHACL required properties use conservative dummy values (no restrictions)
  - Production: Properties should be sourced from infrastructure documentation or field surveys

---

### 3.10 Tunnels → `era:Tunnel` (`10-tunnels.sparql`)

**Source** (0-2 instances): `railml:overCrossing` with `xyz:constructionType="tunnel"` with properties:
- `xyz:id` — unique identifier (e.g., `"tun199"`)
- `xyz:constructionType` — construction type (`"tunnel"`)
- `fx:name` → child with `xyz:name`, `xyz:language` (optional) — tunnel name
- `fx:areaLocation` → child containing linear extent positioning
  - `fx:associatedNetElement` — one or more segments
    - `xyz:netElementRef` — reference to `railml:netElement`
    - `xyz:posBegin`, `xyz:posEnd` — topological extent on netElement
    - `xyz:sequence` — segment ordering (optional, defaults to 1)
    - `fx:linearCoordinateBegin`, `fx:linearCoordinateEnd` — LRS coordinates (optional)
      - `xyz:measure` — position in meters
      - `xyz:positioningSystemRef` — reference to `railml:linearPositioningSystem`

**Target**: `era:Tunnel` with point-based start/end references
- `era:tunnelIdentification` — identifier string (**REQUIRED by SHACL minCount=1**)
- `rdfs:label` — tunnel name (langString, optional)
- `era:inCountry` → `country:NOR` (Norway country code, maxCount=1)
- `era:infrastructureManager` → `era:OrganisationRole` (hardcoded to `organisations/0076_IM` for workshop)
- `era:lineReferenceTunnelStart` → `era:NetPointReference` (tunnel entrance)
- `era:lineReferenceTunnelEnd` → `era:NetPointReference` (tunnel exit)

**Optional Properties** (included for workshop completeness with conservative defaults):
- `era:lengthOfTunnel` → calculated from start/end positions (double) — length in metres
- `era:complianceInfTsi` → `true` (boolean) — TSI compliance
- `era:crossSectionArea` → `50` (integer) — cross-section area in m²
- `era:dieselThermalAllowed` → `true` (boolean) — diesel thermal allowed
- `era:hasEmergencyPlan` → `true` (boolean)
- `era:hasEvacuationAndRescuePoints` → `true` (boolean)
- `era:hasWalkway` → `true` (boolean)
- `era:maxTunnelSpeed` → `120` (integer) — speed limit in km/h
- `era:nationalRollingStockFireCategory` → `"A"` (string) — national fire category
- `era:rollingStockFireCategory` → `concepts/rolling-stock-fire/10` (SKOS Concept) — Category A

**Note**: Only `era:tunnelIdentification` is required by SHACL (minCount=1). All other properties are optional but included in this workshop example to demonstrate common tunnel attributes.

**NetPointReference structure** (for tunnel start/end):
- `era:hasTopoCoordinate` → `era:TopologicalCoordinate`
  - `era:onLinearElement` → micro-level `era:LinearElement`
  - `era:offsetFromOrigin` — position on element (xsd:double)
- `era:hasLrsCoordinate` → `era:LinearPositioningSystemCoordinate` (if LRS coordinates available)
  - `era:kmPost` → `era:KilometricPost`
  - `era:offsetFromKilometricPost` — offset in meters (xsd:double)

Each `era:KilometricPost`:
- `era:hasLRS` → `era:LinearPositioningSystem`
- `era:kilometer` — km number (xsd:integer, rounded from measure)

**URI Patterns**:
- Tunnel: `functionalInfrastructure/tunnels/{id}`
- NetPointReference (start/end): `topology/netPointReferences/{tunnelId}_{start|end}`
- TopologicalCoordinate: `topology/topologicalCoordinates/{tunnelId}_{netElementId}_{position}`
- LinearPositioningSystemCoordinate: `topology/linearPositioningSystemCoordinates/{tunnelId}_{start|end}_{posSystemRef}_{measure}`
- KilometricPost: `kilometricPosts/{posSystemRef}_km_{kmNumber}`

**Mapping Notes**:
- railML represents tunnels as `railml:overCrossing` with `xyz:constructionType="tunnel"`
- ERA Tunnel uses `era:lineReferenceTunnelStart` and `era:lineReferenceTunnelEnd` (NetPointReference) instead of NetLinearReference
- Start/end points extracted from first/last segment in areaLocation:
  - Start: `posBegin` of first segment (sequence=1 or lowest)
  - End: `posEnd` of last segment (sequence=max or highest)
- Follows same dual positioning pattern as other infrastructure (topological + LRS coordinates)
- ⚠️ **Micro topology conversion**: Link to topology via `xyz:netElementRef`, resolving to micro-level LinearElements
- LRS coordinates from `linearCoordinateBegin/End` provide KilometricPost references (if available)
- `era:tunnelIdentification` uses the railML `xyz:id` value
- Length calculation: Distance between start and end TopologicalCoordinates (using offsets and element lengths)
- Start/end locations: Create GeoSPARQL Point geometries from TopologicalCoordinate positions (if visualization data available)
- Rolling stock fire category: Default to Category A (`concepts/rolling-stock-fire/10`) for workshop
- ⚠️ **Workshop simplification**: 
  - All tunnels assigned to infrastructure manager `organisations/0076_IM` (Belgian IM)
  - SHACL required properties use conservative dummy values (standard European tunnel specs)
  - Production: Properties must be sourced from tunnel safety documentation and infrastructure surveys

---

### 3.11 Level Crossings → `era:LevelCrossing` (`11-level-crossings.sparql`)

**Source** (1 instance): `railml:levelCrossingIS` with properties:
- `xyz:id` — unique identifier (e.g., `"lcr28"`)
- `fx:name` → child with `xyz:name`, `xyz:language` (optional) — level crossing name
- `fx:spotLocation` → positioning with `xyz:netElementRef`, `xyz:pos`, `xyz:applicationDirection` (optional)
  - `fx:linearCoordinate` → LRS coordinate (optional)
- `fx:linearLocation` → linear extent positioning (optional)
- `fx:crossesElement` → references to crossed infrastructure elements

**Target**: `era:LevelCrossing` with point positioning via `era:NetPointReference`
- `rdfs:label` — level crossing name (langString, optional)
- `era:inCountry` → `country:NOR` (Norway country code, maxCount=1)
- `era:infrastructureManager` → `era:OrganisationRole` (hardcoded to `organisations/0076_IM` for workshop)
- `era:netReference` → `era:NetPointReference` (topological positioning)

**SHACL Properties**: No additional required properties beyond inherited InfrastructureElement constraints

**NetPointReference structure**:
- `era:hasTopoCoordinate` → `era:TopologicalCoordinate`
  - `era:onLinearElement` → micro-level `era:LinearElement`
  - `era:offsetFromOrigin` — position on element (xsd:double)
- `era:hasLrsCoordinate` → `era:LinearPositioningSystemCoordinate` (if LRS coordinates available)
  - `era:kmPost` → `era:KilometricPost`
  - `era:offsetFromKilometricPost` — offset in meters (xsd:double)

Each `era:KilometricPost`:
- `era:hasLRS` → `era:LinearPositioningSystem`
- `era:kilometer` — km number (xsd:integer, rounded from measure)

**URI Patterns**:
- LevelCrossing: `functionalInfrastructure/levelCrossings/{id}`
- NetPointReference: `topology/netPointReferences/{levelCrossingId}_on_{netElementId}`
- TopologicalCoordinate: `topology/topologicalCoordinates/{levelCrossingId}_{netElementId}_{position}`
- LinearPositioningSystemCoordinate: `topology/linearPositioningSystemCoordinates/{levelCrossingId}_{positioningSystemRef}_{measure}`
- KilometricPost: `kilometricPosts/{posSystemRef}_km_{kmNumber}`

**Mapping Notes**:
- Level crossings are point-based infrastructure elements (use spotLocation for positioning)
- Follows same NetPointReference pattern as signals and switches (Section 3.5)
- Extract position from `fx:spotLocation/xyz:pos` and convert to `xsd:double`
- LRS coordinates from `fx:linearCoordinate` if available (same pattern as signals)
- ⚠️ **Micro topology only**: `xyz:netElementRef` must resolve to micro-level LinearElements
- ⚠️ **Workshop simplification**: All level crossings assigned to infrastructure manager `organisations/0076_IM` (Belgian IM)
- **Template pattern**: Uses the standard point-based infrastructure positioning model

---

### 3.12 ETCS → `era:ETCS` (`12-etcs.sparql`)

**Source** (4 instances): `railml:etcsArea` with properties:
- `xyz:id` — unique identifier (e.g., `"trp679"`, `"trp680"`, `"trp687"`, `"trp772"`)
- `xyz:mVersion` — ETCS system version / M_VERSION variable (e.g., `"33"`)
- `fx:name` → child element with:
  - `xyz:description` — ETCS level description (e.g., `"ETCS L2w/oS"`, `"ETCS L2wS"`)
  - `xyz:language` — language code (e.g., `"no"`)
- `fx:linearLocation` → linear extent positioning (coverage area)
  - `fx:associatedNetElement` — one or more netElement segments
    - `xyz:netElementRef` — reference to `railml:netElement`
    - `xyz:posBegin`, `xyz:posEnd` — topological extent on netElement
    - `fx:linearCoordinateBegin`, `fx:linearCoordinateEnd` — LRS coordinates

**Data Coverage** (discovered from railML XML):
- 4 ETCS areas covering different parts of the infrastructure
- 2 instances with "ETCS L2w/oS" (Level 2 without signaling): trp679, trp680
- 2 instances with "ETCS L2wS" (Level 2 with signaling): trp687, trp772
- All instances use M_VERSION 33
- Multiple netElement segments per area (3-14 segments each)

**Target**: `era:ETCS` (functional resource, NOT a subclass of `era:InfrastructureElement`)

**⚠️ CRITICAL Architecture Note**:
- `era:ETCS` is a **functional resource** (similar to `era:ContactLineSystem` in Section 3.8)
- ❌ Does NOT have `era:netReference` property (not positioned on topology)
- ✅ Referenced FROM `era:RunningTrack` via `era:etcs` property
- ✅ Linked to tracks via shared netElement references (same pattern as ContactLineSystem)

**Mapped Properties**:
- `era:etcsLevel` → SKOS Concept (ETCS level, REQUIRED)
  - **Mapped from** `fx:name/xyz:description` by parsing level designation:
    - Description contains `"L2"` → `concepts/etcs-levels/20` (ETCS Level 2)
    - Description contains `"L1"` → `concepts/etcs-levels/10` (ETCS Level 1)
    - Description contains `"L3"` → `concepts/etcs-levels/30` (ETCS Level 3)
    - **Default**: `concepts/etcs-levels/20` if parsing fails
  - **Note**: Parses level from text description rather than using separate level attribute
- `era:etcsSystemVersion` → xsd:integer (ETCS system version / M_VERSION)
  - **Mapped from** `xyz:mVersion` attribute
  - **Data conversion**: String to xsd:integer
- `rdfs:label` → xsd:string (human-readable label)
  - **Mapped from** `fx:name/xyz:description`
  - **Fallback**: Construct label from version if description unavailable: `"ETCS v{mVersion}"`
- `era:inCountry` → `country:NOR` (Norway country code)
- `era:infrastructureManager` → `era:OrganisationRole` (hardcoded to `organisations/0076_IM` for workshop)

**Track Linking Pattern** (via shared netElements):
- ETCS areas and tracks are linked via common `netElementRef` values
- Query pattern:
  1. Get `netElementRef` from ETCS area's `fx:linearLocation/fx:associatedNetElement`
  2. Find tracks with the same `netElementRef` in their `fx:linearLocation/fx:associatedNetElement`
  3. Create `era:etcs` property from matching track to ETCS instance
- **Filtering**: Only link to running tracks (`mainTrack`, `secondaryTrack`, `connectingTrack`)
- **Exclusion**: Do NOT link sidings to ETCS (sidings typically not equipped with ETCS)

**URI Patterns**:
- ETCS: `http://data.europa.eu/949/functionalInfrastructure/etcs/{id}`
- Track (referencing): `http://data.europa.eu/949/functionalInfrastructure/tracks/{id}`

**Linking Implementation**:
```sparql
# ETCS coverage area
?etcsArea fx:linearLocation/fx:associatedNetElement/xyz:netElementRef ?sharedNetElement .

# Track sharing same netElement
?track fx:linearLocation/fx:associatedNetElement/xyz:netElementRef ?sharedNetElement .
FILTER(?trackType IN ("mainTrack", "secondaryTrack", "connectingTrack"))

# Create link
?eraTrack era:etcs ?eraETCS .
```

**Mapping Notes**:
- Similar functional resource pattern to ContactLineSystem (Section 3.8) and TrainDetectionSystem (Section 3.6)
- ETCS level parsed from free-text description field (no structured level attribute in railML 3.2)
- Coverage areas typically span multiple netElements (similar to electrification sections)
- Each ETCS instance can be linked to multiple tracks (many-to-many relationship)
- Each track can reference multiple ETCS instances if covered by overlapping areas
- ⚠️ **Workshop limitation**: Level parsing relies on string matching ("L1", "L2", "L3" patterns)
- ⚠️ **Workshop simplification**: All ETCS instances assigned to infrastructure manager `organisations/0076_IM` (Belgian IM)

**Additional available properties** (from ERA ontology, not mapped in workshop):
- `era:etcsBaseline` — ETCS baseline version (e.g., 3.6.0)
- `era:etcsInfill` — ETCS infill type/coverage (SKOS concept)
- `era:etcsTransmitsTrackAheadFreeDistanceInformation` — boolean flag
- Additional ETCS system configuration properties

---

### 3.13 Sections of Line → `era:SectionOfLine` (`11-sections-of-line-*.sparql`)

**Source**: railML line elements with parent-child relationships

**Mapping Logic**:
- **Lines WITH `belongsToParent`** → `era:SectionOfLine` (actual sections)
  - Child lines represent actual railway sections between operational points
  - Example: `ls_ne_ml_294` with name "OGR-OXK" belongs to parent line `lin2`
- **Lines WITHOUT `belongsToParent`** → `era:nationalLine` property value (parent line identifier)
  - Top-level lines represent national line designations
  - Example: `lin2` with name "9333" provides the national line number for its child sections

**Operational Point Boundaries** (`era:opStart`, `era:opEnd`):
- Calculated from netRelations on the meso netElement
- Each line section has a linearLocation on a meso netElement
- That meso netElement has max 2 netRelations (one at each end)
- The other netElements in those netRelations are referenced in operational point areaLocations
- Position determines start vs. end:
  - `positionOnA/B="0"` (origin) → `era:opStart`
  - `positionOnA/B="1"` (end) → `era:opEnd`

**Example**:
```
Line: ls_ne_ml_294 (name "OGR-OXK")
  belongsToParent: lin2 (name "9333") → nationalLine = "9333"
  linearLocation: ne_ml_294 (meso element)
  
NetRelations on ne_ml_294:
  nr_ne_ml_294_ne_ms_375: elementA=ne_ml_294 (pos 0), elementB=ne_ms_375
    → ne_ms_375 in areaLocation of opp375 (Grestin, OGR)
    → opStart = opp375
    
  nr_ne_ml_294_ne_ml_471: elementA=ne_ml_294 (pos 1), elementB=ne_ml_471
    → ne_ml_471 connects to ne_ms_373
    → ne_ms_373 in areaLocation of opp373 (Kudowa, OXK)
    → opEnd = opp373
```

**Target**: `era:SectionOfLine`
- `era:infrastructureManager` → `era:Body`
- `era:inCountry` → `xsd:string` (country code)
- `era:solNature` → SKOS concept (default: `concepts/sol-natures/01` = "Line")
- `era:nationalLine` → `xsd:string` (from parent line name)
- `era:opStart` → `era:OperationalPoint` (calculated from netRelations)
- `era:opEnd` → `era:OperationalPoint` (calculated from netRelations)

**URI Pattern**: `http://data.europa.eu/949/functionalInfrastructure/sectionsOfLine/{id}`

**Mapping Notes**:
- Only child lines (with belongsToParent) become SectionOfLine resources
- Parent line names provide the nationalLine identifier
- ⚠️ **Workshop simplification**: Infrastructure manager hardcoded to Belgian IM (`0076_IM`)
- **⚠ Deprecated**: Do NOT use `era:NationalRailwayLine` (class) or `era:lineReference` (property)

---

## Linear Positioning System Architecture (Dual Positioning Model)

ERA infrastructure elements support **dual positioning**: both topology-based (via TopologicalCoordinate) and LRS-based (via LinearPositioningSystemCoordinate). This enables both topological queries ("find signals at position X on element Y") and linear referencing queries ("find signals at kilometer post 4.5").

### Linear Positioning System Resources (`02-linear-positioning-systems.sparql`)

**Source** (4 instances): `railml:linearPositioningSystem` with properties:
- `xyz:id` — unique identifier (e.g., `"LPS_8176"`, `"km"`)
- `xyz:name` — name/description
- `xyz:units` — measurement units (always `"m"` for metres)
- `fx:linearPositioningSystemRange` — valid range start/end values

**Target**: `era:LinearPositioningSystem`
- `dct:identifier` → `xsd:string` — the positioning system identifier (temporary)
- **Note**: `era:lineId` will be added later when lines are mapped (Phase 3, Section 3.11)

**URI Pattern**: `http://data.europa.eu/949/linearPositioningSystems/{id}`

**Systems in Dataset**:
- `km` — Default Linear Positioning System (450-53560m)
- `LPS_8176` — System 8176 (0-14000m)
- `LPS_9333` — System 9333 (-308-8203m)
- `LPS_2444` — System 2444 (52017-54417m)

**Mapping Notes**:
- Simple 1:1 mapping from railML positioning systems to ERA
- Creates shared resources referenced by KilometricPost instances
- All systems use metres as measurement units

### KilometricPost Inference Pattern

railML 3.2 does not explicitly define kilometer posts. They are **inferred** from linearCoordinate measure values used by infrastructure elements (signals, borders, etc.).

**Inference Logic**:
```sparql
# Get measure value from linearCoordinate (in metres)
?spotLoc fx:linearCoordinate ?linearCoord .
?linearCoord xyz:positioningSystemRef ?positioningSystemRef ;
             xyz:measure ?measureStr .

# Calculate KP number and offset
BIND (xsd:double(?measureStr) AS ?measure)
BIND (ROUND(?measure / 1000.0) AS ?kmNumber)
BIND ((?measure - (?kmNumber * 1000.0)) AS ?kmOffset)
```

**Example Calculation**:
- Input: `measure = 4401.0` metres (signal sig812)
- KP number: `ROUND(4401.0 / 1000.0) = 4.0`
- Offset: `4401.0 - (4.0 * 1000.0) = 401.0` metres (401m after KP 4)

**Shared Resource Pattern**:
- One `era:KilometricPost` resource per positioning system + kilometer combination
- URI: `kilometricPosts/{positioningSystemRef}_km_{kmNumber}`
- Example: `kilometricPosts/LPS_8176_km_4` is shared by all elements at KP 4 on system LPS_8176
- Multiple elements (signals, borders) reference the same KilometricPost URI

**KilometricPost Structure**:
```sparql
?kmPost a era:KilometricPost ;
        era:hasLRS ?eraLPS ;
        era:kilometer ?kmNumber .
```

Where:
- `?eraLPS` → `era:LinearPositioningSystem` (e.g., `linearPositioningSystems/LPS_8176`)
- `?kmNumber` → `xsd:double` (e.g., `4.0`)

**Distribution** (in advanced example dataset):
- 16 unique KilometricPost resources created
- Most-used: `LPS_8176_km_4` (shared by 8 elements)
- Range: KP 0 to KP 54 across different positioning systems

### LinearPositioningSystemCoordinate Pattern

For each infrastructure element with a linearCoordinate, create a **unique** `era:LinearPositioningSystemCoordinate` that links to the (shared) KilometricPost and specifies the offset.

**Structure**:
```sparql
# In CONSTRUCT clause (for signals, borders, etc.):
?netPointRef era:hasLrsCoordinate ?lrsCoord .

?lrsCoord a era:LinearPositioningSystemCoordinate ;
          era:kmPost ?kmPost ;
          era:offsetFromKilometricPost ?kmOffset .
```

**URI Pattern**: `linearPositioningSystemCoordinates/{elementId}_{positioningSystemRef}_{measure}`
- Example: `linearPositioningSystemCoordinates/sig812_LPS_8176_4401.0`
- Unique per element, positioning system, and measure value
- Multiple elements can reference the same KilometricPost but have different LRS coordinates

**WHERE Clause** (extraction from railML):
```sparql
# Get linear coordinate for LRS positioning
OPTIONAL {
  ?spotLoc fx:linearCoordinate ?linearCoord .
  
  ?linearCoord xyz:positioningSystemRef ?positioningSystemRef ;
               xyz:measure ?measureStr .
  
  # Convert and calculate
  BIND (xsd:double(?measureStr) AS ?measure)
  BIND (ROUND(?measure / 1000.0) AS ?kmNumber)
  BIND ((?measure - (?kmNumber * 1000.0)) AS ?kmOffset)
  
  # Mint URIs
  BIND (IRI(CONCAT("http://data.europa.eu/949/linearPositioningSystemCoordinates/", 
                   ?elementId, "_", ?positioningSystemRef, "_", STR(?measure))) AS ?lrsCoord)
  
  BIND (IRI(CONCAT("http://data.europa.eu/949/kilometricPosts/", 
                   ?positioningSystemRef, "_km_", STR(?kmNumber))) AS ?kmPost)
  
  BIND (IRI(CONCAT("http://data.europa.eu/949/linearPositioningSystems/", 
                   ?positioningSystemRef)) AS ?eraLPS)
}
```

### Dual Positioning Model — Complete Pattern

For point-based infrastructure elements (signals, borders, switches, train detection elements, buffer stops):

**Complete Structure**:
```
Element (e.g., era:Signal)
  ├─ era:netReference → NetPointReference
      ├─ era:hasTopoCoordinate → TopologicalCoordinate (topology-based)
      │   ├─ era:onLinearElement → LinearElement
      │   └─ era:offsetFromOrigin → xsd:double
      └─ era:hasLrsCoordinate → LinearPositioningSystemCoordinate (LRS-based)
          ├─ era:kmPost → KilometricPost (shared)
          │   ├─ era:hasLRS → LinearPositioningSystem (shared)
          │   └─ era:kilometer → xsd:double
          └─ era:offsetFromKilometricPost → xsd:double
```

**Dual Coordinate Example** (signal sig812):
```turtle
# Signal
signals/sig812 a era:Signal ;
               era:netReference netPointReferences/sig812_on_ne_126 .

# NetPointReference (connects both positioning methods)
netPointReferences/sig812_on_ne_126 a era:NetPointReference ;
                                     era:hasTopoCoordinate topoCoord/sig812_ne_126_400.0 ;
                                     era:hasLrsCoordinate lrsCoord/sig812_LPS_8176_4401.0 .

# Topological Coordinate
topoCoord/sig812_ne_126_400.0 a era:TopologicalCoordinate ;
                               era:onLinearElement netElements/ne_126 ;
                               era:offsetFromOrigin 400.0 .

# LRS Coordinate (unique)
lrsCoord/sig812_LPS_8176_4401.0 a era:LinearPositioningSystemCoordinate ;
                                 era:kmPost kilometricPosts/LPS_8176_km_4 ;
                                 era:offsetFromKilometricPost 401.0 .

# KilometricPost (shared by multiple signals)
kilometricPosts/LPS_8176_km_4 a era:KilometricPost ;
                               era:hasLRS linearPositioningSystems/LPS_8176 ;
                               era:kilometer 4.0 .

# LinearPositioningSystem (shared by all elements on this system)
linearPositioningSystems/LPS_8176 a era:LinearPositioningSystem ;
                                   dct:identifier "LPS_8176" .
```

**Benefits**:
- **Topological queries**: "Find signals on netElement ne_126 between offset 0-500m"
- **LRS queries**: "Find signals between KP 4 and KP 5"
- **Cross-validation**: Compare topology-based and LRS-based positions for consistency
- **Flexible referencing**: Support both engineering (topology) and operational (LRS) use cases
- **Standard compliance**: Matches ERA ontology's dual positioning capability

**Implementation Queries**:
- `01-common/02-linear-positioning-systems.sparql` — creates LinearPositioningSystem resources
- `03-functional-infrastructure/05-signals.sparql` — creates dual coordinates for signals

**Coverage** (in advanced example dataset):
- 4 LinearPositioningSystem resources
- 16 KilometricPost resources (shared)
- 45 LinearPositioningSystemCoordinate resources (unique)
- 45 NetPointReference resources (all have both topology and LRS coordinates)

---

## Implementation Order

1. **Phase 1 first** — common/organization provides infrastructure manager URIs referenced elsewhere
2. **Phase 2 next** — all other phases depend on the `era:NetElement` URI scheme for topology links
3. **Phase 3 last** — functional infrastructure elements reference topology and organization URIs from phases 1–2

## Cross-Cutting Concerns

- **Reference Dereferencing Pattern**: Every query that follows a `xyz:ref` must include a lookup sub-pattern:
  ```sparql
  ?child xyz:ref ?refValue .
  ?target xyz:id ?refValue .
  ```
  Then mint the target URI from `?refValue`.

- **Name Extraction Pattern**:
  ```sparql
  ?entity fx:name ?nameNode .
  ?nameNode xyz:name ?nameValue .
  ?nameNode xyz:language ?lang .
  ```

- **SpotLocation Pattern** (topology linking) — ⚠️ **Micro Topology Only**:
  ```sparql
  ?entity fx:spotLocation ?loc .
  ?loc xyz:netElementRef ?neRef .
  ?loc xyz:pos ?position .
  ?loc xyz:applicationDirection ?dir .
  ```
  Then dereference `?neRef` to mint the `era:NetElement` URI.
  
  **Critical**: If `?neRef` references a meso/macro element (e.g., `"ne_ml_163"`), you must:
  1. Identify which micro-level element(s) the position maps to by traversing `fx:elementCollectionUnordered` → `fx:elementPart`
  2. Calculate the relative position on the micro element
  3. Use the micro element's URI instead
  
  **Filter**: Ensure `?neRef` only resolves to netElements that have `xyz:length` (micro level)

- **NetPointReference Pattern** (precise topological positioning for point-based infrastructure):
  
  For infrastructure elements positioned at specific points (signals, switches, train detection elements, buffer stops, borders, etc.), use the standard ERA pattern: `Element → NetPointReference → TopologicalCoordinate → LinearElement`
  
  ```sparql
  # In CONSTRUCT clause:
  ?element era:netReference ?netPointRef .
  
  ?netPointRef a era:NetPointReference ;
               era:appliesToDirection ?orientation ;
               era:hasTopoCoordinate ?topoCoord .
  
  ?topoCoord a era:TopologicalCoordinate ;
             era:onLinearElement ?linearElement ;
             era:offsetFromOrigin ?posDouble .
  
  # In WHERE clause:
  ?element fx:spotLocation ?spotLoc .
  ?spotLoc xyz:netElementRef ?neRef ;
           xyz:pos ?posStr ;
           xyz:applicationDirection ?appDirection .
  
  # Convert position to double
  BIND (xsd:double(?posStr) AS ?posDouble)
  
  # Map orientation to SKOS concept
  BIND (IF(?appDirection = "normal", IRI("http://data.europa.eu/949/concepts/orientations/00"),
        IF(?appDirection = "reverse", IRI("http://data.europa.eu/949/concepts/orientations/01"),
        IF(?appDirection = "both", IRI("http://data.europa.eu/949/concepts/orientations/02"),
        ?unbound))) AS ?orientation)
  
  # Mint URIs
  BIND (IRI(CONCAT("http://data.europa.eu/949/topology/netElements/", ?neRef)) AS ?linearElement)
  BIND (IRI(CONCAT("http://data.europa.eu/949/topology/netPointReferences/", 
                   ?elementId, "_on_", ?neRef)) AS ?netPointRef)
  BIND (IRI(CONCAT("http://data.europa.eu/949/topology/topologicalCoordinates/", 
                   ?elementId, "_", ?neRef, "_", STR(?posDouble))) AS ?topoCoord)
  ```
  
  **Benefits**:
  - Enables precise spatial queries by position
  - Supports distance calculations
  - Provides direction context for operational logic
  - Allows multiple elements to share the same topological coordinate
  - Follows ERA's standardized infrastructure positioning model
  
  **⚠️ Note**: Use `era:netReference` to link infrastructure elements to NetPointReference (not deprecated properties)

- **Functional Resource Linking Pattern** (for non-InfrastructureElement resources):
  
  Some ERA classes represent **functional resources** that are NOT subclasses of `era:InfrastructureElement` and thus do NOT have `era:netReference`. These include:
  - `era:ContactLineSystem` (electrification)
  - `era:TrainDetectionSystem` (train detection)
  - `era:LoadingGaugeProfile` (loading gauges)
  - `era:TrackGaugeProfile` (track gauges)
  
  **Linking pattern**: `era:Track` (or other InfrastructureElement) references the functional resource
  - Example: `?track era:contactLineSystem ?contactLineSystem`
  - Example: `?track era:trainDetection ?trainDetectionSystem`
  - Example: `?track era:gaugingProfile ?loadingGaugeProfile`
  - Example: `?track era:wheelSetGauge ?trackGaugeProfile`
  
  **Implementation approach** (when railML elements share netElements):
  ```sparql
  # CONSTRUCT the functional resource + link from Track
  ?contactLineSystem a era:ContactLineSystem ; era:contactLineSystemType ?concept .
  ?track era:contactLineSystem ?contactLineSystem .
  
  # WHERE: join via shared netElements
  ?railmlTrack a railml:track ;
               fx:linearLocation/fx:associatedNetElement/xyz:netElementRef ?sharedNetElement .
  
  ?railmlElectrificationSection a railml:electrificationSection ;
                                 fx:linearLocation/fx:associatedNetElement/xyz:netElementRef ?sharedNetElement .
  ```
  
  **Discovery via MCP**:
  1. Query for properties with the functional resource as range: `?property rdfs:range era:ContactLineSystem`
  2. Examine SHACL shapes to find which classes have the property (e.g., `sh:path era:contactLineSystem`)
  3. Typically find the property on `era:Track`, `era:RunningTrack`, or similar InfrastructureElement subclasses
  
  **⚠️ Critical**: Do NOT give functional resources a `era:netReference` — they are referenced, not referencing

- **LinearLocation Pattern** (extent on topology) — ⚠️ **Micro Topology Only**:
  ```sparql
  ?entity fx:linearLocation ?linLoc .
  ?linLoc fx:associatedNetElement ?aneNode .
  ?aneNode xyz:netElementRef ?neRef .
  ?aneNode xyz:applicationDirection ?dir .
  ```
  Same conversion rule applies: resolve meso/macro references to constituent micro elements.
  
  For linear extents spanning multiple micro elements, you may need to create multiple mappings or compute the aggregate extent across micro elements.

- **Geometry Pattern** (WKT coordinates for spatial queries):
  
  All ERA infrastructure elements are subclasses of `era:Feature` and thus `gsp:Feature` (GeoSPARQL).
  Elements should include `gsp:hasGeometry` links to geometry objects containing `gsp:asWKT` WKT strings.
  
  **Source**: Geometry data comes from `railml:infrastructureVisualization/linearElementProjection`:
  - Each projection has `xyz:refersToElement` pointing to a track or platformEdge ID
  - Coordinates are in `fx:coordinate` children with `xyz:x` and `xyz:y` attributes
  - Original coordinates are local (x: 44-544, y: 50-190)
  
  **Coverage**:
  - 36 tracks have visualizations
  - 13 platformEdges have visualizations
  - 54 netElements have visualizations (inherited from their associated track)
  - Other netElements (89 out of 143) have no visualization data
  
  **Transformation**:
  - Coordinates are transformed to WGS84 lat/lon in the North Sea region (for demo purposes)
  - Simple linear mapping: lon = 3 + x/10000, lat = 53 + y/10000
  - Results in coordinates around 3-3.05°E, 53-53.02°N (North Sea)
  
  **URI Pattern**: Geometry URIs use actual coordinate values: `http://data.europa.eu/949/geometry/{lon}/{lat}`
  - Example: `http://data.europa.eu/949/geometry/3.052e0/53.007e0`
  - Each unique coordinate point gets a unique geometry URI
  - Multiple features can reference the same geometry URI if they share a coordinate
  
  **Pattern for tracks/platformEdges** (direct mapping with LINESTRING aggregation):
  ```sparql
  # In CONSTRUCT clause (separate triple patterns):
  ?element gsp:hasGeometry ?geometry .
  ?geometry a gsp:Geometry .
  ?geometry gsp:asWKT ?wkt .
  
  # In WHERE clause:
  OPTIONAL {
    ?viz a railml:infrastructureVisualization .
    ?viz fx:linearElementProjection ?proj .
    ?proj xyz:refersToElement ?elementId .  # matches track or platformEdge ID
    
    {
      SELECT ?elementId (GROUP_CONCAT(?coordPair; separator=",") AS ?coordString)
      WHERE {
        ?viz fx:linearElementProjection ?proj .
        ?proj xyz:refersToElement ?elementId .
        ?proj fx:coordinate ?coord .
        ?coord xyz:x ?x ; xyz:y ?y .
        
        BIND (3.0 + (xsd:decimal(?x) / 10000.0) AS ?lon)
        BIND (53.0 + (xsd:decimal(?y) / 10000.0) AS ?lat)
        BIND (CONCAT(STR(?lon), " ", STR(?lat)) AS ?coordPair)
      }
      GROUP BY ?elementId
    }
    
    # Calculate representative coordinate for geometry URI (e.g., first point)
    ?proj fx:coordinate ?firstCoord .
    ?firstCoord xyz:x ?firstX ; xyz:y ?firstY .
    BIND (3.0 + (xsd:decimal(?firstX) / 10000.0) AS ?lon)
    BIND (53.0 + (xsd:decimal(?firstY) / 10000.0) AS ?lat)
    
    # Mint geometry URI using coordinate values
    BIND (IRI(CONCAT("http://data.europa.eu/949/geometry/", STR(?lon), "/", STR(?lat))) AS ?geometry)
    BIND (STRDT(CONCAT("<http://www.opengis.net/def/crs/OGC/1.3/CRS84> LINESTRING(", 
                       ?coordString, ")"), gsp:wktLiteral) AS ?wkt)
  }
  ```
  
  **Simplified pattern for multiple POINTs** (used for netElements):
  ```sparql
  # In CONSTRUCT clause (separate triple patterns to avoid filtering):
  ?element gsp:hasGeometry ?geometry .
  ?geometry a gsp:Geometry .
  ?geometry gsp:asWKT ?wkt .
  
  # In WHERE clause - creates one POINT per coordinate vertex:
  OPTIONAL {
    # ... locate visualization data ...
    
    ?proj fx:coordinate ?coord .
    ?coord xyz:x ?x ; xyz:y ?y .
    
    # Transform to WGS84 (use decimal to avoid scientific notation)
    BIND (3.0 + (xsd:decimal(?x) / 10000.0) AS ?lon)
    BIND (53.0 + (xsd:decimal(?y) / 10000.0) AS ?lat)
    
    # Mint geometry URI using actual coordinate values
    BIND (IRI(CONCAT("http://data.europa.eu/949/geometry/", STR(?lon), "/", STR(?lat))) AS ?geometry)
    
    # Create WKT POINT for this coordinate
    BIND (STRDT(CONCAT("<http://www.opengis.net/def/crs/OGC/1.3/CRS84> POINT(", STR(?lon), " ", STR(?lat), ")"), 
                gsp:wktLiteral) AS ?wkt)
  }
  # This creates multiple geometry triples - one POINT per coordinate vertex
  ```
  
  **Pattern for netElements** (via intrinsicCoordinate and spotElementProjection):
  ```sparql
  # NetElements access geometry through their intrinsicCoordinate IDs
  # Uses nested SELECT to aggregate coordinates into LINESTRING
  
  # In WHERE clause OPTIONAL block:
  OPTIONAL {
    {
      SELECT ?netElementId 
             (GROUP_CONCAT(?coordPair; separator=", ") AS ?coordString)
             (SAMPLE(?firstLon) AS ?lon)
             (SAMPLE(?firstLat) AS ?lat)
      WHERE {
        # Get intrinsicCoordinate IDs for this netElement
        ?ne2 a railml:netElement ;
             xyz:id ?netElementId .
        ?ne2 fx:associatedPositioningSystem ?aps .
        ?aps fx:intrinsicCoordinate ?ic .
        ?ic xyz:id ?icId .
        
        # Find spotElementProjection that references this intrinsicCoordinate
        ?viz a railml:infrastructureVisualization .
        ?viz fx:spotElementProjection ?sep .
        ?sep xyz:refersToElement ?icId .
        ?sep fx:coordinate ?coord .
        ?coord xyz:x ?x ; xyz:y ?y .
        
        # Transform to WGS84 (use decimal to avoid scientific notation)
        BIND (3.0 + (xsd:decimal(?x) / 10000.0) AS ?coordLon)
        BIND (53.0 + (xsd:decimal(?y) / 10000.0) AS ?coordLat)
        
        # Store first coordinate for geometry URI
        BIND (?coordLon AS ?firstLon)
        BIND (?coordLat AS ?firstLat)
        
        # Create coordinate pair string
        BIND (CONCAT(STR(?coordLon), " ", STR(?coordLat)) AS ?coordPair)
      }
      GROUP BY ?netElementId
    }
    
    # Mint geometry URI using first coordinate values
    BIND (IRI(CONCAT("http://data.europa.eu/949/geometry/", STR(?lon), "/", STR(?lat))) AS ?geometry)
    
    # Create WKT LINESTRING from aggregated coordinates
    BIND (STRDT(CONCAT("<http://www.opengis.net/def/crs/OGC/1.3/CRS84> LINESTRING(", ?coordString, ")"), 
                gsp:wktLiteral) AS ?wkt)
  }
  ```
