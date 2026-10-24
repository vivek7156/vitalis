## Technology Stack

# Vitalis – Technology Stack Document

## 1. Stack principles

The Vitalis stack shall be:

- Open source where practical
- Reproducible on a student laptop
- Modular across disease models
- Suitable for tabular machine learning
- Explainable and auditable
- Compatible with offline training and online inference
- Replaceable at storage and model boundaries
- Simple enough for a four-person student team

The stack is a baseline. Any change shall be recorded in the decision log and checked against the project requirements.

## 2. Final baseline stack

| Layer | Selected technology | Baseline |
|---|---|---|
| Programming language | Python | 3.11; Python 3.10 minimum |
| Frontend language | TypeScript or JavaScript | Current Node.js LTS |
| Data handling | Pandas, NumPy | Latest pinned compatible versions |
| ML framework | scikit-learn | Pipelines, preprocessing, metrics and tuning |
| Boosting model | CatBoost | Primary candidate; XGBoost fallback |
| Imbalance handling | Class weights; imbalanced-learn optional | Resampling only within training folds |
| Explainability | SHAP TreeExplainer | Primary explanation method |
| Optional explanation comparison | LIME | Research comparison only |
| Visualisation | Plotly, Matplotlib, Seaborn | Dashboard and report figures |
| Backend API | FastAPI and Uvicorn | REST API and OpenAPI contract |
| Validation | Pydantic | Request, response and configuration schemas |
| Frontend | React with Vite | Responsive single-page interface |
| Styling | Tailwind CSS | Shared responsive components |
| Database | SQLite through SQLAlchemy | Runs, models, users and controlled logs |
| Authentication | OAuth2 password flow, JWT, bcrypt | Researcher and administrator access |
| Model artifacts | joblib | Saved pipelines and explainers |
| Configuration | YAML and JSON | Features, experiments, thresholds and messages |
| Testing | pytest, FastAPI TestClient, Vitest | Unit, API and UI tests |
| Browser testing | Playwright | Optional end-to-end demo tests |
| Code quality | ruff, Git | Linting and version control |
| CI | GitHub Actions | Tests and lint on every push |
| Packaging | venv and pinned requirements | Docker Compose optional |
| Deployment | Local student laptop first | Optional free-tier hosted demo |

## 3. Architecture baseline

Vitalis shall use the following separation:

```text
Offline training pipeline
  → dataset audit
  → disease-specific preprocessing
  → training and tuning
  → calibration and evaluation
  → explanations
  → versioned model artifacts

FastAPI inference service
  → input validation
  → routing and eligibility
  → specialist model tools
  → explanation and result aggregation
  → safety checks
  → controlled logging

React web application
  → screening form
  → disease results
  → explanations
  → wellness panel
  → researcher dashboard
  → administrator console
```

The API shall load trained artifacts. It shall not train models during a user request.

## 4. Recommended repository structure

```text
vitalis/
├── README.md
├── pyproject.toml
├── requirements.txt
├── package.json
├── .env.example
├── .gitignore
├── config/
│   ├── diseases.yaml
│   ├── features.yaml
│   ├── experiments.yaml
│   ├── explanations.yaml
│   ├── safety.yaml
│   ├── tips.yaml
│   └── wellness_bands.yaml
├── data/
│   ├── raw/
│   │   ├── obesity/
│   │   ├── diabetes/
│   │   ├── cardiovascular/
│   │   ├── masld/
│   │   └── wearable/
│   ├── processed/
│   └── manifests/
├── pipeline/
│   ├── audit.py
│   ├── validation.py
│   ├── splitting.py
│   ├── preprocessing.py
│   ├── training.py
│   ├── calibration.py
│   ├── evaluation.py
│   ├── robustness.py
│   ├── explainability.py
│   └── registry.py
├── artifacts/
│   └── <model_id>/
│       ├── pipeline.joblib
│       ├── explainer.joblib
│       ├── metrics.json
│       ├── model_card.md
│       └── manifest.json
├── api/
│   ├── main.py
│   ├── routers/
│   ├── schemas/
│   ├── services/
│   ├── disease_tools/
│   ├── repositories/
│   ├── auth/
│   └── safety/
├── web/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── types/
│   │   └── charts/
│   └── package.json
├── database/
│   ├── models.py
│   └── migrations/
├── tests/
│   ├── pipeline/
│   ├── api/
│   ├── routing/
│   ├── leakage/
│   ├── determinism/
│   └── web/
└── docs/
    ├── project-requirements.md
    ├── tech-stack.md
    ├── model-cards/
    ├── dataset-audits/
    └── decisions.md
```

