"""Comprehensive dataset audit with leakage analysis.

Covers tasks T-AUDIT-01 through T-AUDIT-14 from the Module 1 checklist.
Generates both machine-readable JSON and human-readable Markdown reports.
"""

import datetime
import json
from pathlib import Path
from typing import Any

import pandas as pd

from pipeline.loader import (
    OBESITY_TARGET_CLASSES,
    compute_sha256,
    load_and_validate,
    load_dataset_config,
    load_feature_config,
)

# ---------------------------------------------------------------------------
# Audit helpers
# ---------------------------------------------------------------------------

def _class_distribution(df: pd.DataFrame, target: str) -> dict[str, Any]:
    """T-AUDIT-01: Class counts and proportions."""
    counts = df[target].value_counts().sort_index()
    total = len(df)
    return {
        "counts": counts.to_dict(),
        "proportions": {k: round(v / total, 4) for k, v in counts.items()},
        "total": total,
    }


def _missing_and_types(df: pd.DataFrame) -> dict[str, Any]:
    """T-AUDIT-02: Missing counts, types, numeric summaries."""
    info: dict[str, Any] = {}
    for col in df.columns:
        col_info: dict[str, Any] = {
            "dtype": str(df[col].dtype),
            "missing": int(df[col].isna().sum()),
            "unique": int(df[col].nunique()),
        }
        if pd.api.types.is_numeric_dtype(df[col]):
            col_info["min"] = float(df[col].min())
            col_info["max"] = float(df[col].max())
            col_info["mean"] = round(float(df[col].mean()), 6)
            col_info["std"] = round(float(df[col].std()), 6)
            col_info["median"] = float(df[col].median())
            # T-AUDIT-08: Flag fractional values in frequency fields
            if col in ("FCVC", "NCP", "CH2O", "FAF", "TUE"):
                frac_count = int((df[col] != df[col].round(0)).sum())
                col_info["fractional_values"] = frac_count
        else:
            col_info["categories"] = sorted(df[col].dropna().unique().tolist())
        info[col] = col_info
    return info


def _exact_duplicates(df: pd.DataFrame) -> dict[str, Any]:
    """T-AUDIT-03: Identify exact duplicate rows."""
    dup_mask = df.duplicated(keep=False)
    dup_count = int(df.duplicated(keep="first").sum())
    dup_groups = []
    if dup_count > 0:
        dup_df = df[dup_mask]
        # Group by all columns to find duplicate clusters
        for _, group in dup_df.groupby(list(df.columns)):
            if len(group) > 1:
                dup_groups.append({
                    "row_indices": group.index.tolist(),
                    "count": len(group),
                })
    return {
        "duplicate_row_count": dup_count,
        "duplicate_groups": dup_groups[:20],  # cap for report size
        "total_groups": len(dup_groups),
    }


def _conflicting_target_duplicates(
    df: pd.DataFrame,
    target: str,
    feature_cols: list[str],
) -> dict[str, Any]:
    """T-AUDIT-04: Duplicate feature rows with conflicting targets."""
    available_features = [c for c in feature_cols if c in df.columns]
    if not available_features:
        return {"conflicting_count": 0, "details": []}

    grouped = df.groupby(available_features, sort=False)
    conflicts = []
    for _name, group in grouped:
        if group[target].nunique() > 1:
            conflicts.append({
                "row_indices": group.index.tolist(),
                "targets": group[target].unique().tolist(),
                "count": len(group),
            })
    return {
        "conflicting_count": len(conflicts),
        "details": conflicts[:20],
    }


