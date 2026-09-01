#!/usr/bin/env python3
"""Extract Bayt al-Ahzan (Ghaemiyeh HTML export) into the kit's batch JSON shape.

  bayt_extract.py <source.htm> > bayt.json

The Ghaemiyeh export is flat: <h1> title, <h2> chapters, <h3> subsections, and
prose separated by <br>. This turns that into

  [{"n":1,"title":...,"blocks":[{"tag":"h3"|"p","i":N,"fa":...}, ...]}, ...]

'fa' rather than 'ar' because this book's source language is Persian — unlike
every other book in the library, whose source of record is Arabic.
"""
import argparse, html, json, pathlib, re, sys

SRC_LANG = "fa"


def clean(fragment):
    """HTML fragment -> plain text, preserving nothing but the words."""
    t = re.sub(r"(?is)<br\s*/?>", "\n", fragment)
    t = re.sub(r"(?s)<[^>]+>", "", t)
    t = html.unescape(t)
    t = t.replace("‌", "‌")            # keep ZWNJ, Persian needs it
    t = re.sub(r"[ \t ]+", " ", t)
    return [ln.strip() for ln in t.split("\n") if ln.strip()]


def extract(path):
    s = pathlib.Path(path).read_text(encoding="utf-8-sig", errors="replace")
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", "", s)

    m = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", s)
    book_title = " ".join(clean(m.group(1))) if m else ""

    # split into chapters on <h2>, then walk each chapter for <h3> + prose
    parts = re.split(r"(?is)(<h2[^>]*>.*?</h2>)", s)
    chapters = []
    for i in range(1, len(parts), 2):
        title = " ".join(clean(parts[i]))
        rest = parts[i + 1] if i + 1 < len(parts) else ""

        blocks, idx = [], 0
        # a chapter is a sequence of optional <h3> headings and prose between them
        chunks = re.split(r"(?is)(<h3[^>]*>.*?</h3>|<h4[^>]*>.*?</h4>)", rest)
        for c in chunks:
            if not c or not c.strip():
                continue
            hm = re.match(r"(?is)<(h3|h4)[^>]*>(.*?)</\1>", c)
            if hm:
                txt = " ".join(clean(hm.group(2)))
                if txt:
                    # the export uses uppercase <H3>; normalise or the builder,
                    # which tests lowercase tags, silently demotes every heading
                    blocks.append({"tag": hm.group(1).lower(), "i": idx,
                                   SRC_LANG: txt})
                    idx += 1
            else:
                for line in clean(c):
                    blocks.append({"tag": "p", "i": idx, SRC_LANG: line})
                    idx += 1
        chapters.append({"n": len(chapters) + 1, "title": title, "blocks": blocks})

    return {"title": book_title, "chapters": chapters}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("--stats", action="store_true")
    a = ap.parse_args()
    data = extract(a.source)
    if a.stats:
        tot = sum(len(c["blocks"]) for c in data["chapters"])
        chars = sum(len(b[SRC_LANG]) for c in data["chapters"] for b in c["blocks"])
        print(f"title    : {data['title']}", file=sys.stderr)
        print(f"chapters : {len(data['chapters'])}", file=sys.stderr)
        print(f"blocks   : {tot}", file=sys.stderr)
        print(f"chars    : {chars:,}", file=sys.stderr)
        for c in data["chapters"]:
            heads = sum(1 for b in c["blocks"] if b["tag"] != "p")
            ch = sum(len(b[SRC_LANG]) for b in c["blocks"])
            print(f"  {c['n']:>3}  blocks={len(c['blocks']):>4} heads={heads:>3} "
                  f"chars={ch:>7,}  {c['title'][:52]}", file=sys.stderr)
    print(json.dumps(data, ensure_ascii=False))