## 5. Python dependencies

### 5.1 Required runtime and ML packages

```text
python==3.11.*
pandas
numpy
scikit-learn
catboost
shap
joblib
pyyaml
pydantic
fastapi
uvicorn[standard]
sqlalchemy
python-multipart
python-jose[cryptography]
bcrypt
```

### 5.2 Optional packages

```text
imbalanced-learn
xgboost
lime
plotly
matplotlib
seaborn
alembic
psycopg2-binary
```

Optional packages shall be added only when a documented requirement needs them. Dependency versions shall be pinned after the initial environment is tested.

## 6. Frontend dependencies

Recommended packages:

```text
react
react-dom
vite
tailwindcss
axios or fetch
react-router-dom
plotly.js or react-plotly.js
zod or equivalent client validation library
vitest
```

The frontend shall use shared components for:

- Consent and disclaimer banners
- Validated form fields
- Disease result cards
- Explanation factors
- Uncertainty notices
- Wellness indicators
- Researcher charts
- Error messages

## 7. Disease-model technology pattern

Every disease module shall implement the same conceptual interface:

```python
class DiseaseModelTool:
    disease_name: str
    model_id: str
    required_features: list[str]

    def validate_inputs(self, profile): ...
    def predict(self, profile): ...
    def explain(self, profile, prediction): ...
    def metadata(self): ...
```

The concrete implementation may differ by disease, but the external response contract shall remain consistent.

### 7.1 Obesity module

- Dataset: UCI obesity-level dataset or an approved version.
- E1: BMI-inclusive configuration with height and weight.
- E2: lifestyle-only configuration excluding height and weight.
- Candidate models: Logistic Regression, Decision Tree, Random Forest and CatBoost.
- Explanation: SHAP TreeExplainer for tree models.
- Special audit: BMI-derived target dependence and synthetic-data fraction.

### 7.2 Diabetes module

- Use a separately documented dataset and target.
- Clearly distinguish glucose prediction from diabetes-status classification.
- Inspect whether glucose or related values are direct components of the target.
- Do not present glucose forecasting as disease diagnosis.
- Use a separate preprocessing pipeline and model artifact.

### 7.3 Cardiovascular module

- Use a separate cardiovascular-risk dataset and target definition.
- Define the prediction horizon and required clinical measurements.
- Do not impute important clinical measurements by guessing.
- Report subgroup performance where sample sizes permit.
- Use SHAP or a documented model-specific explanation method.

### 7.4 MASLD module

- Use anthropometric, metabolic and laboratory inputs only when documented by the selected dataset.
- Use compact feature selection where it improves auditability.
- Label the output as MASLD screening support.
- Do not present the result as confirmed liver disease.

## 8. Data and preprocessing rules

- Raw datasets are read-only.
- Each disease has its own data directory and manifest.
- Dataset checksums shall be stored.
- Preprocessing shall be implemented with scikit-learn pipelines.
- Categorical and numeric columns shall be handled explicitly.
- Splitting shall occur before resampling.
- Imputation and scaling shall be fitted only on training folds.
- Test data shall not influence feature selection or calibration decisions.
- Duplicate and near-duplicate records shall be investigated.
- Synthetic records shall be documented rather than treated as equivalent to independently collected clinical data.
- Wearable data shall use a separate cleaning and storage path.

## 9. Model artifacts and registry

Each model artifact directory shall contain:

