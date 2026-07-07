"""Tests for the source registry loader and provenance check."""

import textwrap

import pytest

from statute_watch.catalog import load_catalog
from statute_watch.models import ValidationError
from statute_watch.sources import (
    Source,
    check_provenance,
    load_sources,
)


def test_bundled_registry_loads_and_covers_dataset():
    catalog = load_catalog()
    registry = load_sources()
    # Every state in the dataset must have an official source (backlog 2.4).
    check_provenance(catalog, registry)
    assert registry.official_states() >= {s.state for s in catalog}


def test_official_source_requires_valid_state():
    with pytest.raises(ValidationError, match="official source needs a 'state'"):
        Source.from_dict({"id": "x", "name": "X", "url": "https://x.gov", "kind": "official"})


def test_unknown_kind_rejected():
    with pytest.raises(ValidationError, match="unknown kind"):
        Source.from_dict({"id": "x", "name": "X", "url": "https://x.gov", "kind": "blog"})


def test_non_http_source_url_rejected():
    with pytest.raises(ValidationError, match="http"):
        Source.from_dict(
            {"id": "x", "name": "X", "url": "ftp://x.gov", "kind": "official", "state": "CA"}
        )


def test_index_source_needs_no_state():
    src = Source.from_dict(
        {"id": "i", "name": "Index", "url": "https://i.org", "kind": "index"}
    )
    assert src.state is None


def test_provenance_fails_on_uncovered_state(tmp_path):
    # A dataset with a state that has no official source must be rejected.
    dataset = tmp_path / "statutes.yaml"
    dataset.write_text(
        textwrap.dedent(
            """
            - id: ak-1
              state: AK
              title: Alaska privacy bill
              bill_number: HB 1
              categories: [comprehensive]
              stage: introduced
              summary: A summary.
              source_url: https://akleg.gov/hb1
            """
        ),
        encoding="utf-8",
    )
    catalog = load_catalog(dataset)
    registry = load_sources()  # bundled registry has no AK official source
    with pytest.raises(ValidationError, match="AK"):
        check_provenance(catalog, registry)


def test_duplicate_source_id_rejected(tmp_path):
    registry = tmp_path / "sources.yaml"
    registry.write_text(
        textwrap.dedent(
            """
            - id: dup
              name: One
              url: https://a.gov
              kind: official
              state: CA
            - id: dup
              name: Two
              url: https://b.gov
              kind: official
              state: NY
            """
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValidationError, match="duplicate source id"):
        load_sources(registry)


def test_missing_registry_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_sources(tmp_path / "nope.yaml")
