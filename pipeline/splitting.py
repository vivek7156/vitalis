"""Leakage-safe dataset partitioning.

Covers tasks T-SPLIT-01 through T-SPLIT-11 from the Module 1 checklist.
Creates stratified train/validation/test splits, deduplicates before
splitting, freezes split manifests, and ensures E1/E2 share identical
record membership.
"""

import datetime
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedShuffleSplit

from pipeline.loader import (
    compute_sha256,
    load_and_validate,
    load_dataset_config,
    load_feature_config,
)

# ---------------------------------------------------------------------------
# Default split parameters (T-SPLIT-01)
# ---------------------------------------------------------------------------

DEFAULT_TRAIN_RATIO = 0.70
DEFAULT_VAL_RATIO = 0.15
DEFAULT_TEST_RATIO = 0.15
DEFAULT_SEED = 42


def _deduplicate(
    df: pd.DataFrame,
    keep: str = "first",
) -> tuple[pd.DataFrame, list[int]]:
    """Remove exact duplicate rows (T-SPLIT-03).

    Returns the deduplicated DataFrame and the list of dropped indices.
    """
    dup_mask = df.duplicated(keep=keep)
    dropped_indices = df.index[dup_mask].tolist()
    return df[~dup_mask].reset_index(drop=True), dropped_indices


def _stratified_split(
    df: pd.DataFrame,
    target: str,
    train_ratio: float,
    val_ratio: float,
    test_ratio: float,
    seed: int,
) -> dict[str, np.ndarray]:
    """Create stratified train/val/test split (T-SPLIT-02).

    Returns dict mapping partition name → array of integer indices into *df*.
    """
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-9

    y = df[target].values
    indices = np.arange(len(df))

    # First split: train+val vs test
    test_frac = test_ratio
    sss1 = StratifiedShuffleSplit(
        n_splits=1,
        test_size=test_frac,
        random_state=seed,
    )
    trainval_idx, test_idx = next(sss1.split(indices, y))

    # Second split: train vs val (from the train+val portion)
    val_frac_of_trainval = val_ratio / (train_ratio + val_ratio)
    sss2 = StratifiedShuffleSplit(
        n_splits=1,
        test_size=val_frac_of_trainval,
        random_state=seed,
    )
    y_trainval = y[trainval_idx]
    train_sub_idx, val_sub_idx = next(sss2.split(trainval_idx, y_trainval))

    return {
        "train": trainval_idx[train_sub_idx],
        "val": trainval_idx[val_sub_idx],
        "test": test_idx,
    }


def _verify_no_overlap(partitions: dict[str, np.ndarray]) -> None:
    """T-SPLIT-04: Verify no record crosses partition boundaries."""
    names = list(partitions.keys())
    for i, name_a in enumerate(names):
        for name_b in names[i + 1:]:
            overlap = set(partitions[name_a]) & set(partitions[name_b])
            if overlap:
                raise RuntimeError(
                    f"Partition overlap between {name_a} and {name_b}: "
                    f"{len(overlap)} shared indices"
                )


def _partition_class_counts(
    df: pd.DataFrame,
    target: str,
    partitions: dict[str, np.ndarray],
) -> dict[str, dict[str, int]]:
    """T-SPLIT-05: Check class counts per partition."""
    result = {}
    for name, idx in partitions.items():
        counts = df.iloc[idx][target].value_counts().sort_index().to_dict()
        result[name] = counts
    return result


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------

def _create_manifest(
    disease: str,
    source_file: str,
    source_checksum: str,
    partitions: dict[str, np.ndarray],
    partition_class_counts: dict[str, dict[str, int]],
    dropped_indices: list[int],
    seed: int,
    train_ratio: float,
    val_ratio: float,
    test_ratio: float,
    config_version: str | None = None,
) -> dict[str, Any]:
    """T-SPLIT-07: Create split manifest."""
    return {
        "manifest_version": "1.0",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "disease": disease,
        "source_file": source_file,
        "source_checksum_sha256": source_checksum,
        "split_method": "stratified_shuffle_split",
        "seed": seed,
        "ratios": {
            "train": train_ratio,
            "val": val_ratio,
            "test": test_ratio,
        },
        "deduplication": {
            "method": "exact_duplicate_removal_keep_first",
            "dropped_count": len(dropped_indices),
        },
        "partitions": {
            name: {
                "size": len(idx),
                "indices": sorted(idx.tolist()),
            }
            for name, idx in partitions.items()
        },
        "partition_class_counts": partition_class_counts,
        "config_version": config_version,
        "notes": [
            "E1 and E2 share identical split membership (T-SPLIT-06).",
            "Test partition is frozen; do not use for tuning or preprocessing (T-SPLIT-08).",
            "Synthetic lineage unavailable at row level (T-SPLIT-11).",
        ],
    }


# ---------------------------------------------------------------------------
# Main splitter
# ---------------------------------------------------------------------------

