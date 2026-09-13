#!/usr/bin/env python3
"""Prove a Bihar extraction lost no text, by word frequency against the raw export.

    python bihar_ar_audit.py <export.htm> bihar_v<N>.json

Page counts prove nothing. Every one of the four faults found in volumes 2-3 —
a segment with two markers, text after a segment's last marker, a page with no
marker of its own, notes in the recovery branch — produced a plausible page
count and silently dropped text. What caught all four was counting each Arabic
token in the source and in the output and comparing the two multisets.

The export carries chrome that is deliberately NOT published: the Ghaemiyeh
publisher blurb («تعريف مرکز») and its trailing contact block. Those tokens are
expected to be missing, so the audit reports the shortfall split in two — inside
the dropped chrome (fine) and outside it (a real loss). Only the second number
has to be zero.
"""

import html as htmlmod
import json
import pathlib
import re
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

PROMO = "تعريف مرکز"
# The page marker is structure, not text: the extractor turns «ص: 12» into the
# page's number and publishes it as a folio label, so its «ص» is legitimately
# absent from the body. Strip the markers before counting or every volume
# reports exactly one uncaptured token per page and the real signal is buried.
MARKER = re.compile(
    r"<P class=content_paragraph>\s*<SPAN class=content_text>\s*ص\s*:\s*\d+\s*</SPAN>\s*</P>",
    re.I)
# Arabic/Persian letters plus the ZWNJ that Ghaemiyeh sprinkles through compounds.
WORD = re.compile(r"[ء-يٮ-ۓ‌]+")


def text_of(fragment):
    t = re.sub(r"<BR\s*/?>", " ", fragment, flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    return htmlmod.unescape(t)


def tokens(s):
    """Diacritic-insensitive tokens: the builder escapes, it never re-spells."""
    s = re.sub(r"[ً-ٰٟـ]", "", s)
    return WORD.findall(s)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    raw = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
    data = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))

    body = raw[raw.find("<BODY"):] if "<BODY" in raw else raw

    # Split the export into the part that should be published and the chrome
    # that should not, on the same marker the extractor drops on.
    segs = re.split(r"<SPAN class=chapter>\s*</SPAN>", body, flags=re.I)
    keep, chrome = [], []
    for seg in segs:
        t = text_of(MARKER.sub(" ", seg))
        (chrome if (PROMO in t and len(re.sub(r"\s+", " ", t)) < 4000) else keep).append(t)

    src = Counter(tokens(" ".join(keep)))
    drop = Counter(tokens(" ".join(chrome)))

    out = Counter()
    for p in data["pages"]:
        for b in p["blocks"]:
            out.update(tokens(b["ar"]))
        for n in p["notes"]:
            out.update(tokens(n["ar"]))

    missing = src - out
    in_chrome = Counter({w: min(c, drop[w]) for w, c in missing.items() if drop[w]})
    real = missing - in_chrome

    print(f"  source tokens (excluding dropped chrome): {sum(src.values()):,}")
    print(f"  output tokens:                            {sum(out.values()):,}")
    print(f"  extra in output (escaping, note numbers): {sum((out - src).values()):,}")
    print(f"  shortfall explained by publisher chrome:  {sum(in_chrome.values()):,}")
    print(f"  ** UNCAPTURED SOURCE TOKENS: {sum(real.values()):,} **")
    if real:
        for w, c in real.most_common(15):
            print(f"       {c:>5}  {w}")
    return 1 if real else 0


if __name__ == "__main__":
    sys.exit(main())