```text
artifacts/<model_id>/
├── pipeline.joblib
├── explainer.joblib
├── metrics.json
├── model_card.md
├── config.yaml
└── manifest.json
```

The manifest should include:

- Model ID
- Disease name
- Feature-set ID
- Dataset name and version
- Dataset checksum
- Training seed
- Algorithm and hyperparameters
- Calibration method
- Python and package versions
- Creation timestamp
- Intended use
- Known limitations
- Self-check input and expected output

## 10. API design

### 10.1 Public endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/screen` | Validate profile, route to eligible tools and return aggregated results |
| POST | `/api/v1/predict/{disease}` | Run one specialist model when the required inputs are available |
| GET | `/api/v1/wellness/profiles` | List sample wellness profiles |
| GET | `/api/v1/wellness/profiles/{id}` | Return one wellness summary |
| GET | `/api/v1/health` | Return service status and active model IDs |

### 10.2 Protected endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/auth/login` | Authenticate researcher or administrator |
| GET | `/api/v1/experiments` | List experiment runs |
| GET | `/api/v1/experiments/{id}` | View metrics and plots for a run |
| GET | `/api/v1/experiments/compare` | Compare disease or obesity experiments |
| GET | `/api/v1/experiments/{id}/export` | Export approved results |
| GET | `/api/v1/models` | List model versions |
| POST | `/api/v1/models/{id}/activate` | Activate a model after self-check |
| GET/POST | `/api/v1/admin/users` | Manage researcher accounts |
| GET | `/api/v1/admin/logs` | Review controlled logs |
| DELETE | `/api/v1/admin/logs/predictions` | Purge prediction logs |

The exact endpoint names shall be finalised in the FastAPI OpenAPI document. The API may use `/api/v1/predict` instead of `/api/v1/screen` if the team keeps the original SRS route, but the contract must remain consistent.

## 11. Database technology

SQLite through SQLAlchemy shall store:

- Users and roles
- Dataset metadata
- Feature configurations
- Experiment runs
- Model versions
- Model metrics
- Robustness results
- Controlled prediction logs
- Application and error logs

Large model artifacts shall remain files rather than database blobs.

Repository interfaces shall isolate database access so PostgreSQL can be considered later without changing the API contract.

## 12. Security and privacy implementation

- Use bcrypt or Argon2 for passwords.
- Use JWT access tokens for protected routes.
- Enforce role checks in one reusable FastAPI dependency.
- Use Pydantic validation on every request.
- Use SQLAlchemy bound parameters.
- Keep secrets in environment variables, never in Git.
- Provide `.env.example` without real credentials.
- Avoid direct identifiers in screening requests and logs.
- Require explicit consent before storing prediction inputs.
- Provide an administrator-controlled purge operation.
- Use HTTPS for any hosted demo.
- Do not store medical data unnecessarily.

## 13. Testing strategy

### 13.1 Unit tests

Test:

- Input validators
- Feature mappings
- Dataset audits
- Preprocessing pipelines
- Factor aggregation
- Explanation templates
- Confidence and uncertainty rules
- Wellness thresholds

### 13.2 API and integration tests

Use `pytest` and FastAPI `TestClient` to verify:

- Valid screening requests produce responses matching the common result schema.
- Invalid types, unknown categories, unsupported units and out-of-range values return field-level errors.
- Missing required clinical measurements produce `insufficient_input`, not a fabricated prediction.
- Requests without authentication receive `401` on protected routes.
- Authenticated researchers receive `403` when calling administrator-only routes.
- Inactive accounts cannot obtain new access tokens.
- Missing or invalid model artifacts produce structured errors without stack traces.
- A failure in one specialist tool does not remove successful results from other tools.
- Disclaimers and model identifiers remain present in every successful specialist result.
- Prediction inputs are not persisted when logging consent is absent.
- Purging prediction logs removes the intended records without deleting experiment metadata.

Declare static routes such as `/experiments/compare` before dynamic routes such as `/experiments/{id}`, or use unambiguous path designs, to prevent route conflicts.

