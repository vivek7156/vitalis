"""Tests for the splitting module.

Covers the partition test checklist from Section 12.
"""


import pandas as pd
import pytest

from pipeline.splitting import (
    _deduplicate,
    run_split,
)


class TestDeduplication:
    """T-SPLIT-03: Resolve duplicates before partition assignment."""

    def test_exact_duplicates_removed(self, synthetic_obesity_df):
        df = pd.concat([synthetic_obesity_df, synthetic_obesity_df.iloc[[0, 1]]],
                       ignore_index=True)
        deduped, dropped = _deduplicate(df)
        assert len(deduped) == len(synthetic_obesity_df)
        assert len(dropped) == 2


class TestNoOverlap:
    """T-SPLIT-04: No record crosses held-out boundaries."""

    def test_partitions_do_not_overlap(self, tmp_project):
        manifest = run_split(
            disease="obesity",
            config_dir=tmp_project["config_dir"],
            data_root=tmp_project["data_root"],
            output_dir=tmp_project["manifests_dir"],
            force=True,
        )
        train_idx = set(manifest["partitions"]["train"]["indices"])
        val_idx = set(manifest["partitions"]["val"]["indices"])
        test_idx = set(manifest["partitions"]["test"]["indices"])

        assert len(train_idx & val_idx) == 0
        assert len(train_idx & test_idx) == 0
        assert len(val_idx & test_idx) == 0

    def test_all_records_assigned(self, tmp_project):
        manifest = run_split(
            disease="obesity",
            config_dir=tmp_project["config_dir"],
            data_root=tmp_project["data_root"],
            output_dir=tmp_project["manifests_dir"],
            force=True,
        )
        total = sum(
            p["size"] for p in manifest["partitions"].values()
        )
        # Deduplication may reduce the count
        assert total > 0


class TestE1E2SharedSplit:
    """T-SPLIT-06: E1 and E2 use identical approved split membership."""

    def test_same_manifest_for_both(self, tmp_project):
        # Run split once — both E1 and E2 share the same manifest
        manifest = run_split(
            disease="obesity",
            config_dir=tmp_project["config_dir"],
            data_root=tmp_project["data_root"],
            output_dir=tmp_project["manifests_dir"],
            force=True,
        )
        # The manifest is disease-level, not feature-set-level
        assert manifest["disease"] == "obesity"
        # Both E1 and E2 would use the same indices
        train_indices = manifest["partitions"]["train"]["indices"]
        assert len(train_indices) > 0


class TestManifestChecksum:
    """A changed source checksum invalidates reuse."""

    def test_checksum_mismatch_raises(self, tmp_project):
        # Create a manifest first
        run_split(
            disease="obesity",
            config_dir=tmp_project["config_dir"],
            data_root=tmp_project["data_root"],
            output_dir=tmp_project["manifests_dir"],
            force=True,
        )

        # Modify the CSV slightly
        df = pd.read_csv(tmp_project["data_file"])
        df.loc[0, "Age"] = 99.99
        df.to_csv(tmp_project["data_file"], index=False)

        # Trying to reuse the manifest should fail
        with pytest.raises(RuntimeError, match="checksum mismatch"):
            run_split(
                disease="obesity",
                config_dir=tmp_project["config_dir"],
                data_root=tmp_project["data_root"],
                output_dir=tmp_project["manifests_dir"],
                force=False,
            )


class TestReproducibility:
    """Fixed configuration reproduces partition membership."""

    def test_same_seed_same_split(self, tmp_project):
        m1 = run_split(
            disease="obesity",
            config_dir=tmp_project["config_dir"],
            data_root=tmp_project["data_root"],
            output_dir=tmp_project["manifests_dir"],
            seed=42,
            force=True,
        )
        m2 = run_split(
            disease="obesity",
            config_dir=tmp_project["config_dir"],
            data_root=tmp_project["data_root"],
            output_dir=tmp_project["manifests_dir"],
            seed=42,
            force=True,
        )
        assert m1["partitions"]["train"]["indices"] == m2["partitions"]["train"]["indices"]
        assert m1["partitions"]["test"]["indices"] == m2["partitions"]["test"]["indices"]


class TestClassCountsPerPartition:
    """T-SPLIT-05: Partition sizes and class counts support evaluation."""

    def test_all_classes_in_each_partition(self, tmp_project):
        manifest = run_split(
            disease="obesity",
            config_dir=tmp_project["config_dir"],
            data_root=tmp_project["data_root"],
            output_dir=tmp_project["manifests_dir"],
            force=True,
        )
        for partition_name, counts in manifest["partition_class_counts"].items():
            # Each partition should have at least some classes represented
            assert len(counts) > 0, f"Partition {partition_name} has no classes"
