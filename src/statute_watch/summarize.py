"""Editorial helpers that turn a statute's fields into display-ready English.

The dataset carries a hand-written ``summary``; this module derives the *other*
human-facing strings the site needs — a lifecycle label, a one-line status line,
and category labels — so that presentation logic lives in one place and stays
consistent between the CLI and the site builder.
"""

from __future__ import annotations

import datetime as _dt

from .models import Statute

# Display labels for the closed vocabularies. Keeping them here (rather than in
# the model) separates storage codes from presentation copy.
CATEGORY_LABELS: dict[str, str] = {
    "geolocation": "Geolocation",
    "biometric": "Biometric",
    "data-broker": "Data broker",
    "comprehensive": "Comprehensive",
    "health-data": "Health data",
    "childrens": "Children's data",
}

STAGE_LABELS: dict[str, str] = {
    "introduced": "Introduced",
    "passed": "Passed",
    "enacted": "Enacted",
    "effective": "In effect",
}

# Present-tense verb describing what just happened at each stage.
_STAGE_VERB: dict[str, str] = {
    "introduced": "introduced",
    "passed": "passed the legislature",
    "enacted": "signed into law",
    "effective": "in effect",
}


def category_labels(statute: Statute) -> list[str]:
    """Human labels for a statute's categories, in dataset order."""
    return [CATEGORY_LABELS.get(c, c) for c in statute.categories]


def stage_label(statute: Statute) -> str:
    """Human label for a statute's lifecycle stage."""
    return STAGE_LABELS.get(statute.stage, statute.stage.title())


def status_line(statute: Statute, *, today: _dt.date | None = None) -> str:
    """A one-line 'what changed' status, e.g. 'Signed into law · Jul 2024'.

    For effective laws with a future effective date, notes the countdown so a
    not-yet-live law reads correctly.
    """
    today = today or _dt.date.today()
    verb = _STAGE_VERB.get(statute.stage, statute.stage)

    if statute.stage == "effective" and statute.effective:
        if statute.effective > today:
            return f"Takes effect {_fmt_month(statute.effective)}"
        return f"In effect since {_fmt_month(statute.effective)}"

    marker = statute.last_action or statute.introduced
    if marker:
        return f"{verb.capitalize()} · {_fmt_month(marker)}"
    return verb.capitalize()


def _fmt_month(date: _dt.date) -> str:
    """Format a date as 'Jul 2024' — precise enough, not fussy."""
    return date.strftime("%b %Y")
