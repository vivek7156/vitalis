"""Leakage-safe Module 2 training, calibration and frozen-test evaluation."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline

from pipeline.evaluation import evaluate_classifier
from pipeline.loader import load_feature_config
from pipeline.preprocessing import create_preprocessing_pipeline

TARGET_CLASS_MAP = {
    "Insufficient_Weight": 0,
    "Normal_Weight": 1,
    "Overweight_Level_I": 2,
    "Overweight_Level_II": 3,
    "Obesity_Type_I": 4,
    "Obesity_Type_II": 5,
    "Obesity_Type_III": 6,
}


def _candidate_models(seed: int) -> dict[str, tuple[str, Any]]:
    return {
        "LogisticRegression": (
            "linear",
            LogisticRegression(
                max_iter=2000,
                class_weight="balanced",
                random_state=seed,
            ),
        ),
        "RandomForest": (
            "tree",
            RandomForestClassifier(
                n_estimators=250,
                class_weight="balanced",
                random_state=seed,
                n_jobs=-1,
            ),
        ),
        "CatBoost": (
            "tree",
            CatBoostClassifier(
                iterations=350,
                depth=6,
                learning_rate=0.05,
                loss_function="MultiClass",
                verbose=False,
                random_seed=seed,
                thread_count=1,
            ),
        ),
    }


def _build_estimator(
    disease: str,
    feature_set: str,
    model_family: str,
    classifier: Any,
    config_dir: Path,
) -> Pipeline:
    preprocessing, _ = create_preprocessing_pipeline(
        disease=disease,
        feature_set=feature_set,
        config_dir=config_dir,
        model_family=model_family,
    )
    return Pipeline(
        [("preprocessor", preprocessing.named_steps["preprocessor"]),
         ("classifier", classifier)]
    )


def _cv_model(
    model_name: str,
    model_family: str,
    classifier: Any,
    train: pd.DataFrame,
    feature_list: list[str],
    target: str,
    classes: np.ndarray,
    folds: int,
    seed: int,
    disease: str,
    feature_set: str,
    config_dir: Path,
) -> dict[str, Any]:
    splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
    fold_results = []
    X = train[feature_list]
    y = train[target].to_numpy()
    for fold, (train_indices, valid_indices) in enumerate(splitter.split(X, y), 1):
        estimator = _build_estimator(
            disease,
            feature_set,
            model_family,
            clone(classifier),
            config_dir,
        )
        started = time.perf_counter()
        estimator.fit(X.iloc[train_indices], y[train_indices])
        metrics = evaluate_classifier(
            estimator,
            X.iloc[valid_indices],
            y[valid_indices],
            classes,
        )
        metrics["fold"] = fold
        metrics["runtime_seconds"] = round(time.perf_counter() - started, 4)
        fold_results.append(metrics)
    return {
        "model_name": model_name,
        "model_family": model_family,
        "macro_f1_mean": float(np.mean([item["macro_f1"] for item in fold_results])),
        "macro_f1_std": float(np.std([item["macro_f1"] for item in fold_results])),
        "accuracy_mean": float(np.mean([item["accuracy"] for item in fold_results])),
        "accuracy_std": float(np.std([item["accuracy"] for item in fold_results])),
        "balanced_accuracy_mean": float(
            np.mean([item["balanced_accuracy"] for item in fold_results])
        ),
        "log_loss_mean": float(np.mean([item["log_loss"] for item in fold_results])),
        "folds": fold_results,
    }


def train_feature_set(
    feature_set: str,
    data_dir: Path = Path("data/processed"),
    output_dir: Path = Path("artifacts"),
    config_dir: Path = Path("config"),
    disease: str = "obesity",
    folds: int = 5,
    seed: int = 42,
) -> dict[str, Any]:
    """Train candidates on train-only folds and calibrate the champion on val."""
    train = pd.read_csv(data_dir / f"{disease}_train.csv")
    validation = pd.read_csv(data_dir / f"{disease}_val.csv")
    test = pd.read_csv(data_dir / f"{disease}_test.csv")
    feature_config = load_feature_config(config_dir, disease)
    target = feature_config["target"]
    feature_list = feature_config[feature_set]
    classes = np.asarray(feature_config["target_classes"])
    candidates = _candidate_models(seed)

    cv_results = {}
    for name, (family, classifier) in candidates.items():
        cv_results[name] = _cv_model(
            name, family, classifier, train, feature_list, target, classes,
            folds, seed, disease, feature_set, config_dir,
        )
    champion_name = max(cv_results, key=lambda name: cv_results[name]["macro_f1_mean"])
    champion_family, champion_classifier = candidates[champion_name]
    base_estimator = _build_estimator(
        disease, feature_set, champion_family, champion_classifier, config_dir
    )
    base_estimator.fit(train[feature_list], train[target])

    validation_metrics = evaluate_classifier(
        base_estimator, validation[feature_list], validation[target].to_numpy(), classes
    )
    try:
        from sklearn.frozen import FrozenEstimator
    except ImportError:
        calibrated = CalibratedClassifierCV(
            estimator=base_estimator, method="sigmoid", cv="prefit"
        )
    else:
        calibrated = CalibratedClassifierCV(
            estimator=FrozenEstimator(base_estimator), method="sigmoid"
        )
    calibrated.fit(validation[feature_list], validation[target])
    test_metrics = evaluate_classifier(
        calibrated, test[feature_list], test[target].to_numpy(), classes
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"{disease}_{feature_set}"
    model_path = output_dir / f"{prefix}_model.joblib"
    metrics_path = output_dir / f"{prefix}_training_metrics.json"
    joblib.dump(calibrated, model_path)
    metrics = {
        "disease": disease,
        "feature_set": feature_set,
        "feature_count": len(feature_list),
        "target": target,
        "classes": classes.tolist(),
        "champion_model": champion_name,
        "calibration": {
            "method": "sigmoid",
            "fit_partition": "validation",
            "test_partition_excluded": True,
        },
        "cv_folds": folds,
        "seed": seed,
        "cv_summary": cv_results[champion_name],
        "all_cv_results": cv_results,
        "validation_base_model": validation_metrics,
        "test_calibrated_model": test_metrics,
        "artifacts": {
            "model": str(model_path),
            "metrics": str(metrics_path),
        },
    }
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Train and evaluate obesity models.")
    parser.add_argument("--feature-set", choices=["e1_bmi_inclusive", "e2_lifestyle_only"])
    parser.add_argument("--data-dir", default="data/processed")
    parser.add_argument("--output-dir", default="artifacts")
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    feature_sets = [args.feature_set] if args.feature_set else [
        "e2_lifestyle_only", "e1_bmi_inclusive"
    ]
    for feature_set in feature_sets:
        result = train_feature_set(
            feature_set,
            data_dir=Path(args.data_dir),
            output_dir=Path(args.output_dir),
            folds=args.folds,
            seed=args.seed,
        )
        print(
            f"{feature_set}: {result['champion_model']} "
            f"CV macro-F1={result['cv_summary']['macro_f1_mean']:.4f}"
        )


if __name__ == "__main__":
    main()
