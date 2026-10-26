"""Configurable dataset loader with validation.

Covers tasks T-LOAD-01 through T-LOAD-11 from the Module 1 checklist.
Loads datasets based on config/datasets.yaml and config/features.yaml,
validates columns, types, categories, numeric ranges, and returns
structured error reporting.
"""

import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------

def _load_yaml(path: Path) -> dict:
    """Load a YAML configuration file."""
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_dataset_config(
    config_dir: Path = Path("config"),
    disease: str = "obesity",
) -> dict:
    """Return the dataset configuration for *disease*."""
    cfg = _load_yaml(config_dir / "datasets.yaml")
    datasets = cfg.get("datasets", cfg)
    if disease not in datasets:
        raise ValueError(
            f"Unknown disease '{disease}'. "
            f"Available: {list(datasets.keys())}"
        )
    return datasets[disease]


def load_feature_config(
    config_dir: Path = Path("config"),
    disease: str = "obesity",
) -> dict:
    """Return the feature configuration for *disease*."""
    cfg = _load_yaml(config_dir / "features.yaml")
    if disease not in cfg:
        raise ValueError(
            f"No feature config for disease '{disease}'. "
            f"Available: {list(cfg.keys())}"
        )
    return cfg[disease]


# ---------------------------------------------------------------------------
# Checksum
# ---------------------------------------------------------------------------

