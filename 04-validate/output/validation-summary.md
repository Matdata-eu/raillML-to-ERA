# SHACL Validation Summary

**Status:** ❌ FAILED

**Date:** 2026-02-19 19:54:18

Found 18 types of violations

## Violation Details

| Property Path | Constraint Component | Violations | Message | Example Node |
|---------------|---------------------|------------|---------|-------------|
| `<era:endsAt>` | `<sh:MinCountConstraintComponent>` | 1 | "endsAt: The net linear reference specifies an ending point that must be an instance of a NetPointReference. This error is due to not having a value, having more than one value or having a value that is not an instance of NetPointReference."@en | `<era:topology/netLinearReferences/bri200_segment_1>` |
| `<era:nationalLine>` | `<sh:ClassConstraintComponent>` | 6 | "nationalLine (1.1.0.0.0.2): Each SoL belongs to exactly one linear positioning system. This error is due to not having a value, having more than one value, or having a value that is not an instance of LinearPositioningSystem."@en | `<era:functionalInfrastructure/sectionsOfLine/ls_ne_ml_471>` |
| `<era:nationalLine>` | `<sh:NodeKindConstraintComponent>` | 6 | "nationalLine (1.1.0.0.0.2): Each SoL belongs to exactly one linear positioning system. This error is due to not having a value, having more than one value, or having a value that is not an instance of LinearPositioningSystem."@en | `<era:functionalInfrastructure/sectionsOfLine/ls_ne_ml_471>` |
| `<era:netReference>` | `<sh:ClassConstraintComponent>` | 23 | "netReference: Each OperationalPoint must have at least one netReference pointing to an instance of NetBasicReference. This error is due to not having a value or having a value that is not a NetBasicReference."@en | `<era:functionalInfrastructure/operationalPoints/opp190>` |
| `<era:netReference>` | `<sh:ClassConstraintComponent>` | 6 | "netReference: Each SectionOfLine must have at least one netReference pointing to an instance of NetBasicReference. This error is due to not having a value or having a value that is not a NetBasicReference."@en | `<era:functionalInfrastructure/sectionsOfLine/ls_ne_ml_724>` |
| `<era:opEnd>` | `<sh:MinCountConstraintComponent>` | 4 | "opEnd (1.1.0.0.0.4): There must be exactly one OP end for this section of line and it must be different from the OP start."@en | `<era:functionalInfrastructure/sectionsOfLine/ls_ne_ml_294>` |
| `<era:opName>` | `<sh:DatatypeConstraintComponent>` | 10 | "opName (1.2.0.0.0.1): Each Operational Point must have at least one name in English (@en). Additional multilingual names are allowed, but only one value per language tag is permitted. All values must be language-tagged string literals."@en | `<era:functionalInfrastructure/operationalPoints/opp580>` |
| `<era:opName>` | `<sh:SPARQLConstraintComponent>` | 10 | "opName (1.2.0.0.0.1): Each Operational Point must have at least one name in English (@en). Additional multilingual names are allowed, but only one value per language tag is permitted. All values must be language-tagged string literals."@en | `<era:functionalInfrastructure/operationalPoints/opp580>` |
| `<era:opStart>` | `<sh:DisjointConstraintComponent>` | 3 | "opStart (1.1.0.0.0.3): There must be exactly one OP start for this section of line and it must be different from the OP end."@en | `<era:functionalInfrastructure/sectionsOfLine/ls_ne_ml_163>` |
| `<era:opStart>` | `<sh:MinCountConstraintComponent>` | 1 | "opStart (1.1.0.0.0.3): There must be exactly one OP start for this section of line and it must be different from the OP end."@en | `<era:functionalInfrastructure/sectionsOfLine/ls_ne_ml_291>` |
| `<era:organisationCode>` | `<sh:MaxCountConstraintComponent>` | 1 | "organisationCode (1.2.1.0.6.1, 1.1.0.0.0.1, 1.1.1.1.8.1, 1.2.1.0.0.1, 1.2.1.0.5.1, 1.2.2.0.0.1, 1.2.2.0.5.1): A Body must have exactly one value of organisationCode. This error may be due to not having a value, having more than one value, having a value that is not a string or having a value that is not a four character code"@en | `<era:organisations/0076>` |
| `<era:platformId>` | `<sh:MinCountConstraintComponent>` | 7 | "platformId (1.2.1.0.6.2): Each Platform must have exactly one platformId. This error may be due to having a platform without or with more than one platformId or it value is not a string."@en | `<era:functionalInfrastructure/platformEdges/ple392>` |
| `<era:uopid>` | `<sh:MaxCountConstraintComponent>` | 1 | "uopid (1.2.0.0.0.2): This error is due to having more than one op id, not having an op id, having a value that is not a string, or having a value that does not follow the pattern where the first part 'AA' is the country code in two-letter system of ISO (or 'EU' for border points) and the second part is the alphanumeric OP code within the MS."@en | `<era:functionalInfrastructure/operationalPoints/opp740>` |
| `<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>` | `<sh:MinCountConstraintComponent>` | 90 | "Resource must have at least one rdf:type" | `<era:concepts/navigabilities/Both>` |
| `<http://www.w3.org/2000/01/rdf-schema#label>` | `<sh:SPARQLConstraintComponent>` | 4 | "rdfs:label: Each LinearPositioningSystem must have at least one label in English (@en). Additional multilingual labels are allowed, but only one value per language tag is permitted. All values must be language-tagged string literals."@en | `<era:linearPositioningSystems/LPS_2444>` |
| `<http://www.w3.org/2000/01/rdf-schema#label>` | `<sh:DatatypeConstraintComponent>` | 1 | "rdfs:label: Each infrastructure element must have at least one label in English (@en). Additional multilingual labels are allowed, but only one value per language tag is permitted. All values must be language-tagged string literals."@en | `<era:functionalInfrastructure/bridges/bri200>` |
| `<http://www.w3.org/2000/01/rdf-schema#label>` | `<sh:SPARQLConstraintComponent>` | 1 | "rdfs:label: Each infrastructure element must have at least one label in English (@en). Additional multilingual labels are allowed, but only one value per language tag is permitted. All values must be language-tagged string literals."@en | `<era:functionalInfrastructure/bridges/bri200>` |
| `_:efd2ced2206a37b162fed72d200e0931_1` | `<sh:ClassConstraintComponent>` | 17 | "hasPart: The SectionOfLine must have a hasPart reference that is an IRI that refers to an instance of Track. This error is due to not having a value or having a value that is not an instance of Track."@en | `<era:functionalInfrastructure/sectionsOfLine/ls_ne_ml_724>` |

## Recommendations

1. Review the violations table above
2. Check the full validation report in `validation-report.ttl`
3. Update CONSTRUCT queries or add shape fixes as needed
4. Re-run the validation after making corrections
