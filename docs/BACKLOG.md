# Statute Watch — Backlog

Epic/story breakdown driving the build. Every story has verifiable acceptance criteria a
later run can confirm true/false. Build runs implement to the criteria; QA attacks them.

Status legend: `[ ]` todo · `[~]` in progress · `[x]` done.

---

## Epic 1 — The filterable dossier (the wow moment)

The core experience: browse every tracked statute and slice it by state and data type in
one click, each card explaining what changed in plain English.

- [x] **1.1 Live-filterable statute grid** — _the wow moment._
  The built page shows all tracked statutes as cards and filters them **live** by state and
  data type with no page reload.
  - AC1: Selecting a state in the filter reduces the grid to only that state's cards and
    updates the visible result count.
  - AC2: Selecting a data type (e.g. biometric) shows only cards tagged with it; combining
    state + data type + stage applies all three (AND).
  - AC3: With JavaScript disabled, every statute is still visible as a server-rendered card
    (progressive enhancement).

- [x] **1.2 Plain-English statute card** — each card reads as an editorial digest, not a
  bill-tracker row.
  - AC1: A card shows state, bill number, title, lifecycle stage, the "what changed"
    summary, category tags, a status line, and a working link to the source bill.
  - AC2: Lifecycle stage is color-coded per DESIGN (vermilion for moving, green for "in
    effect").

- [x] **1.3 Designed empty & result states** — filtering to nothing is handled gracefully.
  - AC1: A filter combination that matches no statutes shows the designed empty-state
    message, not a blank grid.
  - AC2: The result bar always reflects the current visible count.

- [x] **1.4 Filter bar as a first-class control** — no naked native widgets.
  - AC1: Each `select` is themed (custom chevron, themed hover + focus-visible ring) per
    DESIGN; a Clear button resets all filters and the count.
  - AC2: Filter options are generated from the dataset (no hard-coded state list that can
    drift from the data).

- [x] **1.5 Design polish — hero & grid composition.**
  - AC1: At 390px, 768px, and 1440px the page has no horizontal scroll, no overlap, and no
    large empty margins; the grid owns the majority of the viewport.
  - AC2: Fraunces + Inter load; the `§` wordmark and inline-SVG favicon render (no default
    globe); contrast ≥ 4.5:1 on body text.

---

## Epic 2 — The dataset & its integrity

The dataset is the product; it must be correct, well-categorized, and provably valid.

- [x] **2.1 Expand coverage to a credible v1 slice.**
  - AC1: The dataset covers ≥ 20 statutes across ≥ 15 states, including at least three
    entries in each of biometric, geolocation, data-broker, and comprehensive.
  - AC2: Every lifecycle stage (introduced, passed, enacted, effective) is represented.
  - _Done: 28 statutes / 20 states; core categories ≥ 3; all stages present. Asserted by
    `test_catalog.test_v1_coverage_target_holds`._

- [x] **2.2 Dataset validation gate.**
  - AC1: `statute-watch validate` exits non-zero on an unknown state/category/stage, a
    non-http source URL, or a duplicate id.
  - AC2: CI runs `validate` on every push and fails the build on a bad dataset.
  - _Done: model + catalog validation; CI runs `validate`. `test_cli` covers the non-zero
    exit paths._

- [x] **2.3 Every summary is honest and plain.**
  - AC1: Each statute's `summary` is 1–3 sentences describing what the law *requires*, not
    just restating its title; a QA run spot-checks ≥ 5 against their source URLs.
  - AC2: No placeholder or "TODO" text exists in any record.
  - _Done: every record carries a requirement-describing summary; no placeholder text. QA
    still to spot-check against sources._

- [x] **2.4 Source registry & provenance.**
  - AC1: Every statute's `source_url` resolves to an official legislative record and is
    listed under a jurisdiction in `sources.yaml`.
  - AC2: `sources.yaml` documents each source's authority (official vs index).
  - _Done: `sources.py` + `check_provenance` in the `validate` gate; every dataset state has
    a registered official source._

- [x] **2.5 Design polish — state-coverage cue.**
  - AC1: The page surfaces which/how many states are covered (a map or ranked strip) using
    DESIGN tokens, composed at all three breakpoints.
  - _Done: ranked coverage strip in the hero (navy→vermilion fill), responsive._

---

## Epic 3 — The refresh pipeline

Keep the dataset current without hand-editing YAML forever.

- [x] **3.1 Fetch & stage new bills from a source.**
  - AC1: A `statute-watch fetch <source>` command pulls candidate bills from a registered
    source into a staging file, without touching the curated dataset.
  - AC2: The fetch step is network-guarded and unit-tested against a saved fixture (no live
    network in CI).
  - _Done: `pipeline.fetch` + `statute-watch fetch`; network off unless `--network`; tested
    against `tests/fixtures/feed_ncsl_sample.yaml`._

- [x] **3.2 Diff & review workflow.**
  - AC1: A command reports what changed between the staged fetch and the current dataset
    (new bills, stage advances) so a human can review before merge.
  - AC2: Merging a reviewed change keeps the dataset passing `validate`.
  - _Done: `statute-watch diff` classifies new/advanced/unchanged; `pipeline.apply_merge`
    yields a dataset that still validates (`test_pipeline`)._

- [ ] **3.3 Scheduled build.**
  - AC1: A documented command/GitHub Action rebuilds the site from the dataset on a schedule
    and the output is reproducible (same dataset → same site).

---

## Epic 4 — Ship quality

- [ ] **4.1 Landing/site parity.**
  - AC1: The landing page and the app share the DESIGN direction and tokens (one brand); no
    two-brand mismatch.

- [ ] **4.2 Accessibility pass.**
  - AC1: Focus order is sane, icon-only controls have `aria-label`, the result count uses a
    live region, and touch targets are ≥ 44px.

- [ ] **4.3 Docs & runnability.**
  - AC1: A fresh clone can run `pip install -e .[dev]`, `pytest`, and `statute-watch build`
    following only the README, producing `dist/index.html`.
  - AC2: README documents the build command and output directory.
