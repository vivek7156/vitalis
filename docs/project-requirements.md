# Vitalis – Project Requirements and Technology Stack

## Project Requirements

# Vitalis – Project Requirements Document

## 1. Project identity

| Item | Detail |
|---|---|
| Project | Vitalis – An Explainable Agentic AI Framework for Multi-Disease Health-Risk Screening and Wellness Monitoring |
| Team | Aadi Vinayak S (3401), Aditya Singh Rawat (3404), Vachspati (3457), Vivek Singh (3460) |
| Guide | Dr. N. K. Bansode |
| Document status | Working baseline for implementation and evaluation |
| Primary users | Screening users, researchers and administrators |

## 2. Purpose

Vitalis shall provide a unified web-based research prototype that coordinates independent machine-learning models for:

- Obesity or obesity-level risk
- Diabetes or glucose-related risk
- Cardiovascular disease risk
- Metabolic dysfunction-associated steatotic liver disease (MASLD)

The system shall combine disease-risk screening, explainable predictions and separate wearable wellness information through one interface.

Vitalis is a screening and research-support system. It shall not diagnose disease, prescribe treatment, replace a clinician or provide emergency medical advice.

## 3. Product vision

Vitalis shall use a constrained agentic orchestration layer rather than one unrestricted generative model. The orchestrator shall:

1. Receive a structured patient profile.
2. Validate available inputs and units.
3. Identify which specialist models are eligible to run.
4. Request missing information where appropriate.
5. Invoke specialist models through controlled tool interfaces.
6. Preserve the original model outputs.
7. Combine results using a common response structure.
8. Display explanations, limitations and uncertainty clearly.

Wearable values such as steps, sleep, heart rate and SpO₂ shall remain in a separate wellness panel and shall not silently alter disease predictions.

## 4. Scope

### 4.1 In scope

- Unified patient-profile form
- Server-side and client-side input validation
- Independent obesity, diabetes, CVD and MASLD model modules
- Obesity BMI-inclusive and lifestyle-only configurations
- Dataset audits and leakage analysis
- Disease-specific preprocessing and training pipelines
- Model comparison and calibration
- SHAP or suitable model-specific explanations
- Plain-language explanation templates
- Constrained model-routing and tool-calling layer
- Common prediction and explanation response schema
- Wearable wellness panel using sample or dataset-derived records
- Researcher dashboard for metrics, calibration, robustness and explanations
- Model-version tracking and controlled logs
- Safety notices and non-diagnostic communication
- End-to-end system evaluation

### 4.2 Out of scope

- Medical diagnosis or treatment recommendations
- Emergency triage
- Live smartwatch, Bluetooth or medical-device integration
- Clinical deployment or clinical validation
- Replacement of validated clinical risk scores
- Unrestricted medical chatbot behaviour
- Automatic filling or guessing of missing clinical values
- Native Android or iOS applications
- Multi-language support in the first version
- Personal accounts for anonymous screening users

## 5. Objectives

The project shall:

1. Develop independent specialist risk-prediction modules for the selected conditions.
2. Audit each dataset for target construction, leakage, missingness, duplicates, synthetic data and population limitations.
3. Compare baseline and advanced machine-learning models for each disease.
4. Evaluate discrimination, calibration, robustness, runtime and explainability.
5. Compare BMI-inclusive and lifestyle-only obesity models.
6. Implement a constrained agentic orchestrator for model selection and tool invocation.
7. Define a common output contract for prediction, confidence, explanations and limitations.
8. Integrate wearable information as non-diagnostic wellness context.
9. Develop a unified web interface for users, researchers and administrators.
10. Evaluate routing accuracy, tool-call reliability, explanation consistency and safety compliance.

## 6. Stakeholders and user classes

| User class | Main responsibilities | Main needs |
|---|---|---|
| Screening user | Provides optional profile information and views results | Simple form, understandable explanations, visible limitations |
| Researcher | Trains models and analyses experiments | Metrics, calibration, SHAP, robustness and exports |
| Administrator | Maintains datasets, models, accounts and logs | Controlled activation, configuration and auditability |
| Guide/examiner | Reviews project quality and research evidence | Traceability, reproducibility and clear limitations |
| Wearable data source | Supplies sample wellness records | Separate, read-only data path |

