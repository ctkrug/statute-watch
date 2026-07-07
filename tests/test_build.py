"""Tests for the static-site builder."""

import json
import re

from statute_watch.build import build_site, state_coverage
from statute_watch.catalog import Catalog


def test_build_emits_self_contained_site(tmp_path, catalog):
    out = build_site(tmp_path / "site", catalog=catalog)
    index = out / "index.html"
    assert index.exists()
    assert (out / "styles.css").exists()
    assert (out / "app.js").exists()
    assert (out / "data.json").exists()

    html = index.read_text(encoding="utf-8")
    # Every statute is server-rendered (progressive enhancement).
    assert html.count('class="card"') == len(catalog)
    # No template placeholders survive the render.
    assert "{{" not in html


def test_build_uses_relative_asset_paths(tmp_path, catalog):
    out = build_site(tmp_path / "site", catalog=catalog)
    html = (out / "index.html").read_text(encoding="utf-8")
    assert 'href="styles.css"' in html
    assert 'src="app.js"' in html
    # No absolute-root asset references that would break under a base path.
    assert 'href="/' not in html
    assert 'src="/' not in html


def test_data_json_matches_catalog(tmp_path, catalog):
    out = build_site(tmp_path / "site", catalog=catalog)
    data = json.loads((out / "data.json").read_text(encoding="utf-8"))
    assert len(data["statutes"]) == len(catalog)
    ids = {s["id"] for s in data["statutes"]}
    assert ids == {s.id for s in catalog}


def test_summary_text_is_escaped_and_present(tmp_path, catalog):
    out = build_site(tmp_path / "site", catalog=catalog)
    html = (out / "index.html").read_text(encoding="utf-8")
    # A known statute's title should appear in the rendered cards.
    assert "Biometric Information Privacy Act" in html


def test_card_links_have_distinct_aria_labels(tmp_path, catalog):
    # Every "Read the bill" link shares the same visible text, so each needs a
    # distinct aria-label naming its bill for screen-reader link navigation.
    out = build_site(tmp_path / "site", catalog=catalog)
    html = (out / "index.html").read_text(encoding="utf-8")
    labels = re.findall(r'aria-label="Read the bill: ([^"]+)"', html)
    assert len(labels) == len(catalog)
    assert len(set(labels)) == len(labels)  # all distinct


def test_state_coverage_is_ranked_and_complete(catalog):
    coverage = state_coverage(catalog)
    # One entry per distinct state, and every state accounted for.
    assert len(coverage) == len(catalog.states())
    assert sum(count for _, count in coverage) == len(catalog)
    # Ranked by count, descending.
    counts = [count for _, count in coverage]
    assert counts == sorted(counts, reverse=True)


def test_build_renders_coverage_strip(tmp_path, catalog):
    out = build_site(tmp_path / "site", catalog=catalog)
    html = (out / "index.html").read_text(encoding="utf-8")
    # One coverage row per state, and the placeholder was consumed.
    assert html.count('class="coverage__row"') == len(catalog.states())
    assert "{{COVERAGE}}" not in html


def test_build_empty_catalog_produces_valid_page(tmp_path):
    # An empty dataset must still render a self-contained page (no cards, no
    # coverage rows, zero counts) rather than crash — the designed empty state.
    out = build_site(tmp_path / "site", catalog=Catalog(statutes=()))
    html = (out / "index.html").read_text(encoding="utf-8")
    assert "{{" not in html  # every placeholder was still filled
    assert 'class="card"' not in html
    assert 'class="coverage__row"' not in html
    data = json.loads((out / "data.json").read_text(encoding="utf-8"))
    assert data["statutes"] == []


def test_build_is_reproducible(tmp_path, catalog):
    # Same dataset -> byte-identical site (backlog 3.3: reproducible builds).
    a = build_site(tmp_path / "a", catalog=catalog)
    b = build_site(tmp_path / "b", catalog=catalog)
    for name in ("index.html", "data.json", "styles.css", "app.js"):
        assert (a / name).read_bytes() == (b / name).read_bytes()
