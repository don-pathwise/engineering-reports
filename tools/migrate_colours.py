#!/usr/bin/env python3
"""Rewrite Tailwind colour utilities onto the token layer.

Hard-fails on any utility it was not taught. An unmapped step is a migration
bug — silently passing it through is how half a page ends up off-theme.
"""
import glob, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_theme import EXEMPT_DARK, COLOUR_UTIL

# The already-dark code panels keep their own tokens, applied by hand in Task 6.
# Plus the utilities actually used inside those panels' hardcoded-dark sub-areas
# (e.g. the file-tree listing and its inline badges, and syntax-highlight spans
# in the code samples themselves): migrating them would make them resolve
# against a still-hardcoded near-black background, not a token surface,
# tanking contrast. Leaving them raw is the intended behaviour here.
#
# Fix round 1 / Critical: text-emerald-300, text-amber-300, text-sky-300 are
# syntax-highlight spans *inside* the 7 hand-edited code panels. They were
# missing from this set, so the generic accent loop below migrated them onto
# the themed `*-border` role while their panel is pinned theme-invariant via
# `var(--code-panel-bg/-fg)` — in dark theme the panel's fixed near-black
# background against the *dark-theme* `border` hue (chosen to read against a
# themed dark `--surface`, not a near-black fixed one) collapsed to
# 2.52-3.05:1. Added here so they stay Tailwind's own raw (also
# theme-invariant) colour, matching the panel they live in.
SKIP_IN_EXEMPT = {
    "bg-slate-900", "bg-slate-950", "text-slate-50", "text-slate-100",
    "text-slate-400",
    "bg-sky-800", "text-sky-100",
    "bg-emerald-800", "text-emerald-100",
    "text-emerald-300", "text-amber-300", "text-sky-300",
}

ACCENT_NAMES = ("rose", "sky", "amber", "emerald", "purple", "teal")

MAP = {
    # neutrals -> semantic tokens
    "bg-white": "bg-surface",
    "bg-slate-50": "bg-surface-2",
    "bg-slate-100": "bg-page",
    "bg-slate-200": "bg-chip",
    "border-slate-100": "border-hairline",
    "border-slate-200": "border-hairline",
    "border-slate-300": "border-token",
    "border-slate-400": "border-token",
    "divide-slate-200": "divide-hairline",
    "text-slate-950": "text-ink",
    "text-slate-900": "text-ink",
    "text-slate-800": "text-ink",
    "text-slate-700": "text-body",
    "text-slate-600": "text-mute",
    "text-slate-500": "text-mute",
    "text-slate-400": "text-mute",
    "text-slate-300": "text-mute",

    # Ruling H (accent-consolidation.md): mid-slate FILLS, judged per what
    # sits on top rather than by step number.
    #  - bg-slate-300: a badge-num circle (text-slate-900/text-ink on top)
    #    and a grid gap-line divider — both are direct uses of the same
    #    "rule line" neutral as border-slate-300 already maps to, so it
    #    gets the bg-flavoured twin of that same token. ink-on-token clears
    #    13.6:1 (light) / 11.7:1 (dark) — nowhere near the AA floor.
    #  - bg-slate-400 / bg-slate-500: bare `rounded-full` legend dots with
    #    no text on them at all, so body-text AA doesn't apply — the bar is
    #    the 3:1 non-text/UI-component contrast guideline against the page
    #    they sit on. --border is far too close to --page/--surface to read
    #    as a dot (1.36:1 / 1.46:1 measured) that ships in the same class as
    #    today's clearly-visible slate-400/500 dot. --ink-mute clears 6.5:1+
    #    against both --page and --surface in both themes, so it keeps the
    #    dot's original visual weight; used for both steps since neither
    #    has any text riding on it to differentiate by contrast.
    "bg-slate-300": "bg-token",
    "bg-slate-400": "bg-mute",
    "bg-slate-500": "bg-mute",
    # bg-slate-700 (one `toast-demo ... text-white` mockup in ezrd-1949) is
    # deliberately NOT mapped here: neither --token nor --ink-mute nor any
    # other themed token can hold white text legibly in both themes (checked
    # via tokens.contrast(): --border 1.48:1 light / --ink-mute 3.06:1 dark,
    # both fail body AA). It's hand-edited before migration runs, same as
    # the 7 code panels — see task-6-report.md. Fix round 1 corrected its
    # replacement colour: rgb(66 66 66), matching the page's own second,
    # identically-worded "Grey" toast at ezrd-1949/index.html:773 — not the
    # code-panel tokens (near-black), which contradicted that label.
}

