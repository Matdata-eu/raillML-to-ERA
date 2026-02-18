"""Patch railML XML to add workshop content.

Reads the clean railML 3.2 Advanced Example XML (as downloaded from railml.org)
and produces a patched version with additional properties needed to demonstrate
the full ERA ontology conversion pipeline.

Uses string-based patching to preserve original XML formatting, comments,
and attribute ordering.

Additions applied:
- electrificationSystems definitions in <common>
- Detailed child elements on select <electrificationSection> elements
- <loadingGauges> section in functionalInfrastructure
- <length> on overCrossing tun199
- height attribute on select <platformEdge> elements
- <trackGauges> section in functionalInfrastructure
"""

import re

SOURCE = "2025-11-03_railML_AdvancedExample_v14_railML3.2.xml"
OUTPUT = "2025-11-03_railML_AdvancedExample_v14_railML3.2_patched.xml"


def indent_xml(xml: str, base: int) -> str:
    """Indent each line of xml by `base` spaces.
    Assumes input uses 0-based indent with 2-space nesting."""
    prefix = " " * base
    return "\n".join(prefix + line for line in xml.strip().split("\n"))


# ---------------------------------------------------------------------------
# 1. Electrification systems (before <organizationalUnits> in <common>)
# ---------------------------------------------------------------------------
ELECTRIFICATION_SYSTEMS = """\
    <electrificationSystems>
      <electrificationSystem frequency="50" id="els_ac25kv50hz" voltage="25000"/>
      <electrificationSystem frequency="0" id="els_dc3kv" voltage="3000"/>
    </electrificationSystems>
"""

