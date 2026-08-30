#!/usr/bin/env python3
"""Recover a batch JSON from pages that have already been built.

  reextract.py --lang ur <built index.html ...> > batch.json

Why this exists: the translation modules (tr_<lang>_<a>_<b>.py) are working
files from whichever session produced a batch, and they are not kept. The
published pages are the durable record — they carry the Arabic and the
translation together, with markup intact — so this reads them back into the
exact shape build.py and merge_build.py expect.

That makes a template change safe: reextract the pages, re-run build.py with
the new shell, verify, and commit. No translation is ever retyped.

Unlike bihar/assets/tr/<lang>.json, which stores plain text for the search and
in-page translation layer, this preserves footnote anchors and inline markup,
so a round-trip is lossless.
"""
import argparse, json, pathlib, re, sys


def reextract(path, lang):
    src = pathlib.Path(path).read_text(encoding="utf-8")

    m = re.search(r'data-pagenum="(\d+)"', src)
    if not m:
        sys.exit(f"{path}: no data-pagenum — is this a built page?")
    pagenum = int(m.group(1))
    total = int(re.search(r'data-total="(\d+)"', src).group(1))
    volume = int(re.search(r'data-volume="(\d+)"', src).group(1))

    bm = re.search(
        r'<div class="body"[^>]*>(.*)</div>\s*\n?\s*(?:<div class="notes">|</div>)',
        src, re.S)
    if not bm:
        sys.exit(f"{path}: could not locate the body block")
    body = bm.group(1)

    pair = re.compile(
        r'<(p|h3) lang="ar" data-i="(\d+)">(.*?)</\1>'
        r'<(?:p|h3) class="tr-line" lang="' + lang + r'">(.*?)</(?:p|h3)>', re.S)
    nodes = [{"i": int(i), "tag": tag, "ar": ar, lang: tr}
             for tag, i, ar, tr in pair.findall(body)]
    if not nodes:
        sys.exit(f"{path}: no {lang} nodes found — wrong --lang?")
    if [n["i"] for n in nodes] != list(range(len(nodes))):
        sys.exit(f"{path}: data-i not contiguous after reextract")

    notes = []
    nm = re.compile(
        r'<div class="note" lang="ar" id="(fn-[\d-]+)">'
        r'<span class="note-n">\((.*?)\)</span>'
        r'<span>(.*?)<span class="tr-note-line" lang="' + lang + r'">(.*?)</span>'
        r'</span></div>', re.S)
    start = src.find('<div class="notes">')
    if start != -1:
        end = src.find('<nav class="pager">', start)
        for nid, n, ar, tr in nm.findall(src[start:end if end != -1 else len(src)]):
            notes.append({"id": nid, "n": n, "ar": ar, lang: tr})

    return {"page": pagenum, "total": total, "volume": volume,
            "nodes": nodes, "notes": notes}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pages", nargs="+")
    ap.add_argument("--lang", required=True, choices=["en", "fa", "ur"])
    a = ap.parse_args()
    out = [reextract(p, a.lang) for p in a.pages]
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