def compute_sha256(path: Path) -> str:
    """Return the SHA-256 hex-digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

# Expected categorical values per column for the obesity dataset.
OBESITY_CATEGORICAL_VALUES: dict[str, list[str]] = {
    "Gender": ["Female", "Male"],
    "family_history_with_overweight": ["no", "yes"],
    "FAVC": ["no", "yes"],
    "CAEC": ["Always", "Frequently", "Sometimes", "no"],
    "SMOKE": ["no", "yes"],
    "SCC": ["no", "yes"],
    "CALC": ["Always", "Frequently", "Sometimes", "no"],
    "MTRANS": ["Automobile", "Bike", "Motorbike", "Public_Transportation", "Walking"],
}

OBESITY_TARGET_CLASSES = [
    "Insufficient_Weight",
    "Normal_Weight",
    "Overweight_Level_I",
    "Overweight_Level_II",
    "Obesity_Type_I",
    "Obesity_Type_II",
    "Obesity_Type_III",
]

# Reasonable numeric ranges (min, max) based on dataset description / domain.
OBESITY_NUMERIC_RANGES: dict[str, tuple[float, float]] = {
    "Age": (0, 150),
    "Height": (0.5, 2.5),   # metres
    "Weight": (10, 400),     # kg
    "FCVC": (1, 3),
    "NCP": (1, 4),
    "CH2O": (1, 3),
    "FAF": (0, 3),
    "TUE": (0, 2),
}


class ValidationReport:
    """Collects row/field validation results."""

    def __init__(self) -> None:
        self.errors: list[dict[str, Any]] = []
        self.warnings: list[dict[str, Any]] = []
        self.accepted: int = 0
        self.rejected: int = 0
        self.quarantined: int = 0

    def add_error(self, **kwargs: Any) -> None:
        self.errors.append(kwargs)

    def add_warning(self, **kwargs: Any) -> None:
        self.warnings.append(kwargs)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "rejected": self.rejected,
            "quarantined": self.quarantined,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.errors[:50],   # cap for readability
            "warnings": self.warnings[:50],
        }


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def load_and_validate(
    disease: str = "obesity",
    config_dir: Path = Path("config"),
    data_root: Path = Path("."),
) -> tuple[pd.DataFrame, ValidationReport]:
    """Load, validate, and return the dataset along with a validation report.

    Parameters
    ----------
    disease : str
        Disease identifier (must match keys in datasets.yaml).
    config_dir : Path
        Directory containing datasets.yaml and features.yaml.
    data_root : Path
        Root directory that the ``file`` path in datasets.yaml is relative to.

    Returns
    -------
    df : pd.DataFrame
        The loaded (but uncleaned) DataFrame.
    report : ValidationReport
        Structured validation report.
    """
    # --- Config validation first (T-LOAD-11) ---
    ds_cfg = load_dataset_config(config_dir, disease)
    feat_cfg = load_feature_config(config_dir, disease)

    target_col = ds_cfg.get("target") or feat_cfg.get("target")
    if not target_col:
        raise ValueError(f"No target column defined for disease '{disease}'")

    # --- Check pending approval status (T-DATA-11) ---
    if ds_cfg.get("status") == "pending_approval" or "file" not in ds_cfg:
        raise ValueError(
            f"Dataset for disease '{disease}' is pending approval and cannot be loaded (T-DATA-11)."
        )

    # --- File existence and format (T-LOAD-02) ---
    file_path = data_root / ds_cfg["file"]
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset not found: {file_path}")

    suffix = file_path.suffix.lower()
    if suffix not in {".csv", ".tsv"}:
        raise ValueError(f"Unsupported file format: {suffix}")

    report = ValidationReport()

    # --- Load with explicit encoding/delimiter (T-LOAD-03) ---
    delimiter = "\t" if suffix == ".tsv" else ","
    df = pd.read_csv(file_path, delimiter=delimiter, encoding="utf-8")

    # --- Detect accidental index columns / duplicate col names (T-LOAD-04) ---
    if df.columns[0] == "Unnamed: 0":
        report.add_warning(
            field="index",
            issue="Detected accidental index column; dropping it.",
        )
        df = df.drop(columns=["Unnamed: 0"])

    if len(df.columns) != len(set(df.columns)):
        dup_cols = [c for c in df.columns if list(df.columns).count(c) > 1]
        report.add_error(
            field="columns",
            issue=f"Duplicate column names detected: {dup_cols}",
        )

    # --- Expected columns (T-LOAD-02) ---
    all_features = set()
    for key in ("e1_bmi_inclusive", "e2_lifestyle_only"):
        if key in feat_cfg:
            all_features.update(feat_cfg[key])
    expected = all_features | {target_col}

    missing_cols = expected - set(df.columns)
    extra_cols = set(df.columns) - expected
    if missing_cols:
        report.add_error(
            field="columns",
            issue=f"Missing expected columns: {sorted(missing_cols)}",
        )
    if extra_cols:
        report.add_warning(
            field="columns",
            issue=f"Unexpected columns present: {sorted(extra_cols)}",
        )

    # --- Row-level validation (T-LOAD-05 → T-LOAD-07) ---
    rows_expected = ds_cfg.get("rows_expected")
    cols_expected = ds_cfg.get("columns_expected")
    if rows_expected and len(df) != rows_expected:
        report.add_warning(
            field="row_count",
            issue=f"Expected {rows_expected} rows, got {len(df)}",
        )
    if cols_expected and len(df.columns) != cols_expected:
        report.add_warning(
            field="column_count",
            issue=f"Expected {cols_expected} columns, got {len(df.columns)}",
        )

    # Validate categories
    for col, valid_vals in OBESITY_CATEGORICAL_VALUES.items():
        if col in df.columns:
            actual = set(df[col].dropna().unique())
            invalid = actual - set(valid_vals)
            if invalid:
                report.add_error(
                    field=col,
                    issue=f"Unknown categories: {sorted(invalid)}",
                )

    # Validate numeric ranges and non-finite numbers (T-LOAD-06)
    for col, (lo, hi) in OBESITY_NUMERIC_RANGES.items():
        if col in df.columns:
            non_finite = int((~np.isfinite(df[col])).sum())
            if non_finite > 0:
                report.add_error(
                    field=col,
                    issue=f"{non_finite} non-finite values detected",
                )
            out_of_range = int(((df[col] < lo) | (df[col] > hi)).sum())
            if out_of_range > 0:
                report.add_warning(
                    field=col,
                    issue=f"{out_of_range} values outside expected range [{lo}, {hi}]",
                )

    # --- Target validation (T-LOAD-10) ---
    if target_col not in df.columns:
        report.add_error(
            field=target_col,
            issue="Target column is missing from the dataset",
        )
    else:
        missing_target = int(df[target_col].isna().sum())
        if missing_target > 0:
            report.add_error(
                field=target_col,
                issue=f"{missing_target} rows have missing target values",
            )
        # Validate target classes for obesity
        if disease == "obesity":
            actual_classes = set(df[target_col].dropna().unique())
            expected_classes = set(OBESITY_TARGET_CLASSES)
            if actual_classes != expected_classes:
                extra = actual_classes - expected_classes
                missing = expected_classes - actual_classes
                report.add_error(
                    field=target_col,
                    issue=(
                        f"Target class mismatch. "
                        f"Extra: {sorted(extra)}, Missing: {sorted(missing)}"
                    ),
                )

    # --- Missing values (T-LOAD-07) ---
    total_missing = int(df.isna().sum().sum())
    if total_missing > 0:
        per_col = df.isna().sum()
        cols_with_missing = per_col[per_col > 0].to_dict()
        report.add_warning(
            field="missing_values",
            issue=f"Total missing values: {total_missing}",
            details=cols_with_missing,
        )

    # --- Counts (T-LOAD-08) ---
    report.accepted = len(df) - report.rejected
    report.quarantined = 0  # all rows kept for now; audit will flag issues

    return df, report