### 13.3 Routing tests

Maintain a version-controlled routing test suite containing synthetic profiles and expected eligible tools. These profiles are software test fixtures, not clinical validation evidence.

| Scenario | Expected behaviour |
|---|---|
| Complete obesity E2 inputs only | Run the eligible obesity E2 tool; explain why other tools cannot run |
| Complete inputs for multiple diseases | Invoke each eligible tool independently |
| A required laboratory measurement is absent | Mark the affected tool `insufficient_input`; list the missing field |
| Required values use an unsupported unit | Return a validation error; do not reinterpret the number |
| Profile lies outside a model's supported population | Apply the documented eligibility policy and display the limitation |
| No specialist tool is eligible | Return structured insufficient-information results, not a disease estimate |
| An eligible tool is unavailable | Report `model_unavailable` for that tool while preserving other results |
| Wearable sample profile changes | Disease predictions and routing remain unchanged |
| An unexpected field contains instructions | Reject or ignore it according to the schema; never execute it |

Evaluate expected and actual tool sets, including unnecessary selections and missed eligible tools. Define metric denominators in the evaluation report; a single routing-accuracy percentage is insufficient without a scoring rule.

### 13.4 Leakage and reproducibility tests

- Check that the same individual or identified duplicate group cannot appear across training and held-out partitions.
- Use group-aware or temporal splitting where the dataset structure requires it; stratification alone is not sufficient for repeated measurements.
- Confirm preprocessing, feature selection and resampling are fitted only within the training process.
- Confirm hyperparameter selection and calibration do not use the final test set.
- Verify obesity E1 and E2 use the same eligible records, split membership and seeds.
- Verify E2 excludes height, weight, BMI and configured direct derivatives.
- Save the split manifest and dataset checksum with every run.
- Compare repeat runs within documented numerical tolerances in the same supported environment.

Exact bit-for-bit reproducibility across operating systems, library versions and hardware is not assumed.

### 13.5 Explainability and safety tests

- Verify local explanations identify the model, explained class or output, explanation method and output scale.
- Check that transformed features map back to the correct original fields.
- Use deterministic sorting and tie-breaking for displayed factors.
- Check explanation templates for unsupported causal, diagnostic or treatment claims.
- Verify missing or failed explanations are explicitly labelled unavailable.
- Test that uncertainty, population restrictions and dataset limitations remain visible.
- Test the actual rendered result text, not just individual template files.

**Calibration boundary:** SHAP values from a base classifier explain that classifier's output, not automatically the final calibrated probability. Record the explained output and scale. Either explain the final prediction function using a suitable method or label the base-model explanation clearly; do not imply that its contributions add up to the displayed calibrated probability.

For multiclass obesity models, positive and negative contributions refer to support for the explained class. They do not necessarily mean a higher or lower obesity level.

### 13.6 Frontend and end-to-end tests

Use Vitest for component behaviour and Playwright, if adopted, for the complete browser journey:

1. Open the consent screen and accept the screening notice.
2. Enter a valid profile.
3. Submit the screening request.
4. Inspect routing status and each disease result.
5. Inspect explanation, uncertainty and limitation notices.
6. Open the separate wellness panel.
7. Sign in as a researcher and inspect an experiment.
8. Verify an unauthorised administrator action is blocked.

Test keyboard navigation, labelled fields, readable contrast and layouts from 360 px width. Do not rely on colour alone to communicate risk or status.

### 13.7 Coverage and CI gates

Target at least 70% line coverage for pipeline and API code. Critical routing, consent, access-control and leakage rules require explicit tests regardless of the coverage percentage.

CI shall run linting, unit tests and API tests on each pull request. Frontend checks shall run once the web application exists. Full training and performance benchmarks may run separately because they require datasets and longer execution time.

## 14. Development environment and dependency management

### 14.1 Environment baseline

- Use Python 3.11 as the initial development interpreter.
- Treat Python 3.10 support as a compatibility claim that requires testing before release.
- Choose and record a supported Node.js LTS release for the frontend.
- Use an isolated Python environment and a committed frontend lockfile.
- Record exact package versions only after installation, import checks, tests and artifact loading succeed together.

