# Patches applied to the railML Advanced Example

This document describes the changes that [patch-railml.py](patch-railml.py) applies to the original
`2025-11-03_railML_AdvancedExample_v14_railML3.2.xml` to produce
`2025-11-03_railML_AdvancedExample_v14_railML3.2_patched.xml`.

All changes are purely additive (except item 7, which removes one line). None of the original IDs,
structure, or formatting are altered. The additions fill in detail that the ERA ontology requires for
a complete conversion — specifically around electrification, loading gauges, track gauge, platform
heights, and tunnel length.

---

## 1. Add `<electrificationSystems>` to `<common>`

Two system definitions are inserted before `<organizationalUnits>` in `<common>`:

```xml
<electrificationSystems>
  <electrificationSystem frequency="50" id="els_ac25kv50hz" voltage="25000"/>
  <electrificationSystem frequency="0"  id="els_dc3kv"       voltage="3000"/>
</electrificationSystems>
```

These define AC 25 kV / 50 Hz and DC 3 kV as named systems that can be referenced from individual
sections.

---

## 2. Enrich 7 `<electrificationSection>` elements with detailed child elements

For each of the 7 sections listed below, a set of child elements is inserted before the closing
`</electrificationSection>` tag. The child elements vary per section but can include:

| Child element | Example attributes |
|---|---|
| `<electrificationSystemRef>` | `ref="els_ac25kv50hz"` |
| `<energyCatenary>` | `allowsRegenerativeBraking="true"` + nested `<maxTrainCurrent>` |
| `<energyPantograph>` | `compliantTSITypes`, `contactStripMaterials`, `requiresTSIcompliance` |
| `<energyRollingstock>` | `permittedMaxContactForce`, `requiredFireCategory`, `requiresAutomaticDroppingDevice`, … |
| `<etcsElectrification>` | `nid_ctraction` |
| `<hasContactWire>` | `minHeight`, `maxHeight`, `maxDisplacement` |
| `<pantographSpacing>` | `numberPantographsRaised`, `spacingPantographsRaised`, `speed4PantographSpacing` |
| `<phaseSeparationSection>` | `lengthPhaseSeparation`, `lowerPantograph`, `switchOffBreaker` |
| `<systemSeparationSection>` | `isSupplySystemChange`, `lengthSystemSeparation`, … |

Sections enriched: `elc8`, `elc46`, `elc439`, `elc440`, `elc442`, `elc732`, `elc877`.

Example for `elc8` (AC 25 kV section with full detail):

```xml
<electrificationSystemRef ref="els_ac25kv50hz"/>
<energyCatenary allowsRegenerativeBraking="true">
  <maxTrainCurrent maxCurrent="300" operationType="0" trainType="all" validFor="0"/>
  <maxTrainCurrent maxCurrent="250" operationType="1" trainType="passenger" validFor="0"/>
</energyCatenary>
<energyPantograph compliantTSITypes="tsi1950" contactStripMaterials="plainCarbon" requiresTSIcompliance="true"/>
<energyRollingstock permittedMaxContactForce="300" permittedStaticContactForce="120" requiredFireCategory="A"
    requiresAutomaticDroppingDevice="true" requiresPowerLimitation="false"/>
<etcsElectrification nid_ctraction="25000"/>
<hasContactWire maxDisplacement="0.5" maxHeight="6.5" minHeight="5.0"/>
<pantographSpacing numberPantographsRaised="1" spacingPantographsRaised="200" speed4PantographSpacing="160"/>
<phaseSeparationSection lengthPhaseSeparation="20" lowerPantograph="true" switchOffBreaker="true"/>
<systemSeparationSection isSupplySystemChange="false" lengthSystemSeparation="15" lowerPantograph="false" switchOffBreaker="false"/>
```

---

## 3. Add `<loadingGauges>` section to `functionalInfrastructure`

A new `<loadingGauges>` block is inserted before `<operationalPoints>`. It defines 5 loading gauges
with linear locations (network element references and kilometre positions) and kinematic/static
profiles:

| ID | Code | Kinematic h × w | Net elements |
|---|---|---|---|
| `lg_ga1` | GA | 4.20 × 3.15 m | ne_1, ne_55, ne_16 |
| `lg_gb1` | GB | 4.28 × 3.25 m | ne_39 |
| `lg_gc1` | GC | 4.70 × 3.40 m | ne_561 |
| `lg_g1`  | G1 | 4.65 × 3.35 m | ne_565 |
| `lg_gb1_multi` | GB1 | 4.50 × 3.30 m | ne_77 |

---

## 4. Add `<length>` to tunnel `tun199`

A physical length element is inserted inside the `<overCrossing>` element `tun199`:

```xml
<length type="physical" value="2300" />
```

---

## 5. Add `height` attribute to 8 `<platformEdge>` elements

A `height` attribute (platform edge height above rail top, in metres) is added to 8 platform edges:

| ID | Height (m) |
|---|---|
| `ple193`, `ple194` | 0.55 |
| `ple391`, `ple392` | 0.55 |
| `ple388`, `ple390` | 0.76 |
| `ple428`, `ple429` | 0.76 |

Example — before:
```xml
<platformEdge id="ple193" ...>
```
After:
```xml
<platformEdge height="0.55" id="ple193" ...>
```

---

## 6. Add `<trackGauges>` section to `functionalInfrastructure`

Inserted before `<trainDetectionElements>`, a single network-wide standard gauge definition:

```xml
<trackGauges>
  <trackGauge id="tg_standard_network" value="1.435">
    <name description="Standard gauge 1435mm - network wide" language="en" name="Standard Gauge"/>
    <networkLocation networkRef="nw01"/>
  </trackGauge>
</trackGauges>
```

---

## 7. Remove one `<designator>` line

The following line is removed entirely:

```xml
<designator entry="OXB" register="_railML"/>
```

This suppresses a designator so that not two opid's are created in the ERA ontology.
