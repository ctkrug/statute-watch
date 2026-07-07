"""Load and validate the legislative source registry, and check provenance.

The dataset's credibility rests on every record tracing back to an official
legislative record. ``data/sources.yaml`` registers, per jurisdiction, the
authoritative site that record-of-truth comes from. This module parses that
registry and offers :func:`check_provenance`, which asserts every state present
in the dataset has a registered *official* source — a bad or missing source is a
dataset defect the :mod:`~statute_watch.cli` ``validate`` gate rejects.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .catalog import Catalog
from .models import US_STATES, ValidationError

# Closed set of source authorities. ``official`` is a legislature's own record;
# ``index`` is a curated cross-state tracker used only to discover bills.
SOURCE_KINDS: tuple[str, ...] = ("official", "index")

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCES_PATH = _REPO_ROOT / "data" / "sources.yaml"


@dataclass(frozen=True, slots=True)
class Source:
    """One registered legislative source.

    Attributes:
        id: Stable slug, unique across the registry.
        name: Human-readable source name.
        jurisdiction: Free-text jurisdiction label (a state name or "US (all states)").
        url: Public entry point (must be an http(s) URL).
        kind: One of :data:`SOURCE_KINDS`.
        state: Two-letter code an *official* source is the record-of; ``None`` for indexes.
        notes: What the source is used for.
    """

    id: str
    name: str
    jurisdiction: str
    url: str
    kind: str
    state: str | None = None
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValidationError("source: id must be a non-empty slug")
        if not self.name.strip():
            raise ValidationError(f"source {self.id}: name is empty")
        if self.kind not in SOURCE_KINDS:
            raise ValidationError(f"source {self.id}: unknown kind {self.kind!r}")
        if not self.url.startswith(("http://", "https://")):
            raise ValidationError(f"source {self.id}: url must be an http(s) URL")
        if self.kind == "official":
            if self.state is None:
                raise ValidationError(f"source {self.id}: official source needs a 'state'")
            if self.state not in US_STATES:
                raise ValidationError(f"source {self.id}: unknown state {self.state!r}")

    @classmethod
    def from_dict(cls, raw: dict) -> Source:
        if not isinstance(raw, dict):
            raise ValidationError(f"expected a source mapping, got {type(raw).__name__}")
        state = raw.get("state")
        return cls(
            id=str(raw.get("id", "")).strip(),
            name=str(raw.get("name", "")).strip(),
            jurisdiction=str(raw.get("jurisdiction", "")).strip(),
            url=str(raw.get("url", "")).strip(),
            kind=str(raw.get("kind", "")).strip().lower(),
            state=(str(state).strip().upper() if state else None),
            notes=str(raw.get("notes", "")).strip(),
        )


@dataclass(frozen=True, slots=True)
class SourceRegistry:
    """An immutable, validated collection of sources."""

    sources: tuple[Source, ...]

    def __len__(self) -> int:
        return len(self.sources)

    def __iter__(self):
        return iter(self.sources)

    def official(self) -> list[Source]:
        return [s for s in self.sources if s.kind == "official"]

    def official_states(self) -> set[str]:
        """State codes that have at least one registered official source."""
        return {s.state for s in self.sources if s.kind == "official" and s.state}


def load_sources(path: str | Path | None = None) -> SourceRegistry:
    """Load and validate the source registry.

    Raises:
        FileNotFoundError: if the registry file does not exist.
        ValidationError: on a malformed source or a duplicate id.
    """
    src_path = Path(path) if path is not None else DEFAULT_SOURCES_PATH
    if not src_path.exists():
        raise FileNotFoundError(f"sources registry not found: {src_path}")

    try:
        raw = yaml.safe_load(src_path.read_text(encoding="utf-8")) or []
    except (yaml.YAMLError, UnicodeDecodeError) as exc:
        raise ValidationError(f"sources registry could not be read as YAML: {exc}") from exc
    if not isinstance(raw, list):
        raise ValidationError("sources registry must be a YAML list")

    sources: list[Source] = []
    seen: set[str] = set()
    for index, record in enumerate(raw):
        source = Source.from_dict(record)
        if source.id in seen:
            raise ValidationError(f"duplicate source id {source.id!r} at record {index}")
        seen.add(source.id)
        sources.append(source)
    return SourceRegistry(sources=tuple(sources))


def check_provenance(catalog: Catalog, registry: SourceRegistry) -> None:
    """Assert every state in ``catalog`` has a registered official source.

    Raises:
        ValidationError: naming the uncovered states, if any.
    """
    covered = registry.official_states()
    missing = sorted({s.state for s in catalog} - covered)
    if missing:
        raise ValidationError(
            "no official source registered for state(s): " + ", ".join(missing)
        )
