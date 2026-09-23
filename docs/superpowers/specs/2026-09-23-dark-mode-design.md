# Dark mode for the engineering reports — design

**Date:** 2026-09-23
**Status:** approved, ready for implementation planning
**Direction:** B — "Ink & Elevation"
**Mockups:** https://claude.ai/artifact/5yUryqABVeMXkNGDnbx8pu

## Problem

The reports are a committed light theme with no token layer. Every colour is a
hardcoded Tailwind CDN utility: 2,029 slate utilities, 217 `bg-white`, plus
accent utilities spanning the full 50–950 range, across 23 HTML files. Adding
dark mode by hand means editing every one of those and remembering both halves
forever.

The goal is dark mode plus a visual refresh, losing none of what the pages
already do: the print stylesheet, reading-progress bar, section anchors, the
index's search and category filters, horizontally scrolling tables, and
actionable checkboxes.

## Decisions

| Decision | Choice |
|---|---|
| Direction | B — Ink & Elevation |
| Mechanism | CSS custom-property token layer, not `dark:` variants |
| Switching | Manual toggle, defaulting to `prefers-color-scheme`, persisted in `localStorage` |
| Print | Always light, unconditionally |
| Radii | Toned down to the scale below |
| Section nav | Animated segmented slider; no per-report search |
| Scope | All 23 pages retrofitted now, plus the skill |

### Why tokens, not `dark:` variants

`dark:` variants would mean ~2,000 class edits and permanent double
bookkeeping — every future report would have to remember both halves. A token
layer is one edit per token, and the skill's boilerplate carries it, so new
reports get dark mode for free. It is also the only option under which the
print stylesheet, progress bar, anchors, and search keep working untouched:
none of them are colour-aware.

## Architecture

### The token layer

Tokens are defined on `:root` and remapped under `[data-theme="dark"]`, then
wired into `tailwind.config` so existing utility names keep working:

```js
tailwind.config = {
  theme: { extend: { colors: {
    surface:  'var(--surface)',
    surface2: 'var(--surface-2)',
    ink:      'var(--ink)',
    // …
  }}},
};
```

Token set (light value → dark value):

| Token | Light | Dark |
|---|---|---|
| `--page` | `#f1f5f9` | `#0a0b0f` |
| `--surface` | `#ffffff` | `#15171d` |
| `--surface-2` | `#f8fafc` | `#1b1e26` |
| `--border` | `#cbd5e1` | `#272b35` |
| `--border-w` | `2px` | `1px` |
| `--hairline` | `#e2e8f0` | `#242832` |
| `--ink` | `#020617` | `#f4f6fa` |
| `--body` | `#334155` | `#b9c0cc` |
| `--muted` | `#475569` | `#868e9e` |
| `--chip-bg` / `--chip-fg` | `#e2e8f0` / `#0f172a` | `#222630` / `#dbe1ea` |

Per accent (`rose`, `sky`, `amber`, `emerald`, `purple`, `teal`), four tokens —
`--accent-{name}-fill`, `-border`, `-text`, `-dot`. Dark values are in the
`B` theme dict of the mockup generator and carry over verbatim.

### Elevation

Dark mode drops shadows as the separator, because they do not read on a dark
ground. Cards instead get `inset 0 1px 0 rgba(255,255,255,.055)` for a lit top
edge, over a two-layer drop shadow. Borders go from 2px to 1px in dark: the
value step between `--page` and `--surface` already separates the card, and 2px
reads heavy.

### Radius scale

Applied in both themes — this is a system change, not a dark-mode-only one.

| Component | Was | Now |
|---|---|---|
| Section cards, callouts | 16px `rounded-2xl` | 8px `rounded-lg` |
| Table + stat-tile panels | 12px `rounded-xl` | 6px `rounded-md` |
| Code block container | 12px `rounded-xl` | 8px `rounded-lg` |
| `<pre>` | 6px `rounded-md` | 5px |
| Inline `code.k` | 4px `rounded` | 3px |

Status pills, section dots, and the theme switch stay fully round. They are
capsules by definition; squaring them reads as a bug.

### Section slider

Replaces nothing — it is new on report pages. A recessed track with a raised
thumb that slides between equal-width segments:

- Segments are equal width, so the thumb's offset is pure
  `calc(4px + (100% - 8px) * i / 4)` — no measurement, no resize observer.
- Thumb transitions `left` over 280ms ease; labels cross-fade muted → ink.
- `prefers-reduced-motion: reduce` drops the transition.
- Each segment keeps its section's accent dot, so the accent system stays
  readable without spending a colour on the selected state.
