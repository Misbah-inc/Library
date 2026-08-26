#!/usr/bin/env python3
"""Extract translatable content from a Misbah Library Arabic page.

Emits compact JSON: page number, the data-i indexed nodes, and footnotes.
Everything else in the source (edge nav, chrome, cite block) is shell that
build.py regenerates, so it is deliberately dropped here.
"""
import json, re, sys, pathlib

BODY = re.compile(r'<div class="body"[^>]*>(.*?)</div>\s*(?=<div class="notes">|\n\s*\n|\s*</div>)', re.S)
NODE = re.compile(r'<(p|h3)([^>]*?)data-i="(\d+)"([^>]*?)>(.*?)</\1>', re.S)
NOTE = re.compile(
    r'<div class="note"[^>]*id="(fn-[\d-]+)"[^>]*>'
    r'<span class="note-n">\((.*?)\)</span>'
    r'<span>(.*?)</span>\s*</div>', re.S)
NOTES_START = '<div class="notes">'


def extract(path):
    src = pathlib.Path(path).read_text(encoding="utf-8")

    m = re.search(r'data-pagenum="(\d+)"', src)
    pagenum = int(m.group(1)) if m else None
    m = re.search(r'data-total="(\d+)"', src)
    total = int(m.group(1)) if m else 231

    body_m = BODY.search(src)
    body = body_m.group(1) if body_m else ""

    nodes = []
    for m in NODE.finditer(body):
        tag, _pre, idx, _post, inner = m.groups()
        nodes.append({"i": int(idx), "tag": tag, "ar": inner.strip()})
    nodes.sort(key=lambda n: n["i"])

    # Slice from the notes marker to the pager and let NOTE find them all;
    # a non-greedy block regex truncates at the first note's closing divs.
    notes = []
    start = src.find(NOTES_START)
    if start != -1:
        end = src.find('<nav class="pager">', start)
        region = src[start:end if end != -1 else len(src)]
        for m in NOTE.finditer(region):
            nid, num, text = m.groups()
            notes.append({"id": nid, "n": num, "ar": text.strip()})

    return {"page": pagenum, "total": total, "nodes": nodes, "notes": notes}


if __name__ == "__main__":
    out = [extract(p) for p in sys.argv[1:]]
    print(json.dumps(out if len(out) > 1 else out[0], ensure_ascii=False, indent=1))