**Dependency-list clarification:** `python==3.11.*` in Section 5 describes the interpreter requirement. It must not be copied into a pip `requirements.txt` file. Python is installed separately. Likewise, browser `fetch` is built in and is not an npm dependency.

### 14.2 Initial Python environment

Run from the repository root after a tested `requirements.txt` has been committed:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Or on Linux/macOS:

```bash
source .venv/bin/activate
```

Then install dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Development dependencies shall include the chosen test and lint tools, including `pytest`, `pytest-cov`, `httpx` for the API test client and `ruff`. Keep development-only dependencies distinguishable from runtime dependencies.

### 14.3 Frontend environment

Once `web/package.json` and its npm lockfile exist:

```bash
cd web
npm ci
npm run dev
```

The team shall define the `dev`, `build` and `test` scripts in `web/package.json`. Do not document project-specific commands as available until they have been implemented and verified.

### 14.4 Backend startup

Once `api/main.py` exposes the FastAPI application as `app`:

```bash
python -m uvicorn api.main:app --reload
```

Use reload mode for development only. Document artifact prerequisites and the behaviour when no models are active. The service may expose health and administration functions without an active specialist model, but it must never advertise that unavailable model as ready for prediction.

### 14.5 Secrets and local files

Provide `.env.example` containing configuration names and safe placeholders, not working credentials. Application code must explicitly load environment configuration; the existence of a `.env` file alone does not load it.

Exclude the following from Git unless a reviewed exception applies:

- `.env` and signing keys
- `.venv/` and `node_modules/`
- Local databases and prediction logs
- Personal or restricted health records
- Unlicensed dataset copies
- Large trained artifacts and temporary experiment output

Commit dataset acquisition instructions, checksums, manifests and small synthetic test fixtures instead. Choose a separate approved location for distributing model artifacts.

## 15. Constrained orchestration implementation

### 15.1 Baseline components

| Component | Responsibility |
|---|---|
| Profile validator | Validate supplied fields, units and supported values |
| Tool registry | List approved tools, feature schemas and active model versions |
| Eligibility evaluator | Check required inputs and supported population constraints |
| Routing policy | Select eligible tools using explicit, versioned rules |
| Tool executor | Invoke approved adapters with bounded execution time |
| Result validator | Check each tool response against the common schema |
| Aggregator | Collect independent results without rewriting predictions |
| Safety renderer | Attach approved notices and present cautious explanations |

A lightweight Python service is sufficient for this baseline; an agent framework is not required.

### 15.2 Execution rules

1. Validate the profile and reject contradictory or invalid supplied values.
2. Evaluate eligibility separately for every requested or enabled disease tool.
3. Pass each tool only its approved feature subset.
4. Pin the model ID for each invocation so an activation during the request cannot mix versions within one result.
5. Execute eligible tools with configured timeouts and bounded concurrency.
6. Validate responses and preserve prediction values, probabilities and model identifiers.
7. Return successful results alongside explicit per-tool failures or missing-input statuses.
8. Record routing-policy version and timings without storing raw clinical inputs by default.

Do not average scores across diseases or create a universal health score. Different targets, horizons, datasets and calibration populations make those values non-interchangeable.

### 15.3 Optional LLM experiment

An LLM is not required for the working prototype. If evaluated, it shall operate behind the same tool allowlist, schemas and eligibility checks as the deterministic router.

It shall have no unrestricted code execution, database access, treatment authority or permission to invent inputs. Profile content and external text shall be treated as data, not instructions. Compare its routing correctness, latency, cost and failure behaviour against the deterministic baseline before deciding whether to retain it.

## 16. Evaluation and performance baseline

### 16.1 Training and model selection

- Train a dummy baseline and the approved candidate models for each disease.
- Tune models using training-only cross-validation.
- Fit calibration using training folds or a separate calibration partition, never the final test set.
- Select models using validation performance, calibration, runtime and interpretability.
- Evaluate the frozen selected pipeline on the held-out test set.
- Report unfavourable results and unsupported metrics explicitly rather than omitting them.