# ---------------------------------------------------------------------------
# 2. Electrification section enrichments
#    Raw XML at 0-indent, re-indented to 10 spaces at insertion time
# ---------------------------------------------------------------------------
SECTION_ENRICHMENTS_RAW = {
    "elc8": """\
<electrificationSystemRef ref="els_ac25kv50hz"/>
<energyCatenary allowsRegenerativeBraking="true">
  <maxTrainCurrent maxCurrent="300" operationType="0" trainType="all" validFor="0"/>
  <maxTrainCurrent maxCurrent="250" operationType="1" trainType="passenger" validFor="0"/>
</energyCatenary>
<energyPantograph compliantTSITypes="tsi1950" contactStripMaterials="plainCarbon" requiresTSIcompliance="true"/>
<energyRollingstock permittedMaxContactForce="300" permittedStaticContactForce="120" requiredFireCategory="A" requiresAutomaticDroppingDevice="true" requiresPowerLimitation="false"/>
<etcsElectrification nid_ctraction="25000"/>
<hasContactWire maxDisplacement="0.5" maxHeight="6.5" minHeight="5.0"/>
<pantographSpacing numberPantographsRaised="1" spacingPantographsRaised="200" speed4PantographSpacing="160"/>
<phaseSeparationSection lengthPhaseSeparation="20" lowerPantograph="true" switchOffBreaker="true"/>
<systemSeparationSection isSupplySystemChange="false" lengthSystemSeparation="15" lowerPantograph="false" switchOffBreaker="false"/>""",

    "elc46": """\
<electrificationSystemRef ref="els_ac25kv50hz"/>
<energyCatenary allowsRegenerativeBraking="false">
  <maxTrainCurrent maxCurrent="200" operationType="0" trainType="freight" validFor="1"/>
</energyCatenary>
<energyPantograph compliantTSITypes="tsi2000_2260" contactStripMaterials="copperAlloy" requiresTSIcompliance="false"/>
<energyRollingstock permittedMaxContactForce="250" permittedStaticContactForce="100" requiredFireCategory="A" requiresAutomaticDroppingDevice="false" requiresPowerLimitation="true"/>
<hasContactWire maxDisplacement="0.4" maxHeight="6.2" minHeight="4.8"/>
<pantographSpacing numberPantographsRaised="2" spacingPantographsRaised="400" speed4PantographSpacing="120"/>""",

    "elc439": """\
<electrificationSystemRef ref="els_dc3kv"/>
<energyCatenary allowsRegenerativeBraking="true">
  <maxTrainCurrent maxCurrent="2000" operationType="0" trainType="all" validFor="0"/>
  <maxTrainCurrent maxCurrent="1500" operationType="1" trainType="freight" validFor="0"/>
</energyCatenary>
<energyPantograph compliantTSITypes="tsi1600" contactStripMaterials="plainCarbon" requiresTSIcompliance="true"/>
<energyRollingstock permittedMaxContactForce="350" permittedStaticContactForce="140" requiredFireCategory="A" requiresAutomaticDroppingDevice="true" requiresPowerLimitation="false"/>
<etcsElectrification nid_ctraction="3000"/>
<hasContactWire maxDisplacement="0.6" maxHeight="6.0" minHeight="4.5"/>
<pantographSpacing numberPantographsRaised="1" spacingPantographsRaised="200" speed4PantographSpacing="140"/>""",

    "elc440": """\
<electrificationSystemRef ref="els_dc3kv"/>
<energyCatenary allowsRegenerativeBraking="true">
  <maxTrainCurrent maxCurrent="2000" operationType="0" trainType="passenger" validFor="0"/>
  <maxTrainCurrent maxCurrent="1500" operationType="1" trainType="highspeed" validFor="0"/>
</energyCatenary>
<energyPantograph compliantTSITypes="tsi1950" contactStripMaterials="impregnatedCarbon" requiresTSIcompliance="true"/>
<energyRollingstock permittedMaxContactForce="350" permittedStaticContactForce="140" requiredFireCategory="A" requiresAutomaticDroppingDevice="true" requiresPowerLimitation="false"/>
<etcsElectrification nid_ctraction="3000"/>
<hasContactWire maxDisplacement="0.6" maxHeight="6.0" minHeight="4.5"/>
<pantographSpacing numberPantographsRaised="1" spacingPantographsRaised="200" speed4PantographSpacing="140"/>
<phaseSeparationSection lengthPhaseSeparation="25" lowerPantograph="true" switchOffBreaker="true"/>""",

    "elc442": """\
<electrificationSystemRef ref="els_ac25kv50hz"/>
<energyCatenary allowsRegenerativeBraking="true">
  <maxTrainCurrent maxCurrent="320" operationType="0" trainType="highspeed" validFor="0"/>
  <maxTrainCurrent maxCurrent="280" operationType="1" trainType="passenger" validFor="0"/>
</energyCatenary>
<energyPantograph compliantTSITypes="tsi2000_2260" contactStripMaterials="copperCladCarbon" requiresTSIcompliance="true"/>
<energyRollingstock permittedMaxContactForce="320" permittedStaticContactForce="130" requiredFireCategory="A" requiresAutomaticDroppingDevice="true" requiresPowerLimitation="false"/>
<etcsElectrification nid_ctraction="25000"/>
<hasContactWire maxDisplacement="0.55" maxHeight="6.5" minHeight="5.2"/>
<pantographSpacing numberPantographsRaised="1" spacingPantographsRaised="200" speed4PantographSpacing="200"/>
<systemSeparationSection isSupplySystemChange="true" lengthSystemSeparation="30" lowerPantograph="true" switchOffBreaker="true"/>""",

    "elc732": """\
<electrificationSystemRef ref="els_ac25kv50hz"/>
<energyCatenary allowsRegenerativeBraking="true">
  <maxTrainCurrent maxCurrent="300" operationType="0" trainType="all" validFor="0"/>
  <maxTrainCurrent maxCurrent="260" operationType="1" trainType="passenger" validFor="1"/>
</energyCatenary>
<energyPantograph compliantTSITypes="tsi1950" contactStripMaterials="carbonCladdedCopper" requiresTSIcompliance="true"/>
<energyRollingstock permittedMaxContactForce="310" permittedStaticContactForce="125" requiredFireCategory="A" requiresAutomaticDroppingDevice="true" requiresPowerLimitation="false"/>
<etcsElectrification nid_ctraction="25000"/>
<hasContactWire maxDisplacement="0.5" maxHeight="6.5" minHeight="5.0"/>
<pantographSpacing numberPantographsRaised="1" spacingPantographsRaised="200" speed4PantographSpacing="160"/>
<phaseSeparationSection lengthPhaseSeparation="18" lowerPantograph="false" switchOffBreaker="false"/>
<systemSeparationSection isSupplySystemChange="false" lengthSystemSeparation="12" lowerPantograph="false" switchOffBreaker="false"/>""",

    "elc877": """\
<electrificationSystemRef ref="els_ac25kv50hz"/>
<energyCatenary allowsRegenerativeBraking="false">
  <maxTrainCurrent maxCurrent="180" operationType="0" trainType="freight" validFor="0"/>
</energyCatenary>
<energyPantograph compliantTSITypes="none" contactStripMaterials="plainCarbon" requiresTSIcompliance="false"/>
<energyRollingstock permittedMaxContactForce="280" permittedStaticContactForce="110" requiredFireCategory="B" requiresAutomaticDroppingDevice="false" requiresPowerLimitation="true"/>
<hasContactWire maxDisplacement="0.45" maxHeight="6.3" minHeight="4.9"/>
<pantographSpacing numberPantographsRaised="2" spacingPantographsRaised="300" speed4PantographSpacing="100"/>
<systemSeparationSection isSupplySystemChange="false" lengthSystemSeparation="10" lowerPantograph="false" switchOffBreaker="false"/>""",
}

