# Statute Watch

**A tracker of US state privacy-law changes — geolocation, biometric, and data-broker
rules — as they move through statehouses, filterable by state and data type, each with a
plain-English "what changed" summary.**

State privacy law is a moving target. Every session, a dozen bills touching geolocation
tracking, biometric identifiers, and data-broker registration are introduced, amended,
passed, or take effect — scattered across fifty legislatures, buried in statutory language
few people have time to parse. Statute Watch turns that mess into a clean, correctly
categorized, browsable dataset and refreshes it on a schedule.

## What it does

- **Tracks the laws that matter** — geolocation, biometric, data-broker, and comprehensive
  consumer-privacy statutes across all US states.
- **Categorizes correctly** — every entry is tagged by state, data type, and lifecycle
  stage (introduced → passed → enacted → effective), so you can filter to exactly what you
  care about.
- **Explains in plain English** — each statute carries a short "what changed" summary that
  says what the law actually requires, not just its bill number.
- **Stays current** — a Python pipeline ingests curated legislative records and rebuilds a
  static, self-contained site you can host anywhere.

## Who it's for

Privacy engineers, compliance teams, journalists, and anyone who needs to know *which state
just did what* to biometric or location data — without reading fifty bill trackers.

## Stack

- **Pipeline:** Python 3.11 (standard library + PyYAML) — a small, dependency-light scraper
  and dataset validator.
- **Site:** a static, self-contained page built from the dataset. Relative asset paths only,
  no server required — publishable to any subpath.
- **Tests:** `pytest`. **CI:** GitHub Actions (lint + tests on every push).

## Quick start

```bash
pip install -e .[dev]        # install the package and dev tools
statute-watch validate       # check the dataset + provenance are well-formed
statute-watch build          # render the static site into dist/
python -m http.server -d dist   # preview at http://localhost:8000
```

`build` writes a self-contained site — `index.html`, `styles.css`, `app.js`, and
`data.json` — to `dist/` (or a directory you pass: `statute-watch build path/to/out`).
Every asset path is relative, so the site can be hosted at any subpath.

`statute-watch --help` lists every command.

## Commands

| Command | What it does |
|---------|--------------|
| `validate` | Load the dataset, enforce the closed vocabularies, and fail if any state lacks a registered official source (provenance gate). |
| `build [dir]` | Render the static site into `dir` (default `dist/`). |
| `list [--state XX] [--category C]` | Print tracked statutes to the terminal. |
| `sources` | List the registered legislative sources and their authority. |
| `fetch <source> --feed FILE` | Stage candidate bills from a source feed into `data/staging/` — never touches the curated dataset. |
| `diff <source>` | Report how staged candidates differ from the dataset (new / advanced / unchanged). |

## Refreshing the dataset

The pipeline keeps the dataset current without hand-editing YAML blindly:

```bash
statute-watch fetch congress-ncsl --feed feed.yaml   # -> data/staging/congress-ncsl.yaml
statute-watch diff  congress-ncsl                    # review new bills & stage advances
```

`fetch` is **offline by default** — it reads a local feed file so CI is deterministic; live
fetching is only enabled with `--network`. A curator reviews the diff, folds approved
changes into `data/statutes.yaml`, and re-runs `validate`. The
`.github/workflows/build-site.yml` action rebuilds the site on a weekly schedule and on any
data change; builds are reproducible (same dataset → identical output).

## Layout

```
src/statute_watch/    # models, catalog loader, sources registry, summarizer, builder,
                      #   refresh pipeline, CLI
data/                 # the curated dataset (statutes.yaml) + source registry (sources.yaml)
templates/            # the static-site templates and styles
tests/                # pytest suite (offline)
docs/                 # VISION, BACKLOG, DESIGN, ARCHITECTURE
```

## Project docs

- [`docs/VISION.md`](docs/VISION.md) — the problem, the audience, and what "v1 done" means.
- [`docs/BACKLOG.md`](docs/BACKLOG.md) — the epic/story breakdown driving the build.
- [`docs/DESIGN.md`](docs/DESIGN.md) — the art direction for the site.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — a map of the codebase and data flow.

## License

MIT — see [`LICENSE`](LICENSE).