CatBoost is a primary candidate, not a guaranteed best model for every disease. Logistic Regression and other interpretable alternatives remain valid deployment choices when supported by evaluation.

If a target is continuous glucose forecasting rather than classification, define regression and time-series evaluation separately. Classification metrics and class-probability calibration must not be applied indiscriminately to it.

### 16.2 Timing measurements

Measure validation, routing, each specialist prediction, explanation generation and total request time separately. Record hardware, active model count, concurrency and whether artifacts were already loaded.

The current 2-second prediction target is a working single-request budget; measure and confirm whether it applies to one specialist or the complete multi-tool screen. Do not claim that the complete screen meets the target based only on a single-model benchmark.

Likewise, confirm the 30-minute training target against the full multi-disease configuration. Cap search trials and parallel workers to prevent CPU oversubscription and memory exhaustion.

### 16.3 Evaluation deliverables

Each release candidate shall include:

- Dataset audit and target-definition report per disease
- Split and experiment manifests
- Baseline and candidate-model comparison
- Calibration and robustness results
- Global and example local explanations
- Routing test cases and metric definitions
- End-to-end correctness and latency results
- Known limitations, unsupported populations and unresolved issues

Only report measured results. Keep proposed targets separate from achieved values.

## 17. Deployment and operational design

### 17.1 Local demonstration

The baseline deployment uses one student laptop running the API, frontend and SQLite database. Models are trained beforehand. Pin the demonstration's model versions and prepare a small set of synthetic profiles covering success, missing inputs and partial tool failure.

Document exact startup commands and prerequisites in the root `README.md` after implementation.

### 17.2 Optional hosted demonstration

A hosted deployment shall use HTTPS, restricted CORS origins, protected administrator routes and persistent storage for required metadata and artifacts. Do not assume free-tier hosts retain files or remain continuously available; verify the selected platform's current limits before deployment.

Containerisation is optional. If adopted, keep the API and frontend packaging simple and do not add extra services without a demonstrated need.

### 17.3 Model activation and rollback

Before activation:

1. Verify the artifact's provenance, checksum and supported package versions.
2. Load it in a trusted environment.
3. Validate its input and output schemas.
4. Run its self-check and explanation checks.
5. Confirm that model-card limitations and required metadata exist.
6. Activate the version for the relevant disease and feature configuration.

Keep the previous approved version available for rollback. In a multi-worker deployment, model activation must explicitly refresh every worker; changing a database flag alone does not update objects already held in memory.

**Artifact security:** joblib and pickle-based files can execute code while loading. Load only team-approved artifacts from trusted storage. Never accept public model uploads into the inference process.

### 17.4 Health and readiness

Distinguish service liveness from model readiness. The health response should identify unavailable modules without exposing filesystem paths, secrets or patient inputs. A broken specialist model must be excluded from routing until it passes its checks again.

## 18. Logging, retention and backup

### 18.1 Default logging policy

Record technical metadata such as request ID, routing-policy version, invoked model IDs, status codes and timings. Do not log request bodies, authorisation headers, passwords or raw clinical values by default.

A request ID is for operational tracing, not a screening-user account. Avoid unnecessary persistent linkage between a person's assessments.

### 18.2 Optional prediction logging

Storing prediction inputs requires separate, explicit consent and guide approval. Define retention duration, authorised access and deletion behaviour before enabling it.

Clinical and demographic inputs can remain sensitive or potentially identifying even without names or phone numbers. Do not describe such records as guaranteed anonymous.

### 18.3 Backup and restoration

Back up required experiment metadata, configuration and approved model manifests. Use a SQLite-supported backup approach or stop writes before copying the database. Test restoration at least once before the final demonstration.

Prediction-data retention and purge rules must include backups; deleting live rows alone may leave older copies intact. Store backups outside public web directories and restrict access.

## 19. Implementation roadmap

