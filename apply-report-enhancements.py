#!/usr/bin/env python3
"""Inject the shared report-enhancement block (print styles, reading-progress bar,
shareable section anchors) into report pages. Idempotent: skips files that already
carry the `data-report-enhanced` marker. Run with file args, or with no args to
enhance every report page except the root index.html (which has its own system).

    python3 apply-report-enhancements.py               # all report pages
    python3 apply-report-enhancements.py ezrd-1462/index.html   # one page
"""
import sys, glob, os

BLOCK = """
<!-- report-enhancements v1 · print styles + reading progress + section anchors (shared system) -->
<style data-report-enhanced>
  .reading-progress { position: fixed; top: 0; left: 0; height: 3px; width: 0; z-index: 60;
    background: rgb(2 132 199); transition: width .1s linear; }
  .anchor-h { position: relative; }
  .anchor-link { position: absolute; left: -1.15rem; top: 0.12em; opacity: 0; text-decoration: none;
    color: rgb(148 163 184); font-weight: 600; transition: opacity .12s ease; }
  .anchor-h:hover .anchor-link, .anchor-link:focus { opacity: 1; }
  .anchor-link:hover { color: rgb(37 99 235); }
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


def targets(args):
    if args:
        return args
    files = []
    for f in glob.glob("*/*.html"):
        files.append(f)
    return sorted(files)


def main():
    args = sys.argv[1:]
    changed, skipped = [], []
    for f in targets(args):
        if not os.path.isfile(f):
            print(f"  ! missing: {f}")
            continue
        html = open(f, encoding="utf-8").read()
        if MARKER in html:
            skipped.append(f)
            continue
        idx = html.rfind("</body>")
        if idx == -1:
            print(f"  ! no </body>: {f}")
            continue
        html = html[:idx] + BLOCK + "\n" + html[idx:]
        open(f, "w", encoding="utf-8").write(html)
        changed.append(f)

    print(f"enhanced {len(changed)} file(s):")
    for f in changed:
        print(f"  + {f}")
    if skipped:
        print(f"skipped {len(skipped)} already-enhanced:")
        for f in skipped:
            print(f"  = {f}")


if __name__ == "__main__":
    main()