## 7. Functional requirements

Priority levels:

- **Must:** required for the core prototype
- **Should:** planned feature that may be reduced if schedule constraints arise
- **Could:** optional enhancement

### 7.1 Data and dataset management

| ID | Requirement | Priority |
|---|---|---|
| FR-DATA-01 | The system shall maintain a separate dataset and preprocessing configuration for each disease model. | Must |
| FR-DATA-02 | The pipeline shall record dataset name, version, source, checksum, row count, feature count and licence note. | Must |
| FR-DATA-03 | The pipeline shall audit target construction, class balance, missing values, duplicates, invalid values and population coverage. | Must |
| FR-DATA-04 | The audit shall identify possible target leakage, proxy variables and direct components of the target. | Must |
| FR-DATA-05 | Train, validation and test data shall be separated before resampling or fitting preprocessing steps. | Must |
| FR-DATA-06 | Imputation, encoding, scaling and feature selection shall be fitted only on training data. | Must |
| FR-DATA-07 | Resampling, if used, shall occur only inside training folds. | Must |
| FR-DATA-08 | Wearable datasets shall be cleaned in a separate workflow and shall never be merged into disease-training data without explicit validation. | Must |
| FR-DATA-09 | The pipeline shall produce a reproducible audit report and processed-data manifest. | Should |

### 7.2 Unified patient profile and validation

| ID | Requirement | Priority |
|---|---|---|
| FR-INPUT-01 | The system shall display consent and a non-diagnostic notice before collecting screening inputs. | Must |
| FR-INPUT-02 | The system shall collect only fields required by the selected specialist models. | Must |
| FR-INPUT-03 | The system shall validate types, ranges, units, categories and missing required values on the client and server. | Must |
| FR-INPUT-04 | The system shall show field-level validation messages without exposing stack traces. | Must |
| FR-INPUT-05 | The system shall identify which disease models are eligible from the available inputs. | Must |
| FR-INPUT-06 | The system shall not invent, guess or silently substitute missing clinical values. | Must |
| FR-INPUT-07 | Optional incomplete inputs shall be clearly marked as incomplete and may reduce reliability. | Should |
| FR-INPUT-08 | The system shall not require a name, email address, telephone number or other direct identifier for screening. | Must |
| FR-INPUT-09 | Height and weight shall be optional for the lifestyle-only obesity configuration and required only for the BMI-inclusive configuration. | Must |

### 7.3 Specialist disease models

| ID | Requirement | Priority |
|---|---|---|
| FR-MODEL-01 | The system shall provide an independent obesity model. | Must |
| FR-MODEL-02 | The system shall provide an independent diabetes or glucose-risk model when an approved dataset and target are available. | Must |
| FR-MODEL-03 | The system shall provide an independent cardiovascular-risk model when required inputs are available. | Must |
| FR-MODEL-04 | The system shall provide an independent MASLD screening model when an approved dataset and target are available. | Must |
| FR-MODEL-05 | Each disease model shall have its own feature schema, preprocessing pipeline, target definition and model card. | Must |
| FR-MODEL-06 | Each model shall return a prediction or risk category, model version and applicable limitations. | Must |
| FR-MODEL-07 | Each model shall return class probabilities or calibrated confidence where statistically meaningful. | Should |
| FR-MODEL-08 | Each model shall report performance using metrics suitable for its target type and class distribution. | Must |
| FR-MODEL-09 | Obesity experiments shall compare BMI-inclusive and lifestyle-only feature sets using identical splits and seeds. | Must |
| FR-MODEL-10 | The system shall reject or qualify a prediction when required features are unavailable. | Must |

### 7.4 Agentic orchestration

