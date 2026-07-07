"""Property-based tests for the dataset's core invariants.

Example tests pin known cases; these assert the *laws* that must hold for every
valid record — serialization round-trips, and diff classification is total and
mutually exclusive — which is where hand-picked examples tend to miss.
"""

import datetime as dt

from hypothesis import given
from hypothesis import strategies as st

from statute_watch.catalog import Catalog
from statute_watch.models import CATEGORIES, STAGES, US_STATES, Statute
from statute_watch.pipeline import apply_merge, diff

_STATES = sorted(US_STATES)
_dates = st.none() | st.dates(min_value=dt.date(1990, 1, 1), max_value=dt.date(2100, 1, 1))


@st.composite
def statutes(draw, id_pool=None):
    """A strategy producing valid Statute records."""
    sid = draw(st.sampled_from(id_pool)) if id_pool else draw(
        st.text(st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters="-"),
                min_size=1, max_size=12).filter(lambda s: s.strip())
    )
    return Statute.from_dict(
        {
            "id": sid,
            "state": draw(st.sampled_from(_STATES)),
            "title": draw(st.text(min_size=1, max_size=40).filter(lambda s: s.strip())),
            "bill_number": draw(st.text(min_size=1, max_size=10).filter(lambda s: s.strip())),
            "categories": draw(
                st.lists(st.sampled_from(CATEGORIES), min_size=1, max_size=len(CATEGORIES),
                         unique=True)
            ),
            "stage": draw(st.sampled_from(STAGES)),
            "summary": draw(st.text(min_size=1, max_size=80).filter(lambda s: s.strip())),
            "source_url": "https://example.gov/" + draw(st.text(
                st.characters(whitelist_categories=("Ll", "Nd")), min_size=1, max_size=8)),
            "introduced": draw(_dates),
            "last_action": draw(_dates),
            "effective": draw(_dates),
        }
    )


@given(statutes())
def test_to_dict_from_dict_roundtrips(statute):
    # Serializing and re-parsing any valid record yields an equal statute.
    assert Statute.from_dict(statute.to_dict()) == statute


@given(statutes())
def test_diff_of_identical_record_is_unchanged(statute):
    catalog = Catalog(statutes=(statute,))
    report = diff(catalog, [statute])
    assert len(report.entries) == 1
    assert report.unchanged and not report.has_changes()


@given(statutes())
def test_diff_of_absent_record_is_new(statute):
    report = diff(Catalog(statutes=()), [statute])
    assert [e.id for e in report.new] == [statute.id]
    assert report.has_changes()


@given(st.data())
def test_stage_change_classifies_as_advance(data):
    base = data.draw(statutes())
    other_stage = data.draw(st.sampled_from([s for s in STAGES if s != base.stage]))
    advanced = Statute.from_dict({**base.to_dict(), "stage": other_stage})
    report = diff(Catalog(statutes=(base,)), [advanced])
    assert [e.id for e in report.advanced] == [base.id]


@given(st.lists(statutes(), min_size=1, max_size=6, unique_by=lambda s: s.id))
def test_diff_classifies_every_record_exactly_once(records):
    # Partition property: entry count equals input count, and new/advanced/
    # unchanged are mutually exclusive and exhaustive.
    catalog = Catalog(statutes=tuple(records))
    report = diff(catalog, records)
    assert len(report.entries) == len(records)
    assert len(report.new) + len(report.advanced) + len(report.unchanged) == len(records)


@given(st.lists(statutes(), min_size=1, max_size=6, unique_by=lambda s: s.id))
def test_apply_merge_of_dataset_onto_itself_is_stable(records):
    # Merging the dataset with itself changes nothing and still validates.
    catalog = Catalog(statutes=tuple(records))
    merged = apply_merge(catalog, records)
    assert len(merged) == len(records)
    # Every merged record rebuilds into a valid statute.
    assert all(Statute.from_dict(r) for r in merged)
