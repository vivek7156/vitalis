import json
from pathlib import Path

import pandas as pd

DATA_PATH = Path("data/raw/ObesityDataSet_raw_and_data_sinthetic.csv")
REPORT_PATH = Path("data/processed/obesity_audit.json")

EXPECTED_COLUMNS = [
    "Gender", "Age", "Height", "Weight",
    "family_history_with_overweight", "FAVC", "FCVC", "NCP",
    "CAEC", "SMOKE", "CH2O", "SCC", "FAF", "TUE",
    "CALC", "MTRANS", "NObeyesdad",
]


def main() -> None:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)

    missing_columns = [
        column for column in EXPECTED_COLUMNS
        if column not in df.columns
    ]
    unexpected_columns = [
        column for column in df.columns
        if column not in EXPECTED_COLUMNS
    ]

    numeric_columns = [
        "Age", "Height", "Weight", "FCVC",
        "NCP", "CH2O", "FAF", "TUE",
    ]

    report = {
        "file": str(DATA_PATH),
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": df.columns.tolist(),
        "missing_expected_columns": missing_columns,
        "unexpected_columns": unexpected_columns,
        "missing_values_total": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "target_distribution": df["NObeyesdad"].value_counts().sort_index().to_dict(),
        "categorical_values": {
            column: sorted(df[column].dropna().unique().tolist())
            for column in df.select_dtypes(include="object").columns
        },
        "numeric_summary": {
            column: {
                "min": float(df[column].min()),
                "max": float(df[column].max()),
                "mean": float(df[column].mean()),
            }
            for column in numeric_columns
        },
        "reported_synthetic_share": 0.77,
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()