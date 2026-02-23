# SHACL Validation Summary

**Status:** ❌ FAILED

**Date:** 2026-02-23 21:27:32

Found 3 types of violations

## Violation Details

| Level | Property Path | Constraint Component | Violations | Message | Example Node |
|-------|---------------|---------------------|------------|---------|-------------|
| `sh:Violation` | `None` | `sh:SPARQLConstraintComponent` | 1 | conditionsAppliedRegenerativeBraking (1.1.1.2.2.4.1):The Contact Line System https://data.matdata.eu/_contactLineSystems_elc439 ({?clsLabel}), has a 'Overhead contact line (OCL)' type which makes the conditionsAppliedRegenerativeBraking parameter applicable. This error is due to https://data.matdata.eu/_contactLineSystems_elc439 not having a value for such a parameter. | `https://data.matdata.eu/_contactLineSystems_elc439` |
| `sh:Violation` | `None` | `sh:SPARQLConstraintComponent` | 2 | trackRaisedPantographsDistanceAndSpeed (1.1.1.2.3.3): This error is due to the track or subset with common characteristics 21 , violating the rule: This parameter is applicable ('Y') only if “Overhead contact line (OCL)” is selected for 1.1.1.2.2.1.1. | `https://data.matdata.eu/_tracks_trc6` |
| `sh:Violation` | `era:trackId` | `sh:MinCountConstraintComponent` | 9 | trackId (1.1.1.3.3.3.3, 1.2.1.1.2.3.3): The identification of a track must be a string. This error may be due to having a track with no identification or with more than one value as identification, or having a value that is not a string. | `https://data.matdata.eu/_tracks_trc35` |

## Recommendations

1. Review the violations table above
2. Check the full validation report in `validation-report.ttl`
3. Update CONSTRUCT queries or add shape fixes as needed
4. Re-run the validation after making corrections
