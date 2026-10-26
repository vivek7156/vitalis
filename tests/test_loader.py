"""Tests for the dataset loader and validation module.

Covers the loader and schema test checklist from Section 12.
"""


import numpy as np
import pandas as pd
import pytest
import yaml

from pipeline.loader import (
    compute_sha256,
    load_and_validate,
    load_dataset_config,
    load_feature_config,
)


class TestConfigLoading:
    """Test configuration loading and error handling."""

    def test_load_dataset_config(self, tmp_project):
        cfg = load_dataset_config(tmp_project["config_dir"], "obesity")
        assert cfg["target"] == "NObeyesdad"
        assert cfg["rows_expected"] == 200

    def test_unknown_disease_raises(self, tmp_project):
        with pytest.raises(ValueError, match="Unknown disease"):
            load_dataset_config(tmp_project["config_dir"], "nonexistent")

    def test_load_feature_config(self, tmp_project):
        cfg = load_feature_config(tmp_project["config_dir"], "obesity")
        assert "e1_bmi_inclusive" in cfg
        assert "e2_lifestyle_only" in cfg
        assert "Height" in cfg["e1_bmi_inclusive"]
        assert "Height" not in cfg["e2_lifestyle_only"]


class TestValidSyntheticLoad:
    """Valid synthetic fixture loads successfully."""

    def test_loads_successfully(self, tmp_project):
        df, report = load_and_validate(
            "obesity",
            tmp_project["config_dir"],
            tmp_project["data_root"],
        )
        assert len(df) == 200
        assert report.is_valid
        assert report.accepted > 0

    def test_correct_columns(self, tmp_project):
        df, _report = load_and_validate(
            "obesity",
            tmp_project["config_dir"],
            tmp_project["data_root"],
        )
        assert "NObeyesdad" in df.columns
        assert "Gender" in df.columns
        assert len(df.columns) == 17


class TestMissingFileErrors:
    """Missing file, unsupported format and missing column produce clear errors."""

    def test_missing_file_raises(self, tmp_project):
        # Change the config to point to a nonexistent file
        cfg_path = tmp_project["config_dir"] / "datasets.yaml"
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
        cfg["datasets"]["obesity"]["file"] = "data/raw/nonexistent.csv"
        cfg_path.write_text(yaml.dump(cfg), encoding="utf-8")

        with pytest.raises(FileNotFoundError):
            load_and_validate(
                "obesity",
                tmp_project["config_dir"],
                tmp_project["data_root"],
            )

    def test_unsupported_format_raises(self, tmp_project):
        # Create a .xlsx file reference
        cfg_path = tmp_project["config_dir"] / "datasets.yaml"
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
        cfg["datasets"]["obesity"]["file"] = "data/raw/test.xlsx"
        cfg_path.write_text(yaml.dump(cfg), encoding="utf-8")

        # Create the file so it exists but has wrong format
        xlsx_path = tmp_project["data_root"] / "data" / "raw" / "test.xlsx"
        xlsx_path.write_bytes(b"fake data")

        with pytest.raises(ValueError, match="Unsupported file format"):
            load_and_validate(
                "obesity",
                tmp_project["config_dir"],
                tmp_project["data_root"],
            )

    def test_missing_column_detected(self, tmp_project):
        # Drop a column from the CSV
        df = pd.read_csv(tmp_project["data_file"])
        df = df.drop(columns=["Gender"])
        df.to_csv(tmp_project["data_file"], index=False)

        # Update expected columns count
        cfg_path = tmp_project["config_dir"] / "datasets.yaml"
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
        cfg["datasets"]["obesity"]["columns_expected"] = 16
        cfg_path.write_text(yaml.dump(cfg), encoding="utf-8")

        _, report = load_and_validate(
            "obesity",
            tmp_project["config_dir"],
            tmp_project["data_root"],
        )
        # Gender should be flagged as missing
        missing_col_errors = [
            e for e in report.errors if "Missing expected" in e.get("issue", "")
        ]
        assert len(missing_col_errors) > 0


class TestCategoryValidation:
    """Unknown categories, invalid numbers and unsupported units are detected."""

    def test_unknown_category_detected(self, tmp_project):
        df = pd.read_csv(tmp_project["data_file"])
        df.loc[0, "Gender"] = "Unknown_Gender"
        df.to_csv(tmp_project["data_file"], index=False)

        _, report = load_and_validate(
            "obesity",
            tmp_project["config_dir"],
            tmp_project["data_root"],
        )
        cat_errors = [
            e for e in report.errors if e.get("field") == "Gender"
        ]
        assert len(cat_errors) > 0

    def test_invalid_target_detected(self, tmp_project):
        df = pd.read_csv(tmp_project["data_file"])
        df.loc[0, "NObeyesdad"] = "Fake_Class"
        df.to_csv(tmp_project["data_file"], index=False)

        _, report = load_and_validate(
            "obesity",
            tmp_project["config_dir"],
            tmp_project["data_root"],
        )
        target_errors = [
            e for e in report.errors if e.get("field") == "NObeyesdad"
        ]
        assert len(target_errors) > 0


class TestMissingValues:
    """Missing values and legitimate zeros remain distinguishable."""

    def test_missing_values_reported(self, tmp_project):
        df = pd.read_csv(tmp_project["data_file"])
        df.loc[0, "Age"] = np.nan
        df.to_csv(tmp_project["data_file"], index=False)

        _, report = load_and_validate(
            "obesity",
            tmp_project["config_dir"],
            tmp_project["data_root"],
        )
        missing_warnings = [
            w for w in report.warnings if "missing" in w.get("field", "").lower()
        ]
        assert len(missing_warnings) > 0

    def test_zero_is_not_missing(self, tmp_project):
        df = pd.read_csv(tmp_project["data_file"])
        # FAF can legitimately be 0
        df.loc[0, "FAF"] = 0.0
        df.to_csv(tmp_project["data_file"], index=False)

        loaded_df, _ = load_and_validate(
            "obesity",
            tmp_project["config_dir"],
            tmp_project["data_root"],
        )
        assert loaded_df.loc[0, "FAF"] == 0.0
        assert not pd.isna(loaded_df.loc[0, "FAF"])


class TestChecksum:
    """Test file checksum computation."""

    def test_checksum_is_deterministic(self, tmp_project):
        cs1 = compute_sha256(tmp_project["data_file"])
        cs2 = compute_sha256(tmp_project["data_file"])
        assert cs1 == cs2
        assert len(cs1) == 64  # SHA-256 hex length
