# SHACL Validation Summary

**Status:** ❌ FAILED

**Date:** 2026-02-19 23:28:42

Found 8 types of violations

## Violation Details

| Level | Property Path | Constraint Component | Violations | Message | Example Node |
|-------|---------------|---------------------|------------|---------|-------------|
| `<sh:Violation>` | `<era:endsAt>` | `<sh:MinCountConstraintComponent>` | 1 | "endsAt: The net linear reference specifies an ending point that must be an instance of a NetPointReference. This error is due to not having a value, having more than one value or having a value that is not an instance of NetPointReference."@en | `<era:topology/netLinearReferences/bri200_segment_1>` |
| `<sh:Violation>` | `<era:uopid>` | `<sh:MaxCountConstraintComponent>` | 1 | "uopid (1.2.0.0.0.2): This error is due to having more than one op id, not having an op id, having a value that is not a string, or having a value that does not follow the pattern where the first part 'AA' is the country code in two-letter system of ISO (or 'EU' for border points) and the second part is the alphanumeric OP code within the MS."@en | `<era:functionalInfrastructure/operationalPoints/opp740>` |
| `<sh:Violation>` | `<http://www.opengis.net/ont/geosparql#hasGeometry>` | `<sh:MaxCountConstraintComponent>` | 3 | "hasGeometry (1.2.0.0.0.5):  Each feature must have at most one location. This error may be due to having a feature with more than one location or having a value that is not a geosparql:Geometry."@en | `<era:topology/netPointReferences/bri200_segment_1_start>` |
| `<sh:Violation>` | `<http://www.w3.org/2000/01/rdf-schema#label>` | `<sh:SPARQLConstraintComponent>` | 3 | "rdfs:label: Each LinearPositioningSystem must have at least one label in English (@en). Additional multilingual labels are allowed, but only one value per language tag is permitted. All values must be language-tagged string literals."@en | `<era:functionalInfrastructure/lps/2444>` |
| `<sh:Violation>` | `<http://www.w3.org/2000/01/rdf-schema#label>` | `<sh:DatatypeConstraintComponent>` | 1 | "rdfs:label: Each infrastructure element must have at least one label in English (@en). Additional multilingual labels are allowed, but only one value per language tag is permitted. All values must be language-tagged string literals."@en | `<era:functionalInfrastructure/bridges/bri200>` |
| `<sh:Violation>` | `<http://www.w3.org/2000/01/rdf-schema#label>` | `<sh:SPARQLConstraintComponent>` | 1 | "rdfs:label: Each infrastructure element must have at least one label in English (@en). Additional multilingual labels are allowed, but only one value per language tag is permitted. All values must be language-tagged string literals."@en | `<era:functionalInfrastructure/bridges/bri200>` |
| `<sh:Violation>` | `_:b7a8c41e0ae9b7b969812701b3de084c_1` | `<sh:ClassConstraintComponent>` | 4 | "hasPart: The SectionOfLine must have a hasPart reference that is an IRI that refers to an instance of Track. This error is due to not having a value or having a value that is not an instance of Track."@en | `<era:functionalInfrastructure/sectionsOfLine/ls_ne_ml_724>` |
| `<sh:Warning>` | `<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>` | `<sh:MinCountConstraintComponent>` | 3 | "Resource must have at least one rdf:type" | `<era:functionalInfrastructure/sectionsOfLine/ls_ne_ml_163>` |

## Recommendations

1. Review the violations table above
2. Check the full validation report in `validation-report.ttl`
3. Update CONSTRUCT queries or add shape fixes as needed
4. Re-run the validation after making corrections
