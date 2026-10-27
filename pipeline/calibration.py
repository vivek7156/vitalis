"""Probability calibration helpers for the obesity specialist models."""

from __future__ import annotations

import itertools
from typing import Any

import numpy as np
from sklearn.metrics import brier_score_loss


def multiclass_brier_score(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    classes: np.ndarray,
) -> float:
    """Return the one-vs-rest multiclass Brier score."""
    truth = np.zeros_like(probabilities, dtype=float)
    class_to_index = {label: index for index, label in enumerate(classes)}
    for row, label in enumerate(y_true):
        truth[row, class_to_index[label]] = 1.0
    return float(np.mean(np.sum((probabilities - truth) ** 2, axis=1)))


def expected_calibration_error(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    classes: np.ndarray,
    bins: int = 10,
) -> float:
    """Calculate top-class expected calibration error."""
    predicted = np.argmax(probabilities, axis=1)
    confidence = probabilities[np.arange(len(probabilities)), predicted]
    correct = (np.asarray(y_true) == classes[predicted]).astype(float)
    edges = np.linspace(0.0, 1.0, bins + 1)
    error = 0.0
    for lower, upper in itertools.pairwise(edges):
        in_bin = (confidence >= lower) & (
            confidence <= upper if upper == 1.0 else confidence < upper
        )
        if np.any(in_bin):
            error += float(np.sum(in_bin)) / len(confidence) * abs(
                float(np.mean(correct[in_bin])) - float(np.mean(confidence[in_bin]))
            )
    return error


def calibration_metrics(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    classes: np.ndarray,
) -> dict[str, Any]:
    """Return calibration metrics without fitting on the supplied data."""
    return {
        "brier_score": multiclass_brier_score(y_true, probabilities, classes),
        "expected_calibration_error": expected_calibration_error(
            y_true, probabilities, classes
        ),
        "sample_count": len(y_true),
    }


def binary_brier_score(y_true: np.ndarray, probability: np.ndarray) -> float:
    """Expose the sklearn binary metric for callers evaluating one class."""
    return float(brier_score_loss(y_true, probability))
