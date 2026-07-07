"""Tests for the dataset loader and its query helpers."""

import textwrap

import pytest

from statute_watch.catalog import load_catalog
from statute_watch.models import ValidationError


def test_bundled_dataset_loads(catalog):
    assert len(catalog) >= 12
    # Every state code is two upper-case letters.
    assert all(len(s.state) == 2 and s.state.isupper() for s in catalog)


def test_v1_coverage_target_holds(catalog):
    # Backlog 2.1: >= 20 statutes across >= 15 states, with at least three each
    # in the four core categories, and every lifecycle stage represented.
    assert len(catalog) >= 20
    assert len(catalog.states()) >= 15

    counts = catalog.category_counts()
    for core in ("biometric", "geolocation", "data-broker", "comprehensive"):
        assert counts[core] >= 3, f"{core} has only {counts[core]}"

    stages = {s.stage for s in catalog}
    assert stages == {"introduced", "passed", "enacted", "effective"}


def test_sorted_newest_activity_first(catalog):
    def key(s):
        return s.last_action or s.introduced

    dates = [key(s) for s in catalog if key(s)]
    assert dates == sorted(dates, reverse=True)


def test_query_helpers(catalog):
    assert all("biometric" in s.categories for s in catalog.by_category("biometric"))
    assert all(s.state == "CA" for s in catalog.by_state("ca"))
    assert all(s.stage == "effective" for s in catalog.by_stage("effective"))


def test_category_counts_sum_matches(catalog):
    counts = catalog.category_counts()
    total_tags = sum(len(s.categories) for s in catalog)
    assert sum(counts.values()) == total_tags


def test_duplicate_ids_rejected(tmp_path):
    dataset = tmp_path / "dupe.yaml"
    dataset.write_text(
        textwrap.dedent(
            """
            - id: dup
              state: CA
              title: A
              bill_number: SB 1
              categories: [biometric]
              stage: introduced
              summary: first
              source_url: https://example.gov/a
            - id: dup
              state: NY
              title: B
              bill_number: SB 2
              categories: [biometric]
              stage: introduced
              summary: second
              source_url: https://example.gov/b
            """
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValidationError, match="duplicate statute id"):
        load_catalog(dataset)


def test_missing_dataset_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_catalog(tmp_path / "nope.yaml")


def test_stage_counts_cover_every_stage_in_canonical_order(catalog):
    counts = catalog.stage_counts()
    # Every lifecycle stage is present as a key, in canonical order, and the
    # counts sum to the whole dataset (each statute has exactly one stage).
    assert list(counts) == ["introduced", "passed", "enacted", "effective"]
    assert sum(counts.values()) == len(catalog)


def test_non_list_dataset_rejected(tmp_path):
    dataset = tmp_path / "mapping.yaml"
    dataset.write_text("id: not-a-list\nstate: CA\n", encoding="utf-8")
    with pytest.raises(ValidationError, match="must be a YAML list"):
        load_catalog(dataset)


def test_empty_dataset_loads_as_empty_catalog(tmp_path):
    dataset = tmp_path / "empty.yaml"
    dataset.write_text("", encoding="utf-8")
    catalog = load_catalog(dataset)
    assert len(catalog) == 0
    assert catalog.states() == []
