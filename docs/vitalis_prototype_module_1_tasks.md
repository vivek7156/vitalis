# Vitalis – Prototype Development and Module 1 Implementation Checklist

```
Vitalis – Prototype Development and Module 1 Implementation Checklist
```

| Item | Baseline |
|---|---|
| Project | Vitalis – Explainable Agentic AI Framework for Multi-Disease Health-Risk Screening and Wellness Monitoring |
| Document type | Working implementation checklist |
| Status | Planned; check items only after verification |
| Module 1 | Data acquisition, audit, validation, leakage-safe splitting and preprocessing |
| Initial implementation | Obesity E2 data pipeline, followed by the E1 comparison and reusable disease configurations |
| Reference documents | Project Requirements, Technology Stack, SRS and System Design Document |
| Maintained as | `docs/prototype-module-1-tasks.md` |

## 1. Scope and working assumption

**Module 1 means M1: Data and Preprocessing Pipeline**, as defined in the system-design document. It does not mean the complete obesity prediction system.

This document contains two connected checklists:

1. **Prototype foundation:** repository, contracts, API/UI scaffolding and a demonstrable development workflow.
2. **Module 1 implementation:** acquiring and auditing data, defining targets and features, preventing leakage, producing reproducible partitions and building reusable preprocessing components.

Obesity E2 is the first implementation path. E1 uses the same records and split membership for a controlled comparison. Diabetes, cardiovascular disease and MASLD receive reusable configuration boundaries, but must not be marked implemented until their datasets and targets are approved.

Training, calibration, model selection and SHAP belong to later modules. Module 1 prepares and tests their inputs; it does not claim to deliver validated disease models.

### Priority labels

- **P0 — Required:** blocks Module 1 completion or a trustworthy prototype foundation.
- **P1 — Next:** required for the broader prototype, but may follow the first Module 1 milestone.
- **P2 — Optional:** enhancement, not a completion blocker.

All items start unchecked. “Done” means implemented, reviewed and supported by the stated evidence—not merely started.

## 2. Milestones and exit gates

| Gate | Deliverable | Exit condition |
|---|---|---|
| G0 | Development baseline | Clean setup works; requirements and module boundaries are agreed |
| G1 | Approved data contract | Target, fields, units, provenance and permitted use are documented |
| G2 | Dataset audit | Audit executes and all blocking findings have an explicit resolution |
| G3 | Frozen partitions | Leakage checks pass and split membership is recorded |
| G4 | Tested preprocessing | Transformers fit on training data only and reload correctly |
| G5 | Module 1 handoff | Artifacts, reports, tests and handoff instructions are reviewed |
| G6 | Prototype integration | API/UI accurately show implemented, unavailable and incomplete states |

## 3. Ownership and coordination — P0

Assign these roles within the four-person team; one person may cover more than one role.

- [ ] **T-ORG-01:** Assign a Module 1 implementation owner.
- [ ] **T-ORG-02:** Assign a dataset-audit and target-definition owner.
- [ ] **T-ORG-03:** Assign a test/reproducibility reviewer other than the primary implementer.
- [ ] **T-ORG-04:** Assign an API/frontend integration owner.
- [ ] **T-ORG-05:** Agree how blocking data or target issues are escalated to the guide.
- [ ] **T-ORG-06:** Record ownership and task status in the project issue tracker.
- [ ] **T-ORG-07:** Map checklist task IDs to the project requirement IDs without renumbering the requirements.

**Evidence:** Assigned issues and one reviewed scope/decision entry.

## 4. Prototype foundation checklist

### 4.1 Repository and environment — P0

- [ ] **T-SETUP-01:** Create the repository structure for `config/`, `pipeline/`, `api/`, `web/`, `tests/`, `data/` and `docs/`.
- [ ] **T-SETUP-02:** Commit `docs/project-requirements.md` and `docs/tech-stack.md` as the working baselines.
- [ ] **T-SETUP-03:** Add this checklist and `docs/decisions.md`.
- [ ] **T-SETUP-04:** Record the initial Python interpreter version and verify the chosen dependencies work together.
- [ ] **T-SETUP-05:** Create an isolated Python environment and separate runtime/development dependency lists.
- [ ] **T-SETUP-06:** Pin tested package versions; do not put the Python interpreter itself in pip requirements.
- [ ] **T-SETUP-07:** Add `pytest`, coverage tooling and `ruff`; verify a minimal test and lint run.
- [ ] **T-SETUP-08:** Add `.gitignore` entries for environments, secrets, local databases, logs, restricted data and generated artifacts.
- [ ] **T-SETUP-09:** Add `.env.example` with safe placeholders and document how configuration is loaded.
- [ ] **T-SETUP-10:** Add CI for lightweight linting and tests using synthetic fixtures, not private or large datasets.
- [ ] **T-SETUP-11:** Verify setup from a clean clone on a second team member’s machine.