def _near_duplicates(
    df: pd.DataFrame,
    numeric_cols: list[str],
    threshold: float = 0.01,
) -> dict[str, Any]:
    """T-AUDIT-05: Near-duplicate detection using normalised numeric distance.

    Similarity rule: Two rows are near-duplicates when all categorical columns
    match exactly and the maximum absolute normalised difference across numeric
    columns is below *threshold*.
    """
    available_numeric = [c for c in numeric_cols if c in df.columns]
    cat_cols = [c for c in df.select_dtypes(include=["object", "str"]).columns]

    near_dup_count = 0
    sample_pairs: list[dict] = []

    if not available_numeric or len(df) > 5000:
        # Skip expensive pairwise comparison for very large datasets
        return {
            "method": f"max_normalised_diff < {threshold}, all categoricals match",
            "near_duplicate_pairs_found": 0,
            "note": "Skipped: dataset too large for pairwise comparison" if len(df) > 5000 else "No numeric columns",
        }

    # Normalise numeric columns
    num_df = df[available_numeric].copy()
    ranges = num_df.max() - num_df.min()
    ranges = ranges.replace(0, 1)  # avoid division by zero
    num_normed = (num_df - num_df.min()) / ranges

    # Group by categoricals to limit comparisons
    if cat_cols:
        groups = df.groupby(cat_cols, sort=False).groups
    else:
        groups = {"all": df.index}

    for indices in groups.values():
        if hasattr(indices, "tolist"):
            idx_list = indices.tolist()
        else:
            idx_list = list(indices)
        if len(idx_list) < 2:
            continue
        sub = num_normed.loc[idx_list]
        for i in range(len(idx_list)):
            for j in range(i + 1, len(idx_list)):
                diff = (sub.iloc[i] - sub.iloc[j]).abs().max()
                if diff < threshold:
                    near_dup_count += 1
                    if len(sample_pairs) < 10:
                        sample_pairs.append({
                            "row_a": idx_list[i],
                            "row_b": idx_list[j],
                            "max_diff": round(float(diff), 6),
                        })

    return {
        "method": f"max_normalised_diff < {threshold}, all categoricals match",
        "near_duplicate_pairs_found": near_dup_count,
        "sample_pairs": sample_pairs,
    }


def _leakage_analysis(
    df: pd.DataFrame,
    target: str,
    e1_features: list[str],
    e2_features: list[str],
) -> dict[str, Any]:
    """T-AUDIT-07 / T-AUDIT-08: Target leakage and proxy analysis."""
    findings: list[dict[str, Any]] = []

    # BMI-derived target dependence (T-AUDIT-07)
    if "Height" in df.columns and "Weight" in df.columns:
        bmi = df["Weight"] / (df["Height"] ** 2)
        bmi_target_corr = float(bmi.corr(
            df[target].map({c: i for i, c in enumerate(OBESITY_TARGET_CLASSES)})
        ))
        findings.append({
            "feature": "BMI (Height, Weight)",
            "severity": "blocking_for_e2",
            "description": (
                "BMI is computed from Height and Weight. The obesity target is "
                "defined using BMI thresholds. E1 uses this with documented "
                "dependence; E2 must exclude Height, Weight, and BMI."
            ),
            "bmi_target_rank_correlation": round(bmi_target_corr, 4),
        })

    # Check each feature for high correlation with ordinal target
    target_encoded = df[target].map(
        {c: i for i, c in enumerate(OBESITY_TARGET_CLASSES)}
    )
    for col in e2_features:
        if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
            corr = float(df[col].corr(target_encoded))
            if abs(corr) > 0.5:
                findings.append({
                    "feature": col,
                    "severity": "investigate",
                    "description": (
                        f"High correlation ({corr:.4f}) with ordinal target. "
                        "Investigate if this is a proxy for the target."
                    ),
                    "correlation": round(corr, 4),
                })

    # Verify E2 exclusion list
    excluded_from_e2 = {"Height", "Weight"}
    e2_set = set(e2_features)
    leaked = excluded_from_e2 & e2_set
    if leaked:
        findings.append({
            "feature": str(leaked),
            "severity": "blocking",
            "description": "E2 feature set contains excluded columns.",
        })

    return {"findings": findings}


def _demographic_coverage(df: pd.DataFrame) -> dict[str, Any]:
    """T-AUDIT-09: Demographic/geographic coverage."""
    coverage: dict[str, Any] = {}
    if "Age" in df.columns:
        coverage["age_range"] = {
            "min": float(df["Age"].min()),
            "max": float(df["Age"].max()),
            "mean": round(float(df["Age"].mean()), 1),
        }
        under_18 = int((df["Age"] < 18).sum())
        coverage["under_18_count"] = under_18
    if "Gender" in df.columns:
        coverage["gender_distribution"] = df["Gender"].value_counts().to_dict()
    coverage["note"] = (
        "Dataset originates from Colombia, Mexico, and Peru. "
        "May not generalise to other populations."
    )
    return coverage