| ID | Requirement | Priority |
|---|---|---|
| FR-AGENT-01 | The orchestrator shall receive a structured patient profile rather than unrestricted free-form medical instructions. | Must |
| FR-AGENT-02 | The orchestrator shall determine model eligibility using explicit routing rules and required-feature schemas. | Must |
| FR-AGENT-03 | The orchestrator shall invoke specialist models only through controlled tool schemas. | Must |
| FR-AGENT-04 | The orchestrator shall record selected tools, unavailable tools, missing inputs and routing decisions. | Must |
| FR-AGENT-05 | The orchestrator shall preserve specialist predictions and shall not alter their probabilities or explanations. | Must |
| FR-AGENT-06 | The orchestrator shall not create a disease result when required inputs are absent. | Must |
| FR-AGENT-07 | The first implementation shall prefer deterministic rules; an LLM may be evaluated only as a constrained optional interface component. | Must |
| FR-AGENT-08 | The system shall return a structured insufficient-information result when no model is eligible. | Must |
| FR-AGENT-09 | The system shall provide a common result schema across all specialist models. | Must |

### 7.5 Explanations and user communication

| ID | Requirement | Priority |
|---|---|---|
| FR-XAI-01 | Each eligible disease model shall provide global feature importance for researchers. | Must |
| FR-XAI-02 | Each eligible prediction shall provide local contributing factors where the model supports them. | Must |
| FR-XAI-03 | Explanations shall indicate direction or contribution without implying causation. | Must |
| FR-XAI-04 | User-facing explanations shall use fixed, reviewed plain-language templates. | Must |
| FR-XAI-05 | Technical explanation data shall be preserved for researchers separately from simplified user text. | Must |
| FR-XAI-06 | Explanations shall identify dependent, proxy or potentially misleading features where relevant. | Should |
| FR-XAI-07 | The obesity E1 result shall disclose that height and weight are closely related to BMI-derived labels. | Must |
| FR-XAI-08 | The system shall show uncertainty when confidence is below a configured threshold or calibration is inadequate. | Should |

### 7.6 Wellness monitoring

| ID | Requirement | Priority |
|---|---|---|
| FR-WELL-01 | The system shall display steps or activity, sleep, heart rate and SpO₂ where available. | Must |
| FR-WELL-02 | The wellness panel shall be visually separate from disease-risk results. | Must |
| FR-WELL-03 | Wellness records shall be labelled as sample, simulated or dataset-derived data where applicable. | Must |
| FR-WELL-04 | Wearable values shall not change specialist-model predictions unless a future validated study explicitly enables this behaviour. | Must |
| FR-WELL-05 | Wellness thresholds shall be configurable and their source shall be documented. | Should |
| FR-WELL-06 | The panel shall display a non-diagnostic notice. | Must |

### 7.7 Researcher and administrator functions

| ID | Requirement | Priority |
|---|---|---|
| FR-ADMIN-01 | Researchers shall be able to run configured experiments with fixed seeds. | Must |
| FR-ADMIN-02 | Researchers shall be able to compare models and disease modules using stored metrics. | Must |
| FR-ADMIN-03 | Researchers shall be able to inspect confusion matrices, calibration, robustness and explanations. | Must |
| FR-ADMIN-04 | Researchers shall be able to export approved tables and plots. | Should |
| FR-ADMIN-05 | Administrators shall be able to register dataset metadata and feature configurations. | Should |
| FR-ADMIN-06 | Administrators shall be able to activate or deactivate model versions after a self-check. | Should |
| FR-ADMIN-07 | Protected dashboards shall require authentication and role authorisation. | Must |
| FR-ADMIN-08 | Experiment metadata, routing events and API errors shall be logged in a controlled manner. | Must |

## 8. Evaluation requirements

### 8.1 Disease-model evaluation

Each specialist model shall report, where applicable:

- Macro-F1
- Balanced accuracy
- Per-class precision and recall
- Confusion matrix
- ROC-AUC or PR-AUC
- Calibration curve
- Brier score for probabilistic classification
- Training and inference time
- Sensitivity to missing and noisy inputs
- Subgroup performance where sample sizes permit

### 8.2 Orchestration evaluation

The orchestration layer shall be evaluated using:

- Routing accuracy
- Correct tool-selection rate
- Tool-call success rate
- Invalid tool-call rate
- Incomplete-input rejection rate
- Response time
- Output-schema consistency
- Preservation of specialist outputs

### 8.3 End-to-end evaluation

The complete system shall be evaluated for:

- Correct model invocation
- Explanation completeness
- User understanding of explanations
- Separation of screening and wellness information
- Correct uncertainty and limitation notices
- Robustness to missing, noisy and contradictory values
- Safety-boundary compliance

