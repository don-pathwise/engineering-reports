#!/usr/bin/env python3
"""Assert every report page is on the token layer. Run from the repo root.

Fails loudly on anything it was not taught, rather than guessing — an unmapped
colour step is a migration bug, not something to pass through silently.
"""
import glob, os, re, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from theme_block import MARKER

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


def pages():
    return sorted(glob.glob("*/*.html") + glob.glob("index.html"))


def main():
    failures = []
    for f in pages():
        html = open(f, encoding="utf-8").read()

        if MARKER not in html:
            failures.append((f, "missing the theme block"))

        if "data-report-theme-boot" not in html:
            failures.append((f, "missing the no-flash boot script in <head>"))

        leftovers = COLOUR_UTIL.findall(html)
        if leftovers and f not in EXEMPT_DARK:
            uniq = sorted(set(leftovers))
            failures.append((f, f"{len(leftovers)} raw colour utilities remain: {uniq[:6]}"))

        old = OLD_RADII.findall(html)
        if old:
            failures.append((f, f"{len(old)} off-scale radii remain: {sorted(set(old))}"))

    for f, msg in failures:
        print(f"  FAIL {f}: {msg}")
    print(f"\n{len(pages())} page(s) checked, {len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
