# Dark Mode — Reports & Token Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the 23 published report pages a dark theme and a tightened radius scale, driven by a single oklch token layer that the other three surfaces can later consume.

**Architecture:** One Python module (`tools/tokens.py`) is the source of truth: it derives oklch values from the approved hex, emits the CSS token block for both themes, and is imported by every other script so no value is ever typed twice. A checker (`tools/check_theme.py`) asserts the invariants and is the test harness this repo otherwise lacks. A migration script rewrites colour utilities and radii across the 23 files, hard-failing on anything it was not taught. The theme block ships inside the existing shared enhancement block, bumped to v2.

**Tech Stack:** Python 3 (stdlib only), Tailwind CSS via CDN, vanilla JS. No build step, no package manager, no dependencies.

**Spec:** `docs/superpowers/specs/2026-09-23-dark-mode-design.md`

## Global Constraints

- **Plan 1 scope is surface 1 only** — the 23 HTML files in this repo plus `~/.claude/skills/engineering-report-page/SKILL.md`. Surfaces 2–4 (chew-ticket template, board shell, board renderers) are Plan 2 and must not be touched here.
- **No dependencies.** Python stdlib only; no `pip install`. No npm, no build step. Pages stay single-file and CDN-only.
- **Colour notation is oklch**, derived by script from the approved hex — never hand-typed. Dark neutrals anchor to the ladder in `~/Code/eng-local-docs/DESIGN.md`: sunken `0.140`, raised `0.212`, row-hover `0.245`, line `0.300`, ink `0.950` / `0.800` / `0.665`.
- **`--ink-mute` is the contrast floor.** Nothing lighter-weight than it may carry body text, in either theme.
- **WCAG AA everywhere:** body text ≥4.5:1, large text (≥24px) ≥3:1. Verified by script, not by eye.
- **Six accents stay six:** `rose`, `sky`, `amber`, `emerald`, `purple`, `teal`. Each keeps the fixed meaning in `DESIGN.md`. The three-accent narrowing in `eng-local-docs` was a property of that document type, not of this system.
- **Radius scale:** cards/callouts 8px, panels 6px, code container 8px, `<pre>` 5px, inline code 3px. Pills, dots, and the theme switch stay `999px`.
- **7 already-dark code panels across 4 files must not be inverted** — `export-student-buses-eks/index.html`, `export-student-buses-eks/export-student-buses-flow.html`, `ezrd-2008/index.html`, `ezrd-2019/index.html`. They get `--code-panel-bg` / `--code-panel-fg`, which stay dark in both themes.
- **Print is always light**, regardless of `data-theme`.
- **Scripts are idempotent.** Every one can be re-run without double-applying; the existing `apply-report-enhancements.py` guards on `data-report-enhanced` and that pattern continues.
- **Commit after every task.** This repo is public; do not commit anything but the files each task names.

---

### Task 1: Token source of truth

Derives oklch from the approved hex so no value is hand-typed, and proves the result clears AA before anything consumes it.

**Files:**
- Create: `tools/tokens.py`
- Create: `tools/check_contrast.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `tools.tokens.LIGHT` and `tools.tokens.DARK`, each a `dict[str, str]` mapping token name (without the leading `--`) to an `oklch(...)` string; `tools.tokens.ACCENTS`, a `dict[str, dict[str, str]]` keyed by accent name then by role (`fill`, `border`, `text`, `dot`); `tools.tokens.srgb_to_oklch(hex: str) -> str`; `tools.tokens.relative_luminance(hex: str) -> float`; `tools.tokens.contrast(hex_a: str, hex_b: str) -> float`.

- [ ] **Step 1: Write the failing test**

Create `tools/check_contrast.py`:

```python
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
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd tools && python3 check_contrast.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'tokens'`

- [ ] **Step 3: Write the token module**

Create `tools/tokens.py`:

```python
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