**Evidence:** Passing CI and verified README setup instructions.

### 4.2 Contracts and architecture — P0

- [ ] **T-CONTRACT-01:** Agree disease identifiers and obesity feature-set identifiers, including E1 and E2.
- [ ] **T-CONTRACT-02:** Define dataset, feature, split and preprocessing manifest schemas.
- [ ] **T-CONTRACT-03:** Define the specialist-result contract and explicit unavailable/insufficient-input/error states.
- [ ] **T-CONTRACT-04:** Distinguish disease-status classification, future-risk prediction and glucose forecasting in the target metadata.
- [ ] **T-CONTRACT-05:** Define the handoff boundary between Module 1 and training/evaluation.
- [ ] **T-CONTRACT-06:** Agree canonical screening endpoint naming and record it in OpenAPI when implemented.
- [ ] **T-CONTRACT-07:** Define required-field policy separately from optional-field imputation policy.
- [ ] **T-CONTRACT-08:** Require target-specific population and input eligibility rules before a disease tool can become active.

**Evidence:** Reviewed schemas and an architecture decision record.

### 4.3 API and frontend scaffolding — P1

- [ ] **T-PROTO-01:** Create the FastAPI application with structured validation/error responses.
- [ ] **T-PROTO-02:** Add health/readiness reporting that distinguishes a running service from ready specialist models.
- [ ] **T-PROTO-03:** Create the React/Vite application and record a supported Node.js release.
- [ ] **T-PROTO-04:** Add consent, assessment, routing-status, result and separate wellness screen components.
- [ ] **T-PROTO-05:** Add loading, empty, validation-error, insufficient-input and unavailable-model states.
- [ ] **T-PROTO-06:** Use clearly labelled synthetic fixtures for UI development; never present mock predictions as real inference.
- [ ] **T-PROTO-07:** Keep unimplemented disease tools unavailable rather than returning invented scores.
- [ ] **T-PROTO-08:** Configure development CORS for explicitly allowed origins.
- [ ] **T-PROTO-09:** Verify the interface at 360 px width and using keyboard navigation.
- [ ] **T-PROTO-10:** Record which screens are scaffolds and which are connected to implemented services.

**Evidence:** Demonstrable scaffold with honest readiness states. A working prediction is not claimed until the training and inference modules are connected.

## 5. Module 1: dataset acquisition and provenance — P0

### 5.1 Obesity dataset

- [ ] **T-DATA-01:** Acquire the approved UCI obesity dataset from its documented source.
- [ ] **T-DATA-02:** Record source, acquisition date, dataset version if provided and licence/usage terms.
- [ ] **T-DATA-03:** Compute and store a checksum of the exact source file.
- [ ] **T-DATA-04:** Keep the raw file read-only and prohibit in-place cleaning.
- [ ] **T-DATA-05:** Record observed row/column counts and compare them with the source description.
- [ ] **T-DATA-06:** Document whether the stated attribute count includes the target column.
- [ ] **T-DATA-07:** Record the source-reported approximately 77% synthetic share; distinguish this from row-level synthetic provenance, which may be unavailable.
- [ ] **T-DATA-08:** Add reproducible acquisition instructions without redistributing data contrary to its terms.

### 5.2 Additional disease datasets

- [ ] **T-DATA-09:** Create separate dataset-config entries for diabetes, CVD and MASLD.
- [ ] **T-DATA-10:** For each selected dataset, record source, licence, target, population, sample structure and clinical-variable requirements.
- [ ] **T-DATA-11:** Mark unselected or unapproved datasets as pending; do not imply selection is complete.
- [ ] **T-DATA-12:** Record whether repeated individuals, multiple visits, sites or timestamps require grouped or temporal splitting.

**Evidence:** Dataset manifests, acquisition instructions and approval/pending status for each disease.

## 6. Module 1: target and feature contract — P0

