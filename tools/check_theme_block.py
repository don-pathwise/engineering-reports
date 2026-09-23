#!/usr/bin/env python3
"""Assert the emitted theme block is well-formed before any page receives it."""
import sys
from theme_block import HEAD_BOOT, style_block, TOGGLE_HTML, MARKER

def main():
    css = style_block()
    checks = [
        ("marker present", MARKER in css),
        ("light :root defined", ":root {" in css),
        ("dark override defined", '[data-theme="dark"]' in css),
        ("system default honoured", "prefers-color-scheme: dark" in css),
        ("print forces light", "@media print" in css and "--page:" in css.split("@media print")[1]),
        ("code panel stays dark both themes", "--code-panel-bg" in css),
        ("boot script sets data-theme", "data-theme" in HEAD_BOOT),
        ("boot script guards storage", "try" in HEAD_BOOT and "catch" in HEAD_BOOT),
        ("toggle is a real switch", 'role="switch"' in TOGGLE_HTML),
        ("toggle is labelled", "aria-label" in TOGGLE_HTML),
        ("toggle drops out of print", "no-print" in TOGGLE_HTML),
        ("balanced braces", css.count("{") == css.count("}")),
    ]
    bad = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  {'ok  ' if ok else 'FAIL'} {name}")
    if bad:
        print(f"\n{len(bad)} check(s) failed")
        return 1
    print("theme block well-formed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
