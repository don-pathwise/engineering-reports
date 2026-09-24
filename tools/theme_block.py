#!/usr/bin/env python3
"""Emits the CSS token block, the no-flash boot script, and the toggle markup."""
import re

from tokens import LIGHT, DARK, ACCENTS, CODE_PANEL_HEX, BORDER_W

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
  // The toggle button doesn't exist yet (we're in <head>), so its
  // aria-checked can't be synced here. Do it as soon as the body has
  // parsed, whether or not the slider builds a bar for this page --
  // otherwise a dark first load reports "off" to assistive tech until
  // the reader's first click.
  document.addEventListener('DOMContentLoaded', function () {
    var sw = document.querySelector('.theme-switch');
    if (sw) sw.setAttribute('aria-checked', document.documentElement.getAttribute('data-theme') === 'dark' ? 'true' : 'false');
  });
})();
</script>"""

TOGGLE_HTML = """<button type="button" class="theme-switch no-print" role="switch" aria-checked="false" aria-label="Dark theme" onclick="__toggleTheme(this)">
  <span class="theme-switch-knob" aria-hidden="true"></span>
</button>"""

TAILWIND_ALIASES = """<script data-report-theme-tw>
tailwind.config = tailwind.config || {};
tailwind.config.theme = tailwind.config.theme || {};
tailwind.config.theme.extend = tailwind.config.theme.extend || {};
tailwind.config.theme.extend.colors = Object.assign({}, tailwind.config.theme.extend.colors, {
  surface: 'var(--surface)', 'surface-2': 'var(--surface-2)', page: 'var(--page)',
  ink: 'var(--ink)', body: 'var(--ink-body)', mute: 'var(--ink-mute)',
  token: 'var(--border)', hairline: 'var(--hairline)', chip: 'var(--chip-bg)',
  rose: { fill: 'var(--accent-rose-fill)', border: 'var(--accent-rose-border)', text: 'var(--accent-rose-text)', dot: 'var(--accent-rose-dot)', solid: 'var(--accent-rose-solid)' },
  sky: { fill: 'var(--accent-sky-fill)', border: 'var(--accent-sky-border)', text: 'var(--accent-sky-text)', dot: 'var(--accent-sky-dot)', solid: 'var(--accent-sky-solid)' },
  amber: { fill: 'var(--accent-amber-fill)', border: 'var(--accent-amber-border)', text: 'var(--accent-amber-text)', dot: 'var(--accent-amber-dot)', solid: 'var(--accent-amber-solid)' },
  emerald: { fill: 'var(--accent-emerald-fill)', border: 'var(--accent-emerald-border)', text: 'var(--accent-emerald-text)', dot: 'var(--accent-emerald-dot)', solid: 'var(--accent-emerald-solid)' },
  purple: { fill: 'var(--accent-purple-fill)', border: 'var(--accent-purple-border)', text: 'var(--accent-purple-text)', dot: 'var(--accent-purple-dot)', solid: 'var(--accent-purple-solid)' },
  teal: { fill: 'var(--accent-teal-fill)', border: 'var(--accent-teal-border)', text: 'var(--accent-teal-text)', dot: 'var(--accent-teal-dot)', solid: 'var(--accent-teal-solid)' },
});
</script>"""


SLIDER_CSS = """
  .section-bar { position: sticky; top: 0; z-index: 40; background: var(--surface);
    border-bottom: var(--border-w) solid var(--border); }
  .section-bar-inner { max-width: 72rem; margin: 0 auto; padding: 12px 1.5rem;
    display: flex; align-items: center; justify-content: space-between; gap: 18px; }
  .seg-track { position: relative; display: grid; flex-grow: 1; max-width: 760px;
    padding: 4px; border-radius: 9px; background: var(--page); border: 1px solid var(--border);
    box-shadow: inset 0 2px 5px rgb(0 0 0 / .45), inset 0 -1px 0 rgb(255 255 255 / .04);
    overflow-x: auto; }
  .seg-thumb { position: absolute; top: 4px; bottom: 4px; border-radius: 6px;
    pointer-events: none; background: var(--surface-2); border: 1px solid var(--border);
    box-shadow: inset 0 1px 0 rgb(255 255 255 / .10), 0 1px 2px rgb(0 0 0 / .45);
    transition: left .28s cubic-bezier(.4, 0, .2, 1), width .28s cubic-bezier(.4, 0, .2, 1); }
  .seg-btn { position: relative; z-index: 1; display: inline-flex; align-items: center;
    justify-content: center; gap: 8px; padding: 8px 14px; border: 0; background: transparent;
    border-radius: 6px; font: inherit; font-size: 13px; font-weight: 600; min-width: 180px;
    white-space: nowrap; cursor: pointer; color: var(--ink-mute); transition: color .2s ease; }
  .seg-btn[aria-pressed="true"] { color: var(--ink); }
  .seg-dot { width: 7px; height: 7px; border-radius: 999px; flex-shrink: 0; }
  @media (prefers-reduced-motion: reduce) { .seg-thumb { transition: none; } }
  /* Narrow screens don't get the segmented nav -- but the bar is also where
     the theme toggle was adopted to, and `display:none` on the bar took the
     toggle with it: 0x0, unreachable, on every slider page at phone width.
     So collapse the bar to nothing instead of removing it, and hand the
     toggle back to its default fixed placement. */
  @media (max-width: 860px) {
    .section-bar { position: static; background: none; border: 0; }
    .section-bar-inner { padding: 0; display: block; }
    .seg-track { display: none; }
    .section-bar .theme-switch { position: fixed; top: 14px; right: 18px; }
  }
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
    // min-content-based min: a column never shrinks below its own button's
    // text (no clipping/overlap for a long heading), 1fr still grows every
    // column evenly to fill the track when there's room, so short labels
    // stay visually equal-width in the common case. .seg-btn's min-width
    // (180px, measured against this repo's real report headings so a
    // typical short 2-3 word label like "Test Environment" never looks
    // cramped) sets the floor for those short labels.
    track.style.gridTemplateColumns = 'repeat(' + heads.length + ', minmax(max-content, 1fr))';
    var thumb = document.createElement('div');
    thumb.className = 'seg-thumb';
    thumb.setAttribute('aria-hidden', 'true');
    track.appendChild(thumb);

    // Positioned from the segment button's own layout box (offsetLeft/Width
    // are relative to .seg-track's padding edge and scroll-invariant), not a
    // percentage-of-track formula: once columns can differ in width (above)
    // and the track can scroll horizontally (.seg-track { overflow-x: auto }
    // in SLIDER_CSS), "100% of the track" no longer equals "100% of the
    // scrollable content", so a percentage-based thumb would drift out of
    // register with its segment as soon as a page needed to scroll the bar.
    function place(i) {
      var b = btns[i];
      if (!b) return;
      thumb.style.left = b.offsetLeft + 'px';
      thumb.style.width = b.offsetWidth + 'px';
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

    var current = 0;
    function select(i) {
      current = i;
      btns.forEach(function (b, n) { b.setAttribute('aria-pressed', n === i ? 'true' : 'false'); });
      place(i);
    }

    inner.appendChild(track);
    var sw = document.querySelector('.theme-switch');
    if (sw) inner.appendChild(sw);
    bar.appendChild(inner);
    var main = document.querySelector('main');
    main.parentNode.insertBefore(bar, main);

    // place() measures real layout (offsetLeft/offsetWidth), so the first
    // call has to happen after the bar is actually in the document -- a
    // detached node's offsets are always 0.
    select(0);

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

    // The grid's columns are 1fr, so the track's own width changing (window
    // resize, a scrollbar appearing, any reflow) redistributes every column
    // and place()'s pixel values go stale -- a ResizeObserver on the track
    // itself catches all of those, not just window resize, rAF-throttled the
    // same way scroll is handled above. Re-runs select() for the CURRENT
    // segment (never select(0)), so a resize can't silently reset which
    // segment the reader was on.
    if (window.ResizeObserver) {
      var resizeTicking = false;
      new ResizeObserver(function () {
        if (!resizeTicking) {
          requestAnimationFrame(function () { select(current); resizeTicking = false; });
          resizeTicking = true;
        }
      }).observe(track);
    }
  });
})();
</script>"""


def strip_theme(html):
    """Remove every theme artifact this module emits, so inject_theme() can be
    called again on a page that already carries one and end up with exactly
    one of each — never zero, never two.

    THEME_MARKER ("data-report-theme") is an unanchored substring that also
    matches inside data-report-theme-boot, -toggle, and -tw, so inject_theme's
    guard cannot tell "fully themed" from "one orphaned artifact left behind
    by a partial strip" unless every artifact is removed together. A strip
    regex written ad hoc at a call site that misses even one of these leaves
    an orphan that still satisfies the guard, so inject_theme silently skips
    re-injection and the page ends up with no boot script and no style block.
    This function is the one supported way to strip the block; it removes the
    comment, the boot script, the style block, the toggle-theme script, the
    Tailwind alias script, the slider script, and the toggle button markup —
    every artifact HEAD_BOOT / style_block() / TOGGLE_HTML can put on a page.
    """
    patterns = [
        r"<!-- report-theme v1[^\n]*-->\n?",
        r"<script data-report-theme-boot>.*?</script>\n?",
        r"<style data-report-theme>.*?</style>\n?",
        r"<script data-report-theme-toggle>.*?</script>\n?",
        r"<script data-report-theme-tw>.*?</script>\n?",
        r"<script data-report-slider>.*?</script>\n?",
        r'<button type="button" class="theme-switch.*?</button>\n?',
    ]
    for pattern in patterns:
        html = re.sub(pattern, "", html, flags=re.S)
    return html


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
    return f"""<!-- report-theme v1 · oklch token layer (shared system — do not hand-edit) -->
