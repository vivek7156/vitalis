"""Configurable preprocessing factory for disease pipelines.

Covers tasks T-PREP-01 through T-PREP-17 from the Module 1 checklist.
Builds scikit-learn Pipeline/ColumnTransformer combinations per disease
and feature set. Fits only on training data, preserves feature mappings,
and supports serialisation round-trips.
"""

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    OneHotEncoder,
    OrdinalEncoder,
    StandardScaler,
)

from pipeline.loader import load_feature_config

# ---------------------------------------------------------------------------
# Feature classification
# ---------------------------------------------------------------------------

# Obesity-specific feature metadata
OBESITY_NUMERIC_FEATURES = ["Age", "FCVC", "NCP", "CH2O", "FAF", "TUE"]
OBESITY_BINARY_FEATURES = [
    "family_history_with_overweight", "FAVC", "SMOKE", "SCC",
]
OBESITY_ORDINAL_FEATURES: dict[str, list[str]] = {
    "CAEC": ["no", "Sometimes", "Frequently", "Always"],
    "CALC": ["no", "Sometimes", "Frequently", "Always"],
}
OBESITY_NOMINAL_FEATURES = ["Gender", "MTRANS"]

# E1-only features
OBESITY_E1_EXTRA_NUMERIC = ["Height", "Weight"]

# Features excluded from E2 (T-PREP: E2 rejects Height, Weight, BMI)
E2_EXCLUDED = {"Height", "Weight"}


def _classify_features(
    feature_list: list[str],
    feature_set: str,
) -> dict[str, list[str]]:
    """Classify features into numeric, binary, ordinal, nominal groups."""
    numeric = []
    binary = []
    ordinal = []
    nominal = []

    for f in feature_list:
        if f in E2_EXCLUDED and feature_set == "e2_lifestyle_only":
            raise ValueError(
                f"Feature '{f}' is excluded from E2 but appears in feature list."
            )
        if f in OBESITY_NUMERIC_FEATURES or f in OBESITY_E1_EXTRA_NUMERIC:
            numeric.append(f)
        elif f in OBESITY_BINARY_FEATURES:
            binary.append(f)
        elif f in OBESITY_ORDINAL_FEATURES:
            ordinal.append(f)
        elif f in OBESITY_NOMINAL_FEATURES:
            nominal.append(f)
        else:
            # Default: treat as nominal
            nominal.append(f)

    return {
        "numeric": numeric,
        "binary": binary,
        "ordinal": ordinal,
        "nominal": nominal,
    }


# ---------------------------------------------------------------------------
# Preprocessing factory (T-PREP-01)
# ---------------------------------------------------------------------------

