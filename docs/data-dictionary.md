# Vitalis Data Dictionary: Obesity Module (E1 & E2)

| Metadata | Specification |
|---|---|
| Target Disease | Obesity Level Screening |
| Target Variable | `NObeyesdad` (7 classes) |
| Source Dataset | UCI Machine Learning Repository (ID: 544, DOI: 10.24432/C5H31Z) |
| Feature Sets | **E2** (Lifestyle/Demographic only, 14 features) & **E1** (BMI-inclusive, 16 features) |
| Target Population | Adults aged 18–65 (Dataset observed 14–61 from Colombia, Mexico, Peru) |
| Document Version | 1.0.0 (Module 1 Data Contract) |

---

## 1. Target Definition and Class Encodings (T-SCHEMA-02, T-SCHEMA-03)

The target variable is `NObeyesdad`, representing obesity classifications derived from the World Health Organization (WHO) and Mexican clinical guidelines using Body Mass Index ($\text{BMI} = \text{weight} / \text{height}^2$).

### Target Classes & Stable Numeric Encodings

| Target Class | Canonical Description | BMI Reference ($kg/m^2$) | Class Index |
|---|---|---|---|
| `Insufficient_Weight` | Underweight | $< 18.5$ | 0 |
| `Normal_Weight` | Healthy Weight | $18.5 - 24.9$ | 1 |
| `Overweight_Level_I` | Pre-obesity / Overweight Grade I | $25.0 - 29.9$ | 2 |
| `Overweight_Level_II` | Pre-obesity / Overweight Grade II | $25.0 - 29.9$ (high risk) | 3 |
| `Obesity_Type_I` | Obesity Class I | $30.0 - 34.9$ | 4 |
| `Obesity_Type_II` | Obesity Class II | $35.0 - 39.9$ | 5 |
| `Obesity_Type_III` | Obesity Class III (Severe/Morbid) | $\ge 40.0$ | 6 |

---

## 2. Feature Sets Overview (T-SCHEMA-04, T-SCHEMA-05, T-SCHEMA-06)

Vitalis implements two distinct feature configurations on the identical dataset records:

1. **E2: Lifestyle & Demographic Feature Set (Primary Screening Model):**
   - Consists of **14 lifestyle and demographic features**.
   - Strictly **excludes Height, Weight, and calculated BMI** to eliminate direct target leakage and provide true lifestyle-risk screening.
2. **E1: BMI-Inclusive Benchmark Configuration:**
   - Consists of all **16 features** (the 14 E2 features plus `Height` and `Weight`).
   - Serves strictly as a researcher baseline. Because BMI has a $0.978$ rank correlation with the target classes, E1 predictions must explicitly disclose that height and weight directly define the label.

---

## 3. Comprehensive Attribute Dictionary (T-SCHEMA-01, T-SCHEMA-12)

