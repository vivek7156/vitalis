"""Health and Readiness reporting endpoints.

Covers T-PROTO-02: Add health/readiness reporting that distinguishes
a running service from ready specialist models.
"""

import datetime
from pathlib import Path

from fastapi import APIRouter

from api.schemas import (
    HealthResponse,
    ReadinessResponse,
    ServiceStatus,
    SpecialistReadiness,
    SpecialistStatus,
)

router = APIRouter(tags=["Health & Readiness"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Return basic service liveness status."""
    return HealthResponse(
        service="vitalis-screening-api",
        status=ServiceStatus.ALIVE,
        version="0.1.0",
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )


@router.get("/readiness", response_model=ReadinessResponse)
def get_readiness() -> ReadinessResponse:
    """Return comprehensive system and specialist readiness status.

    Distinguishes a running API service from trained, calibrated disease models.
    """
    artifacts_dir = Path("artifacts")
    e2_pipe = artifacts_dir / "obesity_e2_lifestyle_only_pipeline.joblib"
    e2_mapping = artifacts_dir / "obesity_e2_lifestyle_only_feature_mapping.json"
    module_1_obesity_ready = e2_pipe.exists() and e2_mapping.exists()

    specialists = {
        "obesity": SpecialistReadiness(
            disease="obesity",
            status=(
                SpecialistStatus.PENDING_TRAINING
                if module_1_obesity_ready
                else SpecialistStatus.UNAVAILABLE
            ),
            module_1_pipeline_ready=module_1_obesity_ready,
            model_trained=False,  # Module 2 pending
            notes=(
                "Module 1 data and preprocessing pipeline complete. "
                "Module 2 specialist classifier training is pending."
                if module_1_obesity_ready
                else "Module 1 data pipeline not yet executed."
            ),
        ),
        "diabetes": SpecialistReadiness(
            disease="diabetes",
            status=SpecialistStatus.PENDING_APPROVAL,
            module_1_pipeline_ready=False,
            model_trained=False,
            notes="Dataset selection and target approval pending guide review.",
        ),
        "cvd": SpecialistReadiness(
            disease="cvd",
            status=SpecialistStatus.PENDING_APPROVAL,
            module_1_pipeline_ready=False,
            model_trained=False,
            notes="Longitudinal cohort evaluation pending clinical selection.",
        ),
        "masld": SpecialistReadiness(
            disease="masld",
            status=SpecialistStatus.PENDING_APPROVAL,
            module_1_pipeline_ready=False,
            model_trained=False,
            notes="Metabolic liver biomarker dataset selection pending.",
        ),
    }

    return ReadinessResponse(
        service_status=ServiceStatus.ALIVE,
        specialists=specialists,
    )
