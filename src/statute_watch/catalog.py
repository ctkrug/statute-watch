"""Load, validate, and query the curated statute dataset.

The dataset lives in ``data/statutes.yaml`` as a list of records. :func:`load_catalog`
parses it into :class:`~statute_watch.models.Statute` objects, enforcing dataset-level
invariants (unique ids) on top of the per-record validation in the model.
"""

from __future__ import annotations

import datetime as _dt
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import yaml

from .models import CATEGORIES, STAGES, Statute, ValidationError

# Sentinel used to sort records with no known dates to the bottom.
_MIN_DATE = _dt.date.min

# The dataset ships inside the repo, two directories up from this module
# (src/statute_watch/ -> repo root -> data/). Resolved lazily so the package is
# import-safe even when the data dir is absent (e.g. a wheel without package data).
_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_PATH = _REPO_ROOT / "data" / "statutes.yaml"


@dataclass(frozen=True, slots=True)
class Catalog:
    """An immutable, validated collection of statutes with query helpers."""

    statutes: tuple[Statute, ...]

    def __len__(self) -> int:
        return len(self.statutes)

    def __iter__(self):
        return iter(self.statutes)

    def states(self) -> list[str]:
        """Sorted list of distinct state codes present in the dataset."""
        return sorted({s.state for s in self.statutes})

    def by_state(self, state: str) -> list[Statute]:
        code = state.strip().upper()
        return [s for s in self.statutes if s.state == code]

    def by_category(self, category: str) -> list[Statute]:
        return [s for s in self.statutes if category in s.categories]

    def by_stage(self, stage: str) -> list[Statute]:
        return [s for s in self.statutes if s.stage == stage]

    def category_counts(self) -> dict[str, int]:
        """Count of statutes per category, in the canonical category order."""
        counter: Counter[str] = Counter()
        for statute in self.statutes:
            counter.update(statute.categories)
        return {c: counter.get(c, 0) for c in CATEGORIES}

    def stage_counts(self) -> dict[str, int]:
        """Count of statutes per lifecycle stage, in canonical stage order."""
        counter = Counter(s.stage for s in self.statutes)
        return {stage: counter.get(stage, 0) for stage in STAGES}


def load_catalog(path: str | Path | None = None) -> Catalog:
    """Load and validate the statute dataset.

    Args:
        path: Optional path to a YAML dataset; defaults to :data:`DEFAULT_DATA_PATH`.

    Raises:
        FileNotFoundError: if the dataset file does not exist.
        ValidationError: on malformed records or duplicate ids.
    """
    data_path = Path(path) if path is not None else DEFAULT_DATA_PATH
    if not data_path.exists():
        raise FileNotFoundError(f"dataset not found: {data_path}")

    raw = yaml.safe_load(data_path.read_text(encoding="utf-8")) or []
    if not isinstance(raw, list):
        raise ValidationError("dataset must be a YAML list of statute records")

    statutes: list[Statute] = []
    seen: set[str] = set()
    for index, record in enumerate(raw):
        statute = Statute.from_dict(record)
        if statute.id in seen:
            raise ValidationError(f"duplicate statute id {statute.id!r} at record {index}")
        seen.add(statute.id)
        statutes.append(statute)

    # Newest activity first, then by state for a stable secondary order.
    statutes.sort(key=lambda s: (s.last_action or s.introduced or _MIN_DATE, s.state), reverse=True)
    return Catalog(statutes=tuple(statutes))
