"""Render the curated dataset into a static, self-contained site.

The build is intentionally simple: read the templates in ``templates/``, inject
the dataset as embedded JSON plus server-rendered statute cards, and write the
result to an output directory (``dist/`` by default). Everything uses **relative
asset paths** so the site works when hosted under any base path.

This SCOPE-phase builder produces a correct, runnable page; the filtering UI,
the state-map hero, and the design polish are BUILD-phase stories (see
``docs/BACKLOG.md``). The contract here — a single output directory with an
``index.html`` and relative assets — is what the later work builds on.
"""

from __future__ import annotations

import json
import shutil
from html import escape
from pathlib import Path

from .catalog import Catalog, load_catalog
from .summarize import CATEGORY_LABELS, STAGE_LABELS, category_labels, stage_label, status_line

_REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = _REPO_ROOT / "templates"
DEFAULT_OUTPUT_DIR = _REPO_ROOT / "dist"


def build_site(
    output_dir: str | Path | None = None,
    *,
    catalog: Catalog | None = None,
) -> Path:
    """Build the static site and return the output directory path.

    Args:
        output_dir: Destination directory; defaults to :data:`DEFAULT_OUTPUT_DIR`.
        catalog: Pre-loaded catalog; loaded from the default dataset if omitted.
    """
    out = Path(output_dir) if output_dir is not None else DEFAULT_OUTPUT_DIR
    catalog = catalog if catalog is not None else load_catalog()

    out.mkdir(parents=True, exist_ok=True)

    template = (TEMPLATES_DIR / "index.html").read_text(encoding="utf-8")
    html = _render(template, catalog)
    (out / "index.html").write_text(html, encoding="utf-8")

    # Copy static assets (stylesheet, app script) verbatim.
    for asset in ("styles.css", "app.js"):
        src = TEMPLATES_DIR / asset
        if src.exists():
            shutil.copyfile(src, out / asset)

    # Emit the machine-readable dataset so the page (and any consumer) can filter
    # client-side without a server round-trip.
    data = {"statutes": [s.to_dict() for s in catalog]}
    (out / "data.json").write_text(json.dumps(data, indent=2), encoding="utf-8")

    return out


def _render(template: str, catalog: Catalog) -> str:
    """Fill the template's placeholders with rendered content."""
    dataset_json = json.dumps({"statutes": [s.to_dict() for s in catalog]})
    replacements = {
        "{{CARDS}}": _render_cards(catalog),
        "{{COVERAGE}}": _render_coverage(catalog),
        "{{COUNT}}": str(len(catalog)),
        "{{STATE_COUNT}}": str(len(catalog.states())),
        "{{DATASET_JSON}}": dataset_json,
        "{{CATEGORY_LABELS}}": json.dumps(CATEGORY_LABELS),
        "{{STAGE_LABELS}}": json.dumps(STAGE_LABELS),
    }
    for key, value in replacements.items():
        template = template.replace(key, value)
    return template


def state_coverage(catalog: Catalog) -> list[tuple[str, int]]:
    """(state, statute-count) pairs, ranked by count then state code.

    The ranked strip in the hero uses this to show the dataset's breadth at a
    glance (backlog 2.5).
    """
    counts: dict[str, int] = {}
    for statute in catalog:
        counts[statute.state] = counts.get(statute.state, 0) + 1
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))


def _render_coverage(catalog: Catalog) -> str:
    """Server-render the ranked state-coverage strip (one themed bar per state)."""
    coverage = state_coverage(catalog)
    if not coverage:
        return ""
    top = coverage[0][1]
    rows = []
    for state, count in coverage:
        pct = round(100 * count / top)
        noun = "statute" if count == 1 else "statutes"
        rows.append(
            f'        <li class="coverage__row" data-state="{escape(state)}">'
            f'<span class="coverage__state">{escape(state)}</span>'
            f'<span class="coverage__bar"><span class="coverage__fill" '
            f'style="width:{pct}%"></span></span>'
            f'<span class="coverage__count" aria-label="{count} {noun}">{count}</span>'
            f"</li>"
        )
    return "\n".join(rows)


def _render_cards(catalog: Catalog) -> str:
    """Server-render each statute as an article card (progressive enhancement)."""
    cards = [_render_card(s) for s in catalog]
    return "\n".join(cards)


def _render_card(statute) -> str:
    cats = "".join(
        f'<span class="tag tag--{escape(c)}">{escape(label)}</span>'
        for c, label in zip(statute.categories, category_labels(statute), strict=True)
    )
    data_categories = " ".join(statute.categories)
    return f"""\
      <article class="card" data-state="{escape(statute.state)}" \
data-categories="{escape(data_categories)}" data-stage="{escape(statute.stage)}">
        <header class="card__head">
          <span class="card__state">{escape(statute.state)}</span>
          <span class="card__stage card__stage--{escape(statute.stage)}">\
{escape(stage_label(statute))}</span>
        </header>
        <h3 class="card__title">{escape(statute.title)}</h3>
        <p class="card__bill">{escape(statute.bill_number)}</p>
        <p class="card__summary">{escape(statute.summary)}</p>
        <footer class="card__foot">
          <div class="card__tags">{cats}</div>
          <p class="card__status">{escape(status_line(statute))}</p>
          <a class="card__link" href="{escape(statute.source_url)}" \
rel="noopener" target="_blank" \
aria-label="Read the bill: {escape(statute.title)} ({escape(statute.bill_number)})">\
Read the bill &rarr;</a>
        </footer>
      </article>"""
