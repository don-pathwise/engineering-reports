#!/usr/bin/env python3
"""Assert every foreground/background pair in the token set clears WCAG AA.

Exit 0 and print the table when all pairs pass; exit 1 listing failures otherwise.
Body text needs 4.5:1; large text (>=24px) needs 3:1.
"""
import sys
from tokens import LIGHT_HEX, DARK_HEX, ACCENTS_HEX, contrast

BODY_MIN, LARGE_MIN = 4.5, 3.0


def pairs():
    """(label, foreground_hex, background_hex, minimum_ratio) for every pair that matters."""
    for theme, t in (("light", LIGHT_HEX), ("dark", DARK_HEX)):
        for fg in ("ink", "ink_body", "ink_mute"):
            for bg in ("page", "surface", "surface_2"):
                minimum = LARGE_MIN if fg == "ink" else BODY_MIN
                yield (f"{theme}/{fg}-on-{bg}", t[fg], t[bg], minimum)
        yield (f"{theme}/chip_fg-on-chip_bg", t["chip_fg"], t["chip_bg"], BODY_MIN)
        for name, roles in ACCENTS_HEX[theme].items():
            yield (f"{theme}/{name}.text-on-fill", roles["text"], roles["fill"], BODY_MIN)
            yield (f"{theme}/{name}.text-on-surface", roles["text"], t["surface"], BODY_MIN)


def main():
    failures = []
    lowest = (None, 99.0)
    for label, fg, bg, minimum in pairs():
        ratio = contrast(fg, bg)
        if ratio < lowest[1]:
            lowest = (label, ratio)
        mark = "ok " if ratio >= minimum else "FAIL"
        print(f"  {mark} {label:<38} {ratio:5.2f}:1  (min {minimum})")
        if ratio < minimum:
            failures.append((label, ratio, minimum))
    print(f"\nlowest: {lowest[0]} at {lowest[1]:.2f}:1")
    if failures:
        print(f"\n{len(failures)} pair(s) below AA:")
        for label, ratio, minimum in failures:
            print(f"  - {label}: {ratio:.2f}:1 < {minimum}")
        return 1
    print("all pairs clear AA")
    return 0


if __name__ == "__main__":
    sys.exit(main())
