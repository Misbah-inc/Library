#!/usr/bin/env python3
"""Pair Ghaemiyeh's HUMAN Farsi Bihar (book 14979) to the Arabic blocks.

    python bihar_fa_pair.py <bihar_fa_v<N>.htm> <volume> [--out fa-<N>.json]
                            [--report]

**Why this exists.** Volume 1's Farsi is machine translation. Ghaemiyeh
publishes «بحار الانوار / دریاهای نور», a human Farsi rendering of the SAME
edition (بيروت، دار احياء التراث العربي) for all 110 volumes, and its export
pairs the two languages page by page. Measured:

    vol   FA pages  AR pages   «N»  روایتN   anchors matched
      2        325       325   116     115            99.1%
      3        341       341    48      48           100.0%
     25        391       391    94      94           100.0%
     80        395       395   106     106           100.0%

Page numbering is IDENTICAL to the Arabic tree — same edition, same pagination —
so a page maps to a page with no searching.

**How the export is laid out.** Each printed page appears TWICE: the Arabic
side, then the Farsi side, linked by anchors rather than by position.

    Arabic side          Farsi side
    «55»                 روایت55.     then the translation
    بیان                 توضیح        then the translation

**Granularity differs, and that is the whole problem.** The Arabic tree splits a
page into `data-i` blocks; the Farsi is organised per HADITH. On volume 2, 1,242
of 2,102 Arabic blocks carry an anchor of their own; the other 860 are
continuations — the tail of a hadith that began in an earlier block or on the
previous page. They are NOT untranslated: their Farsi sits in the hadith's unit.

So this writes the unit's Farsi against the block that OPENS the hadith and
leaves the continuations empty, which is what the source actually supports.
Splitting one Farsi passage across several Arabic blocks would be inventing an
alignment the translator never made — and it would be invisible in the output,
which is the worst kind of wrong.
"""

import argparse
import html as H
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ELEM = re.compile(r"<(P|DIV|H\d)[^>]*class=(content_\w+)[^>]*>(.*?)</\1>", re.I | re.S)
MARK = re.compile(r"<P class=content_paragraph>\s*<SPAN class=content_text>"
                  r"\s*ص\s*:\s*(\d+)\s*</SPAN>\s*</P>", re.I)
AR_HAD = re.compile(r"^«\s*(\d+)\s*»")
FA_HAD = re.compile(r"^روایت\s*(\d+)\s*\.?$")
# al-Majlisi's own rubrics. CLAUDE.md's translation conventions list them:
# بیان → Elucidation, إيضاح → Clarification, أقول → I say. Handling only
# «بیان»/«توضیح» left pages 101, 115, 124 … with no Farsi at all, because
# their Farsi half opens with «إیضاح» or «أقول» and nothing matched.
FA_NOTE = re.compile(r"^(توضیح|بیان|إیضاح|ایضاح|إيضاح|أقول|اقول|شرح)\s*:?$")
BLOCK = re.compile(r'data-i="(\d+)"[^>]*>(.*?)</(?:p|h3|h4)>', re.S)


def clean(x):
    return re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", "", x))).strip()


def fa_pages(path):
    s = open(path, encoding="utf-8").read()
    body = s[s.find("<BODY"):]
    out, prev = {}, 0
    for m in MARK.finditer(body):
        lab, seg, prev = int(m.group(1)), body[prev:m.start()], m.end()
        els = [clean(e.group(3)) for e in ELEM.finditer(seg)]
        out.setdefault(lab, []).extend([e for e in els if e])
    return out


PERSIAN = re.compile(r"(?: است| های| شده| می‌| می | که | را | از | برای | این | آن |"
                     r"گوید|فرمود|روایت|کرده|کند|باشد)")


