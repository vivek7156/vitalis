# Vitalis – Explainable Agentic AI Framework for Multi-Disease Health-Risk Screening

Vitalis is a multi-disease health-risk screening and wellness monitoring system. It provides explainable, calibrated risk assessment for metabolic and chronic conditions using specialist classification pipelines, deterministic guardrails, and transparent disclosures.

---

## Architecture & Modules

- **Module 1 (Data & Preprocessing Pipeline):** Data acquisition, schema validation, leakage audits, frozen stratified partitioning, and scikit-learn preprocessing factories.
- **Module 2 (Model Training & Calibration - Next):** Classifier training, k-fold cross-validation, hyperparameter optimization, and probability calibration.
- **Module 3 (Explainability & SHAP - Planned):** TreeSHAP feature attributions, contrastive explanations, and natural-language risk narratives.
- **API (FastAPI):** High-performance screening REST API with deterministic input validation, health/readiness reporting, and honest prototype states.
- **Web (React/Vite - Planned):** Wellness dashboard and interactive screening questionnaire.

---

## Project Structure

```text
vitalis/
├── api/                       # FastAPI application & REST endpoints
│   ├── main.py                # App entrypoint with CORS & exception handlers
│   ├── schemas.py             # Pydantic input/output schemas
│   └── routes/
│       ├── health.py          # /health & /readiness endpoints
│       └── screening.py       # /api/v1/screen/* endpoints
├── artifacts/                 # Serialized preprocessors and feature mappings (excluded from git)
├── config/                    # Configuration files
│   ├── datasets.yaml          # Dataset provenance, targets, & split strategies
│   └── features.yaml          # Feature sets (E2 lifestyle, E1 BMI-inclusive)
├── data/                      # Dataset directories (raw & processed excluded from git)
│   ├── raw/                   # Raw immutable datasets
│   ├── processed/             # Cleaned, partitioned train/val/test CSVs
│   └── manifests/             # Frozen split manifests (checksummed)
├── docs/                      # Clinical, technical, and implementation documentation
│   ├── data-dictionary.md     # Full attribute contract & units
│   ├── decisions.md           # Architecture Decision Records (ADRs)
│   ├── module-1-handoff.md    # Handoff specification for Module 2
│   ├── project-requirements.md
│   ├── tech-stack.md
│   └── vitalis_prototype_module_1_tasks.md
├── pipeline/                  # Data, training and evaluation components
│   ├── loader.py              # Schema validation & dataset loading
│   ├── audit.py               # Leakage, duplicate & demographic audit
│   ├── splitting.py           # Deduplication & stratified partitioning
│   ├── preprocessing.py       # ColumnTransformer factories & encoders
│   ├── run_pipeline.py        # Unified Module 1 execution CLI
│   ├── training.py            # Module 2 CV, calibration and artifact training
│   ├── evaluation.py          # Classification and calibration metrics
│   └── calibration.py         # Brier score and ECE helpers
├── web/                       # React/Vite screening and wellness interface
├── tests/                     # Backend and pipeline unit/integration tests
├── requirements.txt           # Production dependencies
└── requirements-dev.txt       # Development & test dependencies
```

---

## Quickstart & Setup

### 1. Environment Setup

```bash
# Clone and enter the repository
cd vitalis

# Create virtual environment (Python 3.11)
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt
```

### 2. Run Module 1 Data Pipeline

Execute the end-to-end data acquisition, audit, splitting, and preprocessing workflow for Obesity (E1 & E2):

```bash
# Full pipeline execution
python -m pipeline.run_pipeline --disease obesity

# Audit only (inspect leakage, distributions, duplicates)
python -m pipeline.audit --disease obesity

# Leakage-safe stratified splitting only
python -m pipeline.splitting --disease obesity
```

Pipeline artifacts produced:
- **Audit reports:** `data/processed/obesity_audit.json`, `docs/dataset-audits/obesity_audit_report.md`
- **Frozen split manifest:** `data/manifests/obesity_split_manifest.json` (70% Train, 15% Val, 15% Test; 24 exact duplicates dropped)
- **Partition datasets:** `data/processed/obesity_train.csv`, `obesity_val.csv`, `obesity_test.csv`
- **Serialized preprocessors:** `artifacts/obesity_e2_lifestyle_only_pipeline.joblib`, `artifacts/obesity_e1_bmi_inclusive_pipeline.joblib`

### 3. Run Automated Tests & Coverage

```bash
# Run pytest with coverage report
pytest --cov=pipeline --cov=api tests/ -v
```

Tests execute using lightweight synthetic fixtures and real preprocessing round-trips without external downloads.

### 4. Train Module 2 models

The training command fits Logistic Regression, Random Forest and CatBoost candidates
using fresh preprocessing inside each stratified training fold. It selects a champion
by cross-validated macro-F1, calibrates it on `obesity_val.csv`, and evaluates the
calibrated artifact once on the frozen test partition:

```bash
python -m pipeline.training --folds 5
```

Outputs are written to `artifacts/` and include one model and metrics JSON for each
obesity feature set. The test partition is never used for model selection or
calibration.

### 5. Run the API Server

```bash
# Launch FastAPI development server
uvicorn api.main:app --reload --port 8000
```

- **Interactive Swagger Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check:** `GET http://127.0.0.1:8000/health`
- **Readiness Check:** `GET http://127.0.0.1:8000/readiness` (reports trained and pending specialist states)
- **Obesity E2 Screening:** `POST http://127.0.0.1:8000/api/v1/screen/obesity`

### 6. Run the frontend

```bash
cd web
npm ci
npm run dev
```

The UI includes an explicit consent notice, keyboard-accessible validated screening
fields, model readiness/result states, and a separate wellness panel. Wearable
values remain unavailable until an approved source is connected.

---

## Module 1 Verification Status

| Exit Gate | Status | Evidence |
|---|---|---|
| **G0: Development Baseline** | Completed | Passing CI tests, pinned requirements, structured repo |
| **G1: Approved Data Contract** | Completed | `config/datasets.yaml`, `config/features.yaml`, `docs/data-dictionary.md` |
| **G2: Dataset Audit** | Completed | `docs/dataset-audits/obesity_audit_report.md` (0 blocking findings) |
| **G3: Frozen Partitions** | Completed | `data/manifests/obesity_split_manifest.json` (Seed 42, no overlap, verified reproducibility) |
| **G4: Tested Preprocessing** | Completed | Fit on train only, transformed feature mappings saved, round-trip verified |
| **G5: Module 1 Handoff** | Completed | `docs/module-1-handoff.md`, partitioned CSVs, handoff instructions |
| **G6: Prototype Integration** | Completed | FastAPI scaffold (`api/`), structured 422 errors, 501 for pending diseases |