- Segment IDs come from the slugs the existing anchor-link code already
  generates. No new ID scheme.

Per-report search was considered and dropped — the index keeps its search; the
reports do not need it.

### Theme toggle

A switch in the same material as the slider, at the right end of the bar.

- Default: `prefers-color-scheme`.
- On toggle: set `data-theme` on `<html>`, persist to `localStorage`.
- The read must be wrapped in try/catch and must not block first paint — set
  `data-theme` from an inline script in `<head>` before the body renders, or
  the page flashes light before switching.

### Print

`@media print` forces `data-theme` to have no effect: light tokens are
restated inside the print block so a dark-mode reader still prints on white.
Everything else in the existing print stylesheet is unchanged, including its
deliberate preservation of accent colours.

## The retrofit

23 HTML files. `apply-report-enhancements.py` already does idempotent batch
rewrites and gets extended to carry this pass.

Order matters:

1. **Backfill the enhancement block** into the 4 reports missing it —
   `ezrd-1653-verify`, `ezrd-1949`, `ezrd-2019`, `ezrd-2325`. The theme toggle
   ships inside that block, so they need it first or they get tokens with no
   way to switch.
2. **Inject the token layer** into every `<head>`.
3. **Rewrite colour utilities** to token-backed names.
4. **Apply the radius scale.**
5. **Add the slider + toggle** to the sticky bar.

### The one thing that will break if done mechanically

**7 blocks across 4 files are already dark** — `bg-slate-900 text-slate-50`
and `bg-slate-950 text-slate-50` code panels in `export-student-buses-eks`
(both pages), `ezrd-2008`, and `ezrd-2019`. A naive scale inversion turns
these *light* on a dark page: exactly backwards.

These must be exempted from the inversion and mapped to their own token pair
(`--code-panel-bg` / `--code-panel-fg`) that stays dark in both themes. The
migration script fails loudly on any `bg-slate-9xx` it has not been told
about, rather than guessing.

Second trap: accents are used across the full 50–950 range, wider than the
`-100/-200/-300/-800/-900` that `DESIGN.md` documents. The token map covers
every step actually present; unmapped steps are a hard error, not a silent
pass-through.

## Docs to update

- **`DESIGN.md`** — "Committed light theme… light is deliberate, not a
  default" stops being true. Also the Motion section: the slider and toggle
  introduce material depth, which is the one place the system departs from
  product-register restraint. Both need rewriting, not deleting.
- **`PRODUCT.md`** — the "hacker/terminal-green dark-mode-for-cool"
  anti-reference stays valid and is worth keeping as the guard rail that
  distinguishes this from a console theme.
- **`~/.claude/skills/engineering-report-page/SKILL.md`** — boilerplate
  `<head>`, component snippets, and the shared enhancements block. This lives
  outside the repo; it must land in the same change or new reports will be
  generated light-only.

## Testing

- Every page renders in both themes with no flash of the wrong theme on load.
- Contrast: body text ≥4.5:1, large text ≥3:1, in both themes.
- Print output is light from a dark-mode session.
- Reading progress, anchors, index search, index category filters, table
  horizontal scroll, and checkboxes all still work.
- Slider keyboard-navigable; transition dropped under reduced motion.
- The 4 backfilled reports gain the enhancement block without duplicating it
  (the block guards on `data-report-enhanced`).

---

# Extension: the full surface inventory

Added 2026-09-23 after surveying what else shares this visual language. The
original spec covered one surface. There are **four**, in three repos plus the
skills directory. They are not linked by any build step — each carries its own
copy of the design language — so none of them inherits a change from another.

| # | Surface | Where | Colour utilities | Notes |
|---|---|---|---|---|
| 1 | Published reports | `engineering-reports` (this repo), 23 HTML files | 2,029 slate + 217 `bg-white` + accents 50–950 | Covered above |
| 2 | Ticket doc shell | `~/.claude/skills/chew-ticket/ticket-doc-template.html` | 56 | No enhancement block |
| 3 | Board shell | `~/Code/eng-local-docs/index.html` (53 lines) | 5, plus a hardcoded `#e2e8f0` in `code.k` | Injects markup via `innerHTML` |
| 4 | Board renderers | `~/Code/board` — `src/render.js` (31), `src/render-reviews.js` (36) | 68 | All colour lives in these two files |

## Sharing the token layer without a build step

