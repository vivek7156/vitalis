# Vitalis Module 1 Handoff Report: Obesity Data & Preprocessing Pipeline

| Item | Details |
|---|---|
| Module | Module 1: Data Acquisition, Audit, Partitioning & Preprocessing |
| Target Recipient | Module 2: Model Training, Cross-Validation & Calibration |
| Target Disease | Obesity Level Screening |
| Date | 2026-10-26 |
| Exit Gate | **G5 (Module 1 Handoff Completed)** |

---

## 1. Executive Summary & Verification Evidence

Module 1 has been implemented, validated, and audited. The raw UCI Obesity dataset has undergone:
1. Strict schema and type validation with zero row loss.
2. Comprehensive leakage, duplicate, and demographic audit with zero blocking issues.
3. Leakage-safe deduplication (24 exact duplicates dropped) and stratified 70% / 15% / 15% partitioning frozen in `data/manifests/obesity_split_manifest.json`.
4. Creation of unfitted and train-fitted preprocessing transformers for both **E2 (Lifestyle-only)** and **E1 (BMI-inclusive)** configurations.
5. All 40 unit and integration tests passing with 100% success.

---

## 2. Partitioned Data Deliverables (T-HANDOFF-01)

Partitioned datasets are stored in `data/processed/` with identical split membership shared between E1 and E2:

| Partition File | Record Count | Share | Target Balance Preserved? | Usage Rules |
|---|---|---|---|---|
| `data/processed/obesity_train.csv` | **1,460** | 70% | Yes (Stratified) | Model training, k-fold cross-validation, hyperparameter search, and post-hoc calibration training. |
| `data/processed/obesity_val.csv` | **313** | 15% | Yes (Stratified) | Model checkpoint selection, early stopping, and calibration validation. |
| `data/processed/obesity_test.csv` | **314** | 15% | Yes (Stratified) | **STRICTLY FROZEN.** Must NEVER be used for model selection, feature tuning, or threshold adjustment. Evaluate once for final reporting. |
| **Total Deduplicated** | **2,087** | 100% | — | (24 exact duplicate records removed before splitting). |

---

## 3. Target Variable & Stable Class Mappings (T-HANDOFF-02)

- Target Column: `NObeyesdad`
- Multi-class classification with 7 mutually exclusive classes:

```python
TARGET_CLASS_MAP = {
    "Insufficient_Weight": 0,
    "Normal_Weight": 1,
    "Overweight_Level_I": 2,
    "Overweight_Level_II": 3,
    "Obesity_Type_I": 4,
    "Obesity_Type_II": 5,
    "Obesity_Type_III": 6,
}
```

---

## 4. Feature Configurations & Factory Usage (T-HANDOFF-01, T-HANDOFF-02)

Module 2 has access to:
1. **Unfitted Factory Function:** `pipeline.preprocessing.create_preprocessing_pipeline(disease, feature_set, model_family)`
   - **Crucial Rule:** When running k-fold cross validation, instantiate an unfitted pipeline per fold so that scaling and encoding learn ONLY on the training folds.
2. **Pre-fitted Transformers (Artifacts):**
   - E2 Pipeline: `artifacts/obesity_e2_lifestyle_only_pipeline.joblib`
   - E2 Mapping: `artifacts/obesity_e2_lifestyle_only_feature_mapping.json`
   - E1 Pipeline: `artifacts/obesity_e1_bmi_inclusive_pipeline.joblib`
   - E1 Mapping: `artifacts/obesity_e1_bmi_inclusive_feature_mapping.json`

### E2 Feature Specification (Primary Screening Model)
- **14 Features:** `Gender`, `Age`, `family_history_with_overweight`, `FAVC`, `FCVC`, `NCP`, `CAEC`, `SMOKE`, `CH2O`, `SCC`, `FAF`, `TUE`, `CALC`, `MTRANS`
- **Strictly Excluded:** `Height`, `Weight`, `BMI` (to prevent trivial leakage).
- **Transformed Dimension:** 19 columns (with one-hot nominal encoding and ordinal mapping).

### E1 Feature Specification (Researcher Benchmark)
- **16 Features:** All 14 E2 features + `Height` (m) + `Weight` (kg).
- **Transformed Dimension:** 21 columns.
- **Reporting Disclosure:** Mandatory note that height and weight directly reconstruct BMI thresholds.

---

## 5. Tuning and Calibration Rules (T-HANDOFF-03)

- **Calibration Strategy:** Calibration curves (Brier score, Expected Calibration Error) and Platt scaling / isotonic regression must be fitted on training fold holdouts or the validation partition (`obesity_val.csv`).
- **Never Touch Test Partition:** The test set (`obesity_test.csv`) must not be used to calibrate probability thresholds.

---

## 6. Dataset Limitations and Known Risks (T-HANDOFF-04)

1. **Synthetic Sample Generation (SMOTE):**
   - Approximately 77% of rows in the UCI dataset were synthetically generated prior to repository upload.
   - Individual synthetic provenance is not labeled per row.
   - Frequency features contain continuous fractional numbers (`FCVC`, `NCP`, `CH2O`, `FAF`, `TUE`); models must treat them as continuous floats.
2. **Pediatric Population:**
   - 113 records have ages 14–17. Primary screening targets adults 18–65.
3. **Geographic Demographics:**
   - Data gathered from respondents in Colombia, Mexico, and Peru. External generalization to other demographics requires domain consideration.

---

## 7. How to Execute the Pipeline Workflow (T-HANDOFF-05)

To reproduce the Module 1 artifacts from scratch:

```bash
# Run unit tests
pytest -v

# Run full pipeline end-to-end
python -m pipeline.run_pipeline --disease obesity

# Run audit only
python -m pipeline.audit --disease obesity

# Run partition splitting only
python -m pipeline.splitting --disease obesity
```