| Raw Column | Canonical Form Name | Type | Feature Set | Clinical Unit | Permitted Values / Categories | Observed Dataset Range | Validated Screening Range |
|---|---|---|---|---|---|---|---|
| `Gender` | `gender` | Categorical (Nominal) | E1, E2 | — | `Female`, `Male` | `Female`, `Male` | `Female`, `Male` |
| `Age` | `age` | Numeric (Continuous) | E1, E2 | Years | $\ge 14$ | $14.0 - 61.0$ (mean $24.3$) | $14.0 - 120.0$ (Adults $\ge 18$) |
| `Height` | `height` | Numeric (Continuous) | **E1 only** | Meters ($m$) | Positive float | $1.45 - 1.98$ (mean $1.70$) | $1.00 - 2.50$ |
| `Weight` | `weight` | Numeric (Continuous) | **E1 only** | Kilograms ($kg$) | Positive float | $39.0 - 173.0$ (mean $86.6$) | $25.0 - 300.0$ |
| `family_history_with_overweight` | `family_history_overweight` | Binary | E1, E2 | — | `yes`, `no` | `yes`, `no` | `yes`, `no` |
| `FAVC` | `frequent_high_calorie_food` | Binary | E1, E2 | — | `yes`, `no` | `yes`, `no` | `yes`, `no` |
| `FCVC` | `vegetable_consumption_frequency` | Numeric (Synthetic Cont.) | E1, E2 | Scale ($1-3$) | Float in $[1.0, 3.0]$ | $1.0 - 3.0$ (826 fractional) | $1.0 - 3.0$ |
| `NCP` | `daily_main_meals` | Numeric (Synthetic Cont.) | E1, E2 | Count / Scale | Float in $[1.0, 4.0]$ | $1.0 - 4.0$ (640 fractional) | $1.0 - 4.0$ |
| `CAEC` | `food_between_meals` | Categorical (Ordinal) | E1, E2 | Ordinal frequency | `no`, `Sometimes`, `Frequently`, `Always` | 4 categories | 4 categories |
| `SMOKE` | `smoke_tobacco` | Binary | E1, E2 | — | `yes`, `no` | `yes`, `no` | `yes`, `no` |
| `CH2O` | `daily_water_intake` | Numeric (Synthetic Cont.) | E1, E2 | Liters ($L$) | Float in $[1.0, 3.0]$ | $1.0 - 3.0$ (1290 fractional) | $1.0 - 3.0$ |
| `SCC` | `calorie_intake_monitoring` | Binary | E1, E2 | — | `yes`, `no` | `yes`, `no` | `yes`, `no` |
| `FAF` | `physical_activity_frequency` | Numeric (Synthetic Cont.) | E1, E2 | Days / Scale | Float in $[0.0, 3.0]$ | $0.0 - 3.0$ (1208 fractional) | $0.0 - 3.0$ |
| `TUE` | `device_screen_time` | Numeric (Synthetic Cont.) | E1, E2 | Hours / Scale | Float in $[0.0, 2.0]$ | $0.0 - 2.0$ (1153 fractional) | $0.0 - 2.0$ |
| `CALC` | `alcohol_consumption` | Categorical (Ordinal) | E1, E2 | Ordinal frequency | `no`, `Sometimes`, `Frequently`, `Always` | 4 categories | 4 categories |
| `MTRANS` | `primary_transportation` | Categorical (Nominal) | E1, E2 | Mode | `Automobile`, `Bike`, `Motorbike`, `Public_Transportation`, `Walking` | 5 categories | 5 categories |
| `NObeyesdad` | `obesity_classification` | Categorical (Target) | Target | WHO Class | 7 classes | 7 classes | 7 classes |

---

## 4. Raw-to-Form User Mappings for 14 E2 Fields (T-SCHEMA-07, T-SCHEMA-09)

When presenting questions to end-users in the screening form, user-friendly labels map deterministically to the dataset values:

| # | Feature | Form Question Prompt | User Option in UI | Internal Value Sent to Pipeline |
|---|---|---|---|---|
| 1 | `Gender` | "What is your gender?" | "Female" / "Male" | `"Female"`, `"Male"` |
| 2 | `Age` | "What is your age in years?" | Number input (14–120) | `float` (e.g., `28.0`) |
| 3 | `family_history_with_overweight` | "Has a family member suffered or does suffer from overweight?" | "Yes" / "No" | `"yes"`, `"no"` |
| 4 | `FAVC` | "Do you eat high caloric food frequently?" | "Yes" / "No" | `"yes"`, `"no"` |
| 5 | `FCVC` | "Do you usually eat vegetables in your meals?" | "Never" (1.0), "Sometimes" (2.0), "Always" (3.0) | `1.0`, `2.0`, `3.0` (or intermediate float) |
| 6 | `NCP` | "How many main meals do you have daily?" | "1–2 meals" (1.0–2.0), "Three" (3.0), "More than three" (4.0) | `1.0` to `4.0` |
| 7 | `CAEC` | "Do you eat any food between meals?" | "No", "Sometimes", "Frequently", "Always" | `"no"`, `"Sometimes"`, `"Frequently"`, `"Always"` |
| 8 | `SMOKE` | "Do you smoke tobacco?" | "Yes" / "No" | `"yes"`, `"no"` |
| 9 | `CH2O` | "How much water do you drink daily?" | "Less than 1L" (1.0), "1–2 Liters" (2.0), "More than 2L" (3.0) | `1.0`, `2.0`, `3.0` |
| 10 | `SCC` | "Do you monitor the calories you eat daily?" | "Yes" / "No" | `"yes"`, `"no"` |
| 11 | `FAF` | "How often do you have physical activity per week?" | "None" (0.0), "1 to 2 days" (1.0), "2 to 4 days" (2.0), "4 to 5 days" (3.0) | `0.0`, `1.0`, `2.0`, `3.0` |
| 12 | `TUE` | "How much time do you spend using technological devices daily?" | "0–2 hours" (0.0), "3–5 hours" (1.0), "More than 5 hours" (2.0) | `0.0`, `1.0`, `2.0` |
| 13 | `CALC` | "How often do you drink alcohol?" | "Never" / "Sometimes" / "Frequently" / "Always" | `"no"`, `"Sometimes"`, `"Frequently"`, `"Always"` |
| 14 | `MTRANS` | "Which transportation do you usually use?" | "Walking", "Bicycle", "Public Transit", "Motorbike", "Automobile" | `"Walking"`, `"Bike"`, `"Public_Transportation"`, `"Motorbike"`, `"Automobile"` |

---

## 5. Fractional Values and Synthetic Artifact Policy (T-SCHEMA-08, T-AUDIT-10)

The source UCI Obesity dataset reports approximately **77% synthetically generated records** using SMOTE (Synthetic Minority Over-sampling Technique).
- As a direct consequence of interpolation during synthetic generation, frequency fields (`FCVC`, `NCP`, `CH2O`, `FAF`, `TUE`) contain non-integer continuous values (e.g., `FCVC = 2.419`, `NCP = 2.686`, `CH2O = 2.008`).
- **Policy:** The pipeline preserves these fields as `float64` continuous features. They **must not** be silently rounded or cast to integers, as doing so introduces artificial discretization error and alters the distribution of synthetic training samples.

---

## 6. Required Fields, Missing Data, and Imputation Policy (T-SCHEMA-10, T-LOAD-07)

- **Required Fields Policy:**
  - In screening inference, all **14 E2 features** are clinically necessary to establish an eligible lifestyle risk assessment.
  - If any required field is missing from an inference request, the screening service **must reject the request with `INSUFFICIENT_INPUT`** (HTTP 422). Missing required fields **cannot be silently imputed**.
- **Optional Fields & Training Imputation:**
  - Simple median/mode imputation is configured within training pipelines purely to maintain pipeline robustness against unexpected corrupted records during batch ingestion.
  - Legitimate zeroes (e.g., `FAF = 0.0` meaning no exercise, `TUE = 0.0` meaning no screen time) must remain preserved as `0.0` and distinct from `NaN`.

---

## 7. Supported Population and Eligibility Rules (T-SCHEMA-11)

- **Primary Supported Screening Cohort:** Adults aged **18 to 65 years**.
- **Pediatric Records (Age 14–17):** The UCI source dataset includes 113 records of individuals under age 18. While included in general training/evaluation per original benchmark fidelity, the screening API surfaces an explicit advisory notice when an evaluated user is under 18, noting that adolescent growth trajectories alter BMI and lifestyle thresholds.
- **Unsupported Inputs:** Ages $< 14$ or $> 120$, negative heights/weights, and unrecognized transportation modes trigger deterministic validation errors.

---

## 8. Unknown Category and Unit Handling (T-SCHEMA-13)

- Categorical encoders utilize explicit handling:
  - Nominal features (`Gender`, `MTRANS`): In linear/tree pipelines, unknown categories are handled via `handle_unknown="infrequent_if_exist"` or assigned to an `unseen` fallback category.
  - Ordinal features (`CAEC`, `CALC`): Encoded according to fixed order `["no", "Sometimes", "Frequently", "Always"]`. Unknown values are flagged as validation errors during API schema parsing.