- [ ] **T-SCHEMA-01:** Create a data dictionary covering raw column names, canonical names, types, categories, units and missing-value codes.
- [ ] **T-SCHEMA-02:** Document the exact target definition and how its labels were constructed.
- [ ] **T-SCHEMA-03:** Record the seven obesity classes and a stable class mapping.
- [ ] **T-SCHEMA-04:** Define E1’s approved feature list, including height and weight with explicit units.
- [ ] **T-SCHEMA-05:** Define E2’s lifestyle/demographic feature list, excluding height, weight, BMI and direct derivatives/proxies identified by the audit.
- [ ] **T-SCHEMA-06:** Verify no target column or post-outcome information enters either feature set.
- [ ] **T-SCHEMA-07:** Document raw-to-form mappings for the 14 E2 fields.
- [ ] **T-SCHEMA-08:** Inspect fractional values in source-encoded frequency fields; do not silently coerce them into integer categories.
- [ ] **T-SCHEMA-09:** Decide and document how user-facing choices map to training representations.
- [ ] **T-SCHEMA-10:** Define required and optional fields without treating missing required clinical measurements as imputable defaults.
- [ ] **T-SCHEMA-11:** Define supported ages and other eligibility limits from dataset evidence and guide review.
- [ ] **T-SCHEMA-12:** Separate observed dataset ranges from clinically justified validation ranges; document the source of each rule.
- [ ] **T-SCHEMA-13:** Define handling for unknown categories, unsupported units and extra fields.

**Evidence:** Reviewed data dictionary, feature configuration and target-definition report.

## 7. Module 1: loader and validation implementation — P0

- [ ] **T-LOAD-01:** Implement configurable loading without hard-coded local paths.
- [ ] **T-LOAD-02:** Validate file existence, supported format and expected columns.
- [ ] **T-LOAD-03:** Handle encoding, delimiter and missing-token conventions explicitly.
- [ ] **T-LOAD-04:** Detect accidental index columns and duplicate column names.
- [ ] **T-LOAD-05:** Validate row types, categories, numeric values and units.
- [ ] **T-LOAD-06:** Detect non-finite numbers and impossible or unsupported supplied values.
- [ ] **T-LOAD-07:** Distinguish a missing value from a legitimate zero.
- [ ] **T-LOAD-08:** Return structured row/field errors and counts of accepted, rejected and quarantined records.
- [ ] **T-LOAD-09:** Preserve source row references internally for audit and partition tracing; do not expose them as user identities.
- [ ] **T-LOAD-10:** Fail clearly when the target is missing or unusable.
- [ ] **T-LOAD-11:** Reject invalid configuration before processing the dataset.

**Evidence:** Loader tests and a validation report with no silent row loss.

## 8. Module 1: audit and leakage analysis — P0

- [ ] **T-AUDIT-01:** Generate class counts and proportions.
- [ ] **T-AUDIT-02:** Report missing counts, invalid values, feature types and numeric summaries.
- [ ] **T-AUDIT-03:** Identify exact duplicate rows.
- [ ] **T-AUDIT-04:** Identify duplicate feature rows with conflicting targets.
- [ ] **T-AUDIT-05:** Investigate near duplicates and document the similarity rule used.
- [ ] **T-AUDIT-06:** Check repeated participants or measurements when identifiers are available.
- [ ] **T-AUDIT-07:** Document BMI-derived target dependence in E1; distinguish current-level classification from future disease-risk prediction.
- [ ] **T-AUDIT-08:** Check each feature for target components, proxies and information unavailable at intended prediction time.
- [ ] **T-AUDIT-09:** Describe demographic/geographic coverage and unsupported populations.
- [ ] **T-AUDIT-10:** Record known synthetic-data generation before release; acknowledge that a later split cannot undo that historical generation process.
- [ ] **T-AUDIT-11:** Document any deduplication, exclusion or correction policy and its effect on sample counts.
- [ ] **T-AUDIT-12:** Avoid deleting outliers solely because they are unusual; record justification for exclusions.
- [ ] **T-AUDIT-13:** Produce machine-readable JSON and a human-readable Markdown audit report.
- [ ] **T-AUDIT-14:** Classify findings as blocking, accepted limitation or follow-up; obtain review before proceeding.

**Evidence:** `docs/dataset-audits/` report plus structured audit output and a resolved finding list.

## 9. Module 1: partitioning and reproducibility — P0

