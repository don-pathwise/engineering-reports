# Design

## Theme

Dual theme on one oklch token layer. Light is the default and the print target;
dark follows `prefers-color-scheme` unless the reader chooses, and the choice
persists in `localStorage`. Neither is a variant of the other — tokens are
defined once per theme in `tools/tokens.py` and emitted into every page.

Dark neutrals anchor to a verified lightness ladder: page `0.140`, surface
`0.212`, raised `0.245`, line `0.300`; ink `0.950`, body `0.800`, muted
`0.665`. `--ink-mute` is the contrast floor in both themes — nothing
lighter-weight carries body text. Borders are 2px in light, 1px in dark: the
value step already separates the card, and 2px reads heavy on a dark ground.

This is a documents-not-console surface in both themes. Dark mode is paper at
night, not a terminal.

## Color

Restrained neutral base (the `page`/`surface`/`surface-2`/`border`/`ink` token
ladder — slate-derived in light mode, its own oklch ladder in dark) + a
semantic accent vocabulary applied one-accent-per-section. Six accent
families, each carrying a fixed meaning across the whole system:

| Accent | Meaning |
|---|---|
| rose | required action, secrets, danger, destructive, closed/wrong |
| sky | reference info, manifests, data flow, technical detail |
| amber | warnings, constraints, ops-coordination, guard rails |
| emerald | done / good / safe / no-action / improvement |
| purple | sequencing / process / "new" / coming-up |
| teal | alternate "new" when purple is taken |

Neutral (no accent) — `bg-chip` / `border-token` / `text-ink` / `text-body` /
`text-mute` — covers default / inert / future work.

The corpus had drifted to **thirteen** accent families before this migration;
six is now enforced. The strays were consolidated by meaning, not deleted:
violet/indigo/fuchsia → purple, blue → sky, red → rose, green → emerald,
orange → amber. A `violet` (or `blue`, `red`, …) utility found in git history
was a real accent that got folded into its canonical family on purpose — it
isn't lost work.

Each accent has **five** token-backed roles, defined once per theme in
`tools/tokens.py` and emitted by `tools/theme_block.py`: `fill` (tinted
background), `border`, `text`, `dot` (status-pill / kicker dot), and
**`solid`** — a theme-invariant fifth role (identical hex in light and dark)
for a solid badge background that carries `text-white`. It exists because
white measured 1.48:1 on the themed `text` role in dark mode; `solid` is
pinned to the light theme's darkest step so `bg-{accent}-solid text-white`
stays legible whichever theme is active.

A handful of code panels were already dark in the source and stay dark in
*both* themes on purpose — they get their own theme-invariant pair,
`var(--code-panel-bg)` / `var(--code-panel-fg)`, applied by inline `style=`
rather than a utility class, since they're the only tokens that don't vary
with theme.

Contrast is AA minimum everywhere, enforced by `tools/check_contrast.py`
across 204 pairings: **140 required** (gate the exit code — every pairing the
migration script, or a page following this doc, can actually produce) and
**64 advisory** (printed for visibility, never gate — pairings the token
*values* were never built to sustain standalone, such as a bare accent border
sitting directly on page background with no fill or card to do the real
contrast work). Do not "fix" an advisory row by weakening a required one —
read the module docstring in `check_contrast.py` for why each advisory
pairing is exempt. No global legend — captions, kickers, and pills are
self-describing.

## Typography

- **Inter** (400–800) for everything: headings, body, labels, UI. `font-feature-settings: "cv02","cv03","cv04","cv11"`. Root `17px`.
- **JetBrains Mono** (400–600) for code, identifiers, tabular data (`code.k` = token chip background, JetBrains Mono; `.step-number` uses tabular-nums).
- One family for prose, one for mono — paired on a real contrast axis. Fixed rem scale (product register), not fluid clamp. H1 `text-4xl sm:text-5xl font-extrabold tracking-tight`; H2 `text-2xl font-bold`; kicker `text-sm font-bold uppercase tracking-wider` in the section accent.

## Components

- **Section card**: `bg-surface border-2 border-token rounded-lg` + `.main-card` shadow, `p-7 sm:p-9`. Unnumbered head (accent dot + kicker) by default; numbered `.badge-num` circle only for real ordered sequences.
- **Radius scale**: cards and callouts `rounded-lg` (8px), table and tile
  panels `rounded-md` (6px), code containers 8px, `<pre>` 5px, inline code 3px.
  Pills, dots and the theme switch stay `rounded-full` — they are capsules by
  definition.
- **Pill**: `inline-flex rounded-full`, uppercase `0.72rem` tracked, `border-width:1px`. Status pills earn color per row/item; section-header pills usually don't.
- **Callout banner**: full-width tinted card (`bg-{accent}-fill border-2 border-{accent}-border rounded-lg`), no badge.
- **Table**: token neutral panel (`bg-surface-2 border-2 border-token rounded-md`), uppercase tracked header row (`bg-chip`), `divide-y divide-hairline` body, wrapper `overflow-x-auto` + `min-w-[…]` + `<colgroup>` so wide tables scroll (never clip) inside the card.
- **Code block**: `<pre>` on `bg-surface` inside a tinted `bg-{accent}-fill border-2 border-{accent}-border rounded-md` container (the already-dark, theme-invariant code panels use `var(--code-panel-bg)`/`var(--code-panel-fg)` by inline style instead — see Color).
- **Inline code**: `code.k` (token chip background, JetBrains Mono).

## Layout

`max-w-6xl mx-auto px-6`. Hero header on `bg-surface` with `border-b-2 border-token`; main content `space-y-6`. Responsive is structural: card grids via `repeat(auto-fit, minmax(...))` / breakpoint columns, tables scroll horizontally, never fluid typography. Semantic z-scale (sticky header < progress bar < any future overlay).

## Motion

Product-register restraint: 150–250ms transitions, ease-out. Section reveal-on-scroll enhances already-visible content (never gates visibility on a class) and degrades to instant under `prefers-reduced-motion: reduce`. Reading-progress bar and hover states convey state, not decoration. Two authored moments: the segmented section slider's thumb tracks reading position, and the theme switch's knob travels. Both are 220–280ms ease-out and both drop to instant under `prefers-reduced-motion: reduce`. Everything else is a hover transition.

## Print

First-class: `@media print` forces the light token set regardless of the reader's theme, removes interactive chrome (search, progress bar, sticky nav, theme switch), expands scroll wrappers, and uses `break-inside: avoid` on cards so a report prints/PDFs cleanly for review.
