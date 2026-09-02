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

if __name__ == "__main__":
    d = paginate(json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")))
    print(json.dumps(d, ensure_ascii=False))
