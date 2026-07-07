# Statute Watch — Architecture

A concise map of the codebase so a fresh session can orient fast. For *why*, see
`VISION.md`; for *what's next*, see `BACKLOG.md`; for *how it should look*, see `DESIGN.md`.

## The shape of it

Statute Watch is a small Python pipeline that turns a **hand-curated YAML dataset** of US
state privacy statutes into a **static, self-contained website** you can host at any subpath.
The dataset is the product; the code keeps it correct and renders it.

```
data/
  statutes.yaml       # the curated dataset — one record per tracked bill
  sources.yaml        # the source registry — one authoritative record per jurisdiction
src/statute_watch/
  models.py           # Statute dataclass + closed vocabularies; validates every record
  catalog.py          # loads/validates the dataset; query + count helpers (Catalog)
  sources.py          # loads/validates the source registry; provenance cross-check
  summarize.py        # derives display strings (stage label, status line, category labels)
  build.py            # renders the dataset into dist/ (index.html + assets + data.json)
  pipeline.py         # refresh pipeline: fetch -> staging, diff vs dataset, merge back in
  cli.py              # argparse: validate | build | list | sources | fetch | diff | merge
  __main__.py         # `python -m statute_watch`
templates/
  index.html          # page shell with {{PLACEHOLDER}} tokens the builder fills
  styles.css          # civic-gazette theme (see DESIGN.md); copied verbatim
  app.js              # client-side filtering over the server-rendered cards
tests/                # pytest suite (no network); conftest wires src/ onto sys.path
dist/                 # build output (git-ignored except as a preview)
```

## Data flow

1. **Author** edits `data/statutes.yaml` (or the pipeline stages candidates into
   `data/staging/`).
2. **`catalog.load_catalog()`** parses the YAML, builds a `Statute` for each record
   (per-record validation in `models.py`), enforces unique ids, and sorts newest-activity
   first. Returns an immutable `Catalog`.
3. **`sources.load_sources()`** parses `data/sources.yaml` into `Source` records;
   `sources.check_provenance(catalog, registry)` asserts every statute's state has a
   registered official source.
4. **`build.build_site()`** reads the templates, server-renders every statute as a card
   (progressive enhancement), embeds the dataset as JSON, renders the state-coverage strip,
   and writes `index.html`, `styles.css`, `app.js`, and `data.json` to the output dir with
   **relative asset paths only**.
5. In the browser, **`app.js`** populates the filter selects from the embedded data and
   shows/hides cards live — the page is fully useful with JavaScript disabled.

## The refresh pipeline (`pipeline.py`)

Keeps the dataset current without hand-editing YAML forever, and stays CI-safe (no live
network in tests):

- **`fetch(source, feed=…)`** reads a source's raw bill feed (a local fixture by default;
  live network only behind an explicit opt-in) and writes candidate records to
  `data/staging/<source>.yaml` — it never touches the curated dataset.
- **`diff(catalog, staged)`** classifies each staged record against the current dataset as
  `new`, a `stage-advance`, or `unchanged`, so a human can review before merging.
- **`apply_merge(catalog, staged)`** folds approved records back in (append new, update
  advanced) and returns record dicts; the `merge --write` CLI validates the merged result
  in full — structure **and** the provenance gate — *before* writing, and refuses (exit 1,
  no file written) if it would leave a dataset `validate` rejects, so a merge can never ship
  a broken dataset.

## Invariants worth protecting

- **Closed vocabularies.** State, category, and stage are validated on load; a bad record
  fails the build rather than shipping wrong law (`models.CATEGORIES/STAGES/US_STATES`).
- **Relative asset paths only.** The site is served from a subpath; a leading-slash asset
  path would 404. `test_build.py` guards this.
- **Editorial summaries are data.** The "what changed" text is stored with the record, not
  generated at render time, so it is reviewable and stable.

## Run it

```bash
pip install -e .[dev]     # or: PYTHONPATH=src for a dependency-free run
pytest -q                 # the full suite (no network)
ruff check src tests      # lint
python -m statute_watch validate   # dataset + provenance gate
python -m statute_watch build      # -> dist/index.html
```
