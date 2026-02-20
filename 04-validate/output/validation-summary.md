# SHACL Validation Summary

**Status:** ❌ FAILED

**Date:** 2026-02-20 23:37:17

Found 7 types of violations

## Violation Details

| Level | Property Path | Constraint Component | Violations | Message | Example Node |
|-------|---------------|---------------------|------------|---------|-------------|
| `<sh:Violation>` | `None` | `<sh:SPARQLConstraintComponent>` | 7 | "conditionsAppliedRegenerativeBraking (1.1.1.2.2.4.1):The Contact Line System <http://data.europa.eu/949/functionalInfrastructure/contactLineSystems/elc732> (), has a 'Overhead contact line (OCL)' type which makes the conditionsAppliedRegenerativeBraking parameter applicable. This error is due to <http://data.europa.eu/949/functionalInfrastructure/contactLineSystems/elc732> not having a value for such a parameter."@en | `<era:functionalInfrastructure/contactLineSystems/elc732>` |
| `<sh:Violation>` | `None` | `<sh:SPARQLConstraintComponent>` | 3 | "ObjectProperty <http://data.europa.eu/949/definesSubset> has deprecated class <http://data.europa.eu/949/InfrastructureManager> in its domain" | `<era:definesSubset>` |
| `<sh:Violation>` | `None` | `<sh:SPARQLConstraintComponent>` | 5 | "ObjectProperty <http://data.europa.eu/949/tdsMinAxleLoadVehicleCategory> has deprecated class <http://data.europa.eu/949/MinAxleLoadVehicleCategory> in its range" | `<era:tdsMinAxleLoadVehicleCategory>` |
| `<sh:Violation>` | `None` | `<sh:SPARQLConstraintComponent>` | 8 | "referenceBorderPoint: The OperationalPoint <http://data.europa.eu/949/functionalInfrastructure/operationalPoints/opp740> with name "Kudowa chranice"@no is a border point but does not have a referenceBorderPoint property."@en | `<era:functionalInfrastructure/operationalPoints/opp740>` |
| `<sh:Violation>` | `None` | `<sh:SPARQLConstraintComponent>` | 14 | "There should be at least one Track Direction. There is a problem with SoL <http://data.europa.eu/949/functionalInfrastructure/sectionsOfLine/ls_ne_ml_16> ("OAR-OC"@no) and its track <http://data.europa.eu/949/functionalInfrastructure/tracks/trc2> ("H"@en). This track has no values for this property"@en | `<era:functionalInfrastructure/sectionsOfLine/ls_ne_ml_16>` |
| `<sh:Violation>` | `None` | `<sh:SPARQLConstraintComponent>` | 114 | "trainDetectionSystemSpecificCheckDocument (1.1.1.3.7.1.3, 1.2.1.1.6.2):The Train Detection System <http://data.europa.eu/949/functionalInfrastructure/trainDetectionSystems/tde214> (), has a type that makes the trainDetectionSystemSpecificCheckDocument parameter applicable. This error is due to <http://data.europa.eu/949/functionalInfrastructure/trainDetectionSystems/tde214> not having a value for such a parameter."@en | `<era:functionalInfrastructure/trainDetectionSystems/tde214>` |
| `<sh:Warning>` | `<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>` | `<sh:MinCountConstraintComponent>` | 2 | "Resource must have at least one rdf:type" | `<era:bridgeWindRestriction>` |

## Recommendations

1. Review the violations table above
2. Check the full validation report in `validation-report.ttl`
3. Update CONSTRUCT queries or add shape fixes as needed
4. Re-run the validation after making corrections
