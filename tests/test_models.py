"""Tests for the Statute model's validation and (de)serialization."""

import datetime as dt

import pytest

from statute_watch.models import Statute, ValidationError


def _record(**overrides):
    base = {
        "id": "tx-hb-4-2023",
        "state": "tx",
        "title": "Texas Data Privacy and Security Act",
        "bill_number": "HB 4",
        "categories": ["comprehensive"],
        "stage": "effective",
        "summary": "Gives Texans data rights.",
        "source_url": "https://example.gov/hb4",
        "effective": "2024-07-01",
    }
    base.update(overrides)
    return base


def test_from_dict_normalizes_and_parses():
    s = Statute.from_dict(_record())
    assert s.state == "TX"  # upper-cased
    assert s.effective == dt.date(2024, 7, 1)  # ISO parsed to date
    assert s.categories == ("comprehensive",)


def test_unknown_state_rejected():
    with pytest.raises(ValidationError, match="unknown state"):
        Statute.from_dict(_record(state="ZZ"))


def test_unknown_category_rejected():
    with pytest.raises(ValidationError, match="unknown category"):
        Statute.from_dict(_record(categories=["telepathy"]))


def test_unknown_stage_rejected():
    with pytest.raises(ValidationError, match="unknown stage"):
        Statute.from_dict(_record(stage="vetoed"))


def test_non_http_source_rejected():
    with pytest.raises(ValidationError, match="source_url"):
        Statute.from_dict(_record(source_url="ftp://example.gov/hb4"))


def test_empty_categories_rejected():
    with pytest.raises(ValidationError, match="at least one category"):
        Statute.from_dict(_record(categories=[]))


def test_bad_date_rejected():
    with pytest.raises(ValidationError, match="not an ISO date"):
        Statute.from_dict(_record(effective="July 2024"))


@pytest.mark.parametrize("bad", [None, 5, True, {"a": 1}])
def test_non_list_categories_rejected_cleanly(bad):
    # A malformed 'categories' (null, a number, a bool, a mapping) must fail as a
    # ValidationError the CLI can report — never an uncaught TypeError traceback.
    with pytest.raises(ValidationError, match="categories must be a list"):
        Statute.from_dict(_record(categories=bad))


def test_scalar_string_categories_rejected():
    # A bare string must not be silently char-split into single-letter categories.
    with pytest.raises(ValidationError, match="categories must be a list"):
        Statute.from_dict(_record(categories="biometric"))


@pytest.mark.parametrize("bad", [5, True, "foo"])
def test_non_list_tags_rejected_cleanly(bad):
    # 'tags' has the same coercion hazard as 'categories': a scalar must be a
    # clean ValidationError, not a TypeError or a char-split list.
    with pytest.raises(ValidationError, match="tags must be a list"):
        Statute.from_dict(_record(tags=bad))


def test_empty_id_rejected():
    with pytest.raises(ValidationError, match="non-empty slug"):
        Statute.from_dict(_record(id="   "))


def test_empty_title_rejected():
    with pytest.raises(ValidationError, match="title is empty"):
        Statute.from_dict(_record(title=""))


def test_empty_summary_rejected():
    with pytest.raises(ValidationError, match="summary is empty"):
        Statute.from_dict(_record(summary="   "))


def test_missing_categories_key_rejected():
    record = _record()
    del record["categories"]
    with pytest.raises(ValidationError, match="missing 'categories'"):
        Statute.from_dict(record)


def test_from_dict_rejects_non_mapping():
    with pytest.raises(ValidationError, match="expected a mapping"):
        Statute.from_dict(["not", "a", "mapping"])


def test_non_string_date_rejected():
    # A numeric 'effective' is neither a date nor an ISO string.
    with pytest.raises(ValidationError, match="expected an ISO date string"):
        Statute.from_dict(_record(effective=2024))


def test_roundtrip_to_dict():
    s = Statute.from_dict(_record())
    d = s.to_dict()
    assert d["state"] == "TX"
    assert d["effective"] == "2024-07-01"
    # Rebuilding from the serialized form yields an equal statute.
    assert Statute.from_dict(d) == s
