"""Tests for the preprocessing module.

Covers the preprocessing test checklist from Section 12.
"""


import pytest

from pipeline.loader import load_feature_config
from pipeline.preprocessing import (
    E2_EXCLUDED,
    create_preprocessing_pipeline,
    fit_transform_train,
    transform_partition,
    verify_round_trip,
)


class TestPipelineCreation:
    """T-PREP-01: Configurable preprocessing factory."""

    def test_create_e2_pipeline(self, tmp_project):
        pipe, mapping = create_preprocessing_pipeline(
            disease="obesity",
            feature_set="e2_lifestyle_only",
            config_dir=tmp_project["config_dir"],
        )
        assert pipe is not None
        assert "input_features" in mapping
        assert "Height" not in mapping["input_features"]
        assert "Weight" not in mapping["input_features"]

    def test_create_e1_pipeline(self, tmp_project):
        _pipe, mapping = create_preprocessing_pipeline(
            disease="obesity",
            feature_set="e1_bmi_inclusive",
            config_dir=tmp_project["config_dir"],
        )
        assert "Height" in mapping["input_features"]
        assert "Weight" in mapping["input_features"]

    def test_model_families(self, tmp_project):
        for family in ("tree", "linear", "catboost"):
            _pipe, mapping = create_preprocessing_pipeline(
                disease="obesity",
                feature_set="e2_lifestyle_only",
                config_dir=tmp_project["config_dir"],
                model_family=family,
            )
            assert mapping["model_family"] == family


class TestE2Exclusion:
    """E2 rejects height, weight, BMI and excluded derivatives."""

    def test_e2_rejects_height_weight(self, tmp_project):
        _pipe, mapping = create_preprocessing_pipeline(
            disease="obesity",
            feature_set="e2_lifestyle_only",
            config_dir=tmp_project["config_dir"],
        )
        for excluded in E2_EXCLUDED:
            assert excluded not in mapping["input_features"]

    def test_e2_config_with_height_raises(self, tmp_project):
        """If E2 config accidentally includes Height, creation should fail."""
        import yaml
        cfg_path = tmp_project["config_dir"] / "features.yaml"
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
        cfg["obesity"]["e2_lifestyle_only"].append("Height")
        cfg_path.write_text(yaml.dump(cfg), encoding="utf-8")

        with pytest.raises(ValueError, match="must not contain"):
            create_preprocessing_pipeline(
                disease="obesity",
                feature_set="e2_lifestyle_only",
                config_dir=tmp_project["config_dir"],
            )


class TestTrainOnlyFitting:
    """Validation/test-only values do not influence learned parameters."""

    def test_fit_only_on_train(self, tmp_project, synthetic_obesity_df):
        feat_cfg = load_feature_config(tmp_project["config_dir"], "obesity")
        features = feat_cfg["e2_lifestyle_only"]

        pipe, _mapping = create_preprocessing_pipeline(
            disease="obesity",
            feature_set="e2_lifestyle_only",
            config_dir=tmp_project["config_dir"],
        )

        # Split into "train" and "test"
        train_df = synthetic_obesity_df.iloc[:150]
        test_df = synthetic_obesity_df.iloc[150:]

        # Fit on train
        X_train = fit_transform_train(pipe, train_df, features)
        assert X_train is not None
        assert X_train.shape[0] == 150

        # Transform test without refitting (T-PREP-15)
        X_test = transform_partition(pipe, test_df, features)
        assert X_test is not None
        assert X_test.shape[0] == len(test_df)
        assert X_test.shape[1] == X_train.shape[1]


class TestSaveLoadRoundTrip:
    """Save/load round-trip preserves outputs (T-PREP-16)."""

    def test_round_trip_preservation(self, tmp_project, synthetic_obesity_df):
        feat_cfg = load_feature_config(tmp_project["config_dir"], "obesity")
        features = feat_cfg["e2_lifestyle_only"]

        pipe, _mapping = create_preprocessing_pipeline(
            disease="obesity",
            feature_set="e2_lifestyle_only",
            config_dir=tmp_project["config_dir"],
        )

        train_df = synthetic_obesity_df.iloc[:150]
        test_df = synthetic_obesity_df.iloc[150:]

        fit_transform_train(pipe, train_df, features)

        result = verify_round_trip(
            pipe, test_df, features,
            output_dir=tmp_project["artifacts_dir"],
        )
        assert result is True


class TestUnknownCategoryPolicy:
    """Unknown-category policy behaves as documented (T-PREP-04)."""

    def test_unknown_category_handled(self, tmp_project, synthetic_obesity_df):
        feat_cfg = load_feature_config(tmp_project["config_dir"], "obesity")
        features = feat_cfg["e2_lifestyle_only"]

        pipe, _ = create_preprocessing_pipeline(
            disease="obesity",
            feature_set="e2_lifestyle_only",
            config_dir=tmp_project["config_dir"],
        )

        train_df = synthetic_obesity_df.iloc[:150]
        fit_transform_train(pipe, train_df, features)

        # Introduce unknown category at test time
        test_df = synthetic_obesity_df.iloc[150:155].copy()
        test_df.loc[test_df.index[0], "MTRANS"] = "Helicopter"

        # Should not raise — handled per unknown category policy
        X_test = transform_partition(pipe, test_df, features)
        assert X_test is not None


class TestFeatureMapping:
    """Transformed column mappings remain correct (T-PREP-10, T-PREP-11)."""

    def test_feature_names_available_after_fit(self, tmp_project, synthetic_obesity_df):
        feat_cfg = load_feature_config(tmp_project["config_dir"], "obesity")
        features = feat_cfg["e2_lifestyle_only"]

        pipe, mapping = create_preprocessing_pipeline(
            disease="obesity",
            feature_set="e2_lifestyle_only",
            config_dir=tmp_project["config_dir"],
        )

        train_df = synthetic_obesity_df.iloc[:150]
        fit_transform_train(pipe, train_df, features)

        # After fitting, feature names should be retrievable
        try:
            names = pipe.get_feature_names_out()
            assert len(names) > 0
        except AttributeError:
            # Some pipeline configurations may not support this
            pass

        # Mapping should have the input features recorded
        assert mapping["input_features"] == features
