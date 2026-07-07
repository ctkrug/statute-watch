"""The refresh pipeline: stage candidate bills, then diff them against the dataset.

Hand-editing YAML forever does not scale, but auto-merging scraped records would
betray the editorial promise. So the pipeline splits the job in two:

* :func:`fetch` reads a source's raw bill *feed* and writes normalized candidate
  records to a **staging** file — it never touches the curated dataset. The
  network is **guarded**: by default it reads a local feed file (so CI is offline
  and deterministic); live fetching happens only behind an explicit opt-in.
* :func:`diff` classifies each staged candidate against the current dataset as
  ``new``, a ``stage-advance``, or ``unchanged`` so a human can review before
  :func:`apply_merge` folds the approved changes back in — and the merged dataset
  still passes :func:`~statute_watch.catalog.load_catalog` validation.

The feed format is a YAML list of raw bill dicts using the same field names as a
dataset record; each entry must be complete enough to form a valid
:class:`~statute_watch.models.Statute`, so staged data is clean and diff-able.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .catalog import Catalog
from .models import Statute
from .sources import Source, SourceRegistry, load_sources

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STAGING_DIR = _REPO_ROOT / "data" / "staging"


class PipelineError(RuntimeError):
    """Raised when a fetch/diff/merge step cannot proceed."""


# --- Fetch: raw feed -> staging ---------------------------------------------


def _find_source(registry: SourceRegistry, source_id: str) -> Source:
    for source in registry:
        if source.id == source_id:
            return source
    known = ", ".join(sorted(s.id for s in registry))
    raise PipelineError(f"unknown source {source_id!r}; registered: {known}")


def _read_feed(feed_path: Path) -> list[dict]:
    if not feed_path.exists():
        raise PipelineError(f"feed file not found: {feed_path}")
    raw = yaml.safe_load(feed_path.read_text(encoding="utf-8")) or []
    if not isinstance(raw, list):
        raise PipelineError("feed must be a YAML list of raw bill records")
    return raw


def staging_path(source_id: str, staging_dir: str | Path | None = None) -> Path:
    """Where a source's staged candidates are written."""
    base = Path(staging_dir) if staging_dir is not None else DEFAULT_STAGING_DIR
    return base / f"{source_id}.yaml"


def fetch(
    source_id: str,
    *,
    registry: SourceRegistry | None = None,
    feed: str | Path | None = None,
    staging_dir: str | Path | None = None,
    allow_network: bool = False,
) -> Path:
    """Stage candidate bills from a source into ``data/staging/<source>.yaml``.

    Args:
        source_id: A source id registered in the source registry.
        registry: The source registry; loaded from the bundle if omitted.
        feed: A local feed file to read instead of the network (the CI path).
        staging_dir: Destination directory; defaults to :data:`DEFAULT_STAGING_DIR`.
        allow_network: Opt in to live fetching from the source URL. Off by default
            so tests and CI never touch the network.

    Returns:
        The path of the written staging file.

    Raises:
        PipelineError: on an unknown source, a bad feed, or a network fetch that
            was not explicitly enabled.
    """
    registry = registry if registry is not None else load_sources()
    source = _find_source(registry, source_id)

    if feed is not None:
        raw = _read_feed(Path(feed))
    elif allow_network:  # pragma: no cover - never exercised in CI
        raw = _fetch_remote(source)
    else:
        raise PipelineError(
            "network is disabled: pass feed=<local feed file>, or allow_network=True "
            "to fetch live"
        )

    candidates = [_normalize(entry, source) for entry in raw]
    out = staging_path(source_id, staging_dir)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        yaml.safe_dump(candidates, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return out


def _normalize(entry: object, source: Source) -> dict:
    """Validate a raw feed entry and return a clean candidate record dict."""
    if not isinstance(entry, dict):
        raise PipelineError(f"feed entry must be a mapping, got {type(entry).__name__}")
    # Building a Statute validates the entry; we store its canonical dict form so
    # staged data is already well-formed and directly comparable to the dataset.
    statute = Statute.from_dict(entry)
    record = statute.to_dict()
    record["fetched_from"] = source.id
    return record


def _fetch_remote(source: Source) -> list[dict]:  # pragma: no cover - live network
    """Placeholder for live fetching. Intentionally unreachable in tests/CI."""
    raise PipelineError(
        f"live fetching from {source.url} is not implemented for v1; "
        "provide a local feed file with feed=…"
    )


# --- Diff: staging vs dataset -----------------------------------------------


def load_staging(path: str | Path) -> list[Statute]:
    """Load a staging file into validated :class:`Statute` records."""
    staging = Path(path)
    if not staging.exists():
        raise PipelineError(f"staging file not found: {staging}")
    raw = yaml.safe_load(staging.read_text(encoding="utf-8")) or []
    if not isinstance(raw, list):
        raise PipelineError("staging file must be a YAML list")
    return [Statute.from_dict(entry) for entry in raw]


@dataclass(frozen=True, slots=True)
class DiffEntry:
    """One staged candidate classified against the current dataset."""

    kind: str  # "new" | "stage-advance" | "unchanged"
    id: str
    detail: str


@dataclass(frozen=True, slots=True)
class DiffReport:
    """The result of diffing a staging set against the dataset."""

    entries: tuple[DiffEntry, ...]

    @property
    def new(self) -> list[DiffEntry]:
        return [e for e in self.entries if e.kind == "new"]

    @property
    def advanced(self) -> list[DiffEntry]:
        return [e for e in self.entries if e.kind == "stage-advance"]

    @property
    def unchanged(self) -> list[DiffEntry]:
        return [e for e in self.entries if e.kind == "unchanged"]

    def has_changes(self) -> bool:
        return bool(self.new or self.advanced)


def diff(catalog: Catalog, staged: list[Statute]) -> DiffReport:
    """Classify each staged candidate against ``catalog``.

    A candidate whose id is absent is ``new``; one whose id exists but whose
    lifecycle stage moved is a ``stage-advance``; an identical id+stage is
    ``unchanged``.
    """
    by_id = {s.id: s for s in catalog}
    entries: list[DiffEntry] = []
    for candidate in staged:
        current = by_id.get(candidate.id)
        if current is None:
            entries.append(
                DiffEntry("new", candidate.id, f"{candidate.state} {candidate.bill_number}")
            )
        elif current.stage != candidate.stage:
            entries.append(
                DiffEntry(
                    "stage-advance",
                    candidate.id,
                    f"{current.stage} -> {candidate.stage}",
                )
            )
        else:
            entries.append(DiffEntry("unchanged", candidate.id, candidate.stage))
    return DiffReport(entries=tuple(entries))


# --- Merge: apply approved changes ------------------------------------------


def apply_merge(catalog: Catalog, staged: list[Statute]) -> list[dict]:
    """Return dataset records with staged ``new`` and ``stage-advance`` folded in.

    Existing records are updated in place (by id); new ones are appended. The
    result is a plain list of record dicts ready to write back and re-validate —
    which it still passes, since every staged record is itself a valid Statute.
    """
    merged: dict[str, Statute] = {s.id: s for s in catalog}
    for candidate in staged:
        merged[candidate.id] = candidate
    return [s.to_dict() for s in merged.values()]
