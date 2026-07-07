# Statute Watch — Vision

## The problem

US state privacy law is fragmenting fast. There is no federal baseline, so fifty
legislatures are each writing their own rules — on biometric identifiers, precise
geolocation, data brokers, children's data, and comprehensive consumer rights. In a
single legislative session, hundreds of relevant bills are introduced, amended, passed,
signed, and take effect. The information exists, but it is:

- **Scattered** across fifty legislative websites, each with its own bill-tracking UI.
- **Written for lawyers** — a bill number and 40 pages of statutory text, not a summary.
- **Hard to slice** — "show me every effective biometric law" is a research project, not
  a filter.

The people who need this — privacy engineers deciding what to build, compliance teams
scoping obligations, journalists covering the beat, advocates tracking momentum — end up
maintaining private spreadsheets that go stale within weeks.

## The core idea

**Turn messy legislative activity into a clean, correctly categorized, browsable dataset,
and keep it current on a schedule.** Each tracked law is one record: which state, which
data types it governs, where it sits in its lifecycle (introduced → passed → enacted →
effective), and a plain-English "what changed" that a non-lawyer can act on. The dataset
renders to a static site you can filter by state and data type in one click.

The editorial judgment — deciding what counts, categorizing it correctly, and writing the
summary honestly — is the product. The pipeline just keeps it fresh.

## Who it's for

- **Privacy & security engineers** — "does my location feature now need opt-in consent in
  Washington?"
- **Compliance / legal ops** — a quick, current map of obligations by state and data type.
- **Journalists & researchers** — momentum and coverage across states at a glance.
- **Privacy advocates** — track which protections are advancing and which stalled.

## Key design decisions

1. **A strict, closed data model.** State, category, and lifecycle stage are closed
   vocabularies validated on load (`models.py`). A malformed or mis-categorized record
   fails the build rather than silently shipping wrong law. Correctness is the whole point.
2. **Editorial summaries are data, not generated at render time.** The "what changed" text
   is hand-written and stored with the record, so the summary is reviewable and stable.
3. **Static, self-contained output.** The site builds to one directory with relative asset
   paths — hostable at any subpath, no server, no database. The dataset also ships as
   `data.json` for anyone who wants the raw data.
4. **Progressive enhancement.** Cards are server-rendered; filtering is a thin JS layer on
   top. The page is useful with JavaScript disabled.
5. **Authoritative sources only.** The dataset is curated from official legislative records
   (`sources.yaml`), not from scraping paywalled trackers.
6. **One brand.** The landing page and the app share the same civic-gazette design
   direction (`DESIGN.md`) — product and page read as one thing.

## What "v1 done" looks like

- The wow moment lands: an at-a-glance grid of tracked statutes that **filters live by
  state and data type**, each card showing the plain-English "what changed" and a link to
  the bill — composed and correct on phone and desktop.
- The dataset covers a meaningful, honest slice of current state privacy law (biometric,
  geolocation, data-broker, comprehensive, plus health and children's data) across a
  spread of states and every lifecycle stage.
- `statute-watch validate` guarantees dataset integrity; CI runs it on every push.
- The site builds to a single directory with relative paths and passes the design bar in
  `DESIGN.md` (real type, depth, interaction states, favicon, responsive).
- A documented path exists for refreshing the dataset from the registered sources.

## Explicitly out of scope for v1

- Live scraping of every state legislature (the pipeline ingests curated records first; a
  scraper is a later epic).
- Legal advice or interpretation — Statute Watch summarizes, it does not counsel.
- User accounts, alerts, or an API server. The static dataset is the API.
