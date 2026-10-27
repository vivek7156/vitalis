"""Disease screening routes and preprocessing verification.

Covers:
- T-PROTO-05: Validation-error and unavailable-model states.
- T-PROTO-07: Keep unimplemented disease tools unavailable rather than returning invented scores.
- T-INTEGRATE-01: API validation and user inputs use reviewed mappings consistent with training.
- T-INTEGRATE-02: Synthetic single-row fixture passes validation and transformation.
- T-INTEGRATE-04: Unimplemented disease adapters return explicit unavailable states.
- T-INTEGRATE-05: Smoke test labelled software integration test, not a usable health model.
"""

import json
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, status

from api.schemas import (
    ErrorResponse,
    ObesityE1Input,
    ObesityE2Input,
    PreprocessingVerificationResponse,
)
from pipeline.preprocessing import load_preprocessing, transform_partition

router = APIRouter(prefix="/api/v1/screen", tags=["Screening"])


def _load_trained_model(artifacts_dir: Path, feature_set: str):
    """Load only artifacts produced by the Module 2 training workflow."""
    model_path = artifacts_dir / f"obesity_{feature_set}_model.joblib"
    metrics_path = artifacts_dir / f"obesity_{feature_set}_training_metrics.json"
    if not model_path.exists() or not metrics_path.exists():
        return None, None
    metadata = json.loads(metrics_path.read_text(encoding="utf-8"))
    if metadata.get("calibration", {}).get("test_partition_excluded") is not True:
        return None, None
    import joblib

    return joblib.load(model_path), metadata


@router.post(
    "/obesity",
    response_model=PreprocessingVerificationResponse,
    responses={
        422: {"model": ErrorResponse, "description": "Validation error or insufficient input"},
        503: {"model": ErrorResponse, "description": "Preprocessing artifacts not found"},
    },
)
def screen_obesity_e2(payload: ObesityE2Input) -> PreprocessingVerificationResponse:
    """Validate E2 lifestyle inputs and verify transformation via Module 1 pipeline.

    Honest prototype behavior: Executes full preprocessing pipeline transformation,
    and returns explicit PENDING_MODULE_2_TRAINING state (no mock/invented predictions).
    """
    artifacts_dir = Path("artifacts")
    try:
        pipeline, mapping = load_preprocessing(
            output_dir=artifacts_dir,
            disease="obesity",
            feature_set="e2_lifestyle_only",
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Module 1 preprocessing pipeline has not been executed yet. Run 'python -m pipeline.run_pipeline'.",
        )

    # Convert to single-row DataFrame
    row_dict = payload.to_pipeline_dict()
    df_single = pd.DataFrame([row_dict])
    feature_list = mapping["input_features"]

    # Transform through fitted pipeline
    try:
        X_trans = transform_partition(pipeline, df_single, feature_list)
    except (ValueError, TypeError, KeyError) as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Preprocessing transformation error: {exc}",
        )

    trained_model, model_metadata = _load_trained_model(
        artifacts_dir, "e2_lifestyle_only"
    )

    # Check advisory notices (e.g. minors under 18)
    advisories: list[str] = []
    if payload.Age < 18:
        advisories.append(
            "Advisory: Respondent is under 18. Pediatric growth standards apply; "
            "standard adult obesity screening thresholds may vary."
        )

    response = PreprocessingVerificationResponse(
        disease="obesity",
        feature_set="e2_lifestyle_only",
        status="PREPROCESSING_SUCCESSFUL",
        transformed_feature_count=int(X_trans.shape[1]),
        model_readiness=(
            "AVAILABLE" if trained_model is not None else "PENDING_MODULE_2_TRAINING"
        ),
        message=(
            "Input was validated and evaluated by the calibrated obesity specialist."
            if trained_model is not None
            else "Software integration test passed. Input was successfully validated and transformed. "
            "Specialist model inference is blocked until Module 2 training and calibration are complete."
        ),
        advisory_notes=advisories,
    )
    if trained_model is not None:
        probabilities = trained_model.predict_proba(df_single[feature_list])[0]
        classes = list(trained_model.classes_)
        best_index = int(probabilities.argmax())
        response.prediction = str(classes[best_index])
        response.probability = float(probabilities[best_index])
        response.uncertain = response.probability < 0.60
        response.model_id = (
            f"obesity-e2-{model_metadata['champion_model'].lower()}-calibrated"
        )
    return response


@router.post(
    "/obesity/e1",
    response_model=PreprocessingVerificationResponse,
)
def screen_obesity_e1(payload: ObesityE1Input) -> PreprocessingVerificationResponse:
    """Validate E1 BMI-inclusive inputs and verify transformation via Module 1 pipeline."""
    artifacts_dir = Path("artifacts")
    try:
        pipeline, mapping = load_preprocessing(
            output_dir=artifacts_dir,
            disease="obesity",
            feature_set="e1_bmi_inclusive",
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Module 1 E1 preprocessing pipeline has not been executed yet.",
        )

    row_dict = payload.to_pipeline_dict()
    df_single = pd.DataFrame([row_dict])
    feature_list = mapping["input_features"]

    try:
        X_trans = transform_partition(pipeline, df_single, feature_list)
    except (ValueError, TypeError, KeyError) as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Preprocessing transformation error: {exc}",
        )

    trained_model, model_metadata = _load_trained_model(
        artifacts_dir, "e1_bmi_inclusive"
    )

    advisories = [
        "Researcher Baseline Notice: E1 includes Height and Weight, which directly reconstruct BMI labels."
    ]
    if payload.Age < 18:
        advisories.append(
            "Advisory: Respondent is under 18. Pediatric growth standards apply."
        )

    response = PreprocessingVerificationResponse(
        disease="obesity",
        feature_set="e1_bmi_inclusive",
        status="PREPROCESSING_SUCCESSFUL",
        transformed_feature_count=int(X_trans.shape[1]),
        model_readiness=(
            "AVAILABLE" if trained_model is not None else "PENDING_MODULE_2_TRAINING"
        ),
        message=(
            "Software integration test passed for E1 baseline. "
            "Model training is pending Module 2."
            if trained_model is None
            else "Input was evaluated by the calibrated researcher baseline."
        ),
        advisory_notes=advisories,
    )
    if trained_model is not None:
        probabilities = trained_model.predict_proba(df_single[feature_list])[0]
        classes = list(trained_model.classes_)
        best_index = int(probabilities.argmax())
        response.prediction = str(classes[best_index])
        response.probability = float(probabilities[best_index])
        response.uncertain = response.probability < 0.60
        response.model_id = (
            f"obesity-e1-{model_metadata['champion_model'].lower()}-calibrated"
        )
    return response


@router.post("/{disease}")
def screen_unimplemented_disease(disease: str):
    """Explicitly reject unimplemented secondary diseases (T-PROTO-07, T-INTEGRATE-04)."""
    pending_diseases = {"diabetes", "cvd", "masld"}
    if disease.lower() in pending_diseases:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=(
                f"The '{disease}' specialist screening tool is unavailable. "
                "Dataset selection and target definition are pending formal approval."
            ),
        )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Unknown disease screening tool '{disease}'.",
    )