# Direction B, snapped to the eng-local-docs oklch ladder. This lightens `page`
# and `surface` slightly versus the mockup's #0a0b0f/#15171d; the ladder's steps
# are the verified ones, so they win. Task 6 re-checks the result on real pages.
DARK_HEX = {
    "page":      "#101216",   # ladder sunken  .140
    "surface":   "#1c1f26",   # ladder raised  .212
    "surface_2": "#22262f",   # ladder hover   .245
    "border":    "#2e333d",   # ladder line    .300
    "hairline":  "#262a33",   # ladder line-soft
    "ink":       "#f2f4f8",   # ladder ink     .950
    "ink_body":  "#bfc6d2",   # ladder ink-body .800
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

ACCENTS_HEX = {
    "light": {
        "rose":    {"fill": "#ffe4e6", "border": "#fda4af", "text": "#9f1239", "dot": "#e11d48"},
        "sky":     {"fill": "#e0f2fe", "border": "#7dd3fc", "text": "#075985", "dot": "#0284c7"},
        "amber":   {"fill": "#fef3c7", "border": "#fcd34d", "text": "#92400e", "dot": "#d97706"},
        "emerald": {"fill": "#d1fae5", "border": "#6ee7b7", "text": "#065f46", "dot": "#059669"},
        "purple":  {"fill": "#f3e8ff", "border": "#d8b4fe", "text": "#6b21a8", "dot": "#9333ea"},
        "teal":    {"fill": "#ccfbf1", "border": "#5eead4", "text": "#115e59", "dot": "#0d9488"},
    },
    "dark": {
        "rose":    {"fill": "#2e1219", "border": "#7c2d43", "text": "#fda4af", "dot": "#f43f5e"},
        "sky":     {"fill": "#0d2233", "border": "#1c5878", "text": "#7dd3fc", "dot": "#38bdf8"},
        "amber":   {"fill": "#2a1e0c", "border": "#7a4c15", "text": "#fbbf24", "dot": "#f59e0b"},
        "emerald": {"fill": "#0b2a20", "border": "#166c50", "text": "#6ee7b7", "dot": "#10b981"},
        "purple":  {"fill": "#231540", "border": "#5b2fae", "text": "#c4b5fd", "dot": "#a78bfa"},
        "teal":    {"fill": "#0a2a28", "border": "#12655e", "text": "#5eead4", "dot": "#14b8a6"},
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
```

- [ ] **Step 4: Run the contrast check to verify it passes**

Run: `cd tools && python3 check_contrast.py`
Expected: PASS — `all pairs clear AA`, every row `ok`, and the printed `lowest:` line at or above 4.5:1.

If any pair fails, adjust only the failing hex in `tokens.py` (darken an accent `text` on light, lighten it on dark) and re-run until clean. Do not lower the thresholds.

- [ ] **Step 5: Eyeball the derived oklch**

Run: `cd tools && python3 tokens.py`
Expected: two blocks of `--token: oklch(L C H);` lines. Confirm the dark ladder reads `page` ≈ `0.140`, `surface` ≈ `0.212`, `surface-2` ≈ `0.245`, `border` ≈ `0.300`, `ink` ≈ `0.950`, `ink-body` ≈ `0.800`, `ink-mute` ≈ `0.665`. If a value is more than `0.015` off its ladder step, nudge the hex and re-run both scripts.

- [ ] **Step 6: Commit**

```bash
git add tools/tokens.py tools/check_contrast.py
git commit -m "feat(tokens): oklch token source of truth with AA verification"
```

---

### Task 2: The theme block and its no-flash boot

The CSS both themes live in, plus the inline script that sets `data-theme` before first paint.

**Files:**
- Create: `tools/theme_block.py`

**Interfaces:**
- Consumes: `tools.tokens.LIGHT`, `DARK`, `ACCENTS`, `CODE_PANEL_HEX`, `BORDER_W`, `RADII`.
- Produces: `tools.theme_block.HEAD_BOOT` (str — the `<script>` that must sit in `<head>`); `tools.theme_block.style_block() -> str` (the `<style data-report-theme>` element); `tools.theme_block.TOGGLE_HTML` (str — the switch markup); `tools.theme_block.MARKER` (str — `"data-report-theme"`).

- [ ] **Step 1: Write the failing test**

Append to `tools/check_contrast.py` a second entry point — create `tools/check_theme_block.py`:

```python
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
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd tools && python3 check_theme_block.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'theme_block'`

- [ ] **Step 3: Write the emitter**

Create `tools/theme_block.py`:

```python
#!/usr/bin/env python3
"""Emits the CSS token block, the no-flash boot script, and the toggle markup."""
from tokens import LIGHT, DARK, ACCENTS, CODE_PANEL_HEX, BORDER_W, RADII

MARKER = "data-report-theme"

# Must run in <head>, before the body paints, or the page flashes light first.
HEAD_BOOT = """<script data-report-theme-boot>
(function () {
  var t = null;
  try { t = localStorage.getItem('report-theme'); } catch (e) {}
  if (t !== 'light' && t !== 'dark') {
    t = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  document.documentElement.setAttribute('data-theme', t);
})();
</script>"""

TOGGLE_HTML = """<button type="button" class="theme-switch no-print" role="switch" aria-checked="false" aria-label="Dark theme" onclick="__toggleTheme(this)">
  <span class="theme-switch-knob" aria-hidden="true"></span>
</button>"""


def _vars(tokens, accents, theme):
    lines = [f"    --{k.replace('_', '-')}: {v};" for k, v in tokens.items()]
    lines.append(f"    --border-w: {BORDER_W[theme]};")
    cp = CODE_PANEL_HEX[theme]
    lines.append(f"    --code-panel-bg: {cp['bg']};")
    lines.append(f"    --code-panel-fg: {cp['fg']};")
    for name, roles in accents.items():
        for role, val in roles.items():
            lines.append(f"    --accent-{name}-{role}: {val};")
    return "\n".join(lines)


def style_block():
    light = _vars(LIGHT, ACCENTS["light"], "light")
    dark = _vars(DARK, ACCENTS["dark"], "dark")
    radii = "\n".join(f"    --radius-{k}: {v};" for k, v in RADII.items())
    return f"""<!-- report-theme v1 · oklch token layer (shared system — do not hand-edit) -->
<style {MARKER}>
  :root {{
    color-scheme: light;
{light}
{radii}
  }}
  /* System preference, only when the reader has not chosen. */
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      color-scheme: dark;
{dark}
    }}
  }}
  /* An explicit choice always wins. */
  :root[data-theme="dark"] {{
    color-scheme: dark;
{dark}
  }}
  .theme-switch {{
    position: relative; width: 60px; height: 30px; padding: 0; flex-shrink: 0;
    border-radius: 999px; cursor: pointer; background: var(--page);
    border: 1px solid var(--border);
    box-shadow: inset 0 2px 5px rgb(0 0 0 / .45), inset 0 -1px 0 rgb(255 255 255 / .04);
  }}
  .theme-switch-knob {{
    position: absolute; top: 3px; left: 3px; width: 22px; height: 22px;
    border-radius: 999px; background: var(--surface-2); border: 1px solid var(--border);
    box-shadow: inset 0 1px 0 rgb(255 255 255 / .13), 0 1px 3px rgb(0 0 0 / .5);
    transition: left .22s cubic-bezier(.4, 0, .2, 1);
  }}
  :root[data-theme="dark"] .theme-switch-knob {{ left: 35px; }}
  @media (prefers-reduced-motion: reduce) {{ .theme-switch-knob {{ transition: none; }} }}
  /* Print is light, whatever the reader chose. */
  @media print {{
    :root, :root[data-theme="dark"] {{
      color-scheme: light;
{light}
    }}
    .theme-switch {{ display: none !important; }}
  }}
</style>
<script data-report-theme-toggle>
window.__toggleTheme = function (el) {
  var next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  if (el) el.setAttribute('aria-checked', next === 'dark' ? 'true' : 'false');
  try { localStorage.setItem('report-theme', next); } catch (e) {}
};
</script>"""


if __name__ == "__main__":
    print(HEAD_BOOT)
    print(style_block())
```

- [ ] **Step 4: Run the check to verify it passes**

Run: `cd tools && python3 check_theme_block.py`
Expected: PASS — every row `ok`, `theme block well-formed`.

- [ ] **Step 5: Commit**

```bash
git add tools/theme_block.py tools/check_theme_block.py
git commit -m "feat(tokens): theme block emitter with no-flash boot and print-light override"
```

---

### Task 3: The repo checker

The test harness this repo lacks. It fails against the repo as it stands today; Tasks 4–7 make it pass.

**Files:**
- Create: `tools/check_theme.py`

**Interfaces:**
- Consumes: `tools.theme_block.MARKER`, `tools.tokens.RADII`.
- Produces: a CLI returning exit 0/1. Later tasks run `python3 tools/check_theme.py` from the repo root as their pass condition.

- [ ] **Step 1: Write the checker**

Create `tools/check_theme.py`:

```python
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
    r"(?:slate|gray|zinc|neutral|stone|rose|red|sky|blue|amber|yellow|emerald|green|purple|violet|teal|indigo)-"
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
```

- [ ] **Step 2: Run it to verify it fails against today's repo**

Run: `python3 tools/check_theme.py`
Expected: FAIL — 23 pages checked, roughly 90+ failures (every page missing the theme block and the boot script, plus raw colour utilities and `rounded-2xl`/`rounded-xl` on nearly all of them). This is the baseline the rest of the plan drives to zero.

- [ ] **Step 3: Record the baseline**

Run: `python3 tools/check_theme.py > /tmp/theme-baseline.txt 2>&1; tail -1 /tmp/theme-baseline.txt`
Expected: a line reading `23 page(s) checked, N failure(s)`. Note N — Task 7 drives it to 0.

- [ ] **Step 4: Commit**

```bash
git add tools/check_theme.py
git commit -m "test(tokens): checker asserting every page is on the token layer"
```

---

### Task 4: Enhancement block v2 — theme block plus the four backfills

The theme block ships inside the existing shared block. Four reports do not have that block at all, so they get it here.

**Files:**
- Modify: `apply-report-enhancements.py`
- Modify: `ezrd-1653-verify/index.html`, `ezrd-1949/index.html`, `ezrd-2019/index.html`, `ezrd-2325/index.html` (by script)
- Modify: all 23 pages (by script — head boot + theme block)

**Interfaces:**
- Consumes: `tools.theme_block.HEAD_BOOT`, `style_block()`, `TOGGLE_HTML`, `MARKER`.
- Produces: `apply-report-enhancements.py` gains `inject_theme(html: str) -> tuple[str, bool]`, returning the updated HTML and whether it changed.

- [ ] **Step 1: Confirm which four pages lack the block**

Run: `grep -L 'data-report-enhanced' */index.html`
Expected exactly: `ezrd-1653-verify/index.html`, `ezrd-1949/index.html`, `ezrd-2019/index.html`, `ezrd-2325/index.html`

If the list differs, stop — the repo has changed since the spec was written, and the migration's assumptions need re-checking before proceeding.

- [ ] **Step 2: Extend the script**

In `apply-report-enhancements.py`, add the import and the new function above `def targets(args):`

```python
import sys, glob, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools"))
from theme_block import HEAD_BOOT, style_block, TOGGLE_HTML, MARKER as THEME_MARKER
```

```python
def inject_theme(html):
    """Add the boot script and token block to <head>. Idempotent.

    Both go in <head>, not before </body>: the boot must set data-theme before
    the body paints, and the block carries Tailwind colour aliases that must be
    defined before the CDN evaluates.
    """
    if THEME_MARKER in html:
        return html, False
    head_end = html.find("</head>")
    if head_end == -1:
        raise ValueError("no </head>")
    html = html[:head_end] + HEAD_BOOT + "\n" + style_block() + "\n" + html[head_end:]
    return html, True
```

- [ ] **Step 3: Call it from `main()`**

In `apply-report-enhancements.py`, replace the body of the `for f in targets(args):` loop's tail. After the existing enhancement-block injection, and before the write, add the theme pass so both land in one run:

```python
    for f in targets(args):
        if not os.path.isfile(f):
            print(f"  ! missing: {f}")
            continue
        html = open(f, encoding="utf-8").read()
        touched = False

        if MARKER not in html:
            idx = html.rfind("</body>")
            if idx == -1:
                print(f"  ! no </body>: {f}")
                continue
            html = html[:idx] + BLOCK + "\n" + html[idx:]
            touched = True

        html, themed = inject_theme(html)
        touched = touched or themed

        if touched:
            open(f, "w", encoding="utf-8").write(html)
            changed.append(f)
        else:
            skipped.append(f)
```

- [ ] **Step 4: Widen the default target list to include the root index**

The root `index.html` needs the theme block too. Replace `targets`:

```python
def targets(args):
    if args:
        return args
    return sorted(glob.glob("*/*.html") + glob.glob("index.html"))
```

- [ ] **Step 5: Run it**

Run: `python3 apply-report-enhancements.py`
Expected: `enhanced 23 file(s)` — every page listed with a `+`.

- [ ] **Step 6: Run it again to prove idempotence**

Run: `python3 apply-report-enhancements.py`
Expected: `enhanced 0 file(s)` and `skipped 23 already-enhanced`. If any file is re-enhanced, the marker guard is wrong — fix before continuing.

- [ ] **Step 7: Confirm the checker's block failures are gone**

Run: `python3 tools/check_theme.py 2>&1 | grep -c 'missing the theme block\|missing the no-flash boot'`
Expected: `0`

Colour and radius failures still remain — those are Tasks 5–7.

- [ ] **Step 8: Commit**

```bash
git add apply-report-enhancements.py *.html */*.html
git commit -m "feat(reports): ship the token layer to all 23 pages, backfill 4 missing enhancement blocks"
```

---

### Task 5: The colour migration script

Rewrites colour utilities onto the token layer. Refuses to guess.

**Files:**
- Create: `tools/migrate_colours.py`

**Interfaces:**
- Consumes: `tools.check_theme.EXEMPT_DARK` and `tools.check_theme.COLOUR_UTIL`. Accent names are declared locally in `ACCENT_NAMES` — the map must stay readable on its own.
- Produces: `tools.migrate_colours.MAP` (`dict[str, str]` — Tailwind utility to token-backed replacement) and a CLI taking optional file arguments.

- [ ] **Step 1: Inventory exactly what must be mapped**

Run:
```bash
grep -ohE '\b(bg|text|border|divide|ring|accent|placeholder)-(slate|gray|zinc|neutral|stone|rose|red|sky|blue|amber|yellow|emerald|green|purple|violet|teal|indigo)-[0-9]{2,3}\b|\bbg-white\b' */*.html index.html | sort -u > /tmp/utilities.txt
wc -l /tmp/utilities.txt
```
Expected: a file of roughly 90–120 distinct utilities. Every line must appear in `MAP` or the script will refuse to run.

- [ ] **Step 2: Write the migration script**

Create `tools/migrate_colours.py`:

```python
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
```

- [ ] **Step 3: Dry-run against one page to prove the hard-fail works**

Temporarily remove one entry from `MAP` (e.g. delete the `"text-slate-700"` line), then run:

Run: `python3 tools/migrate_colours.py ezrd-1462/index.html`
Expected: FAIL — `! ezrd-1462/index.html: unmapped utilities, refusing to guess: ['text-slate-700']`

Restore the deleted line. This proves the guard rather than assuming it.

- [ ] **Step 4: Add the Tailwind colour aliases the replacements reference**

The replacements emit names like `bg-surface` and `text-rose-text`, which Tailwind must know. In `tools/theme_block.py`, add this module-level constant above `def style_block():`, then append it to that function's return value (Step 5 below) so it ships with every block:

```python
TAILWIND_ALIASES = """<script data-report-theme-tw>
tailwind.config = tailwind.config || {};
tailwind.config.theme = tailwind.config.theme || {};
tailwind.config.theme.extend = tailwind.config.theme.extend || {};
tailwind.config.theme.extend.colors = Object.assign({}, tailwind.config.theme.extend.colors, {
  surface: 'var(--surface)', 'surface-2': 'var(--surface-2)', page: 'var(--page)',
  ink: 'var(--ink)', body: 'var(--ink-body)', mute: 'var(--ink-mute)',
  token: 'var(--border)', hairline: 'var(--hairline)', chip: 'var(--chip-bg)',
  rose: { fill: 'var(--accent-rose-fill)', border: 'var(--accent-rose-border)', text: 'var(--accent-rose-text)', dot: 'var(--accent-rose-dot)' },
  sky: { fill: 'var(--accent-sky-fill)', border: 'var(--accent-sky-border)', text: 'var(--accent-sky-text)', dot: 'var(--accent-sky-dot)' },
  amber: { fill: 'var(--accent-amber-fill)', border: 'var(--accent-amber-border)', text: 'var(--accent-amber-text)', dot: 'var(--accent-amber-dot)' },
  emerald: { fill: 'var(--accent-emerald-fill)', border: 'var(--accent-emerald-border)', text: 'var(--accent-emerald-text)', dot: 'var(--accent-emerald-dot)' },
  purple: { fill: 'var(--accent-purple-fill)', border: 'var(--accent-purple-border)', text: 'var(--accent-purple-text)', dot: 'var(--accent-purple-dot)' },
  teal: { fill: 'var(--accent-teal-fill)', border: 'var(--accent-teal-border)', text: 'var(--accent-teal-text)', dot: 'var(--accent-teal-dot)' },
});
</script>"""
```

Then change the final line of `style_block()`'s return from `</style>"""` to `</style>""" + TAILWIND_ALIASES` so the aliases ship with every block.

Run: `cd tools && python3 check_theme_block.py`
Expected: PASS.

Task 4's `inject_theme` already places the whole block in `<head>`, which is what these aliases require — they must be defined before the Tailwind CDN evaluates. No change needed there.

- [ ] **Step 5: Re-run the enhancement pass so the aliases reach every page**

Run:
```bash
python3 - <<'PY'
import glob, re
for f in sorted(glob.glob("*/*.html") + glob.glob("index.html")):
    h = open(f, encoding="utf-8").read()
    h = re.sub(r"<!-- report-theme v1.*?</script>\n?", "", h, flags=re.S)
    h = re.sub(r"<script data-report-theme-boot>.*?</script>\n?", "", h, flags=re.S)
    open(f, "w", encoding="utf-8").write(h)
PY
python3 apply-report-enhancements.py
```
Expected: `enhanced 23 file(s)`, and `grep -c 'data-report-theme-tw' index.html` returns `1`.

- [ ] **Step 6: Commit**

```bash
git add tools/migrate_colours.py tools/theme_block.py apply-report-enhancements.py *.html */*.html
git commit -m "feat(tokens): colour migration map and Tailwind token aliases"
```

---

### Task 6: Migrate the 23 pages and hand-fix the already-dark panels

**Files:**
- Modify: all 23 pages (by script)
- Modify by hand: the 7 code panels in the 4 exempt files

**Interfaces:**
- Consumes: `tools/migrate_colours.py`.
- Produces: no new interfaces — this task is the migration run itself.

- [ ] **Step 1: Run the migration**

Run: `python3 tools/migrate_colours.py`
Expected: `migrated 23 file(s)` with each listed. If it exits with `unmapped utilities`, add the missing entries to `MAP` in `tools/migrate_colours.py` and re-run. Do not weaken the guard.

- [ ] **Step 2: Confirm the colour failures are gone**

Run: `python3 tools/check_theme.py 2>&1 | grep 'raw colour utilities' || echo "none"`
Expected: `none`

- [ ] **Step 3: Find the already-dark panels**

Run: `grep -n 'bg-slate-900\|bg-slate-950' export-student-buses-eks/*.html ezrd-2008/index.html ezrd-2019/index.html`
Expected: 7 matches, each a `<pre>` or panel wrapper.

- [ ] **Step 4: Point them at the code-panel tokens by hand**

For each of the 7 matches, replace the colour classes with the token pair. For example, this:

```html
<pre class="bg-slate-900 text-slate-50 rounded-lg p-4 font-mono text-xs leading-relaxed mb-4 overflow-x-auto">
```

becomes:

```html
<pre class="rounded-md p-4 font-mono text-xs leading-relaxed mb-4 overflow-x-auto" style="background: var(--code-panel-bg); color: var(--code-panel-fg);">
```

Inline `style` is deliberate here: these two tokens are the only ones that do not vary with theme, so routing them through a Tailwind alias would imply a switch that does not exist.

- [ ] **Step 5: Verify no already-dark panel inverted**

Run: `grep -c 'code-panel-bg' export-student-buses-eks/index.html export-student-buses-eks/export-student-buses-flow.html ezrd-2008/index.html ezrd-2019/index.html`
Expected: counts summing to 7 across the four files, and `grep -c 'bg-slate-9' *.html */*.html | grep -v ':0' || echo "none left"` prints `none left`.

- [ ] **Step 6: Re-run the contrast check against the real pages**

Run: `cd tools && python3 check_contrast.py && cd ..`
Expected: PASS. Task 1 Step 3 noted that snapping to the ladder lightened `page` and `surface` versus the mockup; this is where that gets confirmed against the shipped token values rather than assumed.

- [ ] **Step 7: Commit**

```bash
git add *.html */*.html
git commit -m "refactor(reports): migrate all 23 pages onto the oklch token layer"
```

---

### Task 7: The radius pass

**Files:**
- Create: `tools/migrate_radii.py`
- Modify: all 23 pages (by script)

**Interfaces:**
- Consumes: `tools.tokens.RADII`.
- Produces: a CLI; no importable surface.

- [ ] **Step 1: Write the script**

Create `tools/migrate_radii.py`:

```python
#!/usr/bin/env python3
"""Tighten the radius scale. Pills, dots and switches keep rounded-full."""
import glob, re, sys

# rounded-2xl (16px) -> rounded-lg (8px); rounded-xl (12px) -> rounded-md (6px).
# rounded-full is untouched: pills and dots are capsules by definition.
SUBS = [(r"\brounded-2xl\b", "rounded-lg"), (r"\brounded-xl\b", "rounded-md")]


def main():
    files = sys.argv[1:] or sorted(glob.glob("*/*.html") + glob.glob("index.html"))
    changed = 0
    for f in files:
        html = open(f, encoding="utf-8").read()
        out = html
        for pat, repl in SUBS:
            out = re.sub(pat, repl, out)
        if out != html:
            open(f, "w", encoding="utf-8").write(out)
            changed += 1
            print(f"  + {f}")
    print(f"retuned {changed} file(s)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it**

Run: `python3 tools/migrate_radii.py`
Expected: `retuned` roughly 20+ files.

- [ ] **Step 3: Confirm `rounded-full` survived**

Run: `grep -c 'rounded-full' index.html`
Expected: a non-zero count. If it is 0, the substitution was too greedy — the `\b` anchors are missing and must be restored before continuing.

- [ ] **Step 4: Run the full checker — this is the task's real gate**

Run: `python3 tools/check_theme.py`
Expected: PASS — `23 page(s) checked, 0 failure(s)`. Compare against the baseline recorded in Task 3 Step 3.

- [ ] **Step 5: Commit**

```bash
git add tools/migrate_radii.py *.html */*.html
git commit -m "style(reports): tighten the radius scale across all 23 pages"
```

---

### Task 8: The segmented section slider

The horizontal nav, as an animated segmented control. Ships inside the theme block so every page gets it.

**Files:**
- Modify: `tools/theme_block.py`
- Modify: all 23 pages (by re-running the enhancement pass)

**Interfaces:**
- Consumes: the section ids that the existing enhancement block's anchor code already generates.
- Produces: `tools.theme_block.SLIDER_CSS` and `SLIDER_JS`, both appended into `style_block()`'s output.

- [ ] **Step 1: Add the slider CSS and JS to the emitter**

In `tools/theme_block.py`, add above `def style_block():`

```python
SLIDER_CSS = """
  .section-bar { position: sticky; top: 0; z-index: 40; background: var(--surface);
    border-bottom: var(--border-w) solid var(--border); }
  .section-bar-inner { max-width: 72rem; margin: 0 auto; padding: 12px 1.5rem;
    display: flex; align-items: center; justify-content: space-between; gap: 18px; }
  .seg-track { position: relative; display: grid; flex-grow: 1; max-width: 760px;
    padding: 4px; border-radius: 9px; background: var(--page); border: 1px solid var(--border);
    box-shadow: inset 0 2px 5px rgb(0 0 0 / .45), inset 0 -1px 0 rgb(255 255 255 / .04); }
  .seg-thumb { position: absolute; top: 4px; bottom: 4px; border-radius: 6px;
    pointer-events: none; background: var(--surface-2); border: 1px solid var(--border);
    box-shadow: inset 0 1px 0 rgb(255 255 255 / .10), 0 1px 2px rgb(0 0 0 / .45);
    transition: left .28s cubic-bezier(.4, 0, .2, 1), width .28s cubic-bezier(.4, 0, .2, 1); }
  .seg-btn { position: relative; z-index: 1; display: inline-flex; align-items: center;
    justify-content: center; gap: 8px; padding: 8px 14px; border: 0; background: transparent;
    border-radius: 6px; font: inherit; font-size: 13px; font-weight: 600;
    white-space: nowrap; cursor: pointer; color: var(--ink-mute); transition: color .2s ease; }
  .seg-btn[aria-pressed="true"] { color: var(--ink); }
  .seg-dot { width: 7px; height: 7px; border-radius: 999px; flex-shrink: 0; }
  @media (prefers-reduced-motion: reduce) { .seg-thumb { transition: none; } }
  @media (max-width: 860px) { .section-bar { display: none; } }
  @media print { .section-bar { display: none !important; } }
"""

SLIDER_JS = """<script data-report-slider>
(function () {
  if (window.__reportSlider) return; window.__reportSlider = true;
  document.addEventListener('DOMContentLoaded', function () {
    var heads = [].slice.call(document.querySelectorAll('main section h2[id]'));
    if (heads.length < 2) return;                    // one section needs no nav
    var bar = document.createElement('div');
    bar.className = 'section-bar no-print';
    var inner = document.createElement('div');
    inner.className = 'section-bar-inner';
    var track = document.createElement('div');
    track.className = 'seg-track';
    track.setAttribute('role', 'group');
    track.setAttribute('aria-label', 'Jump to section');
    track.style.gridTemplateColumns = 'repeat(' + heads.length + ', minmax(0, 1fr))';
    var thumb = document.createElement('div');
    thumb.className = 'seg-thumb';
    thumb.setAttribute('aria-hidden', 'true');
    track.appendChild(thumb);

    function place(i) {
      thumb.style.left = 'calc(4px + (100% - 8px) * ' + i + ' / ' + heads.length + ')';
      thumb.style.width = 'calc((100% - 8px) / ' + heads.length + ')';
    }

    var btns = heads.map(function (h, i) {
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'seg-btn';
      b.setAttribute('aria-pressed', i === 0 ? 'true' : 'false');
      var dot = document.createElement('span');
      dot.className = 'seg-dot';
      // Reuse the accent already on the section's own kicker dot, so the bar
      // cannot drift from the section colours.
      var src = h.parentNode.querySelector('[class*="bg-"][class*="-dot"]');
      dot.style.background = src ? getComputedStyle(src).backgroundColor : 'var(--ink-mute)';
      b.appendChild(dot);
      b.appendChild(document.createTextNode(h.textContent.replace(/^#/, '').trim()));
      b.addEventListener('click', function () {
        document.getElementById(h.id).scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
      track.appendChild(b);
      return b;
    });

    function select(i) {
      btns.forEach(function (b, n) { b.setAttribute('aria-pressed', n === i ? 'true' : 'false'); });
      place(i);
    }
    select(0);

    inner.appendChild(track);
    var sw = document.querySelector('.theme-switch');
    if (sw) inner.appendChild(sw);
    bar.appendChild(inner);
    var main = document.querySelector('main');
    main.parentNode.insertBefore(bar, main);

    // Track reading position: the last heading whose top crossed 33% of the viewport.
    var ticking = false;
    function sync() {
      var mark = window.innerHeight * 0.33, idx = 0;
      for (var i = 0; i < heads.length; i++) {
        if (heads[i].getBoundingClientRect().top <= mark) idx = i;
      }
      select(idx);
      ticking = false;
    }
    window.addEventListener('scroll', function () {
      if (!ticking) { requestAnimationFrame(sync); ticking = true; }
    }, { passive: true });
    sync();
  });
})();
</script>"""
```

- [ ] **Step 2: Ship them with the block**

In `style_block()`, add `{SLIDER_CSS}` immediately before the closing `</style>` inside the f-string, and change the final concatenation to `</style>""" + TAILWIND_ALIASES + SLIDER_JS`.

- [ ] **Step 3: Add the toggle to the page**

The slider moves an existing `.theme-switch` into its bar. Ensure one exists: in `inject_theme` (in `apply-report-enhancements.py`), insert `TOGGLE_HTML` immediately after the opening `<body ...>` tag:

```python
    m = re.search(r"<body[^>]*>", html)
    if m:
        html = html[:m.end()] + "\n" + TOGGLE_HTML + html[m.end():]
```

Add `import re` at the top of `apply-report-enhancements.py` if it is not already imported, and add `TOGGLE_HTML` to the existing `from theme_block import ...` line.

- [ ] **Step 4: Re-emit the block onto every page**

Run:
```bash
python3 - <<'PY'
import glob, re
pat = [r"<!-- report-theme v1.*?</script>\n?", r"<script data-report-theme-boot>.*?</script>\n?",
       r"<button type=\"button\" class=\"theme-switch.*?</button>\n?"]
for f in sorted(glob.glob("*/*.html") + glob.glob("index.html")):
    h = open(f, encoding="utf-8").read()
    for p in pat:
        h = re.sub(p, "", h, flags=re.S)
    open(f, "w", encoding="utf-8").write(h)
PY
python3 apply-report-enhancements.py
python3 tools/check_theme.py
```
Expected: `enhanced 23 file(s)`, then `23 page(s) checked, 0 failure(s)`.

- [ ] **Step 5: Verify in a browser**

Run: `open -a "Google Chrome" export-student-buses-eks/index.html`

Confirm by hand, because none of this is script-checkable:
1. The page loads dark with no flash of light (if the OS is in dark mode).
2. The toggle flips the theme and the choice survives a reload.
3. The slider thumb slides between segments and tracks scroll position.
4. Segment dots match their sections' kicker colours.
5. `Cmd+P` shows a light preview with no slider and no toggle.
6. Tables still scroll horizontally inside their cards; checkboxes still tick.
7. `Tab` reaches every segment and the toggle, each shows a visible focus ring, and `Enter`/`Space` activates them — the slider is built from real `<button>` elements so this should hold without extra work; if it does not, that is a bug to fix here.

- [ ] **Step 6: Commit**

```bash
git add tools/theme_block.py apply-report-enhancements.py *.html */*.html
git commit -m "feat(reports): animated segmented section slider with theme switch"
```

---

### Task 9: Update the design docs and the skill

Without this, every new report is generated light-only and the system splits.

**Files:**
- Modify: `DESIGN.md`
- Modify: `~/.claude/skills/engineering-report-page/SKILL.md`

**Interfaces:**
- Consumes: the shipped token names from `tools/theme_block.py`.
- Produces: the canonical documented copy that Plan 2's surfaces are checked against.

- [ ] **Step 1: Rewrite `DESIGN.md`'s Theme section**

Replace the opening paragraph — currently `Committed light theme. Slate-100 … light is deliberate, not a default.` — with:

```markdown
## Theme

Dual theme on one oklch token layer. Light is the default and the print target;
dark follows `prefers-color-scheme` unless the reader chooses, and the choice
persists in `localStorage`. Neither is a variant of the other — tokens are
defined once per theme in `tools/tokens.py` and emitted into every page.

Dark neutrals anchor to a verified lightness ladder: page `0.140`, surface
`0.212`, raised `0.245`, line `0.300`; ink `0.950`, body `0.800`, muted
`0.665`. `--ink-mute` is the contrast floor in both themes — nothing
lighter-weight carries body text. Borders are 2px in light, 1px in dark: the
value step already separates the card, and 2px reads heavy on a dark ground.

This is a documents-not-console surface in both themes. Dark mode is paper at
night, not a terminal.
```

- [ ] **Step 2: Add the radius scale to `DESIGN.md`'s Components section**

Under `## Components`, after the Section card bullet, insert:

```markdown
- **Radius scale**: cards and callouts `rounded-lg` (8px), table and tile
  panels `rounded-md` (6px), code containers 8px, `<pre>` 5px, inline code 3px.
  Pills, dots and the theme switch stay `rounded-full` — they are capsules by
  definition.
```

- [ ] **Step 3: Update `DESIGN.md`'s Motion and Print sections**

Replace the Motion section's final sentence with:

```markdown
Two authored moments: the segmented section slider's thumb tracks reading
position, and the theme switch's knob travels. Both are 220–280ms ease-out and
both drop to instant under `prefers-reduced-motion: reduce`. Everything else is
a hover transition.
```

Replace the Print section's first clause `forces black ink on white` with `forces the light token set regardless of the reader's theme`.

- [ ] **Step 4: Update the skill's boilerplate**

In `~/.claude/skills/engineering-report-page/SKILL.md`, in the `## Boilerplate <head>` section, replace the `<style>` block's hardcoded colours with a pointer to the emitted block, and add above it:

```markdown
The token block, no-flash boot script, Tailwind aliases and section slider are
emitted by `tools/theme_block.py` in the `engineering-reports` repo and injected
by `apply-report-enhancements.py`. Do not hand-write colours into a new report:
write it with the token-backed utility names below, then run

    python3 apply-report-enhancements.py path/to/new-report.html

which adds everything and is idempotent.
```

- [ ] **Step 5: Replace the skill's colour table with token names**

In the `## Color system` section, replace the Tailwind-step column with the token-backed names the migration produces: `bg-{accent}-fill`, `border-{accent}-border`, `text-{accent}-text`, `bg-{accent}-dot`, plus the neutrals `bg-page`, `bg-surface`, `bg-surface-2`, `text-ink`, `text-body`, `text-mute`, `border-token`, `border-hairline`, `bg-chip`.

Keep the meaning column exactly as it is — the six accents and their fixed meanings do not change.

- [ ] **Step 6: Update the skill's radius guidance**

Throughout `SKILL.md`, replace `rounded-2xl` with `rounded-lg` and `rounded-xl` with `rounded-md` in every component snippet. Leave `rounded-full` alone.

- [ ] **Step 7: Verify a fresh report picks it all up**

Run:
```bash
cp export-student-buses-eks/index.html /tmp/fresh-test.html
python3 - <<'PY'
import re
h = open("/tmp/fresh-test.html", encoding="utf-8").read()
for p in [r"<!-- report-theme v1.*?</script>\n?", r"<script data-report-theme-boot>.*?</script>\n?",
          r"<button type=\"button\" class=\"theme-switch.*?</button>\n?",
          r"<!-- report-enhancements v1.*?</script>\n?"]:
    h = re.sub(p, "", h, flags=re.S)
open("/tmp/fresh-test.html", "w", encoding="utf-8").write(h)
PY
python3 apply-report-enhancements.py /tmp/fresh-test.html
open -a "Google Chrome" /tmp/fresh-test.html
```
Expected: the stripped page comes back fully themed — dark ground, working toggle, working slider. This proves the skill's instruction actually works for a new report.

- [ ] **Step 8: Commit**

```bash
git add DESIGN.md
git commit -m "docs(design): dual-theme token layer, radius scale, slider motion"
```

The skill lives outside this repo and is not committed here. Note its path in the
PR body so the change is not lost: `~/.claude/skills/engineering-report-page/SKILL.md`.

---

## Done when

- `python3 tools/check_theme.py` reports `23 page(s) checked, 0 failure(s)`.
- `cd tools && python3 check_contrast.py` reports `all pairs clear AA`.
- `python3 apply-report-enhancements.py` run twice reports 0 changes the second time.
- A report opened in Chrome loads in the system theme with no flash, toggles, persists across reload, slides its section thumb, and prints light.
- `DESIGN.md` and the skill describe what actually shipped.

## Not in this plan

Surfaces 2–4 — the chew-ticket ticket-doc template, the `eng-local-docs` board
shell, and the `board` repo's two renderers — are Plan 2. They consume the token
block this plan produces and cannot be written against it until it exists.