SECTION_ENRICHMENTS = {
    sid: indent_xml(raw, 10) + "\n"
    for sid, raw in SECTION_ENRICHMENTS_RAW.items()
}

# ---------------------------------------------------------------------------
# 3. Loading gauges (before <operationalPoints>)
# ---------------------------------------------------------------------------
LOADING_GAUGES = indent_xml("""\
<loadingGauges>
  <loadingGauge code="GA" id="lg_ga1">
    <name description="European standard gauge GA" language="en" name="GA"/>
    <linearLocation applicationDirection="both" id="lg_ga1_lloc">
      <associatedNetElement keepsOrientation="true" netElementRef="ne_1" posBegin="0.0" posEnd="500.0">
        <linearCoordinateBegin measure="0.0" positioningSystemRef="LPS_8176"/>
        <linearCoordinateEnd measure="500.0" positioningSystemRef="LPS_8176"/>
      </associatedNetElement>
      <associatedNetElement keepsOrientation="true" netElementRef="ne_55" posBegin="0.0" posEnd="200.0">
        <linearCoordinateBegin measure="550.0" positioningSystemRef="LPS_8176"/>
        <linearCoordinateEnd measure="700.0" positioningSystemRef="LPS_8176"/>
      </associatedNetElement>
      <associatedNetElement keepsOrientation="true" netElementRef="ne_16" posBegin="0.0" posEnd="3265.0">
        <linearCoordinateBegin measure="700.0" positioningSystemRef="LPS_8176"/>
        <linearCoordinateEnd measure="3965.0" positioningSystemRef="LPS_8176"/>
      </associatedNetElement>
    </linearLocation>
    <kinematicProfile height="4.2" width="3.15"/>
    <staticProfile height="4.32" width="3.15"/>
  </loadingGauge>
  <loadingGauge code="GB" id="lg_gb1">
    <name description="European standard gauge GB" language="en" name="GB"/>
    <linearLocation applicationDirection="both" id="lg_gb1_lloc">
      <associatedNetElement keepsOrientation="true" netElementRef="ne_39" posBegin="0.0" posEnd="500.0">
        <linearCoordinateBegin measure="0.0" positioningSystemRef="LPS_8176"/>
        <linearCoordinateEnd measure="500.0" positioningSystemRef="LPS_8176"/>
      </associatedNetElement>
    </linearLocation>
    <kinematicProfile height="4.28" width="3.25"/>
    <staticProfile height="4.4" width="3.25"/>
  </loadingGauge>
  <loadingGauge code="GC" id="lg_gc1">
    <name description="European standard gauge GC" language="en" name="GC"/>
    <linearLocation applicationDirection="both" id="lg_gc1_lloc">
      <associatedNetElement keepsOrientation="true" netElementRef="ne_561" posBegin="0.0" posEnd="7315.0">
        <linearCoordinateBegin measure="5600.0" positioningSystemRef="LPS_8176"/>
        <linearCoordinateEnd measure="12915.0" positioningSystemRef="LPS_8176"/>
      </associatedNetElement>
    </linearLocation>
    <kinematicProfile height="4.7" width="3.4"/>
    <staticProfile height="4.82" width="3.4"/>
  </loadingGauge>
  <loadingGauge code="G1" id="lg_g1">
    <name description="International gauge G1" language="en" name="G1"/>
    <linearLocation applicationDirection="both" id="lg_g1_lloc">
      <associatedNetElement keepsOrientation="true" netElementRef="ne_565" posBegin="0.0" posEnd="7315.0">
        <linearCoordinateBegin measure="5600.0" positioningSystemRef="LPS_8176"/>
        <linearCoordinateEnd measure="12915.0" positioningSystemRef="LPS_8176"/>
      </associatedNetElement>
    </linearLocation>
    <kinematicProfile height="4.65" width="3.35"/>
    <staticProfile height="4.77" width="3.35"/>
  </loadingGauge>
  <loadingGauge code="GB1" id="lg_gb1_multi">
    <name description="Multilateral gauge GB1" language="en" name="GB1"/>
    <linearLocation applicationDirection="both" id="lg_gb1_multi_lloc">
      <associatedNetElement keepsOrientation="true" netElementRef="ne_77" posBegin="64.0" posEnd="118.0">
        <linearCoordinateBegin measure="4264.0" positioningSystemRef="LPS_8176"/>
        <linearCoordinateEnd measure="4318.0" positioningSystemRef="LPS_8176"/>
      </associatedNetElement>
    </linearLocation>
    <kinematicProfile height="4.5" width="3.3"/>
    <staticProfile height="4.62" width="3.3"/>
  </loadingGauge>
</loadingGauges>""", 6) + "\n"

