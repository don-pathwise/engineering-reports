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
