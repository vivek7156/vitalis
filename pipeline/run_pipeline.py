"""Unified Module 1 Data and Preprocessing Pipeline Runner.

Fulfills Section 13 (Run Interface & Required Outputs) of the Module 1 checklist.
Orchestrates:
1. Dataset loading and schema validation (T-LOAD-01 through T-LOAD-11)
2. Dataset audit and leakage analysis (T-AUDIT-01 through T-AUDIT-14)
3. Leakage-safe, deduplicated partitioning (T-SPLIT-01 through T-SPLIT-11)
4. Configurable preprocessing factory, training-only fit, serialization, and round-trip verification (T-PREP-01 through T-PREP-17)
5. Export of partitioned dataset slices and Module 2 handoff summary (T-HANDOFF-01 through T-HANDOFF-05)
"""

import argparse
import datetime
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from pipeline.audit import run_audit
from pipeline.loader import (
    compute_sha256,
    load_and_validate,
    load_dataset_config,
    load_feature_config,
)
from pipeline.preprocessing import (
    create_preprocessing_pipeline,
    fit_transform_train,
    save_preprocessing,
    transform_partition,
    verify_round_trip,
)
from pipeline.splitting import (
    DEFAULT_SEED,
    get_partition_data,
    load_manifest,
    run_split,
)


