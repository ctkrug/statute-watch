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
statute-watch validate       # check the dataset is well-formed
statute-watch build          # render the static site into dist/
python -m http.server -d dist   # preview at http://localhost:8000
```

`statute-watch --help` lists every command.

## Layout

```
src/statute_watch/    # the pipeline: models, catalog loader, summarizer, site builder, CLI
data/                 # the curated dataset (statutes.yaml) + source registry (sources.yaml)
templates/            # the static-site templates and styles
tests/                # pytest suite
docs/                 # VISION, BACKLOG, DESIGN
```

## Project docs

- [`docs/VISION.md`](docs/VISION.md) — the problem, the audience, and what "v1 done" means.
- [`docs/BACKLOG.md`](docs/BACKLOG.md) — the epic/story breakdown driving the build.
- [`docs/DESIGN.md`](docs/DESIGN.md) — the art direction for the site.

## License

MIT — see [`LICENSE`](LICENSE).
