"""API data schemas and validation models for Vitalis."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ServiceStatus(str, Enum):
    ALIVE = "alive"
    DEGRADED = "degraded"
    DOWN = "down"


class SpecialistStatus(str, Enum):
    AVAILABLE = "available"
    PENDING_TRAINING = "pending_training"
    PENDING_APPROVAL = "pending_approval"
    UNAVAILABLE = "unavailable"


class HealthResponse(BaseModel):
    service: str = "vitalis-screening-api"
    status: ServiceStatus
    version: str = "0.1.0"
    timestamp: str


class SpecialistReadiness(BaseModel):
    disease: str
    status: SpecialistStatus
    module_1_pipeline_ready: bool
    model_trained: bool
    notes: str


class ReadinessResponse(BaseModel):
    service_status: ServiceStatus
    specialists: dict[str, SpecialistReadiness]


# --- Enums for Obesity Features ---

class Gender(str, Enum):
    FEMALE = "Female"
    MALE = "Male"


class BinaryYesNo(str, Enum):
    YES = "yes"
    NO = "no"


class MealFrequency(str, Enum):
    NO = "no"
    SOMETIMES = "Sometimes"
    FREQUENTLY = "Frequently"
    ALWAYS = "Always"


class Transportation(str, Enum):
    AUTOMOBILE = "Automobile"
    BIKE = "Bike"
    MOTORBIKE = "Motorbike"
    PUBLIC_TRANS = "Public_Transportation"
    WALKING = "Walking"


# --- Screening Inputs ---

class ObesityE2Input(BaseModel):
    """E2 Lifestyle & Demographic Screening Input (14 features).
    Strictly excludes Height, Weight, and BMI.
    """
    Gender: Gender
    Age: float = Field(..., ge=14.0, le=120.0, description="Age in years (14–120)")
    family_history_with_overweight: BinaryYesNo
    FAVC: BinaryYesNo = Field(..., description="Frequent consumption of high caloric food")
    FCVC: float = Field(..., ge=1.0, le=3.0, description="Frequency of vegetable consumption (1–3)")
    NCP: float = Field(..., ge=1.0, le=4.0, description="Number of main meals per day (1–4)")
    CAEC: MealFrequency = Field(..., description="Consumption of food between meals")
    SMOKE: BinaryYesNo = Field(..., description="Smokes tobacco")
    CH2O: float = Field(..., ge=1.0, le=3.0, description="Daily water intake in liters (1–3)")
    SCC: BinaryYesNo = Field(..., description="Calories consumption monitoring")
    FAF: float = Field(..., ge=0.0, le=3.0, description="Physical activity frequency in days/week (0–3)")
    TUE: float = Field(..., ge=0.0, le=2.0, description="Time using technology devices daily (0–2)")
    CALC: MealFrequency = Field(..., description="Consumption of alcohol")
    MTRANS: Transportation = Field(..., description="Primary mode of transportation")

    def to_pipeline_dict(self) -> dict[str, Any]:
        return {
            "Gender": self.Gender.value,
            "Age": float(self.Age),
            "family_history_with_overweight": self.family_history_with_overweight.value,
            "FAVC": self.FAVC.value,
            "FCVC": float(self.FCVC),
            "NCP": float(self.NCP),
            "CAEC": self.CAEC.value,
            "SMOKE": self.SMOKE.value,
            "CH2O": float(self.CH2O),
            "SCC": self.SCC.value,
            "FAF": float(self.FAF),
            "TUE": float(self.TUE),
            "CALC": self.CALC.value,
            "MTRANS": self.MTRANS.value,
        }


class ObesityE1Input(ObesityE2Input):
    """E1 BMI-inclusive benchmark screening input (16 features)."""
    Height: float = Field(..., ge=1.0, le=2.5, description="Height in meters (1.0–2.5)")
    Weight: float = Field(..., ge=25.0, le=300.0, description="Weight in kilograms (25–300)")

    def to_pipeline_dict(self) -> dict[str, Any]:
        d = super().to_pipeline_dict()
        d["Height"] = float(self.Height)
        d["Weight"] = float(self.Weight)
        return d


# --- Screening Response ---

class PreprocessingVerificationResponse(BaseModel):
    disease: str = "obesity"
    feature_set: str
    status: str = "PREPROCESSING_SUCCESSFUL"
    transformed_feature_count: int
    model_readiness: str = "PENDING_MODULE_2_TRAINING"
    message: str
    advisory_notes: list[str] = Field(default_factory=list)
    prediction: str | None = None
    probability: float | None = None
    uncertain: bool | None = None
    model_id: str | None = None


class ErrorItem(BaseModel):
    field: str | None = None
    issue: str


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: list[ErrorItem] = Field(default_factory=list)