def run_split(
    disease: str = "obesity",
    config_dir: Path = Path("config"),
    data_root: Path = Path("."),
    output_dir: Path | None = None,
    seed: int = DEFAULT_SEED,
    train_ratio: float = DEFAULT_TRAIN_RATIO,
    val_ratio: float = DEFAULT_VAL_RATIO,
    test_ratio: float = DEFAULT_TEST_RATIO,
    force: bool = False,
) -> dict[str, Any]:
    """Execute dataset splitting and write a frozen manifest.

    Parameters
    ----------
    disease : str
        Disease identifier.
    config_dir : Path
        Configuration directory.
    data_root : Path
        Root directory.
    output_dir : Path or None
        Output directory. Defaults to data/manifests/.
    seed : int
        Random seed for reproducibility.
    train_ratio, val_ratio, test_ratio : float
        Partition proportions.
    force : bool
        If True, overwrite existing manifest.

    Returns
    -------
    dict
        The split manifest.
    """
    if output_dir is None:
        output_dir = data_root / "data" / "manifests"
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = output_dir / f"{disease}_split_manifest.json"

    # Check for existing manifest (T-SPLIT-08: frozen test set)
    if manifest_path.exists() and not force:
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        # Validate checksum compatibility
        ds_cfg = load_dataset_config(config_dir, disease)
        file_path = data_root / ds_cfg["file"]
        current_checksum = compute_sha256(file_path)
        if existing.get("source_checksum_sha256") == current_checksum:
            print(f"Reusing existing compatible manifest: {manifest_path}")
            return existing
        else:
            raise RuntimeError(
                "Source checksum mismatch. Existing manifest was built from "
                "a different file. Use --force to regenerate."
            )

    # Load and validate
    ds_cfg = load_dataset_config(config_dir, disease)
    feat_cfg = load_feature_config(config_dir, disease)
    df, validation = load_and_validate(disease, config_dir, data_root)

    if not validation.is_valid:
        blocking = [e for e in validation.errors]
        raise RuntimeError(
            f"Dataset has {len(blocking)} validation error(s). "
            f"Resolve before splitting. First: {blocking[0] if blocking else 'N/A'}"
        )

    target = feat_cfg["target"]
    file_path = data_root / ds_cfg["file"]
    checksum = compute_sha256(file_path)

    # Deduplicate (T-SPLIT-03)
    df_clean, dropped = _deduplicate(df)
    print(f"Deduplication: dropped {len(dropped)} exact duplicates, "
          f"{len(df_clean)} records remain.")

    # Split (T-SPLIT-02)
    partitions = _stratified_split(
        df_clean, target,
        train_ratio, val_ratio, test_ratio, seed,
    )

    # Verify no overlap (T-SPLIT-04)
    _verify_no_overlap(partitions)

    # Class counts (T-SPLIT-05)
    class_counts = _partition_class_counts(df_clean, target, partitions)

    # Build manifest (T-SPLIT-07)
    manifest = _create_manifest(
        disease=disease,
        source_file=str(ds_cfg["file"]),
        source_checksum=checksum,
        partitions=partitions,
        partition_class_counts=class_counts,
        dropped_indices=dropped,
        seed=seed,
        train_ratio=train_ratio,
        val_ratio=val_ratio,
        test_ratio=test_ratio,
    )

    # Write manifest
    manifest_path.write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    print(f"\nSplit manifest written to: {manifest_path}")
    print(f"  Train: {len(partitions['train'])} records")
    print(f"  Val:   {len(partitions['val'])} records")
    print(f"  Test:  {len(partitions['test'])} records")
    print(f"  Seed:  {seed}")

    # Verify reproducibility (T-SPLIT-10)
    partitions2 = _stratified_split(
        df_clean, target,
        train_ratio, val_ratio, test_ratio, seed,
    )
    for name in partitions:
        if not np.array_equal(
            np.sort(partitions[name]), np.sort(partitions2[name])
        ):
            raise RuntimeError(
                f"Reproducibility check failed for partition '{name}'"
            )
    print("[OK] Reproducibility verified.")

    return manifest


def load_manifest(
    disease: str = "obesity",
    data_root: Path = Path("."),
    manifest_dir: Path | None = None,
) -> dict[str, Any]:
    """Load an existing split manifest."""
    if manifest_dir is None:
        manifest_dir = data_root / "data" / "manifests"
    path = manifest_dir / f"{disease}_split_manifest.json"
    if not path.exists():
        raise FileNotFoundError(f"No split manifest found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def get_partition_data(
    df: pd.DataFrame,
    manifest: dict[str, Any],
    partition: str,
) -> pd.DataFrame:
    """Return the DataFrame slice for a given partition."""
    total_assigned = sum(
        len(manifest["partitions"][p]["indices"])
        for p in manifest["partitions"]
    )
    if len(df) > total_assigned and "dropped_indices" in manifest:
        df = df.drop(index=manifest["dropped_indices"]).reset_index(drop=True)
    indices = manifest["partitions"][partition]["indices"]
    return df.iloc[indices].reset_index(drop=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run dataset splitting")
    parser.add_argument("--disease", default="obesity")
    parser.add_argument("--config-dir", default="config")
    parser.add_argument("--data-root", default=".")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    out = Path(args.output_dir) if args.output_dir else None
    run_split(
        disease=args.disease,
        config_dir=Path(args.config_dir),
        data_root=Path(args.data_root),
        output_dir=out,
        seed=args.seed,
        force=args.force,
    )
