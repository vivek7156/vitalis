"""Tests for the Vitalis FastAPI application.

Covers T-PROTO-01, T-PROTO-02, T-PROTO-05, T-PROTO-07, T-INTEGRATE-01,
T-INTEGRATE-02, and T-INTEGRATE-04.
"""

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert data["docs_url"] == "/docs"


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert data["service"] == "vitalis-screening-api"


def test_readiness_endpoint():
    response = client.get("/readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["service_status"] == "alive"
    assert "specialists" in data
    specs = data["specialists"]
    assert "obesity" in specs
    assert specs["obesity"]["module_1_pipeline_ready"] is True
    assert specs["obesity"]["model_trained"] is False
    assert specs["diabetes"]["status"] == "pending_approval"
    assert specs["cvd"]["status"] == "pending_approval"
    assert specs["masld"]["status"] == "pending_approval"


def test_obesity_e2_valid_fixture():
    payload = {
        "Gender": "Female",
        "Age": 28.0,
        "family_history_with_overweight": "yes",
        "FAVC": "yes",
        "FCVC": 2.5,
        "NCP": 3.0,
        "CAEC": "Sometimes",
        "SMOKE": "no",
        "CH2O": 2.0,
        "SCC": "no",
        "FAF": 1.5,
        "TUE": 0.5,
        "CALC": "no",
        "MTRANS": "Public_Transportation",
    }
    response = client.post("/api/v1/screen/obesity", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PREPROCESSING_SUCCESSFUL"
    assert data["disease"] == "obesity"
    assert data["feature_set"] == "e2_lifestyle_only"
    assert data["model_readiness"] == "PENDING_MODULE_2_TRAINING"
    assert data["transformed_feature_count"] > 0


def test_obesity_e2_under_18_advisory():
    payload = {
        "Gender": "Male",
        "Age": 16.0,
        "family_history_with_overweight": "no",
        "FAVC": "no",
        "FCVC": 2.0,
        "NCP": 3.0,
        "CAEC": "Sometimes",
        "SMOKE": "no",
        "CH2O": 2.0,
        "SCC": "no",
        "FAF": 2.0,
        "TUE": 1.0,
        "CALC": "no",
        "MTRANS": "Walking",
    }
    response = client.post("/api/v1/screen/obesity", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert any("under 18" in note.lower() for note in data["advisory_notes"])


def test_obesity_e2_missing_field_rejected():
    # Missing required 'Gender' and 'Age'
    payload = {
        "FAVC": "yes",
        "FCVC": 2.0,
    }
    response = client.post("/api/v1/screen/obesity", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["error"] == "VALIDATION_ERROR"
    assert len(data["details"]) > 0


def test_obesity_e2_invalid_category_rejected():
    payload = {
        "Gender": "InvalidGender",
        "Age": 25.0,
        "family_history_with_overweight": "yes",
        "FAVC": "yes",
        "FCVC": 2.0,
        "NCP": 3.0,
        "CAEC": "Sometimes",
        "SMOKE": "no",
        "CH2O": 2.0,
        "SCC": "no",
        "FAF": 1.0,
        "TUE": 1.0,
        "CALC": "no",
        "MTRANS": "Walking",
    }
    response = client.post("/api/v1/screen/obesity", json=payload)
    assert response.status_code == 422


def test_obesity_e1_valid_fixture():
    payload = {
        "Gender": "Male",
        "Age": 35.0,
        "Height": 1.75,
        "Weight": 80.0,
        "family_history_with_overweight": "yes",
        "FAVC": "yes",
        "FCVC": 2.0,
        "NCP": 3.0,
        "CAEC": "Sometimes",
        "SMOKE": "no",
        "CH2O": 2.0,
        "SCC": "no",
        "FAF": 1.0,
        "TUE": 1.0,
        "CALC": "Sometimes",
        "MTRANS": "Automobile",
    }
    response = client.post("/api/v1/screen/obesity/e1", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["feature_set"] == "e1_bmi_inclusive"
    assert any("baseline" in note.lower() for note in data["advisory_notes"])


def test_unimplemented_diseases_return_501():
    for disease in ["diabetes", "cvd", "masld"]:
        response = client.post(f"/api/v1/screen/{disease}")
        assert response.status_code == 501
        assert "pending formal approval" in response.json()["detail"]


def test_unknown_disease_returns_404():
    response = client.post("/api/v1/screen/unknown_cancer")
    assert response.status_code == 404
