# Contributing to Statute Watch

The value of Statute Watch is the accuracy of its dataset. Contributions that add or
correct statutes are the most useful thing you can do — but they must be correct, honestly
categorized, and sourced.

## Adding a statute

Add one record to [`data/statutes.yaml`](data/statutes.yaml). Fields:

| Field | Required | Notes |
|-------|----------|-------|
| `id` | ✓ | Stable slug, unique across the file. Convention: `state-billtype-number-year` (e.g. `tx-hb-4-2023`). |
| `state` | ✓ | Two-letter USPS code (50 states + `DC`). |
| `title` | ✓ | The bill's human-readable title. |
| `bill_number` | ✓ | Legislative identifier as commonly cited (e.g. `HB 4`). |
| `categories` | ✓ | One or more of: `geolocation`, `biometric`, `data-broker`, `comprehensive`, `health-data`, `childrens`. |
| `stage` | ✓ | Lifecycle: `introduced` → `passed` → `enacted` → `effective`. |
| `summary` | ✓ | 1–3 sentences on **what the law requires** — plain English, not the title restated. |
| `source_url` | ✓ | An `http(s)` link to an **official** legislative record (see `data/sources.yaml`). |
| `introduced` / `last_action` / `effective` | — | ISO dates (`YYYY-MM-DD`) where known. |
| `tags` | — | Free-form keywords for search (not used by the closed filters). |

### Rules of thumb

- **Categorize by what the law governs**, not by its sponsor's framing. A comprehensive
  privacy act that carves out biometric identifiers gets both `comprehensive` and
  `biometric`.
- **The summary must be honest.** Describe the operative requirement (consent, opt-out,
  registration, a ban). Do not editorialize about whether the law is good.
- **Source of record only.** Prefer the state legislature's own bill page over a secondary
  tracker. Add the jurisdiction to `data/sources.yaml` if it isn't there.
- **No placeholders.** A record with `TODO` text should not be committed.

## Before you open a PR

```bash
pip install -e .[dev]
statute-watch validate    # dataset integrity — must pass
ruff check src tests
pytest -q
```

`validate` will reject an unknown state/category/stage, a non-http source URL, or a
duplicate id. CI runs the same checks on every push.

## Commit style

Conventional commits, imperative mood, with a body explaining *why* for anything
non-trivial (e.g. `data: add WA My Health My Data Act`). One logical change per commit.