def fa_start(blocks):
    """Where the Farsi half of a page begins.

    The export prints each page twice — Arabic, then Farsi — and USUALLY the
    Farsi half opens with an anchor («روایت55.», «توضیح»). It does not always:
    a page that continues a hadith from the page before has no anchor at all,
    and the first version of this waited for one, collected nothing, and left
    55 of volume 2's 325 pages with no Farsi despite the translation being
    right there. So fall back to the language itself — the first block that
    reads as Persian prose.
    """
    anchored = next((i for i, b in enumerate(blocks)
                     if FA_HAD.match(b) or FA_NOTE.match(b)), None)
    if anchored is not None:
        return anchored
    for i, b in enumerate(blocks):
        if len(PERSIAN.findall(b)) >= 3 and len(b) > 60:
            return i
    return len(blocks)


def split_units(blocks):
    """The Farsi half of a page -> ({hadith no: text}, [بیان passages])."""
    start = fa_start(blocks)
    units, notes, cur, key = {}, [], [], None

    def flush():
        if not cur:
            return
        t = " ".join(cur).strip()
        if not t:
            return
        if key is None:
            notes.append(t)
        else:
            units[key] = (units.get(key, "") + " " + t).strip()

    for b in blocks[start:]:
        m = FA_HAD.match(b)
        if m:
            flush(); cur, key = [], int(m.group(1)); continue
        if FA_NOTE.match(b):
            flush(); cur, key = [], None; continue
        cur.append(b)
    flush()
    return units, notes


# Bihar's source sigla and the name the Farsi translator uses for each. The
# trailing block of a multi-block hadith is nearly always a SECOND chain
# («یر، بصائر الدرجات … مثله») or al-Majlisi's «أقول», and the Farsi names its
# source outright — so the cut point is evidence in both texts, not a guess.
#
# The first version of this carried four sigla, required the siglum at the very
# start of the block, and searched only forward from the previous cut: it split
# 28 of 217 blocks. These are read off the actual pages.
SIGLA = {
    "یر": "بصائر", "ثو": "ثواب", "ع": "علل", "لی": "امالی", "ما": "امالی",
    "سن": "محاسن", "شی": "عیاشی", "جا": "مجالس", "سر": "سرائر", "ن": "عیون",
    "ب": "قرب", "ل": "خصال", "نهج": "نهج", "م": "تفسیر امام", "ك": "کمال",
    "ید": "توحید", "فس": "تفسیر قمی", "مع": "معانی", "غو": "غوالی",
    "ختص": "اختصاص", "ص": "صحیفه", "كا": "کافی", "شا": "ارشاد", "ir": "",
}
AQWAL = {"أقول": "مؤلف", "اقول": "مؤلف", "بیان": "توضیح", "إیضاح": "ایضاح"}


def landmarks(ar):
    """Farsi strings that should mark where this Arabic block's text begins."""
    out = []
    m = re.match(r"^\s*(?:«\d+»\s*-\s*)?([ء-ي]{1,4})\s*[،,]", ar)
    if m and m.group(1) in SIGLA and SIGLA[m.group(1)]:
        out.append(SIGLA[m.group(1)])
    for k, v in AQWAL.items():
        if ar.startswith(k):
            out.append(v)
    return out


def split_across(fa_text, ar_blocks):
    """Divide one hadith's Farsi across the Arabic blocks it covers.

    Cuts only where a landmark from a later block is FOUND in the Farsi. If no
    landmark is found the whole passage stays on the opening block, which is
    the conservative behaviour — a wrong split is invisible on the page, so it
    must never be guessed.
    """
    if len(ar_blocks) <= 1 or not fa_text:
        return [fa_text] + [""] * (len(ar_blocks) - 1), 0
    cuts, confident = [0], 0
    pos = 0
    for b in ar_blocks[1:]:
        cut = None
        for lm in landmarks(b):
            j = fa_text.find(lm, pos + 10)
            if j > 0:
                cut = j
                break
        if cut is not None:
            cuts.append(cut); pos = cut; confident += 1
        else:
            cuts.append(None)
    out, prev = [], 0
    real = [c for c in cuts if c is not None]
    for k, c in enumerate(cuts):
        if c is None:
            out.append("")
            continue
        nxt = next((x for x in cuts[k + 1:] if x is not None), len(fa_text))
        out.append(fa_text[c:nxt].strip())
    return out, confident