- [ ] **T-SPLIT-01:** Agree partition proportions and seed before running experiments.
- [ ] **T-SPLIT-02:** Choose stratified, group-aware or temporal splitting according to the dataset structure.
- [ ] **T-SPLIT-03:** Resolve duplicate/group relationships before partition assignment.
- [ ] **T-SPLIT-04:** Verify no identified participant or duplicate group crosses held-out boundaries.
- [ ] **T-SPLIT-05:** Check that partition sizes and class counts support the proposed evaluation.
- [ ] **T-SPLIT-06:** Create one shared obesity split manifest for E1 and E2 using the same eligible records.
- [ ] **T-SPLIT-07:** Save source checksum, record references, partition assignments, method, seed and configuration version.
- [ ] **T-SPLIT-08:** Freeze the held-out test partition and prohibit using it for tuning or preprocessing decisions.
- [ ] **T-SPLIT-09:** Document how later calibration will use training folds or a separate calibration partition, not the test set.
- [ ] **T-SPLIT-10:** Verify reruns reproduce partition membership in the supported environment.
- [ ] **T-SPLIT-11:** Record limitations when synthetic lineage or participant identity is unavailable; do not claim all dependence has been eliminated.

**Evidence:** Frozen split manifest and passing overlap/reproducibility tests.

## 10. Module 1: preprocessing implementation — P0

- [ ] **T-PREP-01:** Build a configurable preprocessing factory per disease and feature set.
- [ ] **T-PREP-02:** Separate numeric, categorical and any ordinal features explicitly.
- [ ] **T-PREP-03:** Select an approved encoding strategy for each candidate-model family.
- [ ] **T-PREP-04:** Define a documented policy for unseen categories at inference.
- [ ] **T-PREP-05:** Fit optional-field imputation only on the applicable training partition/fold.
- [ ] **T-PREP-06:** Prevent the imputer from bypassing required-field eligibility checks.
- [ ] **T-PREP-07:** Fit scaling only where the chosen algorithm needs it.
- [ ] **T-PREP-08:** Keep any learned feature selection inside training folds.
- [ ] **T-PREP-09:** Use scikit-learn `Pipeline`/`ColumnTransformer` where appropriate; document a separate compatible path if CatBoost uses native categorical inputs.
- [ ] **T-PREP-10:** Preserve training/inference feature ordering and transformed-feature names.
- [ ] **T-PREP-11:** Store mappings from transformed columns to original input fields for later explanations.
- [ ] **T-PREP-12:** Keep class weights as the initial imbalance strategy; introduce resampling only as an explicit experiment.
- [ ] **T-PREP-13:** If SMOTENC is used, retain categorical semantics at the resampling stage and place resampling inside an appropriate training pipeline—not after a global one-hot transformation.
- [ ] **T-PREP-14:** Keep validation/test samples at their original distribution; never resample them.
- [ ] **T-PREP-15:** Test fitting on training data and transformation of validation/test data without refitting.
- [ ] **T-PREP-16:** Save and reload a trusted test transformer; verify output values, shape, order and schema compatibility.
- [ ] **T-PREP-17:** Ensure the production training module receives an unfitted preprocessing factory so cross-validation does not reuse a transformer fitted on all training folds.

**Evidence:** Tested preprocessing factory, feature mappings and serialization round-trip report.

## 11. Separate wearable preparation — P1

- [ ] **T-WELL-01:** Record smartwatch and sleep dataset provenance, licence and available fields.
- [ ] **T-WELL-02:** Implement a separate cleaner and output directory.
- [ ] **T-WELL-03:** Validate available step, sleep, heart-rate and SpO₂ units and values.
- [ ] **T-WELL-04:** Show unavailable indicators as unavailable; do not fabricate readings.
- [ ] **T-WELL-05:** Preserve sample-data provenance in exported wellness records.
- [ ] **T-WELL-06:** Do not join unrelated smartwatch and sleep rows and imply they belong to one real person; label any assembled demonstration profile as synthetic.
- [ ] **T-WELL-07:** Keep status bands disabled until their sources and applicability are approved.
- [ ] **T-WELL-08:** Verify wearable columns cannot enter disease feature sets or influence routing.

**Evidence:** Cleaned sample records, provenance notes and isolation tests.

## 12. Module 1 automated test checklist — P0

### Loader and schema tests

- [ ] Valid synthetic fixture loads successfully.
- [ ] Missing file, unsupported format and missing column produce clear errors.
- [ ] Unknown categories, invalid numbers and unsupported units are detected.
- [ ] Missing values and legitimate zeros remain distinguishable.
- [ ] Invalid target labels and extra target-like columns are handled explicitly.

### Audit and partition tests

