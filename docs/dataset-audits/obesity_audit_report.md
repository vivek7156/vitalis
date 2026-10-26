# Dataset Audit Report: Obesity

**Generated:** 2026-10-26T10:16:32.276653+00:00

## 1. Source and Provenance

- **Name:** Estimation of Obesity Levels Based on Eating Habits and Physical Condition
- **Source:** UCI Machine Learning Repository
- **DOI:** 10.24432/C5H31Z
- **License:** CC BY 4.0
- **Acquired on:** 2026-10-24
- **File:** `data/raw/ObesityDataSet_raw_and_data_sinthetic.csv`
- **SHA-256:** `28b6991062855d3d15642e38b1aa9d1b32fb7abbb5abf5b096f1868cd706154b`

## 2. Dimensions

- **Rows:** 2111 (expected: 2111)
- **Columns:** 17 (expected: 17)

## 3. Target Distribution

| Class | Count | Proportion |
|---|---|---|
| Insufficient_Weight | 272 | 0.1288 |
| Normal_Weight | 287 | 0.1360 |
| Overweight_Level_I | 290 | 0.1374 |
| Overweight_Level_II | 290 | 0.1374 |
| Obesity_Type_I | 351 | 0.1663 |
| Obesity_Type_II | 297 | 0.1407 |
| Obesity_Type_III | 324 | 0.1535 |
| **Total** | **2111** | **1.0000** |

## 4. Field Details

| Field | Type | Missing | Unique | Min | Max | Mean | Fractional |
|---|---|---|---|---|---|---|---|
| Gender | str | 0 | 2 | — | — | — | — |
| Age | float64 | 0 | 1402 | 14.0 | 61.0 | 24.3126 | — |
| Height | float64 | 0 | 1574 | 1.45 | 1.98 | 1.701677 | — |
| Weight | float64 | 0 | 1525 | 39.0 | 173.0 | 86.586058 | — |
| family_history_with_overweight | str | 0 | 2 | — | — | — | — |
| FAVC | str | 0 | 2 | — | — | — | — |
| FCVC | float64 | 0 | 810 | 1.0 | 3.0 | 2.419043 | 826 |
| NCP | float64 | 0 | 635 | 1.0 | 4.0 | 2.685628 | 640 |
| CAEC | str | 0 | 4 | — | — | — | — |
| SMOKE | str | 0 | 2 | — | — | — | — |
| CH2O | float64 | 0 | 1268 | 1.0 | 3.0 | 2.008011 | 1290 |
| SCC | str | 0 | 2 | — | — | — | — |
| FAF | float64 | 0 | 1190 | 0.0 | 3.0 | 1.010298 | 1208 |
| TUE | float64 | 0 | 1129 | 0.0 | 2.0 | 0.657866 | 1153 |
| CALC | str | 0 | 4 | — | — | — | — |
| MTRANS | str | 0 | 5 | — | — | — | — |
| NObeyesdad | str | 0 | 7 | — | — | — | — |

## 5. Duplicate Analysis

- **Exact duplicate rows:** 24
- **Duplicate groups:** 9

- **Feature-duplicate groups with conflicting targets:** 0

- **Near-duplicate method:** max_normalised_diff < 0.01, all categoricals match
- **Near-duplicate pairs:** 147

## 6. Leakage Analysis

### BMI (Height, Weight)
- **Severity:** blocking_for_e2
- BMI is computed from Height and Weight. The obesity target is defined using BMI thresholds. E1 uses this with documented dependence; E2 must exclude Height, Weight, and BMI.
- **BMI-Target rank correlation:** 0.9778

## 7. Demographic Coverage

- **Age range:** 14.0 – 61.0 (mean: 24.3)
- **Under 18:** 113
- **Gender:** {'Male': 1068, 'Female': 1043}
- **Note:** Dataset originates from Colombia, Mexico, and Peru. May not generalise to other populations.

## 8. Synthetic Data

- **Reported share:** 0.77
- Approximately 77% of rows are reported as synthetically generated (SMOTE). Row-level provenance is unavailable. A later split cannot undo the historical generation process.

## 9. Findings Summary

| ID | Classification | Description |
|---|---|---|
| DUP-exact | accepted_limitation | 24 exact duplicate rows found. Deduplication policy: keep first occurrence for splitting, document e |
| LEAK-BMI (Height, Weight) | accepted_limitation | BMI is computed from Height and Weight. The obesity target is defined using BMI thresholds. E1 uses  |
| SYNTH-provenance | accepted_limitation | Approximately 77% of rows are reported as synthetically generated (SMOTE). Row-level provenance is u |
| DEMO-under18 | follow_up | 113 records with Age < 18. Confirm supported population and handling policy. |
| FRAC-FCVC | accepted_limitation | FCVC: 826 rows have fractional values. These are synthetic continuous values, not integer categories |
| FRAC-NCP | accepted_limitation | NCP: 640 rows have fractional values. These are synthetic continuous values, not integer categories. |
| FRAC-CH2O | accepted_limitation | CH2O: 1290 rows have fractional values. These are synthetic continuous values, not integer categorie |
| FRAC-FAF | accepted_limitation | FAF: 1208 rows have fractional values. These are synthetic continuous values, not integer categories |
| FRAC-TUE | accepted_limitation | TUE: 1153 rows have fractional values. These are synthetic continuous values, not integer categories |

## 10. Validation Report

- **Accepted:** 2111
- **Rejected:** 0
- **Errors:** 0
- **Warnings:** 0