def run_full_pipeline(
    disease: str = "obesity",
    feature_sets: list[str] | None = None,
    config_dir: Path = Path("config"),
    data_root: Path = Path("."),
    output_dir: Path = Path("data/processed"),
    artifacts_dir: Path = Path("artifacts"),
    manifest_dir: Path = Path("data/manifests"),
    seed: int = DEFAULT_SEED,
    audit_only: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    """Execute the end-to-end Module 1 pipeline."""
    print("=" * 70)
    print(f"Vitalis Module 1 Data Pipeline: {disease.upper()}")
    print("=" * 70)

    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)

    # 1. Config & Validation Check
    print("\n[Step 1/5] Loading configuration and validating raw dataset...")
    ds_cfg = load_dataset_config(config_dir, disease)
    feat_cfg = load_feature_config(config_dir, disease)

    if ds_cfg.get("status") == "pending_approval":
        raise ValueError(f"Dataset for '{disease}' is marked pending approval and cannot proceed.")

    df_raw, validation = load_and_validate(disease, config_dir, data_root)
    if not validation.is_valid:
        print(f"[FAIL] Dataset validation failed with {validation.error_count} error(s):")
        for err in validation.errors:
            print(f"  - {err}")
        sys.exit(1)
    print(f"[OK] Validated {len(df_raw)} raw records ({validation.accepted} accepted, 0 rejected).")

    # 2. Comprehensive Audit
    print("\n[Step 2/5] Running dataset audit and leakage checks...")
    audit_report = run_audit(
        disease=disease,
        config_dir=config_dir,
        data_root=data_root,
        output_dir=output_dir,
    )
    blocking_findings = [
        f for f in audit_report.get("findings_summary", [])
        if f.get("classification") == "blocking"
    ]
    if blocking_findings:
        print(f"[FAIL] Audit discovered {len(blocking_findings)} blocking findings:")
        for b in blocking_findings:
            print(f"  - [{b['id']}] {b['description']}")
        sys.exit(1)
    print("[OK] Audit completed successfully with 0 blocking findings.")

    if audit_only:
        print("\nAudit-only mode requested. Halting before partitioning.")
        return {"audit": audit_report}

    # 3. Partitioning and Frozen Split Manifest
    print("\n[Step 3/5] Generating/verifying leakage-safe frozen split manifest...")
    manifest_path = manifest_dir / f"{disease}_split_manifest.json"
    if manifest_path.exists() and not force:
        print(f"Loading existing split manifest: {manifest_path}")
        manifest = load_manifest(disease, data_root, manifest_dir)
        # Check integrity
        source_file = data_root / ds_cfg["file"]
        current_checksum = compute_sha256(source_file)
        manifest_checksum = manifest.get("source_checksum_sha256") or manifest.get("source_checksum")
        if current_checksum != manifest_checksum:
            raise RuntimeError(
                f"Source checksum mismatch ({current_checksum} vs {manifest_checksum})! Use --force to regenerate."
            )
        print("[OK] Reusing verified compatible split manifest.")
    else:
        manifest = run_split(
            disease=disease,
            config_dir=config_dir,
            data_root=data_root,
            output_dir=manifest_dir,
            seed=seed,
            force=force,
        )

    # Export partitioned slices
    print("\n[Step 4/5] Slicing and exporting partition datasets...")
    partitions_data: dict[str, pd.DataFrame] = {}
    for part in ["train", "val", "test"]:
        part_df = get_partition_data(df_raw, manifest, part)
        partitions_data[part] = part_df
        part_file = output_dir / f"{disease}_{part}.csv"
        part_df.to_csv(part_file, index=False)
        print(f"  - {part.capitalize()} partition: {len(part_df)} rows -> {part_file}")

    # 4. Preprocessing Factories and Transformers
    print("\n[Step 5/5] Building and fitting preprocessing transformers...")
    if feature_sets is None:
        feature_sets = ["e2_lifestyle_only", "e1_bmi_inclusive"]

    prep_results: dict[str, Any] = {}
    for fset in feature_sets:
        if fset not in feat_cfg:
            continue
        print(f"\n--- Processing feature set: {fset} ---")
        feature_list = feat_cfg[fset]

        # Build unfitted pipeline
        pipeline, feature_mapping = create_preprocessing_pipeline(
            disease=disease,
            feature_set=fset,
            config_dir=config_dir,
            model_family="tree",
        )

        # Fit ONLY on training data
        train_df = partitions_data["train"]
        val_df = partitions_data["val"]
        test_df = partitions_data["test"]

        X_train_trans = fit_transform_train(pipeline, train_df, feature_list)
        X_val_trans = transform_partition(pipeline, val_df, feature_list)
        X_test_trans = transform_partition(pipeline, test_df, feature_list)

        # Extract transformed column names
        try:
            preprocessor = pipeline.named_steps["preprocessor"]
            out_names = list(preprocessor.get_feature_names_out())
            feature_mapping["transformed_features"] = out_names
            feature_mapping["transformed_feature_count"] = len(out_names)
        except (AttributeError, ValueError):
            feature_mapping["transformed_features"] = []
            feature_mapping["transformed_feature_count"] = X_train_trans.shape[1]

        # Save pipeline and mapping
        save_preprocessing(
            pipeline=pipeline,
            feature_mapping=feature_mapping,
            output_dir=artifacts_dir,
            disease=disease,
            feature_set=fset,
        )

        # Verify serialisation round-trip
        rt_pass = verify_round_trip(
            pipeline=pipeline,
            df_test=test_df,
            feature_list=feature_list,
            output_dir=artifacts_dir,
            disease=disease,
            feature_set=fset,
            feature_mapping=feature_mapping,
        )
        if not rt_pass:
            raise RuntimeError(f"Serialization round-trip verification failed for {fset}!")

        prep_results[fset] = {
            "input_feature_count": len(feature_list),
            "transformed_shape_train": X_train_trans.shape,
            "transformed_shape_val": X_val_trans.shape,
            "transformed_shape_test": X_test_trans.shape,
            "round_trip_verified": rt_pass,
        }

    # Summary
    summary = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "disease": disease,
        "raw_records": len(df_raw),
        "deduplicated_records": sum(len(partitions_data[p]) for p in partitions_data),
        "partitions": {p: len(partitions_data[p]) for p in partitions_data},
        "feature_sets_processed": list(prep_results.keys()),
        "preprocessing_results": prep_results,
        "manifest_path": str(manifest_path),
        "artifacts_dir": str(artifacts_dir),
    }

    summary_file = output_dir / f"{disease}_pipeline_summary.json"
    summary_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("\n" + "=" * 70)
    print("MODULE 1 PIPELINE COMPLETED SUCCESSFULLY")
    print(f"Summary written to: {summary_file}")
    print("=" * 70)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vitalis Module 1 Data Pipeline Runner")
    parser.add_argument("--disease", default="obesity", help="Target disease")
    parser.add_argument("--config-dir", default="config", help="Config directory")
    parser.add_argument("--data-root", default=".", help="Data root path")
    parser.add_argument("--output-dir", default="data/processed", help="Output directory")
    parser.add_argument("--artifacts-dir", default="artifacts", help="Artifacts directory")
    parser.add_argument("--manifest-dir", default="data/manifests", help="Manifest directory")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Partition random seed")
    parser.add_argument("--audit-only", action="store_true", help="Run audit only")
    parser.add_argument("--force", action="store_true", help="Force regenerate split manifest")
    args = parser.parse_args()

    run_full_pipeline(
        disease=args.disease,
        config_dir=Path(args.config_dir),
        data_root=Path(args.data_root),
        output_dir=Path(args.output_dir),
        artifacts_dir=Path(args.artifacts_dir),
        manifest_dir=Path(args.manifest_dir),
        seed=args.seed,
        audit_only=args.audit_only,
        force=args.force,
    )