def create_preprocessing_pipeline(
    disease: str = "obesity",
    feature_set: str = "e2_lifestyle_only",
    config_dir: Path = Path("config"),
    model_family: str = "tree",
) -> tuple[Pipeline, dict[str, Any]]:
    """Create an unfitted preprocessing pipeline for the given configuration.

    Parameters
    ----------
    disease : str
        Disease identifier.
    feature_set : str
        Feature set key (e.g. "e1_bmi_inclusive" or "e2_lifestyle_only").
    config_dir : Path
        Config directory.
    model_family : str
        One of "tree", "linear", or "catboost".
        Controls encoding strategy (T-PREP-03).

    Returns
    -------
    pipeline : sklearn.pipeline.Pipeline
        Unfitted preprocessing pipeline.
    feature_mapping : dict
        Maps transformed column positions to original field names (T-PREP-11).
    """
    feat_cfg = load_feature_config(config_dir, disease)

    if feature_set not in feat_cfg:
        available = [k for k in feat_cfg if k not in ("target", "target_classes")]
        raise ValueError(
            f"Unknown feature set '{feature_set}'. Available: {available}"
        )

    feature_list = feat_cfg[feature_set]

    # Validate E2 exclusion (T-PREP: E2 rejects Height, Weight, BMI)
    if feature_set == "e2_lifestyle_only":
        for excluded in E2_EXCLUDED:
            if excluded in feature_list:
                raise ValueError(
                    f"E2 feature set must not contain '{excluded}'"
                )

    classified = _classify_features(feature_list, feature_set)

    # --- Build transformers per feature type (T-PREP-02) ---
    transformers = []

    # Numeric features: impute + scale
    if classified["numeric"]:
        if model_family == "tree":
            # Trees don't strictly need scaling, but imputation is still needed
            num_pipeline = Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
            ])
        else:
            num_pipeline = Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ])
        transformers.append(("numeric", num_pipeline, classified["numeric"]))

    # Binary features: ordinal encode (yes/no → 0/1)
    if classified["binary"]:
        bin_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OrdinalEncoder(
                categories=[["no", "yes"]] * len(classified["binary"]),
                handle_unknown="use_encoded_value",
                unknown_value=-1,
            )),
        ])
        transformers.append(("binary", bin_pipeline, classified["binary"]))

    # Ordinal features: ordinal encode with known order
    if classified["ordinal"]:
        ord_categories = [
            OBESITY_ORDINAL_FEATURES[f] for f in classified["ordinal"]
        ]
        ord_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OrdinalEncoder(
                categories=ord_categories,
                handle_unknown="use_encoded_value",
                unknown_value=-1,
            )),
        ])
        transformers.append(("ordinal", ord_pipeline, classified["ordinal"]))

    # Nominal features: encoding strategy depends on model family (T-PREP-03)
    if classified["nominal"]:
        if model_family == "catboost":
            # CatBoost handles categoricals natively (T-PREP-09)
            # Just impute; pass through as-is
            nom_pipeline = Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
            ])
        elif model_family == "tree":
            nom_pipeline = Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("encoder", OneHotEncoder(
                    sparse_output=False,
                    handle_unknown="infrequent_if_exist",
                    min_frequency=2,
                )),
            ])
        else:  # linear
            nom_pipeline = Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("encoder", OneHotEncoder(
                    sparse_output=False,
                    drop="first",
                    handle_unknown="infrequent_if_exist",
                    min_frequency=2,
                )),
            ])
        transformers.append(("nominal", nom_pipeline, classified["nominal"]))

    # Assemble ColumnTransformer
    preprocessor = ColumnTransformer(
        transformers=transformers,
        remainder="drop",
        verbose_feature_names_out=True,
    )

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
    ])

    # Build feature mapping (T-PREP-11)
    feature_mapping = {
        "feature_set": feature_set,
        "model_family": model_family,
        "classified_features": classified,
        "input_features": feature_list,
        "note": (
            "Transformed column names available after fitting via "
            "pipeline.get_feature_names_out()"
        ),
    }

    return pipeline, feature_mapping


# ---------------------------------------------------------------------------
# Fit / transform helpers (T-PREP-05, T-PREP-15)
# ---------------------------------------------------------------------------

def fit_transform_train(
    pipeline: Pipeline,
    df_train: pd.DataFrame,
    feature_list: list[str],
) -> np.ndarray:
    """Fit the pipeline on training data and return transformed array.

    The pipeline is fitted ONLY on training data (T-PREP-05).
    """
    X = df_train[feature_list]
    return pipeline.fit_transform(X)


def transform_partition(
    pipeline: Pipeline,
    df_partition: pd.DataFrame,
    feature_list: list[str],
) -> np.ndarray:
    """Transform a validation/test partition without refitting (T-PREP-15)."""
    X = df_partition[feature_list]
    return pipeline.transform(X)


# ---------------------------------------------------------------------------
# Serialisation (T-PREP-16)
# ---------------------------------------------------------------------------

