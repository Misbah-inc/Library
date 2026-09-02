#!/usr/bin/env python3
"""Split Bayt al-Ahzan into PRINTED pages.

  bayt_paginate.py bayt.json > bayt_pages.json

The Ghaemiyeh export marks pagination with a standalone block "[ صفحه ۷۷ ]".
Verified against the scanned Naser edition (PDF page = printed + 3):

  printed 76 ends  "...از بیم آنکه شما به آن، دست نیابید."
  printed 77 opens "حضرت علی (ع) بیل را به زمین گذارد..."

...which is exactly where the marker falls. So the marker OPENS the page it
names: a page runs from its own marker up to the next one.

Every chapter 2-17 ends ON a marker, so pages routinely straddle chapter
boundaries. The book therefore has to be flattened into one block stream
before splitting — paginating chapter by chapter would invent a page break at
every chapter start.

Out of stream:
  ch 1  مشخصات کتاب  — colophon, printed pages 1-2; goes on the cover
  ch19  پاورقی        — 98 endnotes, each cited by [n] in the body; each one
                        is attached to the page that cites it
"""
import json, re, sys, pathlib, collections

MARK = re.compile(r'^\[\s*صفحه\s*([۰-۹0-9]+)\s*\]$')
NOTE = re.compile(r'^\[(\d+)\]\s*')
REF  = re.compile(r'\[(\d+)\]')
FA   = "۰۱۲۳۴۵۶۷۸۹"

def toint(s):
    return int("".join(str(FA.index(c)) if c in FA else c for c in s))

def paginate(data):
    chapters = data["chapters"]
    colophon = chapters[0]                       # ch1
    notes_ch = chapters[-1]                      # ch19
    body     = chapters[1:-1]                    # ch2..ch18

    # 98 endnotes, keyed by number
    notes = {}
    for b in notes_ch["blocks"]:
        m = NOTE.match(b["fa"])
        if m:
            notes[int(m.group(1))] = NOTE.sub("", b["fa"]).strip()

    # one flat stream, each block remembering which chapter it came from
    stream = [(c, b) for c in body for b in c["blocks"]]

    # printed page 3 is the run before the first marker (مقدمهٔ مکارم شیرازی)
    pages, cur = [], {"n": 3, "blocks": [], "chapter": body[0]["title"],
                      "chapter_n": body[0]["n"]}
    for c, b in stream:
        m = MARK.match(b["fa"].strip())
        if m:
            pages.append(cur)
            cur = {"n": toint(m.group(1)), "blocks": [],
                   "chapter": c["title"], "chapter_n": c["n"]}
        else:
            # the chapter a page belongs to is the one its FIRST block is in
            if not cur["blocks"]:
                cur["chapter"], cur["chapter_n"] = c["title"], c["n"]
            cur["blocks"].append({"tag": b["tag"], "fa": b["fa"]})
    pages.append(cur)

    # attach each endnote to the page that cites it
    seen = set()
    for p in pages:
        used = []
        for b in p["blocks"]:
            for r in REF.findall(b["fa"]):
                r = int(r)
                if r in notes and r not in seen:
                    seen.add(r); used.append(r)
        p["notes"] = [{"n": r, "fa": notes[r]} for r in sorted(used)]

    return {
        "title": data["title"],
        "colophon": [b["fa"] for b in colophon["blocks"]],
        "chapters": [{"n": c["n"], "title": c["title"]} for c in body],
        "pages": pages,
        "orphan_notes": sorted(set(notes) - seen),
    }

def fill_gaps(result):
    """Insert colophon pages 1-2 and blank pages for every hole in 1..last_page.

    The Naser edition runs 1..262; bayt_paginate emits only the 229 pages that
    had text in the Ghaemiyeh HTML. This inserts the missing 33 so navigation is
    continuous and every printed page number has a URL.

    * Pages 1-2: colophon (مشخصات کتاب) split across the two pages.
    * All other gaps: empty pages whose 'chapter' label is the title of the
      chapter they lead INTO (displayed above the blank area), and chapter_n=0
      so the starts dict is never corrupted (ch0 is not in data["chapters"]).
    """
    colophon = result["colophon"]           # list of strings
    pages    = result["pages"]              # already sorted ascending by n

    # colophon split: slightly larger first half
    mid = (len(colophon) + 1) // 2
    colo_p1 = [{"tag": "p", "fa": x} for x in colophon[:mid]]
    colo_p2 = [{"tag": "p", "fa": x} for x in colophon[mid:]]

    # pre-compute: for each gap page n, which chapter comes next?
    def next_chapter(n):
        for p in pages:
            if p["n"] > n:
                return p["chapter"]
        return pages[-1]["chapter"]

    augmented = [
        {"n": 1, "blocks": colo_p1, "chapter": "مشخصات کتاب", "chapter_n": 1, "notes": []},
        {"n": 2, "blocks": colo_p2, "chapter": "مشخصات کتاب", "chapter_n": 1, "notes": []},
    ]
    prev_n = 2
    for p in pages:
        for gap_n in range(prev_n + 1, p["n"]):
            augmented.append({"n": gap_n, "blocks": [],
                              "chapter": next_chapter(gap_n),
                              "chapter_n": 0, "notes": []})
        augmented.append(p)
        prev_n = p["n"]

    result["pages"] = augmented
    return result


if __name__ == "__main__":
    d = paginate(json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")))
    d = fill_gaps(d)
    print(json.dumps(d, ensure_ascii=False))