# Ruling H: the corpus's 13 accent families collapse onto the 6 the design
# system documents. Each stray folds into the canonical family that carries
# the same DESIGN.md meaning; entries are generated the same way as the
# canonical ones (same step->role collapse) so the alias table and the
# generator can never drift apart. The *_UTIL name is what's found in HTML;
# the *_CSS name is the token family that actually has CSS variables +
# Tailwind aliases (rose/sky/amber/emerald/purple/teal) — strays have
# neither, so every stray entry's value must resolve to a canonical name,
# never to its own.
STRAY_ALIASES = {
    "violet": "purple", "indigo": "purple", "fuchsia": "purple",
    "blue": "sky",
    "red": "rose",
    "green": "emerald",
    "orange": "amber",
}
_ACCENT_FAMILIES = [(name, name) for name in ACCENT_NAMES] + sorted(STRAY_ALIASES.items())

# Fix round 1 / Important (defect 4): the step->role table was not
# property-aware enough — it used ONE table for bg-/text-/border-/divide-
# alike, and it lumped steps 500/600 in with a "dot" role regardless of
# which property carried them. Two real defects came from that:
#
#  1. `text-{accent}-{500,600}` -> `dot`. These are FOREGROUND text (8 links
#     and ticket IDs in ezrd-2008/2019/2325), not decorative marks — `dot`'s
#     hue was picked to read as a small bright bullet, not as body-weight
#     text, and measured 4.10:1 on surface / 3.74:1 on page in the affected
#     pages, down from the `text` role's 5.17:1+. Foreground text- (and
#     border-, and divide-) at step 500+ now always resolves to the `text`
#     role, matching what 700+ already did — merging the two bands rather
#     than keeping a 500/600 special case.
#  2. `bg-{accent}-200` -> `border`, used as a tinted FILL with accent text
#     on top (export-student-buses-eks/index.html:692 and :700), measured
#     4.18:1 / 4.24:1. Verified via tokens.contrast() that `text`-on-`border`
#     fails AA somewhere in EVERY one of the 6 canonical accents in at least
#     one theme (light rose 4.24, dark emerald 4.18, dark amber 4.38 among
#     them) — `border`'s hex was picked to be a subtle 1-2px outline shade,
#     never a text-bearing fill. So `bg-` now never targets the `border`
#     role at all: every low step (50/100/200/300/400) that used to split
#     fill/border under the shared table becomes `fill`. 300/400 have no
#     bg- call sites in the corpus today, but the same contrast problem
#     would apply the moment one appeared, so the table closes the gap
#     rather than patching the one instance the review happened to find.
#
# bg- keeps its own step table for this reason; text-/border-/divide- share
# a second one, since none of the above changes what those three need.
_ROLE_BY_STEP_TEXTLIKE = {  # text-, border-, divide-
    "50": "fill", "100": "fill",
    "200": "border", "300": "border", "400": "border",
    "500": "text", "600": "text", "700": "text", "800": "text", "900": "text", "950": "text",
}
_ROLE_BY_STEP_BG = {  # bg- only: never "border" (see above); 500+ handled below
    "50": "fill", "100": "fill", "200": "fill", "300": "fill", "400": "fill",
}
# Fix round 1 / Important (defect 3): `bg-{accent}-{500..950}` unconditionally
# became `solid` — right for the 3 real `bg-{accent}-{step} text-white`
# badges, wrong for the 66 bare `w-2.5 h-2.5 rounded-full` decorative dots
# that also live at those steps, which don't carry white (or any) text and
# measured 2.02-2.81:1 against page/surface in dark theme where `solid`
# (theme-invariant, pinned to the light-theme dark hex) reads as barely-there
# on a dark page. `solid` is now applied contextually in `migrate()`, keyed
# off whether `text-white` appears in the *same* class attribute — that is
# what the 3 real badges look like and what none of the 66 dots look like.
# Everything else at these steps falls through to `dot`, which clears
# 3:1 against page/surface/surface_2 in both themes for every accent.
_BG_DOT_OR_SOLID_STEPS = ("500", "600", "700", "800", "900", "950")
# {bg-{util}-{step}: bg-{css}-solid} — the upgrade migrate() applies only
# when text-white is present in the same class="..." attribute.
_BG_SOLID_UPGRADE = {}

