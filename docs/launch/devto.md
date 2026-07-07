---
title: "Building Statute Watch: a provenance-gated tracker for US state privacy law"
published: false
tags: python, opensource, privacy, webdev
---

I kept losing track of US state privacy law. Every few weeks another state would pass
something touching biometric data or geolocation, and the only way to stay current was a
pile of bill-tracker tabs and a lot of skimming. So I built [Statute Watch](https://apps.charliekrug.com/statute-watch/):
a browsable dossier of state privacy statutes, filterable by state and data type, each
with a plain-English note on what changed. It is a small Python pipeline that renders a
static site, and the whole thing is [open source](https://github.com/ctkrug/statute-watch).

Here are the two build decisions I found most interesting.

## 1. A provenance gate that can fail the build

The credibility of a legal tracker rests entirely on "says who?" A record that claims
Texas did something has to trace back to the Texas legislature's own record, not to a
blog or a scraped aggregator. So the dataset is only half the story; the other half is a
source registry (`data/sources.yaml`) that maps each state to an authoritative official
source.

The rule I enforce is simple: **every state present in the dataset must have a registered
official source, or the build fails.** It lives in one function:

```python
def check_provenance(catalog, registry):
    covered = registry.official_states()
    missing = sorted({s.state for s in catalog} - covered)
    if missing:
        raise ValidationError(
            "no official source registered for state(s): " + ", ".join(missing)
        )
```

The interesting part is where this runs. The refresh pipeline can fold newly reviewed
bills into the dataset with `merge --write`. An earlier version only re-checked the record
structure after merging, which meant you could add a bill for a state with no source, get
told "revalidated OK," and end up with a dataset that `validate` would then reject. Now
the merge builds the full catalog, runs the provenance check, and only writes if it
passes. A merge can never leave the dataset in a state the gate rejects.

## 2. Progressive enhancement, so the page works with JavaScript off

The site is a static build: a Python step reads the dataset and writes `index.html`,
`styles.css`, `app.js`, and a `data.json`. I wanted the filtering to feel instant, but I
did not want the page to be a blank shell that only renders once JavaScript runs.

So the builder server-renders every statute as a real `<article>` card, embeds the whole
dataset as JSON, and `app.js` only *layers* the filter controls on top. Turn JavaScript
off and you still get all 28 cards, fully readable. Turn it on and the selects populate
from the embedded data and show or hide cards live. The filter options even sort into
lifecycle order (introduced, passed, enacted, in effect) rather than alphabetical, so the
stage dropdown reads the way a lawyer would expect.

Two smaller things that paid off: the fetch step is **offline by default** (it reads a
local feed file, so CI never touches the network and builds are deterministic), and the
data model validates against **closed vocabularies** for state, category, and stage on
load. A typo in the dataset fails the build loudly instead of quietly shipping a wrong
label.

## What I would do differently

Live fetching is stubbed out for v1. I lean on curated feed files that a human reviews
before merge, which keeps the editorial quality high but means updates are manual. The
next step is per-state fetch adapters behind the same staging-and-diff flow, so the
review step stays but the gathering gets automated.

If you work in privacy or compliance, take a look and tell me which state or data type
you would want covered next.

- Live: https://apps.charliekrug.com/statute-watch/
- Code: https://github.com/ctkrug/statute-watch
