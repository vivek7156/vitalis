# Project Decisions Record (ADR)

## DEC-001: Initial development baseline
- **Date:** 2026-10-24
- **Decision:** Use Python 3.11, FastAPI, React/Vite, scikit-learn, CatBoost, SHAP, and SQLite.
- **Initial implementation:** Obesity E2 Module 1 data pipeline.
- **Disease modules:** Diabetes, CVD, and MASLD remain pending dataset and target approval.
- **Artifacts & Data:** Raw datasets and generated artifacts are excluded from Git.
- **Status:** Approved

## DEC-002: Obesity Partitioning and Deduplication Strategy
- **Date:** 2026-10-26
- **Decision:** Perform stratified train/validation/test split at 70% / 15% / 15% proportions with fixed random seed 42.
- **Deduplication:** Exactly 24 duplicate records identified during audit are dropped before splitting (leaving 2,087 unique records).
- **Manifest:** Split membership is frozen in `data/manifests/obesity_split_manifest.json`. Both E1 and E2 use identical record assignments to ensure fair, controlled comparison.
- **Status:** Approved

## DEC-003: E1 vs E2 Feature Sets and BMI Leakage Exclusion
- **Date:** 2026-10-26
- **Decision:** E2 (Lifestyle & Demographics only, 14 features) serves as the primary screening model and strictly excludes `Height`, `Weight`, and calculated `BMI`.
- **Rationale:** Dataset audit confirmed a 0.9778 rank correlation between BMI and target classes. Retaining height/weight creates trivial target reconstruction rather than health-risk screening. E1 is preserved strictly as a researcher baseline with mandatory leakage disclosure.
- **Status:** Approved

## DEC-004: Treatment of Pending Secondary Diseases (Diabetes, CVD, MASLD)
- **Date:** 2026-10-26
- **Decision:** Maintain explicit configuration entries for diabetes, CVD, and MASLD marked as `pending_approval` in `config/datasets.yaml` and `config/features.yaml`.
- **Policy:** The pipeline loader and API screening routes will return explicit unavailable/pending errors rather than presenting mock or unverified predictions.
- **Status:** Approved

## DEC-005: Handling of Synthetic Continuous Artifacts and Age Eligibility
- **Date:** 2026-10-26
- **Decision:** Frequency features with fractional values (`FCVC`, `NCP`, `CH2O`, `FAF`, `TUE`) resulting from SMOTE synthetic interpolation must remain as continuous `float64` values and must not be silently discretized or rounded.
- **Eligibility:** Primary screening targets adults (18–65). Records with age 14–17 will trigger an age advisory note during assessment. All 14 E2 fields are mandatory at inference; missing required inputs cannot be bypassed via imputation.
- **Status:** Approved

## DEC-006: Module 2 Training and Calibration Boundary
- **Date:** 2026-10-27
- **Decision:** Train obesity E1 and E2 candidates with fresh preprocessing inside
  stratified training folds. Select the champion by cross-validated macro-F1,
  calibrate it on the frozen validation partition, and evaluate the calibrated
  artifact once on the frozen test partition.
- **Candidates:** Logistic Regression, Random Forest and CatBoost.
- **Status:** Approved