def save_preprocessing(
    pipeline: Pipeline,
    feature_mapping: dict[str, Any],
    output_dir: Path,
    disease: str = "obesity",
    feature_set: str = "e2_lifestyle_only",
) -> Path:
    """Save a fitted pipeline and feature mapping to disk."""
    output_dir.mkdir(parents=True, exist_ok=True)

    prefix = f"{disease}_{feature_set}"
    pipeline_path = output_dir / f"{prefix}_pipeline.joblib"
    mapping_path = output_dir / f"{prefix}_feature_mapping.json"

    joblib.dump(pipeline, pipeline_path)
    mapping_path.write_text(
        json.dumps(feature_mapping, indent=2, default=str),
        encoding="utf-8",
    )

    print(f"Saved pipeline: {pipeline_path}")
    print(f"Saved mapping:  {mapping_path}")
    return pipeline_path


def load_preprocessing(
    output_dir: Path,
    disease: str = "obesity",
    feature_set: str = "e2_lifestyle_only",
) -> tuple[Pipeline, dict[str, Any]]:
    """Load a saved pipeline and feature mapping."""
    prefix = f"{disease}_{feature_set}"
    pipeline_path = output_dir / f"{prefix}_pipeline.joblib"
    mapping_path = output_dir / f"{prefix}_feature_mapping.json"

    if not pipeline_path.exists():
        raise FileNotFoundError(f"Pipeline not found: {pipeline_path}")

    pipeline = joblib.load(pipeline_path)
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    return pipeline, mapping


# ---------------------------------------------------------------------------
# Round-trip verification (T-PREP-16)
# ---------------------------------------------------------------------------

def verify_round_trip(
    pipeline: Pipeline,
    df_test: pd.DataFrame,
    feature_list: list[str],
    output_dir: Path,
    disease: str = "obesity",
    feature_set: str = "e2_lifestyle_only",
    feature_mapping: dict[str, Any] | None = None,
    atol: float = 1e-10,
) -> bool:
    """Verify save/load round-trip preserves transformation outputs.

    Returns True if outputs match within the specified tolerance.
    """
    # Transform with original pipeline
    original_output = transform_partition(pipeline, df_test, feature_list)

    if feature_mapping is None:
        mapping_path = output_dir / f"{disease}_{feature_set}_feature_mapping.json"
        if mapping_path.exists():
            feature_mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
        else:
            feature_mapping = {}

    # Save and reload
    save_preprocessing(pipeline, feature_mapping, output_dir, disease, feature_set)
    loaded_pipeline, _ = load_preprocessing(output_dir, disease, feature_set)

    # Transform with reloaded pipeline
    reloaded_output = transform_partition(loaded_pipeline, df_test, feature_list)

    # Compare
    if original_output.shape != reloaded_output.shape:
        print(f"[FAIL] Shape mismatch: {original_output.shape} vs {reloaded_output.shape}")
        return False

    # Handle mixed types (numeric arrays may contain strings for catboost)
    try:
        matches = np.allclose(
            original_output.astype(float),
            reloaded_output.astype(float),
            atol=atol,
        )
    except (ValueError, TypeError):
        matches = np.array_equal(original_output, reloaded_output)

    if matches:
        print("[OK] Round-trip verification passed.")
    else:
        print("[FAIL] Round-trip verification FAILED.")
    return matches


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Create preprocessing pipeline"
    )
    parser.add_argument("--disease", default="obesity")
    parser.add_argument("--feature-set", default="e2_lifestyle_only")
    parser.add_argument("--model-family", default="tree",
                        choices=["tree", "linear", "catboost"])
    parser.add_argument("--config-dir", default="config")
    args = parser.parse_args()

    pipe, mapping = create_preprocessing_pipeline(
        disease=args.disease,
        feature_set=args.feature_set,
        config_dir=Path(args.config_dir),
        model_family=args.model_family,
    )
    print(f"Created unfitted pipeline for {args.disease}/{args.feature_set}")
    print(f"  Model family: {args.model_family}")
    print(f"  Input features: {mapping['input_features']}")
    print(f"  Feature groups: { {k: len(v) for k, v in mapping['classified_features'].items()} }")
