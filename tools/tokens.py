#!/usr/bin/env python3
"""Single source of truth for the report design system's colour tokens.

Hex values are the approved Direction B palette. oklch is derived, never typed:
`LIGHT`/`DARK`/`ACCENTS` hold oklch strings for CSS, `*_HEX` hold the source hex
for contrast maths. Dark neutrals anchor to the ladder documented in
~/Code/eng-local-docs/DESIGN.md (sunken .140, raised .212, hover .245, line .300,
ink .950/.800/.665).
"""
import math

# ---------------------------------------------------------------- conversion

def _srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _parse(hex_str):
    h = hex_str.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def srgb_to_oklch(hex_str):
    """'#15171d' -> 'oklch(0.212 0.013 265.4)'."""
    r, g, b = (_srgb_to_linear(v) for v in _parse(hex_str))
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s_ = (math.copysign(abs(v) ** (1 / 3), v) for v in (l, m, s))
    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    bb = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    C = math.sqrt(a * a + bb * bb)
    H = math.degrees(math.atan2(bb, a)) % 360
    return f"oklch({L:.3f} {C:.3f} {H:.1f})"


def relative_luminance(hex_str):
    r, g, b = (_srgb_to_linear(v) for v in _parse(hex_str))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(hex_a, hex_b):
    la, lb = relative_luminance(hex_a), relative_luminance(hex_b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


# ---------------------------------------------------------------- neutrals

LIGHT_HEX = {
    "page":      "#f1f5f9",   # slate-100, unchanged from today
    "surface":   "#ffffff",
    "surface_2": "#f8fafc",
    "border":    "#cbd5e1",
    "hairline":  "#e2e8f0",
    "ink":       "#020617",
    "ink_body":  "#334155",
    "ink_mute":  "#475569",
    "chip_bg":   "#e2e8f0",
    "chip_fg":   "#0f172a",
}

# Direction B, snapped to the eng-local-docs oklch ladder. The brief's starting
# hex derived to L values 0.017-0.042 above their ladder steps (verified via
# check_contrast's Step 5 companion check); each was nudged toward black in
# OKLab space (same a/b, L set to the ladder target) until its derived L came
# back within 0.015 of the step, per the task's Step 5 tolerance ruling.
# ink_mute needed no nudge — it derived exactly on its .665 floor already.
DARK_HEX = {
    "page":      "#07090d",   # ladder sunken  .140 (derives 0.139)
    "surface":   "#16191f",   # ladder raised  .212 (derives 0.213)
    "surface_2": "#1c2029",   # ladder hover   .245 (derives 0.244)
    "border":    "#292e38",   # ladder line    .300 (derives 0.301)
    "hairline":  "#262a33",   # ladder line-soft
    "ink":       "#eceef2",   # ladder ink     .950 (derives 0.949)
    "ink_body":  "#b7beca",   # ladder ink-body .800 (derives 0.800)
    "ink_mute":  "#8c94a2",   # ladder ink-mute .665 — the floor
    "chip_bg":   "#272b34",
    "chip_fg":   "#dce2ea",
}

# Code panels that are already dark in the source stay dark in BOTH themes.
CODE_PANEL_HEX = {"light": {"bg": "#0f172a", "fg": "#f8fafc"},
                  "dark":  {"bg": "#0b0d11", "fg": "#e8edf5"}}

BORDER_W = {"light": "2px", "dark": "1px"}

# ---------------------------------------------------------------- accents

# One hue per meaning; roles share lightness/chroma across hues so no accent
# shouts louder than another.
_HUES = {"rose": 15, "sky": 240, "amber": 75, "emerald": 160, "purple": 300, "teal": 195}

# `solid` is a fifth accent role: a solid badge background meant to carry white
# text. It is THEME-INVARIANT — pinned to the light theme's `text` hex (the
# darkest, most saturated step in the palette) in both light and dark, so a
# `bg-{accent}-solid text-white` badge stays legible whichever theme is active.
# See check_contrast.py's white-on-solid pairs for the verified ratios.
_SOLID_HEX = {
    "rose": "#9f1239", "sky": "#075985", "amber": "#92400e",
    "emerald": "#065f46", "purple": "#6b21a8", "teal": "#115e59",
}

ACCENTS_HEX = {
    "light": {
        "rose":    {"fill": "#ffe4e6", "border": "#fda4af", "text": "#9f1239", "dot": "#e11d48", "solid": _SOLID_HEX["rose"]},
        "sky":     {"fill": "#e0f2fe", "border": "#7dd3fc", "text": "#075985", "dot": "#0284c7", "solid": _SOLID_HEX["sky"]},
        # dot was amber-600 (#d97706) until Task 6 fix round 1: the extended
        # check_contrast.py found bare/standalone amber dots (the "In
        # flight" status-pill dot at ezrd-1462/index.html:306, and any dot
        # sitting on raw --page) at 2.86-2.91:1, under the 3:1 non-text
        # floor, because amber's sRGB luminance is high relative to its
        # OKLCH lightness even at step 600. amber-700 clears every neutral
        # and the accent's own fill at 4.5:1+ in light theme while staying
        # visibly distinct from `text`/`solid` (both amber-800).
        "amber":   {"fill": "#fef3c7", "border": "#fcd34d", "text": "#92400e", "dot": "#b45309", "solid": _SOLID_HEX["amber"]},
        "emerald": {"fill": "#d1fae5", "border": "#6ee7b7", "text": "#065f46", "dot": "#059669", "solid": _SOLID_HEX["emerald"]},
        "purple":  {"fill": "#f3e8ff", "border": "#d8b4fe", "text": "#6b21a8", "dot": "#9333ea", "solid": _SOLID_HEX["purple"]},
        "teal":    {"fill": "#ccfbf1", "border": "#5eead4", "text": "#115e59", "dot": "#0d9488", "solid": _SOLID_HEX["teal"]},
    },
    "dark": {
        "rose":    {"fill": "#2e1219", "border": "#7c2d43", "text": "#fda4af", "dot": "#f43f5e", "solid": _SOLID_HEX["rose"]},
        "sky":     {"fill": "#0d2233", "border": "#1c5878", "text": "#7dd3fc", "dot": "#38bdf8", "solid": _SOLID_HEX["sky"]},
        "amber":   {"fill": "#2a1e0c", "border": "#7a4c15", "text": "#fbbf24", "dot": "#f59e0b", "solid": _SOLID_HEX["amber"]},
        "emerald": {"fill": "#0b2a20", "border": "#166c50", "text": "#6ee7b7", "dot": "#10b981", "solid": _SOLID_HEX["emerald"]},
        "purple":  {"fill": "#231540", "border": "#5b2fae", "text": "#c4b5fd", "dot": "#a78bfa", "solid": _SOLID_HEX["purple"]},
        "teal":    {"fill": "#0a2a28", "border": "#12655e", "text": "#5eead4", "dot": "#14b8a6", "solid": _SOLID_HEX["teal"]},
    },
}

# ---------------------------------------------------------------- oklch views

LIGHT = {k: srgb_to_oklch(v) for k, v in LIGHT_HEX.items()}
DARK = {k: srgb_to_oklch(v) for k, v in DARK_HEX.items()}
ACCENTS = {theme: {name: {role: srgb_to_oklch(h) for role, h in roles.items()}
                   for name, roles in by_name.items()}
           for theme, by_name in ACCENTS_HEX.items()}

RADII = {"card": "8px", "panel": "6px", "code": "8px", "pre": "5px", "chip": "3px"}


if __name__ == "__main__":
    for theme, t in (("light", LIGHT), ("dark", DARK)):
        print(f"--- {theme} ---")
        for k, v in t.items():
            print(f"  --{k.replace('_', '-')}: {v};")
