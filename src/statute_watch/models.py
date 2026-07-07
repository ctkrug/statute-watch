"""Core data model for a tracked privacy statute.

A :class:`Statute` is the atomic unit of the dataset: one bill, in one state,
touching one or more privacy data types, at a known point in its lifecycle. The
model is deliberately strict — every field is validated on construction so that a
malformed dataset fails loudly in the pipeline rather than silently producing a
wrong site.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field

# --- Controlled vocabularies -------------------------------------------------
# Kept small and explicit. The categories are the data types a privacy law
# governs; the stages are the lifecycle a bill moves through. Both are closed
# sets so filtering in the UI is exhaustive and typos in the dataset are caught.

CATEGORIES: tuple[str, ...] = (
    "geolocation",
    "biometric",
    "data-broker",
    "comprehensive",
    "health-data",
    "childrens",
)

STAGES: tuple[str, ...] = (
    "introduced",
    "passed",
    "enacted",
    "effective",
)

# Two-letter USPS codes for the 50 states plus DC.
US_STATES: frozenset[str] = frozenset(
    "AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS "
    "MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV "
    "WI WY DC".split()
)


class ValidationError(ValueError):
    """Raised when a statute record fails validation."""


def _parse_date(value: object, field_name: str) -> _dt.date | None:
    """Coerce ``value`` to a :class:`datetime.date`, or ``None`` if empty."""
    if value in (None, ""):
        return None
    if isinstance(value, _dt.date):
        return value
    if isinstance(value, str):
        try:
            return _dt.date.fromisoformat(value)
        except ValueError as exc:  # pragma: no cover - message tested indirectly
            raise ValidationError(f"{field_name}: not an ISO date: {value!r}") from exc
    raise ValidationError(f"{field_name}: expected an ISO date string, got {type(value).__name__}")


@dataclass(frozen=True, slots=True)
class Statute:
    """A single tracked privacy statute.

    Attributes:
        id: Stable slug, unique across the dataset (e.g. ``"tx-hb-4"``).
        state: Two-letter USPS state code.
        title: Human-readable bill title.
        bill_number: Legislative identifier (e.g. ``"HB 4"``).
        categories: One or more :data:`CATEGORIES` this law governs.
        stage: Current lifecycle :data:`STAGES` value.
        summary: Plain-English "what changed" — one to three sentences.
        source_url: Canonical link to the bill text or a legislative record.
        introduced: Date the bill was introduced, if known.
        last_action: Date of the most recent tracked action, if known.
        effective: Date the law takes (or took) effect, if known.
        tags: Free-form keywords for search (never used for the closed filters).
    """

    id: str
    state: str
    title: str
    bill_number: str
    categories: tuple[str, ...]
    stage: str
    summary: str
    source_url: str
    introduced: _dt.date | None = None
    last_action: _dt.date | None = None
    effective: _dt.date | None = None
    tags: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValidationError("id: must be a non-empty slug")
        if self.state not in US_STATES:
            raise ValidationError(f"{self.id}: unknown state code {self.state!r}")
        if not self.title.strip():
            raise ValidationError(f"{self.id}: title is empty")
        if not self.categories:
            raise ValidationError(f"{self.id}: at least one category is required")
        for category in self.categories:
            if category not in CATEGORIES:
                raise ValidationError(f"{self.id}: unknown category {category!r}")
        if self.stage not in STAGES:
            raise ValidationError(f"{self.id}: unknown stage {self.stage!r}")
        if not self.summary.strip():
            raise ValidationError(f"{self.id}: summary is empty")
        if not self.source_url.startswith(("http://", "https://")):
            raise ValidationError(f"{self.id}: source_url must be an http(s) URL")

    @classmethod
    def from_dict(cls, raw: dict) -> "Statute":
        """Build a :class:`Statute` from a plain dict (e.g. one YAML record)."""
        if not isinstance(raw, dict):
            raise ValidationError(f"expected a mapping, got {type(raw).__name__}")
        try:
            categories = tuple(raw["categories"])
        except KeyError as exc:
            raise ValidationError("record is missing 'categories'") from exc
        return cls(
            id=str(raw.get("id", "")).strip(),
            state=str(raw.get("state", "")).strip().upper(),
            title=str(raw.get("title", "")).strip(),
            bill_number=str(raw.get("bill_number", "")).strip(),
            categories=categories,
            stage=str(raw.get("stage", "")).strip().lower(),
            summary=str(raw.get("summary", "")).strip(),
            source_url=str(raw.get("source_url", "")).strip(),
            introduced=_parse_date(raw.get("introduced"), "introduced"),
            last_action=_parse_date(raw.get("last_action"), "last_action"),
            effective=_parse_date(raw.get("effective"), "effective"),
            tags=tuple(raw.get("tags", ()) or ()),
        )

    def to_dict(self) -> dict:
        """Serialize to a JSON-friendly dict (dates as ISO strings)."""
        return {
            "id": self.id,
            "state": self.state,
            "title": self.title,
            "bill_number": self.bill_number,
            "categories": list(self.categories),
            "stage": self.stage,
            "summary": self.summary,
            "source_url": self.source_url,
            "introduced": self.introduced.isoformat() if self.introduced else None,
            "last_action": self.last_action.isoformat() if self.last_action else None,
            "effective": self.effective.isoformat() if self.effective else None,
            "tags": list(self.tags),
        }
