# SHACL Validation Summary

**Status:** ❌ FAILED

**Date:** 2026-02-23 21:29:27

Found 2 types of violations

## Violation Details

| Level | Property Path | Constraint Component | Violations | Message | Example Node |
|-------|---------------|---------------------|------------|---------|-------------|
| `<sh:Violation>` | `None` | `<sh:SPARQLConstraintComponent>` | 1 | "conditionsAppliedRegenerativeBraking (1.1.1.2.2.4.1):The Contact Line System <https://data.matdata.eu/_contactLineSystems_elc439> ((?clsLabel was unbound)), has a 'Overhead contact line (OCL)' type which makes the conditionsAppliedRegenerativeBraking parameter applicable. This error is due to <https://data.matdata.eu/_contactLineSystems_elc439> not having a value for such a parameter."@en | `<https://data.matdata.eu/_contactLineSystems_elc439>` |
| `<sh:Warning>` | `<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>` | `<sh:MinCountConstraintComponent>` | 2 | "Resource must have at least one rdf:type" | `<era:bridgeWindRestriction>` |

## Recommendations

1. Review the violations table above
2. Check the full validation report in `validation-report.ttl`
3. Update CONSTRUCT queries or add shape fixes as needed
4. Re-run the validation after making corrections
