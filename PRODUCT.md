# Product

## Register

product

## Users

Pathwise engineers and devops teammates. They arrive at a report because they need to *act*: run a UAT test plan, understand a root cause before touching code, follow a migration/cutover procedure, or look up an env/secrets/topology reference. They are technical, time-pressured, and often reading on a second monitor or a printed PDF in a review. The audience is internal, so load-bearing detail (image tags, account IDs, cluster/namespace names, route paths, tenant slugs) is a feature, not something to redact.

## Product Purpose

A published collection of single-file HTML engineering reports (GitHub Pages: `don-pathwise.github.io/engineering-reports`). Each report is self-contained and shareable; the collection needs a front door that makes the right report findable in seconds and signals its type and status at a glance. Success = a teammate lands on the index, finds the report they need without scrolling blindly, and trusts it enough to act on it.

## Brand Personality

Precise, trustworthy, calm, technical. Three words: **exact, legible, credible.** The voice is an engineer writing for engineers — no marketing gloss, no hedging. Confidence comes from information design (clear hierarchy, color that signals meaning, scannable structure), not decoration.

## Anti-references

- The current bare dark `<ul>` index — no hierarchy, broken nesting, disconnected from the reports it links to.
- Generic SaaS marketing pages (hero-metric templates, gradient text, tracked-uppercase eyebrows on every section).
- Cluttered BI dashboards with a rainbow of unrelated widgets.
- Hacker/terminal-green dark-mode-for-cool aesthetic — these are documents, not a console.

## Design Principles

1. **Scannability first.** A reader should locate the right report and understand its state before reading a full sentence. Structure and color do the work.
2. **Color signals meaning, never decorates.** One accent ≈ one meaning within a surface (rose=action/danger, sky=reference, amber=warning, emerald=done/good, purple=process/new, slate=neutral).
3. **Earned familiarity.** Standard affordances (search, filter, cards, links) behaving exactly as expected. The interface disappears into the task.
4. **One system across every report.** The index and every report share type, color, spacing, and component vocabulary. Consistency is the brand.
5. **Built to be read and printed.** Reports get printed to PDF and shared in reviews; the design must survive on paper as well as on screen.

## Accessibility & Inclusion

WCAG AA: body text ≥4.5:1, large text ≥3:1 against its background. Reduced-motion honored on every animation (reveals degrade to instant/visible). Keyboard-navigable search/filter and links with visible focus. Color is never the sole signal — it always pairs with a label, icon, or text.