def pair(fa_path, vol, lib, split=True):
    fa = fa_pages(fa_path)
    root = pathlib.Path(lib) / str(vol)
    out = {}
    stat = {"blocks": 0, "hadith": 0, "bayan": 0, "split": 0, "empty": 0,
            "pages": 0, "positional": 0}
    for d in sorted((p for p in root.iterdir() if p.is_dir() and p.name.isdigit()),
                    key=lambda p: int(p.name)):
        n = int(d.name)
        h = (d / "index.html").read_text(encoding="utf-8")
        mb = re.search(r'<div class="body">(.*?)</div>\s*</div>\s*<nav', h, re.S)
        if not mb:
            continue
        stat["pages"] += 1
        units, notes = split_units(fa.get(n, []))
        blocks = [(int(m.group(1)), clean(m.group(2)))
                  for m in BLOCK.finditer(mb.group(1))]
        stat["blocks"] += len(blocks)
        rows = [{"i": i, "text": "", "src": ""} for i, _ in blocks]
        # group consecutive blocks under the hadith (or rubric) that opens them
        groups, cur = [], None
        ni = 0
        for k, (i, t) in enumerate(blocks):
            hm = AR_HAD.match(t)
            if hm and int(hm.group(1)) in units:
                cur = {"kind": "h", "key": int(hm.group(1)), "idx": [k]}
                groups.append(cur)
            elif t.startswith("بیان") and ni < len(notes):
                cur = {"kind": "n", "key": ni, "idx": [k]}; ni += 1
                groups.append(cur)
            elif cur:
                cur["idx"].append(k)
            else:
                groups.append({"kind": "?", "key": None, "idx": [k]})
                cur = groups[-1]
        for g in groups:
            if g["kind"] == "h":
                txt = units[g["key"]]; stat["hadith"] += 1
            elif g["kind"] == "n":
                txt = notes[g["key"]]; stat["bayan"] += 1
            else:
                # no anchor anywhere on this page: a run of continuation
                # blocks. If the Farsi half yielded exactly as many chunks,
                # pair them in order — pages 88 and 101 of volume 2 are this
                # case, and they came out wholly blank before.
                left = [x for x in notes[ni:]]
                if len(left) == len(g["idx"]) and left:
                    for k, t in zip(g["idx"], left):
                        rows[k]["text"] = t; rows[k]["src"] = "positional"
                    ni += len(left); stat["positional"] += len(left)
                continue
            parts, conf = (split_across(txt, [blocks[k][1] for k in g["idx"]])
                           if split else ([txt] + [""] * (len(g["idx"]) - 1), 0))
            stat["split"] += conf
            for k, part in zip(g["idx"], parts):
                if part:
                    rows[k]["text"] = part
                    rows[k]["src"] = (f"h{g['key']}" if g["kind"] == "h" else "bayan")
        stat["empty"] += sum(1 for r in rows if not r["text"])
        out[str(n)] = rows
    return out, stat


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("export")
    ap.add_argument("volume", type=int)
    ap.add_argument("--lib", default="G:/My Drive/Misbah Library/Library/bihar")
    ap.add_argument("--out")
    a = ap.parse_args()
    out, st = pair(a.export, a.volume, a.lib)
    filled = st["blocks"] - st["empty"]
    cov = 100 * filled / max(st["blocks"], 1)
    print(f"volume {a.volume}: {st['pages']} pages, {st['blocks']:,} Arabic blocks")
    print(f"  blocks carrying Farsi  : {filled:,}  ({cov:.1f}%)")
    print(f"     hadith units        : {st['hadith']:,}")
    print(f"     rubric passages     : {st['bayan']:,}")
    print(f"     split on a landmark : {st['split']:,}")
    print(f"     positional (no anchor on page): {st['positional']:,}")
    print(f"  still empty            : {st['empty']:,}")
    if a.out:
        pathlib.Path(a.out).write_text(json.dumps(out, ensure_ascii=False),
                                       encoding="utf-8")
        print(f"  -> {a.out}")


if __name__ == "__main__":
    main()