- [ ] Duplicate and conflicting-label fixtures are detected.
- [ ] Group leakage is detected when group metadata exists.
- [ ] Train, validation and test record memberships do not overlap.
- [ ] E1 and E2 use identical approved split membership.
- [ ] A changed source checksum invalidates reuse of an incompatible split manifest.
- [ ] Fixed configuration reproduces partition membership.

### Preprocessing tests

- [ ] Validation/test-only values do not influence learned imputation or scaling parameters.
- [ ] Preprocessing is fitted separately inside cross-validation folds.
- [ ] E2 rejects height, weight, BMI and excluded derivatives.
- [ ] Required missing inputs are not silently imputed for inference eligibility.
- [ ] Unknown-category policy behaves as documented.
- [ ] Transformed column mappings remain correct.
- [ ] Save/load round-trip preserves outputs within a documented numerical tolerance.
- [ ] Resampling, when enabled, affects training folds only.
- [ ] Wearable data remain outside disease pipelines.

### Failure and quality tests

- [ ] Configuration errors identify the offending setting.
- [ ] A failed run does not leave a completed manifest or overwrite a valid artifact.
- [ ] Logs do not dump full sensitive records or credentials.
- [ ] Lightweight tests run without downloading external datasets.
- [ ] Coverage is measured; the project’s 70% pipeline/API target does not replace explicit critical-rule tests.

- [ ] Configuration errors identify the offending setting.
- [ ] A failed run does not leave a completed manifest or overwrite a valid artifact.
- [ ] Logs do not dump full sensitive records or credentials.
- [ ] Lightweight tests run without downloading external datasets.
- [ ] Coverage is measured; the project’s 70% pipeline/API target does not replace explicit critical-rule tests.

**Evidence:** Passing test report, coverage report and CI run.

## 13. Proposed run interface and outputs

These are implementation targets, not commands claimed to exist already. Choose final command names during development and document them only after testing.

### Run-interface checklist — P0

- [ ] Provide one documented entry point for validating configuration and loading data.
- [ ] Support selecting disease, feature set, input path, output path and seed through configuration or arguments.
- [ ] Support audit-only execution without training.
- [ ] Support reproducible split generation and safe reuse of an existing compatible manifest.
- [ ] Return a non-zero process exit status on blocking failures.
- [ ] Print a concise summary with counts, findings and output locations—not raw patient records.
- [ ] Avoid overwriting previous successful outputs unless explicitly requested.

### Required output checklist — P0

- [ ] Source-data manifest with checksum and licence note.
- [ ] Target-definition report and data dictionary.
- [ ] Structured validation and audit reports.
- [ ] Reviewed exclusion/correction log.
- [ ] Frozen split manifest.
- [ ] E1/E2 feature configurations.
- [ ] Preprocessing factory and feature-name mapping.
- [ ] Reproducibility/environment record.
- [ ] Module 1 test report.
- [ ] Handoff README with verified commands and known limitations.

Generated cleaned or partitioned datasets must be stored only where their licence and sensitivity permit. A reproducible manifest may be preferable to committing copies of every partition.

## 14. Training and integration handoff

### Required handoff to Module 2 — P0

- [ ] **T-HANDOFF-01:** Training receives approved raw feature partitions, target labels and an unfitted preprocessing factory.
- [ ] **T-HANDOFF-02:** Training receives exact target/class mappings and supported feature schemas.
- [ ] **T-HANDOFF-03:** The handoff states which data may be used for tuning and calibration.
- [ ] **T-HANDOFF-04:** Training receives dataset limitations and unresolved risks.
- [ ] **T-HANDOFF-05:** A second team member executes the handoff workflow from the README.

### Integration preparation — P1

- [ ] **T-INTEGRATE-01:** API validation and frontend choices use reviewed mappings consistent with the training representation.
- [ ] **T-INTEGRATE-02:** A synthetic single-row fixture can pass validation and transformation.
- [ ] **T-INTEGRATE-03:** Required-feature metadata can support deterministic model eligibility checks.
- [ ] **T-INTEGRATE-04:** Unimplemented disease adapters return explicit unavailable states.
- [ ] **T-INTEGRATE-05:** Any dummy-model smoke test is labelled a software integration test, not a usable health model.
- [ ] **T-INTEGRATE-06:** Real inference, calibration and explanations remain blocked until their own implementation and evaluation gates pass.

## 15. Safety, privacy and artifact controls — P0

