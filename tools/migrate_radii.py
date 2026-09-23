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
