#!/usr/bin/env python3
"""Assert every foreground/background pair the token set can actually produce
clears WCAG AA — not just the handful MAP happened to be exercising when this
was last extended.

Exit 0 and print the table when every REQUIRED pair passes; exit 1 listing
failures otherwise. Body text needs 4.5:1; large text (>=24px) and purely
decorative (non-text) marks need 3:1.

Fix round 1 (2026-09-23): the original version only tested 5 pairing kinds
(ink-on-neutrals, chip, text-on-fill, text-on-surface, white-on-solid). MAP
also produces `text-on-border` (156 real substitutions) and `dot`/`solid`
role backgrounds (78 substitutions) that were never tested at all — every
defect found in Task 6's fix round lived in one of those blind spots. This
version tests every pairing kind MAP can produce, labelled so a failure
names the exact pairing.

Two tiers:
  REQUIRED - gates the exit code. Everything the migration script can
    actually put in front of a reader: ink/chip on neutrals, accent text on
    accent fill, accent dot on the neutral surfaces it actually sits inside
    (page/surface/surface_2, and on its own accent fill for the
    dot-inside-a-status-pill pattern), white on solid, and ink/ink_body/
    ink_mute on accent fill (body prose inside a tinted callout banner).
  ADVISORY - printed for visibility (this is what "closes the hole" - a
    silently-untested pairing is exactly how the 4 defects got through) but
    does not fail the build. These are pairings that are real Tailwind
    utilities the design system's token aliases expose, so a hand-authored
    page COULD construct them, but which the token *values* themselves
    (unchanged since Task 1-5, not something this fix round has license to
    redesign) were never built to sustain standalone:
      - accent.border on page/surface: the same ~1.3-2.9:1 the pre-existing
        *neutral* --border token has carried since Task 1 (measured below),
        never flagged before now. Accent and neutral borders are both
        deliberately subtle 1-2px lines in this system, always paired with
        a fill or an already-differentiated card doing the real contrast
        work — never required to stand alone against raw page/surface.
      - accent.text on accent.border: `bg-{accent}-border` no longer exists
        as a migration output after Fix round 1 (bg- never targets the
        `border` role — see migrate_colours.py), so this pairing can no
        longer be produced by anything in this repo. Kept as a tripwire:
        if a `bg-{accent}-border` class ever reappears (by hand-authoring,
        bypassing the migration script), these are the real numbers, and
        several fail AA outright.
      - accent.solid on page/surface (bare, no text): `solid` is only ever
        applied by the migration script when `text-white` is in the same
        class attribute (Fix round 1, defect 3) — a bare solid with no text
        is not something the pipeline produces. Kept because the *token*
        itself (pinned to the light-theme dark hex, by design, so a badge
        stays legible in both themes) was never built to also read as a
        free-floating dark-on-dark mark in dark theme, and never claims to.
"""
import sys
from tokens import LIGHT_HEX, DARK_HEX, ACCENTS_HEX, contrast

BODY_MIN, LARGE_MIN = 4.5, 3.0
ACCENT_NAMES = ("rose", "sky", "amber", "emerald", "purple", "teal")


