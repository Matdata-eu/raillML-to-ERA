# SHACL Validation Summary

**Status:** ❌ FAILED

**Date:** 2026-02-21 19:40:07

Found 2 types of violations

## Violation Details

| Level | Property Path | Constraint Component | Violations | Message | Example Node |
|-------|---------------|---------------------|------------|---------|-------------|
| `<sh:Violation>` | `<http://www.opengis.net/ont/geosparql#hasGeometry>` | `<sh:MinCountConstraintComponent>` | 1 | "A ReferenceBorderPoint must have exactly one geo:hasGeometry, and its value must be an instance of geo:Gemoetry. This error is due to having more than one, having none, or having a value that is not an istance of geo:Geometry."@en | `<era:functionalInfrastructure/borderpoint/opp740>` |
| `<sh:Warning>` | `<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>` | `<sh:MinCountConstraintComponent>` | 3 | "Resource must have at least one rdf:type" | `<era:bridgeWindRestriction>` |

## Recommendations

1. Review the violations table above
2. Check the full validation report in `validation-report.ttl`
3. Update CONSTRUCT queries or add shape fixes as needed
4. Re-run the validation after making corrections