## 9. Non-functional requirements

| ID | Requirement | Working target |
|---|---|---|
| NFR-PERF-01 | Prediction plus explanation shall return promptly on a student laptop. | p95 under 2 seconds for one request |
| NFR-PERF-02 | The local result page shall load promptly after submission. | Within 3 seconds under normal local conditions |
| NFR-PERF-03 | Researcher dashboard views shall load efficiently. | Within 5 seconds for a selected run |
| NFR-PERF-04 | The complete configured training pipeline shall be practical on CPU. | Target under 30 minutes; confirm after benchmarking |
| NFR-SEC-01 | Passwords shall be stored using salted password hashes. | bcrypt or Argon2 |
| NFR-SEC-02 | Protected API routes shall reject unauthenticated and unauthorised requests. | HTTP 401/403 |
| NFR-SEC-03 | Server-side validation and parameterised database access shall be mandatory. | 100% of API paths |
| NFR-PRIV-01 | Direct identifiers shall not be required for screening. | No name, email or phone field |
| NFR-PRIV-02 | Any prediction logging shall require consent and remain purgeable. | Administrator-controlled purge |
| NFR-REL-01 | Errors shall use a structured response format and never expose stack traces. | Automated API tests |
| NFR-REL-02 | Active models shall pass a startup self-check before serving requests. | Startup test |
| NFR-USE-01 | The core screening journey shall be usable on a mobile-width screen. | Minimum 360 px width |
| NFR-USE-02 | Forms shall use labels, keyboard navigation and adequate contrast. | WCAG 2.1 AA basics |
| NFR-MAINT-01 | A clean clone shall be runnable using pinned dependencies and documented setup steps. | Verified by a team member |
| NFR-MAINT-02 | Pipeline and API code shall have automated tests. | Minimum 70% line coverage target |
| NFR-REPRO-01 | Repeated runs with the same data, configuration and seed shall be reproducible. | Same metrics within defined tolerance |

## 10. Common result contract

Every specialist tool should return the following structure:

```json
{
  "disease": "obesity",
  "model_id": "obesity-e2-catboost-v001",
  "status": "available",
  "prediction": "Overweight_Level_I",
  "probability": 0.52,
  "uncertain": false,
  "required_inputs": ["age", "gender", "faf"],
  "missing_inputs": [],
  "top_factors": [],
  "plain_language_explanation": "",
  "limitations": [],
  "disclaimer": "Screening support only; not a diagnosis."
}
```

Possible statuses:

- `available`
- `insufficient_input`
- `model_unavailable`
- `error`

## 11. Safety rules

- The interface shall use screening-support language.
- It shall not state that a user has or does not have a disease.
- It shall not claim that a feature caused a medical condition.
- It shall not treat smartwatch data as diagnostic evidence.
- It shall not invent missing clinical measurements.
- It shall show model and dataset limitations.
- It shall recommend professional consultation for concerning symptoms or decisions without giving treatment instructions.
- It shall keep disease results and wellness context visually and semantically separate.

## 12. Core acceptance criteria

The project is ready for the main demonstration when:

- All selected disease modules have documented targets and input schemas.
- Each active model has a versioned artifact and model card.
- The dataset audit and leakage checks pass.
- The router correctly selects eligible tools and rejects incomplete cases.
- Every result follows the common response contract.
- Obesity E1 and E2 can be compared on identical splits.
- Explanations are deterministic, reviewed and understandable.
- Wellness data cannot alter disease predictions.
- Researcher and administrator routes are protected.
- The system displays non-diagnostic notices consistently.
- The evaluation report includes disease, routing and end-to-end results.
- A clean-clone setup and demonstration path are documented.

## 13. Open decisions

1. Final dataset and target definition for the diabetes module.
2. Final dataset and target definition for the CVD module.
3. Final dataset and target definition for the MASLD module.
4. Accepted age range and handling of users below 18.
5. CatBoost versus XGBoost after comparative benchmarking.
6. Source and wording of wellness thresholds.
7. Whether prediction logging should remain enabled.
8. Final hosting target and dataset licence checks.
9. Whether an LLM routing comparison is included in the final evaluation.
10. Guide approval of consent and disclaimer wording.