#!/usr/bin/env python3
"""Assert every report page is on the token layer.

Run from the repo root, either over the whole corpus or over named pages:

    python3 tools/check_theme.py                       # every report page
    python3 tools/check_theme.py ezrd-1462/index.html  # just this one

Fails loudly on anything it was not taught, rather than guessing — an unmapped
colour step is a migration bug, not something to pass through silently.
"""
import glob, os, re, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from theme_block import MARKER, TOGGLE_HTML

# The 7 already-dark code panels. These are NOT inverted; they use --code-panel-*.
EXEMPT_DARK = {
    "export-student-buses-eks/index.html",
    "export-student-buses-eks/export-student-buses-flow.html",
    "ezrd-2008/index.html",
    "ezrd-2019/index.html",
}

COLOUR_UTIL = re.compile(
    r"\b(?:bg|text|border|divide|ring|accent|placeholder|from|to)-"
    r"(?:slate|gray|zinc|neutral|stone|rose|red|sky|blue|amber|yellow|emerald|green|purple|violet|teal|indigo|"
    r"orange|fuchsia|pink|lime|cyan)-"
    r"\d{2,3}\b|\bbg-white\b"
)
OLD_RADII = re.compile(r"\brounded-(?:2xl|xl)\b")

# Every artifact the theme block puts on a page, each required EXACTLY once.
#
# The old single `MARKER in html` test could not tell "fully themed" from "one
# orphaned artifact left behind by a partial strip": MARKER ("data-report-theme")
# is an unanchored substring that also matches inside data-report-theme-boot,
# -toggle and -tw, so a page stripped of its style block, its Tailwind aliases
# and its slider still contained the substring and still passed — with zero
# custom properties and zero token-backed utilities actually defined. Asserting
# each artifact separately, and asserting a count of exactly one, catches both
# the orphan state and a double injection.
#
# The toggle's literal is TOGGLE_HTML's own opening tag rather than a hand-typed
# prefix so it cannot drift from the emitter — and because the shorter
# `class="theme-switch` prefix also matches the knob's `class="theme-switch-knob"`
# on the very next line, which would make a correctly-themed page read as two.
REQUIRED_ARTIFACTS = [
    ("the theme style block", f"<style {MARKER}>"),
    ("the no-flash boot script", "<script data-report-theme-boot>"),
    ("the Tailwind token aliases", "<script data-report-theme-tw>"),
    ("the section slider", "<script data-report-slider>"),
    ("the theme toggle button", TOGGLE_HTML.splitlines()[0]),
]


def pages():
    return sorted(glob.glob("*/*.html") + glob.glob("index.html"))


def main():
    files = sys.argv[1:] or pages()
    failures = []
    for f in files:
        if not os.path.isfile(f):
            failures.append((f, "no such file"))
            continue
        html = open(f, encoding="utf-8").read()

        for label, literal in REQUIRED_ARTIFACTS:
            n = html.count(literal)
            if n != 1:
                failures.append((f, f"{label}: expected exactly 1, found {n}"))

        leftovers = COLOUR_UTIL.findall(html)
        if leftovers and f not in EXEMPT_DARK:
            uniq = sorted(set(leftovers))
            failures.append((f, f"{len(leftovers)} raw colour utilities remain: {uniq[:6]}"))

        old = OLD_RADII.findall(html)
        if old:
            failures.append((f, f"{len(old)} off-scale radii remain: {sorted(set(old))}"))

    for f, msg in failures:
        print(f"  FAIL {f}: {msg}")
    print(f"\n{len(files)} page(s) checked, {len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
