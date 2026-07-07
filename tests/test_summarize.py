"""Tests for the editorial display helpers (labels + status line)."""

import datetime as dt

from statute_watch.models import Statute
from statute_watch.summarize import (
    category_labels,
    stage_label,
    status_line,
)


def _statute(**overrides):
    base = {
        "id": "x-1",
        "state": "CA",
        "title": "A bill",
        "bill_number": "SB 1",
        "categories": ["biometric", "data-broker"],
        "stage": "passed",
        "summary": "Does a thing.",
        "source_url": "https://example.gov/1",
    }
    base.update(overrides)
    return Statute.from_dict(base)


def test_category_labels_map_to_display_copy():
    labels = category_labels(_statute())
    assert labels == ["Biometric", "Data broker"]


def test_stage_label_known_and_fallback():
    assert stage_label(_statute(stage="effective")) == "In effect"
    # An out-of-vocabulary stage can never be constructed, but the helper should
    # still title-case defensively rather than KeyError.
    forged = _statute()
    object.__setattr__(forged, "stage", "vetoed")
    assert stage_label(forged) == "Vetoed"


def test_status_line_effective_future_counts_down():
    s = _statute(stage="effective", effective="2999-01-01")
    assert status_line(s, today=dt.date(2024, 1, 1)) == "Takes effect Jan 2999"


def test_status_line_effective_past_reads_since():
    s = _statute(stage="effective", effective="2020-07-01")
    assert status_line(s, today=dt.date(2024, 1, 1)) == "In effect since Jul 2020"


def test_status_line_uses_last_action_marker():
    s = _statute(stage="passed", last_action="2023-05-02")
    assert status_line(s, today=dt.date(2024, 1, 1)) == "Passed the legislature · May 2023"


def test_status_line_falls_back_to_verb_without_dates():
    # A record with no last_action/introduced marker still yields a clean line.
    s = _statute(stage="introduced")
    assert status_line(s, today=dt.date(2024, 1, 1)) == "Introduced"