# ---------------------------------------------------------------------------
# Main audit
# ---------------------------------------------------------------------------

def run_audit(
    disease: str = "obesity",
    config_dir: Path = Path("config"),
    data_root: Path = Path("."),
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Execute the full dataset audit and return the structured report.

    Parameters
    ----------
    disease : str
        Disease identifier.
    config_dir : Path
        Config directory.
    data_root : Path
        Root for resolving dataset file paths.
    output_dir : Path or None
        Where to write JSON and Markdown reports. Defaults to
        data/processed/.

    Returns
    -------
    dict
        The structured audit report.
    """
    if output_dir is None:
        output_dir = data_root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load
    ds_cfg = load_dataset_config(config_dir, disease)
    feat_cfg = load_feature_config(config_dir, disease)
    df, validation_report = load_and_validate(disease, config_dir, data_root)

    target = feat_cfg["target"]
    e1_features = feat_cfg.get("e1_bmi_inclusive", [])
    e2_features = feat_cfg.get("e2_lifestyle_only", [])
    all_features = list(set(e1_features) | set(e2_features))
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

    # Checksum (T-DATA-03)
    file_path = data_root / ds_cfg["file"]
    checksum = compute_sha256(file_path)

    # Build audit report
    report: dict[str, Any] = {
        "audit_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "disease": disease,
        "source_file": str(ds_cfg["file"]),
        "source_checksum_sha256": checksum,
        "source_metadata": {
            "name": ds_cfg.get("name"),
            "source": ds_cfg.get("source"),
            "doi": ds_cfg.get("doi"),
            "license": ds_cfg.get("license"),
            "acquired_on": ds_cfg.get("acquired_on"),
        },
        "dimensions": {
            "rows": len(df),
            "columns": len(df.columns),
            "rows_expected": ds_cfg.get("rows_expected"),
            "columns_expected": ds_cfg.get("columns_expected"),
        },
        "validation": validation_report.to_dict(),
        "class_distribution": _class_distribution(df, target),
        "field_details": _missing_and_types(df),
        "exact_duplicates": _exact_duplicates(df),
        "conflicting_label_duplicates": _conflicting_target_duplicates(
            df, target, all_features,
        ),
        "near_duplicates": _near_duplicates(df, numeric_cols),
        "leakage_analysis": _leakage_analysis(
            df, target, e1_features, e2_features,
        ),
        "demographic_coverage": _demographic_coverage(df),
        "synthetic_data_note": {
            "reported_share": ds_cfg.get("synthetic_share_reported"),
            "note": (
                "Approximately 77% of rows are reported as synthetically "
                "generated (SMOTE). Row-level provenance is unavailable. "
                "A later split cannot undo the historical generation process."
            ),
        },
    }

    # Classify findings (T-AUDIT-14)
    findings_summary = _classify_findings(report)
    report["findings_summary"] = findings_summary

    # Write JSON report (T-AUDIT-13)
    json_path = output_dir / f"{disease}_audit.json"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")

    # Write Markdown report (T-AUDIT-13)
    md_path = output_dir / f"{disease}_audit_report.md"
    md_content = _generate_markdown_report(report)
    md_path.write_text(md_content, encoding="utf-8")

    # Also copy to docs/dataset-audits/ (T-AUDIT-13)
    audit_docs_dir = data_root / "docs" / "dataset-audits"
    audit_docs_dir.mkdir(parents=True, exist_ok=True)
    (audit_docs_dir / f"{disease}_audit_report.md").write_text(
        md_content, encoding="utf-8"
    )

    print("Audit complete. Reports written to:")
    print(f"  JSON: {json_path}")
    print(f"  Markdown: {md_path}")
    print(f"  Docs: {audit_docs_dir / f'{disease}_audit_report.md'}")

    return report


def _classify_findings(report: dict) -> list[dict[str, str]]:
    """T-AUDIT-14: Classify findings as blocking / accepted / follow-up."""
    findings: list[dict[str, str]] = []

    # Validation errors
    for err in report["validation"].get("errors", []):
        findings.append({
            "id": f"VAL-{err.get('field', 'unknown')}",
            "classification": "blocking",
            "description": err.get("issue", ""),
        })

    # Duplicates
    dup_count = report["exact_duplicates"]["duplicate_row_count"]
    if dup_count > 0:
        findings.append({
            "id": "DUP-exact",
            "classification": "accepted_limitation",
            "description": (
                f"{dup_count} exact duplicate rows found. "
                "Deduplication policy: keep first occurrence for splitting, "
                "document effect on sample counts."
            ),
        })

    # Conflicting labels
    conf_count = report["conflicting_label_duplicates"]["conflicting_count"]
    if conf_count > 0:
        findings.append({
            "id": "DUP-conflict",
            "classification": "follow_up",
            "description": (
                f"{conf_count} feature-duplicate groups with conflicting targets. "
                "Investigate and document resolution."
            ),
        })

    # Leakage
    for lf in report["leakage_analysis"]["findings"]:
        findings.append({
            "id": f"LEAK-{lf['feature']}",
            "classification": (
                "blocking" if lf["severity"] == "blocking" else "accepted_limitation"
            ),
            "description": lf["description"],
        })

    # Synthetic data
    findings.append({
        "id": "SYNTH-provenance",
        "classification": "accepted_limitation",
        "description": report["synthetic_data_note"]["note"],
    })

    # Under-18
    under18 = report["demographic_coverage"].get("under_18_count", 0)
    if under18 > 0:
        findings.append({
            "id": "DEMO-under18",
            "classification": "follow_up",
            "description": (
                f"{under18} records with Age < 18. "
                "Confirm supported population and handling policy."
            ),
        })

    # Fractional frequency fields
    for col in ("FCVC", "NCP", "CH2O", "FAF", "TUE"):
        details = report["field_details"].get(col, {})
        frac = details.get("fractional_values", 0)
        if frac > 0:
            findings.append({
                "id": f"FRAC-{col}",
                "classification": "accepted_limitation",
                "description": (
                    f"{col}: {frac} rows have fractional values. "
                    "These are synthetic continuous values, not integer categories. "
                    "Do not silently coerce to integers."
                ),
            })

    return findings


def _generate_markdown_report(report: dict) -> str:
    """Generate a human-readable Markdown audit report."""
    lines: list[str] = []
    a = lines.append

    a(f"# Dataset Audit Report: {report['disease'].title()}")
    a("")
    a(f"**Generated:** {report['audit_timestamp']}")
    a("")

    # Source
    a("## 1. Source and Provenance")
    a("")
    meta = report["source_metadata"]
    a(f"- **Name:** {meta.get('name')}")
    a(f"- **Source:** {meta.get('source')}")
    a(f"- **DOI:** {meta.get('doi')}")
    a(f"- **License:** {meta.get('license')}")
    a(f"- **Acquired on:** {meta.get('acquired_on')}")
    a(f"- **File:** `{report['source_file']}`")
    a(f"- **SHA-256:** `{report['source_checksum_sha256']}`")
    a("")

    # Dimensions
    a("## 2. Dimensions")
    a("")
    dim = report["dimensions"]
    a(f"- **Rows:** {dim['rows']} (expected: {dim.get('rows_expected', 'N/A')})")
    a(f"- **Columns:** {dim['columns']} (expected: {dim.get('columns_expected', 'N/A')})")
    a("")

    # Class distribution
    a("## 3. Target Distribution")
    a("")
    a("| Class | Count | Proportion |")
    a("|---|---|---|")
    cd = report["class_distribution"]
    for cls in OBESITY_TARGET_CLASSES:
        cnt = cd["counts"].get(cls, 0)
        prop = cd["proportions"].get(cls, 0)
        a(f"| {cls} | {cnt} | {prop:.4f} |")
    a(f"| **Total** | **{cd['total']}** | **1.0000** |")
    a("")

    # Field details
    a("## 4. Field Details")
    a("")
    a("| Field | Type | Missing | Unique | Min | Max | Mean | Fractional |")
    a("|---|---|---|---|---|---|---|---|")
    for col, info in report["field_details"].items():
        dtype = info["dtype"]
        missing = info["missing"]
        unique = info["unique"]
        mn = info.get("min", "—")
        mx = info.get("max", "—")
        mean = info.get("mean", "—")
        frac = info.get("fractional_values", "—")
        a(f"| {col} | {dtype} | {missing} | {unique} | {mn} | {mx} | {mean} | {frac} |")
    a("")

    # Duplicates
    a("## 5. Duplicate Analysis")
    a("")
    ed = report["exact_duplicates"]
    a(f"- **Exact duplicate rows:** {ed['duplicate_row_count']}")
    a(f"- **Duplicate groups:** {ed['total_groups']}")
    a("")
    cl = report["conflicting_label_duplicates"]
    a(f"- **Feature-duplicate groups with conflicting targets:** {cl['conflicting_count']}")
    a("")
    nd = report["near_duplicates"]
    a(f"- **Near-duplicate method:** {nd.get('method', 'N/A')}")
    a(f"- **Near-duplicate pairs:** {nd.get('near_duplicate_pairs_found', 0)}")
    a("")

    # Leakage
    a("## 6. Leakage Analysis")
    a("")
    for finding in report["leakage_analysis"]["findings"]:
        a(f"### {finding['feature']}")
        a(f"- **Severity:** {finding['severity']}")
        a(f"- {finding['description']}")
        if "bmi_target_rank_correlation" in finding:
            a(f"- **BMI-Target rank correlation:** {finding['bmi_target_rank_correlation']}")
        if "correlation" in finding:
            a(f"- **Correlation:** {finding['correlation']}")
        a("")

    # Demographics
    a("## 7. Demographic Coverage")
    a("")
    demo = report["demographic_coverage"]
    if "age_range" in demo:
        ar = demo["age_range"]
        a(f"- **Age range:** {ar['min']} – {ar['max']} (mean: {ar['mean']})")
        a(f"- **Under 18:** {demo.get('under_18_count', 0)}")
    if "gender_distribution" in demo:
        a(f"- **Gender:** {demo['gender_distribution']}")
    a(f"- **Note:** {demo.get('note', '')}")
    a("")

    # Synthetic data
    a("## 8. Synthetic Data")
    a("")
    syn = report["synthetic_data_note"]
    a(f"- **Reported share:** {syn.get('reported_share', 'N/A')}")
    a(f"- {syn['note']}")
    a("")

    # Findings summary
    a("## 9. Findings Summary")
    a("")
    a("| ID | Classification | Description |")
    a("|---|---|---|")
    for f in report.get("findings_summary", []):
        a(f"| {f['id']} | {f['classification']} | {f['description'][:100]} |")
    a("")

    # Validation
    a("## 10. Validation Report")
    a("")
    v = report["validation"]
    a(f"- **Accepted:** {v['accepted']}")
    a(f"- **Rejected:** {v['rejected']}")
    a(f"- **Errors:** {v['error_count']}")
    a(f"- **Warnings:** {v['warning_count']}")
    a("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run dataset audit")
    parser.add_argument("--disease", default="obesity", help="Disease identifier")
    parser.add_argument("--config-dir", default="config", help="Config directory")
    parser.add_argument("--data-root", default=".", help="Data root directory")
    parser.add_argument("--output-dir", default=None, help="Output directory")
    args = parser.parse_args()

    out = Path(args.output_dir) if args.output_dir else None
    result = run_audit(
        disease=args.disease,
        config_dir=Path(args.config_dir),
        data_root=Path(args.data_root),
        output_dir=out,
    )

    # Print summary
    blocking = [
        f for f in result.get("findings_summary", [])
        if f["classification"] == "blocking"
    ]
    if blocking:
        print(f"\n[WARNING] {len(blocking)} BLOCKING finding(s):")
        for b in blocking:
            print(f"  - [{b['id']}] {b['description']}")
    else:
        print("\n[OK] No blocking findings.")
