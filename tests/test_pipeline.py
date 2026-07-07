"""Tests for the refresh pipeline: fetch (offline), diff, and merge."""

from pathlib import Path

import pytest

from statute_watch.catalog import load_catalog
from statute_watch.pipeline import (
    PipelineError,
    apply_merge,
    diff,
    fetch,
    load_staging,
    staging_path,
)

FEED = Path(__file__).resolve().parent / "fixtures" / "feed_ncsl_sample.yaml"


def test_fetch_stages_without_touching_dataset(tmp_path, catalog):
    before = len(catalog)
    out = fetch("congress-ncsl", feed=FEED, staging_dir=tmp_path)
    assert out == staging_path("congress-ncsl", tmp_path)
    assert out.exists()
    # The curated dataset is untouched (backlog 3.1 AC1).
    assert len(load_catalog()) == before
    staged = load_staging(out)
    assert len(staged) == 3
    # Provenance marker is stamped on staged records.
    assert out.read_text(encoding="utf-8").count("fetched_from: congress-ncsl") == 3


def test_fetch_requires_feed_or_network(tmp_path):
    # Network is guarded: no feed and no opt-in must refuse (backlog 3.1 AC2).
    with pytest.raises(PipelineError, match="network is disabled"):
        fetch("congress-ncsl", staging_dir=tmp_path)


def test_fetch_unknown_source_rejected(tmp_path):
    with pytest.raises(PipelineError, match="unknown source"):
        fetch("no-such-source", feed=FEED, staging_dir=tmp_path)


def test_fetch_rejects_malformed_feed(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("just a string, not a list\n", encoding="utf-8")
    with pytest.raises(PipelineError, match="must be a YAML list"):
        fetch("congress-ncsl", feed=bad, staging_dir=tmp_path)


def test_diff_classifies_new_advanced_and_unchanged(tmp_path, catalog):
    out = fetch("congress-ncsl", feed=FEED, staging_dir=tmp_path)
    report = diff(catalog, load_staging(out))
    assert {e.id for e in report.new} == {"ny-s-365-2025"}
    assert {e.id for e in report.advanced} == {"ny-s-1042-2025"}
    assert {e.id for e in report.unchanged} == {"ma-hd-3263-2025"}
    assert report.has_changes()
    # The advance records the stage transition for review.
    assert report.advanced[0].detail == "passed -> enacted"


def test_diff_empty_staging_has_no_changes(catalog):
    report = diff(catalog, [])
    assert report.entries == ()
    assert not report.has_changes()


def test_merge_folds_changes_and_still_validates(tmp_path, catalog):
    out = fetch("congress-ncsl", feed=FEED, staging_dir=tmp_path)
    staged = load_staging(out)
    merged = apply_merge(catalog, staged)

    # The new bill was appended; the advanced bill was updated in place.
    assert len(merged) == len(catalog) + 1
    by_id = {r["id"]: r for r in merged}
    assert by_id["ny-s-1042-2025"]["stage"] == "enacted"

    # Writing the merged dataset back still passes validation (backlog 3.2 AC2).
    import yaml

    dataset = tmp_path / "merged.yaml"
    dataset.write_text(yaml.safe_dump(merged, sort_keys=False), encoding="utf-8")
    reloaded = load_catalog(dataset)
    assert len(reloaded) == len(catalog) + 1


def test_load_staging_missing_file_raises(tmp_path):
    with pytest.raises(PipelineError, match="staging file not found"):
        load_staging(tmp_path / "nope.yaml")


def test_fetch_missing_feed_file_raises(tmp_path):
    with pytest.raises(PipelineError, match="feed file not found"):
        fetch("congress-ncsl", feed=tmp_path / "absent.yaml", staging_dir=tmp_path)


def test_fetch_rejects_non_mapping_feed_entry(tmp_path):
    bad = tmp_path / "feed.yaml"
    bad.write_text("- just a bare string\n", encoding="utf-8")
    with pytest.raises(PipelineError, match="feed entry must be a mapping"):
        fetch("congress-ncsl", feed=bad, staging_dir=tmp_path)


def test_load_staging_non_list_rejected(tmp_path):
    staging = tmp_path / "staging.yaml"
    staging.write_text("id: not-a-list\n", encoding="utf-8")
    with pytest.raises(PipelineError, match="must be a YAML list"):
        load_staging(staging)


def test_load_staging_malformed_yaml_raises(tmp_path):
    staging = tmp_path / "staging.yaml"
    staging.write_text("- id: [unterminated\n", encoding="utf-8")
    with pytest.raises(PipelineError, match="could not be read as YAML"):
        load_staging(staging)


def test_fetch_malformed_yaml_feed_raises(tmp_path):
    bad = tmp_path / "feed.yaml"
    bad.write_text("- id: [unterminated\n", encoding="utf-8")
    with pytest.raises(PipelineError, match="could not be read as YAML"):
        fetch("congress-ncsl", feed=bad, staging_dir=tmp_path)
