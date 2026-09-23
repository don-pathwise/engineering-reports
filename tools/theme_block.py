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
window.__toggleTheme = function (el) {{
  var next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  if (el) el.setAttribute('aria-checked', next === 'dark' ? 'true' : 'false');
  try {{ localStorage.setItem('report-theme', next); }} catch (e) {{}}
}};
</script>""" + TAILWIND_ALIASES


if __name__ == "__main__":
    print(HEAD_BOOT)
    print(style_block())
