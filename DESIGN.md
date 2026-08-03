# Design

## Theme

Committed light theme. Slate-100 (`rgb(241 245 249)`) page background, white cards with `border-2 border-slate-300` and `rounded-2xl`, soft two-layer card shadow. Ink is slate: headings `slate-950`, body `slate-700` (leading-relaxed), muted `slate-600`. This is a documents-not-console surface — light is deliberate, not a default.

## Color

Restrained neutral base (slate) + a semantic accent vocabulary applied one-accent-per-section. Each accent carries a fixed meaning across the whole system:

| Accent | Meaning |
|---|---|
| rose | required action, secrets, danger, destructive, closed/wrong |
| sky | reference info, manifests, data flow, technical detail |
| amber | warnings, constraints, ops-coordination, guard rails |
| emerald | done / good / safe / no-action / improvement |
| purple | sequencing / process / "new" / coming-up |
| teal | alternate "new" when purple is taken |
| slate | neutral / default / inert / future work |

Accent tints used at `-100/-200/-300` (fills/borders) and `-800/-900` (text). Contrast: AA minimum everywhere; body never lighter than slate-700 on white/slate-100. No global legend — captions, kickers, and pills are self-describing.

## Typography

- **Inter** (400–800) for everything: headings, body, labels, UI. `font-feature-settings: "cv02","cv03","cv04","cv11"`. Root `17px`.
- **JetBrains Mono** (400–600) for code, identifiers, tabular data (`code.k` = slate-200 chip; `.step-number` uses tabular-nums).
- One family for prose, one for mono — paired on a real contrast axis. Fixed rem scale (product register), not fluid clamp. H1 `text-4xl sm:text-5xl font-extrabold tracking-tight`; H2 `text-2xl font-bold`; kicker `text-sm font-bold uppercase tracking-wider` in the section accent.

## Components

- **Section card**: `bg-white border-2 border-slate-300 rounded-2xl` + `.main-card` shadow, `p-7 sm:p-9`. Unnumbered head (accent dot + kicker) by default; numbered `.badge-num` circle only for real ordered sequences.
- **Pill**: `inline-flex rounded-full`, uppercase `0.72rem` tracked, `border-width:1px`. Status pills earn color per row/item; section-header pills usually don't.
- **Callout banner**: full-width tinted card (`bg-{accent}-50 border-2 border-{accent}-300`), no badge.
- **Table**: slate panel, uppercase tracked header row, `divide-y` body, wrapper `overflow-x-auto` + `min-w-[…]` + `<colgroup>` so wide tables scroll (never clip) inside the card.
- **Code block**: `<pre>` on white inside a tinted `bg-{accent}-100 border-2 border-{accent}-300 rounded-xl` container.
- **Inline code**: `code.k` (slate-200 bg, JetBrains Mono).

## Layout

`max-w-6xl mx-auto px-6`. Hero header on white with `border-b-2 border-slate-300`; main content `space-y-6`. Responsive is structural: card grids via `repeat(auto-fit, minmax(...))` / breakpoint columns, tables scroll horizontally, never fluid typography. Semantic z-scale (sticky header < progress bar < any future overlay).

## Motion

Product-register restraint: 150–250ms transitions, ease-out. Section reveal-on-scroll enhances already-visible content (never gates visibility on a class) and degrades to instant under `prefers-reduced-motion: reduce`. Reading-progress bar and hover states convey state, not decoration. No orchestrated page-load choreography.

## Print

First-class: `@media print` forces black ink on white, removes interactive chrome (search, progress bar, sticky nav), expands scroll wrappers, and uses `break-inside: avoid` on cards so a report prints/PDFs cleanly for review.
