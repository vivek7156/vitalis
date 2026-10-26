"""Tests for the audit module.

Covers the audit and partition test checklist from Section 12.
"""


import pandas as pd

from pipeline.audit import run_audit


class TestAuditExecution:
    """Test that the audit executes and produces valid reports."""

    def test_audit_runs_successfully(self, tmp_project):
        report = run_audit(
            disease="obesity",
            config_dir=tmp_project["config_dir"],
            data_root=tmp_project["data_root"],
            output_dir=tmp_project["processed_dir"],
        )
        assert report is not None
        assert "class_distribution" in report
        assert "field_details" in report
        assert "exact_duplicates" in report
        assert "leakage_analysis" in report

    def test_json_report_written(self, tmp_project):
        run_audit(
            disease="obesity",
            config_dir=tmp_project["config_dir"],
            data_root=tmp_project["data_root"],
            output_dir=tmp_project["processed_dir"],
        )
        json_path = tmp_project["processed_dir"] / "obesity_audit.json"
        assert json_path.exists()

    def test_markdown_report_written(self, tmp_project):
        run_audit(
            disease="obesity",
            config_dir=tmp_project["config_dir"],
            data_root=tmp_project["data_root"],
            output_dir=tmp_project["processed_dir"],
        )
        md_path = tmp_project["processed_dir"] / "obesity_audit_report.md"
        assert md_path.exists()
        content = md_path.read_text(encoding="utf-8")
        assert "# Dataset Audit Report" in content


class TestClassDistribution:
    """T-AUDIT-01: Class counts and proportions."""

    def test_all_classes_present(self, tmp_project):
        report = run_audit(
            disease="obesity",
            config_dir=tmp_project["config_dir"],
            data_root=tmp_project["data_root"],
            output_dir=tmp_project["processed_dir"],
        )
        counts = report["class_distribution"]["counts"]
        for cls in [
            "Insufficient_Weight", "Normal_Weight", "Overweight_Level_I",
            "Overweight_Level_II", "Obesity_Type_I", "Obesity_Type_II",
            "Obesity_Type_III",
        ]:
            assert cls in counts
            assert counts[cls] > 0

    def test_proportions_sum_to_one(self, tmp_project):
        report = run_audit(
            disease="obesity",
            config_dir=tmp_project["config_dir"],
            data_root=tmp_project["data_root"],
            output_dir=tmp_project["processed_dir"],
        )
        props = report["class_distribution"]["proportions"]
        assert abs(sum(props.values()) - 1.0) < 0.01


class TestDuplicateDetection:
    """T-AUDIT-03 / T-AUDIT-04: Duplicate detection."""

    def test_exact_duplicates_detected(self, tmp_project):
        # Add a duplicate row
        df = pd.read_csv(tmp_project["data_file"])
        df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
        df.to_csv(tmp_project["data_file"], index=False)

        # Update expected row count
        import yaml
        cfg_path = tmp_project["config_dir"] / "datasets.yaml"
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
        cfg["datasets"]["obesity"]["rows_expected"] = len(df)
        cfg_path.write_text(yaml.dump(cfg), encoding="utf-8")

        report = run_audit(
            disease="obesity",
            config_dir=tmp_project["config_dir"],
            data_root=tmp_project["data_root"],
            output_dir=tmp_project["processed_dir"],
        )
        assert report["exact_duplicates"]["duplicate_row_count"] >= 1


class TestLeakageAnalysis:
    """T-AUDIT-07 / T-AUDIT-08: Leakage detection."""

    def test_bmi_leakage_documented(self, tmp_project):
        report = run_audit(
            disease="obesity",
            config_dir=tmp_project["config_dir"],
            data_root=tmp_project["data_root"],
            output_dir=tmp_project["processed_dir"],
        )
        findings = report["leakage_analysis"]["findings"]
        bmi_findings = [f for f in findings if "BMI" in f["feature"]]
        assert len(bmi_findings) > 0
        assert bmi_findings[0]["severity"] == "blocking_for_e2"

    def test_e2_does_not_contain_height_weight(self, tmp_project):
        report = run_audit(
            disease="obesity",
            config_dir=tmp_project["config_dir"],
            data_root=tmp_project["data_root"],
            output_dir=tmp_project["processed_dir"],
        )
        # Should not have a blocking leak finding for E2
        blocking = [
            f for f in report["leakage_analysis"]["findings"]
            if f["severity"] == "blocking"
        ]
        assert len(blocking) == 0


class TestFindingsClassification:
    """T-AUDIT-14: Findings are classified."""

    def test_findings_have_classification(self, tmp_project):
        report = run_audit(
            disease="obesity",
            config_dir=tmp_project["config_dir"],
            data_root=tmp_project["data_root"],
            output_dir=tmp_project["processed_dir"],
        )
        for f in report["findings_summary"]:
            assert "classification" in f
            assert f["classification"] in (
                "blocking", "accepted_limitation", "follow_up"
            )

    def test_checksum_is_recorded(self, tmp_project):
        report = run_audit(
            disease="obesity",
            config_dir=tmp_project["config_dir"],
            data_root=tmp_project["data_root"],
            output_dir=tmp_project["processed_dir"],
        )
        assert "source_checksum_sha256" in report
        assert len(report["source_checksum_sha256"]) == 64
