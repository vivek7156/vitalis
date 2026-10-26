"""Shared test fixtures for the Vitalis pipeline test suite.

Uses synthetic data that does not require downloading external datasets.
Lightweight tests run without network access (Section 12 checklist).
"""


import numpy as np
import pandas as pd
import pytest
import yaml

# ---------------------------------------------------------------------------
# Synthetic obesity-like data fixture
# ---------------------------------------------------------------------------

SYNTHETIC_ROWS = 200
TARGET_CLASSES = [
    "Insufficient_Weight",
    "Normal_Weight",
    "Overweight_Level_I",
    "Overweight_Level_II",
    "Obesity_Type_I",
    "Obesity_Type_II",
    "Obesity_Type_III",
]


def _make_synthetic_obesity_df(n: int = SYNTHETIC_ROWS) -> pd.DataFrame:
    """Create a small synthetic DataFrame matching the obesity dataset schema."""
    rng = np.random.RandomState(42)

    genders = rng.choice(["Female", "Male"], size=n)
    ages = rng.uniform(14, 60, size=n).round(2)
    heights = rng.uniform(1.45, 1.98, size=n).round(2)
    weights = rng.uniform(39, 170, size=n).round(2)
    fam_hist = rng.choice(["no", "yes"], size=n)
    favc = rng.choice(["no", "yes"], size=n)
    fcvc = rng.uniform(1, 3, size=n).round(6)
    ncp = rng.uniform(1, 4, size=n).round(6)
    caec = rng.choice(["Always", "Frequently", "Sometimes", "no"], size=n)
    smoke = rng.choice(["no", "yes"], size=n)
    ch2o = rng.uniform(1, 3, size=n).round(6)
    scc = rng.choice(["no", "yes"], size=n)
    faf = rng.uniform(0, 3, size=n).round(6)
    tue = rng.uniform(0, 2, size=n).round(6)
    calc = rng.choice(["Always", "Frequently", "Sometimes", "no"], size=n)
    mtrans = rng.choice(
        ["Automobile", "Bike", "Motorbike", "Public_Transportation", "Walking"],
        size=n,
    )
    # Ensure all 7 target classes appear
    targets = list(rng.choice(TARGET_CLASSES, size=n))
    for i, cls in enumerate(TARGET_CLASSES):
        targets[i] = cls  # guarantee each class appears at least once

    return pd.DataFrame({
        "Gender": genders,
        "Age": ages,
        "Height": heights,
        "Weight": weights,
        "family_history_with_overweight": fam_hist,
        "FAVC": favc,
        "FCVC": fcvc,
        "NCP": ncp,
        "CAEC": caec,
        "SMOKE": smoke,
        "CH2O": ch2o,
        "SCC": scc,
        "FAF": faf,
        "TUE": tue,
        "CALC": calc,
        "MTRANS": mtrans,
        "NObeyesdad": targets,
    })


@pytest.fixture
def synthetic_obesity_df():
    """Synthetic obesity DataFrame."""
    return _make_synthetic_obesity_df()


@pytest.fixture
def tmp_project(tmp_path):
    """Create a temporary project directory with configs and synthetic data.

    Returns a dict with paths for config_dir, data_root, data_file, and output_dir.
    """
    # Config dir
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    # datasets.yaml
    datasets_cfg = {
        "datasets": {
            "obesity": {
                "name": "Test Obesity Dataset",
                "file": "data/raw/obesity_test.csv",
                "source": "Synthetic test fixture",
                "license": "Test",
                "acquired_on": "2026-01-01",
                "rows_expected": SYNTHETIC_ROWS,
                "columns_expected": 17,
                "target": "NObeyesdad",
                "synthetic_share_reported": 0.77,
            }
        }
    }
    (config_dir / "datasets.yaml").write_text(
        yaml.dump(datasets_cfg), encoding="utf-8"
    )

    # features.yaml
    features_cfg = {
        "obesity": {
            "target": "NObeyesdad",
            "target_classes": TARGET_CLASSES,
            "e1_bmi_inclusive": [
                "Gender", "Age", "Height", "Weight",
                "family_history_with_overweight", "FAVC", "FCVC", "NCP",
                "CAEC", "SMOKE", "CH2O", "SCC", "FAF", "TUE",
                "CALC", "MTRANS",
            ],
            "e2_lifestyle_only": [
                "Gender", "Age",
                "family_history_with_overweight", "FAVC", "FCVC", "NCP",
                "CAEC", "SMOKE", "CH2O", "SCC", "FAF", "TUE",
                "CALC", "MTRANS",
            ],
        }
    }
    (config_dir / "features.yaml").write_text(
        yaml.dump(features_cfg), encoding="utf-8"
    )

    # Data directory
    data_dir = tmp_path / "data" / "raw"
    data_dir.mkdir(parents=True)
    df = _make_synthetic_obesity_df()
    data_file = data_dir / "obesity_test.csv"
    df.to_csv(data_file, index=False)

    # Output directories
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    manifests_dir = tmp_path / "data" / "manifests"
    manifests_dir.mkdir(parents=True)
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir(parents=True)
    docs_dir = tmp_path / "docs" / "dataset-audits"
    docs_dir.mkdir(parents=True)

    return {
        "root": tmp_path,
        "config_dir": config_dir,
        "data_root": tmp_path,
        "data_file": data_file,
        "processed_dir": processed_dir,
        "manifests_dir": manifests_dir,
        "artifacts_dir": artifacts_dir,
    }
