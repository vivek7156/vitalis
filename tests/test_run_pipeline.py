"""Tests for the unified pipeline runner."""

from pipeline.run_pipeline import run_full_pipeline


def test_run_pipeline_audit_only(tmp_project):
    result = run_full_pipeline(
        disease="obesity",
        config_dir=tmp_project["config_dir"],
        data_root=tmp_project["data_root"],
        output_dir=tmp_project["processed_dir"],
        artifacts_dir=tmp_project["artifacts_dir"],
        manifest_dir=tmp_project["manifests_dir"],
        audit_only=True,
    )
    assert "audit" in result
    assert result["audit"]["dimensions"]["rows"] == 200


def test_run_pipeline_full(tmp_project):
    result = run_full_pipeline(
        disease="obesity",
        feature_sets=["e2_lifestyle_only", "e1_bmi_inclusive"],
        config_dir=tmp_project["config_dir"],
        data_root=tmp_project["data_root"],
        output_dir=tmp_project["processed_dir"],
        artifacts_dir=tmp_project["artifacts_dir"],
        manifest_dir=tmp_project["manifests_dir"],
        force=True,
    )
    assert result["disease"] == "obesity"
    assert "e2_lifestyle_only" in result["feature_sets_processed"]
    assert "e1_bmi_inclusive" in result["feature_sets_processed"]
    assert result["preprocessing_results"]["e2_lifestyle_only"]["round_trip_verified"] is True
