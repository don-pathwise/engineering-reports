#!/usr/bin/env python3
"""Rewrite Tailwind colour utilities onto the token layer.

Hard-fails on any utility it was not taught. An unmapped step is a migration
bug — silently passing it through is how half a page ends up off-theme.
"""
import glob, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_theme import EXEMPT_DARK, COLOUR_UTIL

# The already-dark code panels keep their own tokens, applied by hand in Task 6.
SKIP_IN_EXEMPT = {"bg-slate-900", "bg-slate-950", "text-slate-50", "text-slate-100"}

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
}

# Accents: -50/-100 -> fill, -200/-300/-400 -> border, -500/-600 -> dot, -700/-800/-900/-950 -> text
_ROLE_BY_STEP = {
    "50": "fill", "100": "fill",
    "200": "border", "300": "border", "400": "border",
    "500": "dot", "600": "dot",
    "700": "text", "800": "text", "900": "text", "950": "text",
}
for _name in ACCENT_NAMES:
    for _step, _role in _ROLE_BY_STEP.items():
        for _prefix in ("bg", "text", "border"):
            MAP[f"{_prefix}-{_name}-{_step}"] = f"{_prefix}-{_name}-{_role}"


def migrate(html, path):
    found = set(COLOUR_UTIL.findall(html))
    unmapped = sorted(u for u in found if u not in MAP
                      and not (path in EXEMPT_DARK and u in SKIP_IN_EXEMPT))
    if unmapped:
        raise SystemExit(f"  ! {path}: unmapped utilities, refusing to guess: {unmapped}")
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
