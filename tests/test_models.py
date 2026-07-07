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


def test_roundtrip_to_dict():
    s = Statute.from_dict(_record())
    d = s.to_dict()
    assert d["state"] == "TX"
    assert d["effective"] == "2024-07-01"
    # Rebuilding from the serialized form yields an equal statute.
    assert Statute.from_dict(d) == s