<style {MARKER}>
  :root {{
    color-scheme: light;
{light}
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
  /* The slider adopts this button into its bar (inner.appendChild(sw)), but
     the slider bails on any page with fewer than 2 <h2 id> headings -- 7 pages
     today, including the site landing page. With no placement of its own the
     button then sat as the body's first child at {{x:0, y:0}}: a bare pill in
     the top-left corner, the first thing a visitor to index.html saw. So it
     parks itself top-right by default and the bar overrides that when it does
     adopt it. The override is `relative`, not `static`: the knob is
     position:absolute and needs this button to stay its containing block --
     `static` would hand the knob to the sticky .section-bar instead. */
  .theme-switch {{
    position: fixed; top: 14px; right: 18px; z-index: 50;
    width: 60px; height: 30px; padding: 0; flex-shrink: 0;
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
  .section-bar .theme-switch {{ position: relative; top: auto; right: auto; }}
  :root[data-theme="dark"] .theme-switch-knob {{ left: 35px; }}
  @media (prefers-reduced-motion: reduce) {{ .theme-switch-knob {{ transition: none; }} }}
  /* Print is light, whatever the reader chose -- and whether or not JS ran.
     `:root:not([data-theme="light"])` has to be in this list: with JS
     disabled no data-theme attribute is ever set, so `:root[data-theme="dark"]`
     below cannot match and the bare `:root` (0,1,0) loses to the
     system-preference rule's `:root:not([data-theme="light"])` (0,2,0) above.
     A dark-preferring OS then printed the dark palette. Matching that
     selector here makes the specificity equal, and this block is later in the
     sheet, so it wins. */
  @media print {{
    :root, :root:not([data-theme="light"]), :root[data-theme="dark"] {{
      color-scheme: light;
{light}
    }}
    .theme-switch {{ display: none !important; }}
  }}
{SLIDER_CSS}</style>
<script data-report-theme-toggle>
window.__toggleTheme = function (el) {{
  var next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  if (el) el.setAttribute('aria-checked', next === 'dark' ? 'true' : 'false');
  try {{ localStorage.setItem('report-theme', next); }} catch (e) {{}}
}};
</script>""" + TAILWIND_ALIASES + SLIDER_JS


if __name__ == "__main__":
    print(HEAD_BOOT)
    print(style_block())
