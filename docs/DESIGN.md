# Statute Watch — Design Direction

The art-direction brief. Every build and QA run follows this file; the landing page
(`site/`) and the app share it so product and page are one brand. Change it only
deliberately, in its own commit, with a note on why.

## 1. Aesthetic direction

**Statute Watch is a modern civic gazette rendered as a swiss-grid dashboard: cool
paper-white, ink-navy type set in a warm serif, and a single vermilion "amendment"
accent that marks where the law is moving.** It should read like an authoritative
public-records digest a serious newsroom would publish — composed, legible, and calm —
not a dark SaaS dashboard.

**Portfolio check.** Recent sibling ships lean warm-paper darkroom (Framepick),
prussian-blue and warm-paper blueprints (Phantom Read, Skillcheck), and cold-accent dark
(Metawipe). Statute Watch deliberately departs on two axes: a **cool** paper (blue-gray,
not warm cream) and a **vermilion** accent (not teal, amber, or blueprint blue) — so it
is not another paper/blueprint or dark theme in the wall.

## 2. Tokens (actual values)

| Token | Value | Role |
|-------|-------|------|
| `--bg` | `#eef1f5` | cool paper background |
| `--surface` | `#ffffff` | cards, masthead, footer |
| `--surface-2` | `#f5f7fa` | inset fields, tags |
| `--ink` | `#16203a` | primary text (ink navy) |
| `--muted` | `#5a6478` | secondary text |
| `--line` | `#d5dae3` | hairline borders |
| `--accent` | `#e2483d` | **vermilion** — fills, focus rings, large display type |
| `--accent-ink` | `#c93b31` | darker vermilion for small text (AA ≥4.5:1 on paper) |
| `--accent-2` | `#1b2a4a` | deep civic navy — state chips, rules |
| `--ok` | `#2f7d5b` | "in effect" positive status |

- **Type pairing:** display **Fraunces** (opsz serif, 500/600) for the wordmark,
  headlines, state chips, and stat figures; UI **Inter** (400/500/600) for body, labels,
  and controls. System fallbacks: `Georgia`/serif and `system-ui`/sans.
- **Type scale:** ~1.25 ratio. Hero headline `clamp(2rem, 5.5vw, 3.4rem)`.
- **Spacing:** 4/8px scale; page gutter `clamp(16px, 4vw, 40px)`.
- **Radius:** 10px cards/panels, 6–8px chips/controls, 999px tags.
- **Shadow:** layered — `0 1px 2px rgba(22,32,58,.06), 0 8px 24px rgba(22,32,58,.08)`;
  a deeper variant on card hover.
- **Motion:** UI transitions 140–200ms ease-out; card hover lifts 3px. Honor
  `prefers-reduced-motion`.

## 3. Layout intent

- **Hero of the page is the statute grid** — a responsive card grid
  (`auto-fill, minmax(300px, 1fr)`) that fills the viewport, sitting under a sticky-feeling
  filter bar. The grid, not decoration, owns the majority of the screen.
- **Masthead** is a thin gazette nameplate: wordmark left, tagline right, a 2px navy rule
  under it.
- **Hero band** states the thesis ("Fifty legislatures. One dossier.") with a short lede
  and three stat figures (statutes / states / data types) — no dead space.
- **Composition at breakpoints:** 1440 → 3–4 card columns; 768 → 2 columns; 390 → single
  column, filters stack full-width, no horizontal scroll. Text measures ≤ ~70ch.

## 4. Signature detail

**The `§` glyph wordmark and the vermilion "amendment" accent.** The section-sign glyph in
vermilion anchors the wordmark; lifecycle stages ("Enacted", "Passed") pick up the same
vermilion while "In effect" turns civic green — so the color itself narrates where each law
sits. Cards lift on hover like a page being pulled from a stack. The favicon is an
inline-SVG shield with a check, in navy + vermilion — never a default globe.

## 5. Design polish backlog

Design work is scheduled per epic, not bolted on at the end (see `BACKLOG.md`):

- **Filter bar as a first-class instrument** — themed selects (custom chevron, focus ring),
  a live result count, and a designed empty state.
- **State-coverage cue** — a compact visual of which states are covered (map or ranked
  strip) so the dataset's breadth reads instantly.
- **Squint test each QA** — hierarchy survives, hero fills the screen, every control has
  hover/focus/active states, and the landing page matches these tokens exactly.

_(No juice/SFX plan: Statute Watch is an editorial data tool, not a game — the required
feedback is interaction states, motion on hover, and a designed empty/result state, all
specified above.)_