No surface can import from another — four locations, three repos, no bundler.
The token block therefore has one canonical home in
`engineering-report-page/SKILL.md`, and each surface embeds a copy. Keeping
them in step is a script's job, not discipline's: extend
`apply-report-enhancements.py` (or add a sibling) to re-sync the token block
into all four targets idempotently, the way it already batch-applies the
enhancement block. A copy that has drifted is a failure the script reports,
not something it silently overwrites.

## Per-surface work

### 2 — Ticket doc shell

The template's comment says its style *"intentionally mirrors"* the skill.
Mirrors, not inherits — it drifts the moment the reports change.

- 56 colour utilities and its own radius set (8 `rounded-2xl`, 2
  `rounded-xl`, 5 `rounded-lg`) onto the token layer and the new scale.
- **It carries no enhancement block** (`data-report-enhanced` count is zero):
  no print stylesheet, no anchors, no reading progress. The theme toggle is
  specced to live inside that block, so either backfill the block here, or
  factor the toggle into a standalone snippet. Prefer backfilling — these docs
  get printed and deep-linked for the same reasons reports do.
- The tab machinery (`function select`) is chew-ticket-only and is not touched.

### 3 — Board shell

53 lines. `body` is `bg-slate-100 text-slate-700`; `code.k` hardcodes
`background:#e2e8f0`.

**The gotcha:** the shell polls `board-data.js` every 2s and replaces
`#board`'s `innerHTML` wholesale. Any theme state written *into* the injected
markup is destroyed on the next poll. `data-theme` must therefore live on
`<html>` in the shell, where the swap cannot reach it, and the toggle must sit
outside `#board` — in the existing `<nav>`.

### 4 — Board renderers

The easiest surface: 68 utilities concentrated in two files, no phase→colour
map to thread through (colours are inline at the call sites). Also 3
`rounded-2xl` → `rounded-lg`. Changes ship from the `board` repo and reach the
user on their next `board` run; no migration of existing output is needed
because `board-data.js` is regenerated every time.

## Prior art: there was already a dark surface here

`~/Code/eng-local-docs/DESIGN.md` documents a **"Second surface: the dark
planning document,"** established 2026-08-21 at the user's explicit request
(*"Dark mode, it is a must. The white is blinding."*). It specifies a full
oklch token ladder — ground `oklch(0.170 0.012 250)`, raised `0.212`, sunken
`0.140`; ink `0.950` / `0.800` / `0.665` with `--ink-mute` as a hard floor —
and claims 28 verified foreground/background pairs, none below AA, lowest
5.66:1.

**That documentation is now stale.** Its named reference implementation,
`EZRD-2967-clark-rum-behaviour.html`, no longer contains it: the file's only
non-print `:root` is light (`color-scheme: light`, `--bg: oklch(0.974 0.005
85)`), it has no `data-theme`, `prefers-color-scheme` or `localStorage`, and
the documented `oklch(0.170 …)` ground appears nowhere in it. The file was
modified four days after that section was written.

Two things follow:

1. **No live system competes with Direction B** — so B does not have to
   reconcile with a second dark theme currently in use.
2. **A dark surface here was specced, built, and quietly reverted to light
   once already.** Worth understanding why before repeating the shape of it.
   That history is not in git (`eng-local-docs` does not track these files).

### Open decision: notation for B's neutrals

Direction B's tokens are hex. The prior ladder is oklch, with documented
lightness steps and verified contrast.

**Recommendation:** keep the values the user approved on screen, but express
them in oklch anchored to that ladder's lightness steps. Two reasons — the six
report accents can then be derived at one consistent lightness and chroma
rather than hand-picked per hue, and the contrast verification already done
for the three-accent set carries over as a method. This is a notation change,
not a visual one.

Also reconcile the accent counts: that surface deliberately narrowed to three
(`--key` amber, `--bad` rust, `--ok` teal). The reports need all six, because
each carries a fixed meaning in `DESIGN.md`. Six stays; the narrowing was a
property of that one document type, not of the system.

## Explicitly out of scope

- **The 163 generated ticket docs** in `~/Code/eng-local-docs/`. They are
  ephemeral working files tied to closed tickets. Template-only, going forward.
- `reviews.html` and the other one-off pages in `eng-local-docs` — they are
  generated by `render-reviews.js` (surface 4) and follow from it.

## Docs to update (revised)

Adds to the list above:

- **`~/Code/eng-local-docs/DESIGN.md`** — the "Second surface" section must be
  either refreshed against a real implementation or retired. Leaving a spec
  pointing at a reference that no longer matches it is how the next person
  gets this wrong.
- **`~/Code/board/`** — no design doc today; the renderers become a consumer
  of the token layer and should say so in its README.
