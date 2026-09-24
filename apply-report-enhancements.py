#!/usr/bin/env python3
"""Inject the shared report-enhancement block (print styles, reading-progress bar,
shareable section anchors) into report pages. Idempotent: skips files that already
carry the `data-report-enhanced` marker. Run with file args, or with no args to
enhance every report page except the root index.html (which has its own system).

    python3 apply-report-enhancements.py               # all report pages
    python3 apply-report-enhancements.py ezrd-1462/index.html   # one page
"""
import sys, glob, os, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools"))
from theme_block import HEAD_BOOT, style_block, TOGGLE_HTML, MARKER as THEME_MARKER

BLOCK = """
<!-- report-enhancements v1 · print styles + reading progress + section anchors (shared system) -->
<style data-report-enhanced>
  .reading-progress { position: fixed; top: 0; left: 0; height: 3px; width: 0; z-index: 60;
    background: var(--accent-sky-dot, rgb(2 132 199)); transition: width .1s linear; }
  .anchor-h { position: relative; }
  .anchor-link { position: absolute; left: -1.15rem; top: 0.12em; opacity: 0; text-decoration: none;
    color: var(--ink-mute, rgb(148 163 184)); font-weight: 600; transition: opacity .12s ease; }
  .anchor-h:hover .anchor-link, .anchor-link:focus { opacity: 1; }
  .anchor-link:hover { color: var(--accent-sky-text, rgb(37 99 235)); }
  @media (max-width: 640px) { .anchor-link { display: none; } }
  @media (prefers-reduced-motion: reduce) { .reading-progress { transition: none; } }
  @media print {
    .reading-progress, .no-print, .anchor-link { display: none !important; }
    html { font-size: 11.5pt; }
    body { background: #fff !important; }
    .main-card, [class*="shadow"] { box-shadow: none !important; }
    [class*="sticky"] { position: static !important; }
    section, .main-card, tr, pre, figure { break-inside: avoid; }
    h1, h2, h3 { break-after: avoid; }
    [class*="overflow-"] { overflow: visible !important; }
    table { min-width: 0 !important; width: 100% !important; font-size: 9pt; }
    pre { white-space: pre-wrap !important; overflow-wrap: anywhere; }
    a { text-decoration: none; }
  }
</style>
<div class="reading-progress no-print" aria-hidden="true"></div>
<script data-report-enhanced>
(function () {
  if (window.__reportEnhanced) return; window.__reportEnhanced = true;
  var bar = document.querySelector('.reading-progress'), ticking = false;
  function upd() {
    var h = document.documentElement, max = h.scrollHeight - h.clientHeight;
    var top = h.scrollTop || document.body.scrollTop;
    if (bar) bar.style.width = (max > 0 ? (top / max) * 100 : 0) + '%';
    ticking = false;
  }
  window.addEventListener('scroll', function () {
    if (!ticking) { requestAnimationFrame(upd); ticking = true; }
  }, { passive: true });
  window.addEventListener('resize', upd); upd();

  var used = {};
  function slug(t) {
    return t.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 60) || 'section';
  }
  document.querySelectorAll('main h2, section h2').forEach(function (h) {
    if (h.querySelector('.anchor-link')) return;
    var id = h.id;
    if (!id) { id = slug(h.textContent); while (used[id] || document.getElementById(id)) id += '-x'; h.id = id; }
    used[id] = true;
    h.classList.add('anchor-h');
    var a = document.createElement('a');
    a.className = 'anchor-link'; a.href = '#' + id; a.textContent = '#';
    a.setAttribute('aria-label', 'Link to this section');
    h.insertBefore(a, h.firstChild);
  });
})();
</script>
"""

MARKER = "data-report-enhanced"


def inject_theme(html):
    """Add the boot script and token block to <head>, and the toggle button
    just inside <body>. Idempotent.

    Both the boot script and the token block go in <head>, not before
    </body>: the boot must set data-theme before the body paints, so the
    whole theming unit (vars, aliases, boot) lives together where that
    ordering is guaranteed.

    The guard checks for the specific opening tag `<style data-report-theme>`
    rather than the bare THEME_MARKER substring. THEME_MARKER also matches
    inside data-report-theme-boot/-toggle/-tw, so a page left with only an
    orphaned artifact (see theme_block.strip_theme) would otherwise look
    "already themed" and skip re-injection entirely.
    """
    anchor = f"<style {THEME_MARKER}>"
    if anchor in html:
        return html, False
    head_end = html.find("</head>")
    if head_end == -1:
        raise ValueError("no </head>")
    html = html[:head_end] + HEAD_BOOT + "\n" + style_block() + "\n" + html[head_end:]
    # Search for the body tag AFTER </head>, never from position 0: the block
    # being injected is CSS and JavaScript, and a comment or a string in it can
    # legitimately contain the text "<body>". An unanchored search found one and
    # injected the toggle button inside the <style> element.
    body_search_from = html.find("</head>")
    m = re.compile(r"<body[^>]*>").search(html, body_search_from)
    if m:
        html = html[:m.end()] + "\n" + TOGGLE_HTML + html[m.end():]
    return html, True


def targets(args):
    if args:
        return args
    return sorted(glob.glob("*/*.html") + glob.glob("index.html"))


def main():
    args = sys.argv[1:]
    changed, skipped = [], []
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

    print(f"enhanced {len(changed)} file(s):")
    for f in changed:
        print(f"  + {f}")
    if skipped:
        print(f"skipped {len(skipped)} already-enhanced:")
        for f in skipped:
            print(f"  = {f}")


if __name__ == "__main__":
    main()