def pairs():
    """(label, foreground_hex, background_hex, minimum_ratio, tier)."""
    for theme, t in (("light", LIGHT_HEX), ("dark", DARK_HEX)):
        for fg in ("ink", "ink_body", "ink_mute"):
            for bg in ("page", "surface", "surface_2"):
                minimum = LARGE_MIN if fg == "ink" else BODY_MIN
                yield (f"{theme}/{fg}-on-{bg}", t[fg], t[bg], minimum, "required")
        yield (f"{theme}/chip_fg-on-chip_bg", t["chip_fg"], t["chip_bg"], BODY_MIN, "required")

        for name in ACCENT_NAMES:
            roles = ACCENTS_HEX[theme][name]

            # --- REQUIRED: pairings the migration script (or a hand-authored
            # page using only the documented roles the way they're meant to
            # be used) actually produces. ---

            # accent text on its own fill — a callout banner's kicker/label.
            yield (f"{theme}/{name}.text-on-fill", roles["text"], roles["fill"], BODY_MIN, "required")
            # accent text directly on a white/surface card.
            yield (f"{theme}/{name}.text-on-surface", roles["text"], t["surface"], BODY_MIN, "required")
            # white text on a solid badge (bg-{accent}-solid text-white) —
            # the only way `solid` is ever emitted post-Fix-round-1.
            yield (f"{theme}/{name}.white-on-solid", "#ffffff", roles["solid"], BODY_MIN, "required")
            # bare decorative dot (bg-{accent}-dot, no text) on every neutral
            # surface it's actually found inside in the corpus.
            for bgk in ("page", "surface", "surface_2"):
                yield (f"{theme}/{name}.dot-on-{bgk}", roles["dot"], t[bgk], LARGE_MIN, "required")
            # the same dot, but inside a same-accent status pill
            # (bg-{accent}-fill wrapping a bg-{accent}-dot span) — the
            # pairing that's actually live at e.g.
            # ezrd-1462/index.html:306's "In flight" badge.
            yield (f"{theme}/{name}.dot-on-fill", roles["dot"], roles["fill"], LARGE_MIN, "required")
            # ink/ink_body/ink_mute set as ordinary prose *inside* a tinted
            # callout banner (bg-{accent}-fill container, un-accented text).
            for fgk, minimum in (("ink", LARGE_MIN), ("ink_body", BODY_MIN), ("ink_mute", BODY_MIN)):
                yield (f"{theme}/{fgk}-on-{name}.fill", t[fgk], roles["fill"], minimum, "required")

            # --- ADVISORY: constructible via the exposed Tailwind aliases,
            # but not something anything in this repo currently emits, and
            # not fixable without redesigning Task 1-5 token values. See the
            # module docstring for the reasoning on each. ---

            yield (f"{theme}/{name}.border-on-page", roles["border"], t["page"], LARGE_MIN, "advisory")
            yield (f"{theme}/{name}.border-on-surface", roles["border"], t["surface"], LARGE_MIN, "advisory")
            yield (f"{theme}/{name}.text-on-border", roles["text"], roles["border"], BODY_MIN, "advisory")
            yield (f"{theme}/{name}.solid-on-page", roles["solid"], t["page"], LARGE_MIN, "advisory")
            yield (f"{theme}/{name}.solid-on-surface", roles["solid"], t["surface"], LARGE_MIN, "advisory")

        # The pre-existing *neutral* --border token, printed alongside the
        # accent advisory rows so the "this has always been the pattern"
        # claim above is checkable, not just asserted. Also advisory, for
        # the same reason.
        yield (f"{theme}/neutral.border-on-page", t["border"], t["page"], LARGE_MIN, "advisory")
        yield (f"{theme}/neutral.border-on-surface", t["border"], t["surface"], LARGE_MIN, "advisory")


def main():
    required_failures = []
    advisory_failures = []
    lowest_required = (None, 99.0)
    n_required = n_advisory = 0
    for label, fg, bg, minimum, tier in pairs():
        ratio = contrast(fg, bg)
        if tier == "required":
            n_required += 1
            if ratio < lowest_required[1]:
                lowest_required = (label, ratio)
        else:
            n_advisory += 1
        ok = ratio >= minimum
        mark = "ok  " if ok else ("FAIL" if tier == "required" else "info")
        print(f"  {mark} [{tier:8s}] {label:<32} {ratio:5.2f}:1  (min {minimum})")
        if not ok:
            (required_failures if tier == "required" else advisory_failures).append((label, ratio, minimum))

    print(f"\n{n_required} required pair(s), {n_advisory} advisory pair(s) checked.")
    print(f"lowest required: {lowest_required[0]} at {lowest_required[1]:.2f}:1")

    if advisory_failures:
        print(f"\n{len(advisory_failures)} advisory pair(s) below their floor (not gating — see module docstring):")
        for label, ratio, minimum in advisory_failures:
            print(f"  - {label}: {ratio:.2f}:1 < {minimum}")

    if required_failures:
        print(f"\n{len(required_failures)} REQUIRED pair(s) below AA:")
        for label, ratio, minimum in required_failures:
            print(f"  - {label}: {ratio:.2f}:1 < {minimum}")
        return 1
    print("\nall required pairs clear AA")
    return 0


if __name__ == "__main__":
    sys.exit(main())