for _util_name, _css_name in _ACCENT_FAMILIES:
    for _prefix in ("text", "border", "divide"):
        for _step, _role in _ROLE_BY_STEP_TEXTLIKE.items():
            MAP[f"{_prefix}-{_util_name}-{_step}"] = f"{_prefix}-{_css_name}-{_role}"
    for _step, _role in _ROLE_BY_STEP_BG.items():
        MAP[f"bg-{_util_name}-{_step}"] = f"bg-{_css_name}-{_role}"
    for _step in _BG_DOT_OR_SOLID_STEPS:
        # MAP's own entry is the default (no text-white sibling): `dot`.
        MAP[f"bg-{_util_name}-{_step}"] = f"bg-{_css_name}-dot"
        _BG_SOLID_UPGRADE[f"bg-{_util_name}-{_step}"] = f"bg-{_css_name}-solid"


_CLASS_ATTR = re.compile(r'class="([^"]*)"')
_TEXT_WHITE_TOKEN = re.compile(r"(?<![\w-])text-white(?![\w-])")


def _upgrade_bg_solid(html, path):
    """Context-aware pass: within one class="..." attribute, upgrade the
    `dot`-role bg-{accent}-{500+} utilities MAP defaults to back to `solid`
    when `text-white` is also present in that same attribute (a real white-
    on-solid badge). Everything else is left for MAP's normal substitution
    pass to turn into `dot`. Must run before that pass, on the literal
    Tailwind utility strings — once MAP has substituted `bg-{accent}-dot`
    in, the original step number is gone and this could no longer tell a
    dot from a to-be-upgraded solid.
    """
    def repl(m):
        value = m.group(1)
        if not _TEXT_WHITE_TOKEN.search(value):
            return m.group(0)
        tokens = value.split(" ")
        for i, tok in enumerate(tokens):
            if tok in _BG_SOLID_UPGRADE and not (path in EXEMPT_DARK and tok in SKIP_IN_EXEMPT):
                tokens[i] = _BG_SOLID_UPGRADE[tok]
        return f'class="{" ".join(tokens)}"'
    return _CLASS_ATTR.sub(repl, html)


def migrate(html, path):
    found = set(COLOUR_UTIL.findall(html))
    unmapped = sorted(u for u in found if u not in MAP
                      and not (path in EXEMPT_DARK and u in SKIP_IN_EXEMPT))
    if unmapped:
        raise SystemExit(f"  ! {path}: unmapped utilities, refusing to guess: {unmapped}")
    html = _upgrade_bg_solid(html, path)
    for util, repl in sorted(MAP.items(), key=lambda kv: -len(kv[0])):
        if path in EXEMPT_DARK and util in SKIP_IN_EXEMPT:
            continue
        html = re.sub(rf"\b{re.escape(util)}\b", repl, html)
    return html


def main():
    args = sys.argv[1:]
    files = args or sorted(glob.glob("*/*.html") + glob.glob("index.html"))
    changed = 0
    for f in files:
        html = open(f, encoding="utf-8").read()
        out = migrate(html, f)
        if out != html:
            open(f, "w", encoding="utf-8").write(out)
            changed += 1
            print(f"  + {f}")
    print(f"migrated {changed} file(s)")


if __name__ == "__main__":
    main()
