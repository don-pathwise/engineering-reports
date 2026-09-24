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
from theme_block import MARKER, TOGGLE_HTML, style_block

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


# Every custom property the generated token block defines. A page's own <style>
# must not declare any of these.
#
# The token block is injected at the END of <head>, after the page's own
# <style>, so at equal :root specificity document order hands the win to the
# token layer. Three pages (the GitHub-dark ezrd-976 / ezrd-1276 pair) defined
# their own :root --surface and --border for a dark card look; the token layer
# silently overrode both while their --bg/--text survived, so in LIGHT theme
# the body stayed dark and every card turned white -- 1.18:1, 33 unreadable
# elements on ezrd-976. Nothing caught it because both files were, by every
# other measure, correctly themed.
EMITTED_PROPS = frozenset(re.findall(r"--[a-z0-9-]+(?=\s*:)", style_block()))

_STYLE_RE = re.compile(r"<style([^>]*)>(.*?)</style>", re.S)
_GENERATED = ("data-report-theme", "data-report-enhanced")
_CUSTOM_PROP = re.compile(r"(--[a-zA-Z0-9_-]+)\s*:")


def page_styles(html):
    """The page's OWN <style> bodies -- everything the generators did not emit."""
    return [body for attrs, body in _STYLE_RE.findall(html)
            if not any(g in attrs for g in _GENERATED)]


# ---------------------------------------------------------- hardcoded colours
#
# The token layer only ever touched Tailwind utility CLASSES. COLOUR_UTIL above
# matches a class name; a CSS rule inside a page's own <style> is invisible to
# it, so 74 hardcoded-colour rules across 20 pages survived the migration --
# `code.k { background: rgb(226 232 240); color: rgb(15 23 42) }` on 16 of them,
# 632 inline-code chips rendering as light islands on a dark page. This check
# closes that blind spot.
#
# Deliberately NOT flagged:
#  - box-shadow / text-shadow: a black or ink shadow reads correctly against
#    both a light and a dark surface; these are depth, not colour.
#  - anything inside a var() expression, so the boilerplate's documented
#    `var(--chip-bg, rgb(226 232 240))` fallback form stays legal. The fallback
#    only applies in the window between writing a page and running the
#    injector, which is exactly what it is for.
#  - @media print blocks: print is light by definition, and the token block's
#    own print override pins the light values.
#  - any rule carrying a `theme-invariant` comment in its body or in the
#    comment directly above it. That is the escape hatch for a colour that is
#    genuinely fixed -- syntax highlighting inside an always-dark code panel,
#    white text on a `solid` accent badge -- and it forces the author to say so
#    in the file rather than leaving the next reader to guess.
#  - THEME_INVARIANT_PAGES below, whole pages that are not on the token layer
#    at all.
THEME_INVARIANT_PAGES = {
    # Three self-contained GitHub-dark pages that predate the token layer and
    # render identically in both themes by design. They carry their own private
    # --gh-* palette; nothing on them resolves against a token.
    "ezrd-976/index.html",
    "ezrd-1276/index.html",
    "ezrd-1276/post-save-waterfall.html",
}

_THEME_PROP = re.compile(
    r"^\s*(?:color|background|background-color|background-image|border|border-color"
    r"|border-(?:top|right|bottom|left)(?:-color)?|outline|outline-color|fill|stroke"
    r"|text-decoration-color|caret-color|accent-color|column-rule-color)\s*:", re.I)
_NAMED = ("white|black|silver|gray|grey|red|green|blue|yellow|orange|purple|pink|brown|cyan"
          "|magenta|lime|navy|teal|olive|maroon|aqua|fuchsia|gold|ivory|khaki|salmon|tan"
          "|violet|indigo|crimson|coral|beige|azure|plum|orchid|tomato|wheat|snow|linen")
_COLOUR_LITERAL = re.compile(
    r"#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(|\bhwb\(|\blab\(|\blch\(|\bcolor\("
    r"|(?<![\w-])(?:" + _NAMED + r")(?![\w-])", re.I)
_RULE = re.compile(r"([^{}]*)\{([^{}]*)\}", re.S)
_PRINT_AT = re.compile(r"@media[^{]*\bprint\b[^{]*\{", re.I)


def _strip_var_calls(text):
    """Remove every var(...) expression, braces balanced, so a documented
    `var(--chip-bg, rgb(226 232 240))` fallback is not read as a hardcoded
    colour."""
    out, i = [], 0
    while True:
        j = text.find("var(", i)
        if j == -1:
            out.append(text[i:])
            return "".join(out)
        out.append(text[i:j])
        depth, k = 1, j + 4
        while k < len(text) and depth:
            if text[k] == "(":
                depth += 1
            elif text[k] == ")":
                depth -= 1
            k += 1
        i = k


def _print_spans(css):
    """(start, end) of every @media print block, so rules inside are skipped."""
    spans = []
    for m in _PRINT_AT.finditer(css):
        depth, i = 1, m.end()
        while i < len(css) and depth:
            if css[i] == "{":
                depth += 1
            elif css[i] == "}":
                depth -= 1
            i += 1
        spans.append((m.start(), i))
    return spans


def hardcoded_colours(css):
    """Theme-dependent declarations in a page's own CSS that name a colour
    outright. Returns a list of the offending declaration texts."""
    bad, prev_end = [], 0
    spans = _print_spans(css)
    for m in _RULE.finditer(css):
        preamble, decls = m.group(1), m.group(2)
        if any(a <= m.start() < b for a, b in spans):
            prev_end = m.end()
            continue
        # `theme-invariant` in this rule's body, or in the comment directly
        # above it -- the preamble runs from the previous rule's closing brace
        # to this selector's opening one, so a comment on the line above lands
        # here and covers exactly the rule it introduces.
        prev_end = m.end()
        if "theme-invariant" in decls or "theme-invariant" in preamble:
            continue
        if preamble.strip().startswith("@"):      # at-rule prelude, not a selector
            continue
        for decl in _strip_var_calls(decls).split(";"):
            if _THEME_PROP.match(decl) and _COLOUR_LITERAL.search(decl):
                bad.append(" ".join(decl.split()))
    return bad


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

        own_css = "\n".join(page_styles(html))
        collisions = sorted(set(_CUSTOM_PROP.findall(own_css)) & EMITTED_PROPS)
        if collisions:
            failures.append(
                (f, f"private custom propert{'y' if len(collisions) == 1 else 'ies'} "
                    f"collide with the token layer: {collisions} -- rename them "
                    f"(the token block is injected later in <head> and wins)"))

        if f not in THEME_INVARIANT_PAGES:
            hard = hardcoded_colours(own_css)
            if hard:
                failures.append(
                    (f, f"{len(hard)} hardcoded colour(s) in the page's own <style>: "
                        f"{hard[:4]} -- route them through the token layer, or mark the "
                        f"rule /* theme-invariant */ and say why"))

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
