#!/usr/bin/env python3
"""Audit an ablibrary extraction for the faults that do not raise errors.

    python abl_audit.py <dir with *_v*.json>

`abl_extract.py`'s round-trip check proves no TEXT was lost. It says nothing
about whether the text was split correctly — and every defect this book family
has produced was a splitting defect that round-tripped perfectly:

  * **A whole page as one block.** ablibrary numbers its hadith four different
    ways across these two books — «( 316 ) 7», «[ 28 ] 4 -», «176 - 1» and
    «* ( 125 ) * 76 -». Miss one and every hadith on the page merges into the
    preceding paragraph. Istibsar volume 1 shipped that way: 0 splits, 251
    pages that were a single block, and a perfect round-trip.
  * **A whole volume with no headings.** Istibsar volume 3 brackets its chapter
    titles — «[ 1 - باب من يستحق… ]» — and found 2 of 238 until the pattern
    allowed the bracket. The missing 236 were glued onto paragraphs.
  * **Footnote markers pointing nowhere.** «( 1 )» in the body is only useful if
    a numbered note carries that number; the تخريج lines keyed to hadith numbers
    are a different thing and must not be numbered as if they were footnotes.

So this checks the SHAPE of the result, per volume, and shouts when a volume
looks unlike its siblings. Thresholds are deliberately loose: the point is to
catch a volume that is structurally broken, not to police normal variation.
"""

import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

HAD = re.compile(r"^\s*\*?\s*(?:\[\s*\d+\s*\]|\(\s*\d+\s*\)|\d+)\s*\*?\s*-?\s*\d+\s*-?\s")
REF = re.compile(r"\[(\d{1,3})\]")
GIANT = 900          # characters in a lone block that suggests a missed split
MIN_BLOCKS = 2.0     # average blocks per page below this is suspicious


def audit(path):
    d = json.loads(path.read_text(encoding="utf-8"))
    body = [p for p in d["pages"] if p["blocks"]]
    if not body:
        return [f"{path.name}: no pages with blocks"]
    nb = sum(len(p["blocks"]) for p in body) / len(body)
    had = sum(1 for p in body for b in p["blocks"] if HAD.match(b["ar"]))
    heads = sum(1 for p in body for b in p["blocks"] if b["tag"] != "p")
    giant = [p["id"] for p in body
             if len(p["blocks"]) == 1 and len(p["blocks"][0]["ar"]) > GIANT]
    # every anchored marker must have a numbered note on its own page
    dangling = 0
    for p in body:
        have = {x["n"] for x in p["notes"] if x.get("k") == "fn"}
        for b in p["blocks"]:
            for m in REF.finditer(b["ar"]):
                if int(m.group(1)) not in have:
                    dangling += 1
    fn = sum(1 for p in body for x in p["notes"] if x.get("k") == "fn")
    src = sum(1 for p in body for x in p["notes"] if x.get("k") == "src")

    print(f"  {path.stem:<16} {len(body):>5} pages  {nb:>5.1f} blocks/page  "
          f"{had:>5} hadith  {heads:>4} headings  "
          f"{fn:>5} fn + {src:>5} src notes")
    bad = []
    if nb < MIN_BLOCKS:
        bad.append(f"{path.stem}: only {nb:.1f} blocks per page — a hadith "
                   f"numbering form is probably unmatched")
    # A long single block is NOT itself a fault: a ziyara, one detailed legal
    # hadith, or Imam Ali's endowment document each fill a page continuously.
    # 197 such pages were examined by hand and 179 were genuinely one passage.
    # What matters is the RATE — a volume whose numbering form is unmatched runs
    # 48% (Istibsar v1) to 91% (Tahdhib v2) of its pages together, against ~10%
    # for a healthy one. `abl_extract.py` reports the unmatched line starts
    # themselves, which is the precise signal.
    if len(giant) > len(body) * 0.25:
        bad.append(f"{path.stem}: {len(giant)} of {len(body)} pages are ONE "
                   f"block over {GIANT} chars (e.g. {giant[:3]}) — a hadith "
                   f"numbering form is probably unmatched")
    if heads == 0:
        bad.append(f"{path.stem}: no headings at all")
    if dangling:
        bad.append(f"{path.stem}: {dangling} footnote markers point at a note "
                   f"that does not exist on their page")
    return bad


def main():
    d = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    files = sorted(d.glob("*_v*.json"),
                   key=lambda f: (f.stem.rsplit("_v", 1)[0],
                                  int(f.stem.rsplit("_v", 1)[1])))
    if not files:
        sys.exit(f"no *_v*.json in {d}")
    problems = []
    for f in files:
        problems += audit(f)
    print()
    if problems:
        print(f"  ** {len(problems)} PROBLEM(S) **")
        for p in problems:
            print(f"     {p}")
        return 1
    print("  all volumes look structurally sound")
    return 0


if __name__ == "__main__":
    sys.exit(main())