- [ ] No names, contact details or screening-user accounts are required.
- [ ] Raw prediction-input logging is disabled by default.
- [ ] Any later prediction logging has separate consent, retention and purge rules.
- [ ] Dataset rows without direct identifiers are not automatically described as guaranteed anonymous.
- [ ] Restricted data, local databases and secrets are excluded from Git.
- [ ] Only trusted, team-approved serialized artifacts are loaded; joblib/pickle files can execute code.
- [ ] Prototype notices state screening/research use and no clinical validation.
- [ ] E1 target dependence and the source dataset’s synthetic-data limitation are documented.
- [ ] No wearable value is treated as diagnostic evidence.
- [ ] A dataset or module that fails a blocking check remains unavailable.

## 16. Requirement traceability

The IDs below refer to the current Project Requirements document. This checklist adds implementation tasks; it does not replace the SRS.

| Requirement group | Checklist coverage |
|---|---|
| FR-DATA-01 to FR-DATA-09 | Sections 5–13: provenance, audits, splitting, preprocessing and reports |
| FR-INPUT-03, FR-INPUT-06, FR-INPUT-09 | Sections 6, 7, 10 and 14: validation, missing-data policy and E1/E2 fields |
| FR-MODEL-05, FR-MODEL-09 | Sections 6, 9 and 14: target/schema handoff and shared obesity splits |
| FR-AGENT-02, FR-AGENT-06 | Sections 4 and 14: eligibility metadata and unavailable/incomplete states |
| FR-XAI-05, FR-XAI-07 | Sections 8 and 10: preserved field mappings and E1 dependence disclosure |
| FR-WELL-02 to FR-WELL-04 | Sections 11 and 15: separate, labelled sample-data path |
| NFR-SEC-03, NFR-PRIV-01 | Sections 7 and 15: validated input and minimal data handling |
| NFR-MAINT-01, NFR-MAINT-02, NFR-REPRO-01 | Sections 4, 9, 12 and 13: setup, tests and reproducibility |

## 17. Definition of done: Module 1

Module 1 is complete only when all applicable P0 tasks are checked and the following review passes:

- [ ] The approved obesity dataset can be acquired or located reproducibly.
- [ ] Provenance, licence, target definition and field semantics are recorded.
- [ ] The audit runs and all blocking findings are resolved or prevent use explicitly.
- [ ] E1 and E2 use the same eligible records and frozen partition membership.
- [ ] No identified duplicate or participant group crosses held-out boundaries.
- [ ] Preprocessing learns only from the applicable training partition/fold.
- [ ] Required clinical fields cannot be bypassed through imputation.
- [ ] E2 excludes height, weight, BMI and identified direct derivatives.
- [ ] Feature mappings and saved-transformer tests pass.
- [ ] Reports and manifests identify the exact source data and configuration.
- [ ] Tests pass in CI and the workflow succeeds on a second machine.
- [ ] Module 2 receives a reviewed handoff, not a claim of a validated predictor.

## 18. Definition of done: prototype foundation

- [ ] Repository setup and documented commands work from a clean clone.
- [ ] The API and web scaffold run and handle validation/unavailable states honestly.
- [ ] User-facing notices and separate wellness boundaries are visible.
- [ ] The UI distinguishes mock fixtures from real inference.
- [ ] Unimplemented disease models remain unavailable.
- [ ] Remaining training, orchestration, explanation, dashboard and authentication work is recorded as separate backlog items.

Completing this checklist does **not** mean the entire Vitalis prototype is complete. Full delivery still requires trained and evaluated specialist models, constrained routing, explanations, protected dashboards and end-to-end testing.

## 19. Blockers and decisions to resolve

- [ ] Confirm supported population and handling of users below 18.
- [ ] Confirm final diabetes, CVD and MASLD datasets and exact targets.
- [ ] Confirm obesity class semantics and source-to-form mapping.
- [ ] Confirm split proportions and any grouped/temporal constraints.
- [ ] Confirm optional-field imputation policy.
- [ ] Confirm categorical preprocessing paths for linear, tree and CatBoost candidates.
- [ ] Confirm data/artifact distribution locations and access restrictions.
- [ ] Confirm wellness-data licence and status-band sources before enabling bands.

Record each decision with its owner, date, evidence and affected requirement IDs in `docs/decisions.md`.

## 20. Progress update template

Use this Markdown template for each implementation review:

```markdown
### Implementation update
- Review date:
- Owner:
- Current gate:
- Completed task IDs:
- Evidence: PRs, test runs, reports or manifests
- In progress:
- Blockers and required decisions:
- Changes to scope or configuration:
- Next tasks:
- Reviewer and outcome:
```