# ---------------------------------------------------------------------------
# 4. Length on overCrossing tun199
# ---------------------------------------------------------------------------
LENGTH_TUN199 = "          <length type=\"physical\" value=\"2300\" />\n"

# ---------------------------------------------------------------------------
# 5. Platform edge heights
# ---------------------------------------------------------------------------
PLATFORM_EDGE_HEIGHTS = {
    "ple193": "0.55",
    "ple194": "0.55",
    "ple388": "0.76",
    "ple390": "0.76",
    "ple391": "0.55",
    "ple392": "0.55",
    "ple428": "0.76",
    "ple429": "0.76",
}

# ---------------------------------------------------------------------------
# 6. Track gauges (before <trainDetectionElements>)
# ---------------------------------------------------------------------------
TRACK_GAUGES = indent_xml("""\
<trackGauges>
  <trackGauge id="tg_standard_network" value="1.435">
    <name description="Standard gauge 1435mm - network wide" language="en" name="Standard Gauge"/>
    <networkLocation networkRef="nw01"/>
  </trackGauge>
</trackGauges>""", 6) + "\n"


# ---------------------------------------------------------------------------
# Patch logic
# ---------------------------------------------------------------------------

def enrich_section(text: str, section_id: str, additions: str) -> str:
    """Insert additions before </electrificationSection> after section_id."""
    marker = f'id="{section_id}"'
    pos = text.find(marker)
    if pos == -1:
        print(f"    WARNING: {section_id} not found")
        return text
    closing = "        </electrificationSection>"
    close_pos = text.find(closing, pos)
    if close_pos == -1:
        print(f"    WARNING: closing tag not found for {section_id}")
        return text
    return text[:close_pos] + additions + text[close_pos:]


def main():
    print(f"Loading: {SOURCE}")
    with open(SOURCE, "r", encoding="utf-8") as f:
        text = f.read()

    # 1. Add electrificationSystems before <organizationalUnits>
    print("  + Adding electrificationSystems to common")
    text = text.replace(
        "    <organizationalUnits>",
        ELECTRIFICATION_SYSTEMS + "    <organizationalUnits>",
        1,
    )

    # 2. Enrich electrification sections
    print("  + Enriching electrification sections")
    for section_id, additions in SECTION_ENRICHMENTS.items():
        text = enrich_section(text, section_id, additions)

    # 3. Add loadingGauges before <operationalPoints>
    print("  + Adding loadingGauges section")
    text = text.replace(
        "      <operationalPoints>",
        LOADING_GAUGES + "      <operationalPoints>",
        1,
    )

    # 4. Add length to overCrossing tun199
    print("  + Adding length to overCrossing tun199")
    pos = text.find('id="tun199"')
    if pos == -1:
        print("    WARNING: tun199 not found")
    else:
        closing = "        </overCrossing>"
        close_pos = text.find(closing, pos)
        if close_pos == -1:
            print("    WARNING: closing tag not found for tun199")
        else:
            text = text[:close_pos] + LENGTH_TUN199 + text[close_pos:]

    # 5. Add height to platformEdges
    print("  + Adding height to platformEdges")
    for edge_id, height in PLATFORM_EDGE_HEIGHTS.items():
        pattern = f'(<platformEdge[^>]*?) id="{edge_id}">'
        replacement = f'\\1 height="{height}" id="{edge_id}">'
        text, count = re.subn(pattern, replacement, text, count=1)
        if count == 0:
            print(f"    WARNING: platformEdge {edge_id} not found")

    # 6. Add trackGauges before <trainDetectionElements>
    print("  + Adding trackGauges section")
    text = text.replace(
        "      <trainDetectionElements>",
        TRACK_GAUGES + "      <trainDetectionElements>",
        1,
    )

    print(f"Saving: {OUTPUT}")
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(text)
    print("Patching complete!")


if __name__ == "__main__":
    main()
