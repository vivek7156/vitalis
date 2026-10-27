"""Metrics used by the Module 2 training and evaluation workflow."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)

from pipeline.calibration import calibration_metrics


def evaluate_classifier(
    estimator: Any,
    X: Any,
    y: np.ndarray,
    classes: np.ndarray,
) -> dict[str, Any]:
    """Evaluate one already-fitted classifier on a single partition."""
    predictions = estimator.predict(X)
    probabilities = estimator.predict_proba(X)
    report = classification_report(
        y,
        predictions,
        labels=classes,
        output_dict=True,
        zero_division=0,
    )
    auc_classes = np.sort(classes)
    auc_order = [int(np.where(classes == label)[0][0]) for label in auc_classes]
    return {
        "accuracy": float(accuracy_score(y, predictions)),
        "balanced_accuracy": float(balanced_accuracy_score(y, predictions)),
        "macro_f1": float(f1_score(y, predictions, average="macro")),
        "weighted_f1": float(f1_score(y, predictions, average="weighted")),
        "macro_precision": float(
            precision_score(y, predictions, average="macro", zero_division=0)
        ),
        "macro_recall": float(
            recall_score(y, predictions, average="macro", zero_division=0)
        ),
        "sample_count": len(y),
        "log_loss": float(
            log_loss(y, probabilities[:, auc_order], labels=auc_classes)
        ),
        "roc_auc_ovr": float(
            roc_auc_score(
                y,
                probabilities[:, auc_order],
                labels=auc_classes,
                multi_class="ovr",
            )
        ),
        "confusion_matrix": confusion_matrix(y, predictions, labels=classes).tolist(),
        "per_class": {
            label: {
                "support": int(report[label]["support"]),
                "precision": float(report[label]["precision"]),
                "recall": float(report[label]["recall"]),
                "f1": float(report[label]["f1-score"]),
            }
            for label in classes
        },
        "calibration": calibration_metrics(y, probabilities, classes),
    }