| Stage | Main work | Completion evidence |
|---|---|---|
| 1. Baseline | Repository, environments, requirements and API schemas | A clean setup and passing minimal CI |
| 2. Data | Dataset selection, licences, targets and audits | Approved manifests and audit reports |
| 3. First vertical slice | Obesity E2 pipeline, tool adapter and result screen | One complete screening journey |
| 4. Obesity comparison | E1, shared splits and researcher comparison | Reproducible E1/E2 report |
| 5. Additional specialists | Diabetes, CVD and MASLD pipelines and adapters | Independent model cards and evaluation reports |
| 6. Orchestration | Eligibility, routing, aggregation and partial failures | Passing routing and schema tests |
| 7. Explanation and wellness | Reviewed templates and separate sample-data panel | Explanation checks and isolation tests |
| 8. Research and administration | Metrics views, authentication and activation | Role tests and activation/rollback checks |
| 9. Hardening | Robustness, accessibility, privacy and performance | Recorded end-to-end test results |
| 10. Delivery | Documentation, frozen artifacts and demonstration | Clean-clone trial and approved release checklist |

Frontend prototyping and disease-model development may proceed in parallel after schemas are agreed. Additional disease modules remain blocked from activation until their datasets, targets and supported populations are documented.

## 20. Decisions, changes and long-term reference

### 20.1 Decision log

Maintain `docs/decisions.md` with these fields:

| Field | Meaning |
|---|---|
| Decision ID | Stable identifier such as `ADR-001` |
| Status | Proposed, accepted, superseded or rejected |
| Context | Requirement or problem motivating the decision |
| Options | Alternatives considered |
| Decision | Selected approach and rationale |
| Consequences | Trade-offs, risks and migration work |
| Verification | Tests or evidence needed |
| Owner and date | Person responsible and decision date |

Initial decisions to settle include final disease datasets, frontend language, supported runtime versions, probability-display policy, logging retention, routing timeouts and hosting. Do not record a proposal as accepted without team agreement.

### 20.2 Change-control checklist

Before changing a dependency, model, schema or routing rule:

- Identify the affected project-requirement IDs.
- Record the reason and affected modules.
- Check dataset and software licences where applicable.
- Update configuration and documentation.
- Run relevant tests and artifact compatibility checks.
- Retrain and re-evaluate if the learned pipeline or feature semantics change.
- Update OpenAPI and frontend types if the API changes.
- Preserve a rollback path.

### 20.3 Working-document responsibilities

| File | Maintains |
|---|---|
| `docs/project-requirements.md` | Scope, requirement IDs, acceptance criteria and open decisions |
| `docs/tech-stack.md` | Technology baseline, component boundaries and operational rules |
| `README.md` | Verified setup, startup and test commands |
| `docs/decisions.md` | Reasons for accepted architectural changes |
| `docs/dataset-audits/` | Sources, licences, target construction and dataset limitations |
| `docs/model-cards/` | Intended use, features, evaluation and model limitations |
| Model artifact manifests | Exact data, code, configuration and dependency provenance |

Keep the requirements and stack sections aligned with the SRS and system-design document. Where requirements use different identifiers, maintain an explicit mapping rather than silently renumbering them.

### 20.4 Release checklist

- [ ] Dependencies are pinned and install successfully in a clean environment.
- [ ] Dataset licences, checksums and target definitions are recorded.
- [ ] Active model artifacts pass provenance and self-check tests.
- [ ] No held-out test data influenced fitting or model selection.
- [ ] Routing handles missing inputs, unsupported populations and tool failures.
- [ ] Probability displays and explanations accurately describe their meaning and scale.
- [ ] Screening results remain separate from wellness context.
- [ ] Consent, privacy, retention and disclaimer wording are approved.
- [ ] Protected routes enforce authentication and authorisation.
- [ ] No credentials, sensitive logs or restricted records are committed.
- [ ] Evaluation reports distinguish achieved results from proposed targets.
- [ ] Setup, demonstration and rollback procedures have been tested.
