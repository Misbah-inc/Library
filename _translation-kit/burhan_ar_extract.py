#!/usr/bin/env python3
"""Ghaemiyeh «البرهان في تفسير القرآن» export -> burhan_v<N>.json, one volume.

    python burhan_ar_extract.py <export.htm> <volume> [--abl <abl_burhan dir>]

Why this book needs its own extractor rather than `bihar_ar_extract.py`.
The export is the same publisher and the same shape — `content_paragraph`,
`content_h3/h4/h5`, a «ص: N» page marker — but three of its conventions are
inverted, and each one silently destroys pages if the Bihar rules are reused:

  1. **The marker OPENS its page here; in Bihar it CLOSES it.** A page is
     «البرهان في تفسير القرآن، ج 1، ص: 217» followed by that page's text, and
     page 216's footnotes sit BEFORE the marker, not after. Verified against
     ablibrary page for page: their 216 ends where the marker begins and their
     217 begins with the paragraph after it. CLAUDE.md's جامع المقدمات note
     says to check the tail of a new export before assuming either way; this
     is the export that proves why.
  2. **The running header is split across paragraphs on 4% of pages** — at an
     arbitrary point, sometimes MID-WORD («الب» + «رهان في تفسير القرآن، ج 2»),
     and sometimes leaving the page NUMBER alone in its own paragraph. Matching
     it inside a single paragraph finds 96% of markers and merges the rest into
     their neighbour, which reads as 118 missing pages. `reflow_markers()`
     therefore matches across a window of up to four paragraphs — anchored so
     the header must BEGIN in the window's first paragraph, or the window
     reaches over ordinary prose to the next page's header and republishes that
     prose on the wrong page.
  3. **There are no `content_note` divs at all.** Footnotes are plain
     paragraphs after a `______` rule, and there are two kinds, exactly as in
     ablibrary's التهذيب: «8- تفسير القمّي 1: 29.» is the editor's تخريج keyed
     to the hadith's own bracket number, and «(1) في «س»: عن.» is a numbered
     footnote answering a «1» marker in the body. Flattening the two into one
     numbered list is what made the parentheses look scrambled on التهذيب.

**ablibrary (books 1939-1943) is the same edition with the same pagination**
and is used here as the authority on which printed pages EXIST. Ghaemiyeh drops
one running header roughly every 256 pages — labels 93, 349, 605 and 861 are
absent in almost every volume — and omits blank pages entirely. Neither is
recoverable from the export alone: with no header there is nothing in the
markup to say a page ended. So `--abl` supplies the missing cut, located by
matching that page's opening words, and the blank pages are emitted as blanks
rather than left as holes a citation would 404 on.
"""

import argparse
import html as htmlmod
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

ELEM = re.compile(r"<(P|DIV|H\d)[^>]*class=(content_\w+)[^>]*>(.*?)</\1>", re.I | re.S)
RULE = re.compile(r"^_{5,}$")
LEAD = re.compile(r"\s*\.{3,}\s*ص\s*:\s*\d+\s*$")
N_SRC = re.compile(r"^\s*(\d+)\s*-\s")
N_FN = re.compile(r"^\s*\(\s*(\d+)\s*\)\s")
DIA = re.compile("[\u064b-\u0652\u0670\u0640]")
PROMO = "تعريف مرکز"
# Ghaemiyeh's own catalogue record, in Persian, ahead of the book's first
# page. It is the publisher's metadata, not al-Bahrani's text, and because it
# sits before the first marker the repair pass otherwise adopts it as the
# printed title page — volumes 2-5 published «شابك 964-7866-20-8» as page 1.
CATALOGUE = re.compile(r"^\s*(?:سرشناسه|عنوان و نام|مشخصات|شابك|وضعيت فهرست|"
                       r"يادداشت|موضوع|رده بندي|شماره كتابشناسي|آدرس ثابت)")
TITLE = "البرهان في تفسير القرآن"


def clean(frag):
    t = re.sub(r"<BR\s*/?>", " ", frag, flags=re.I)
    t = re.sub(r"<[^>]+>", "", t)
    t = htmlmod.unescape(t)
    return re.sub(r"[ \t\r\n]+", " ", t).strip()


def fold(s):
    """Whitespace-, diacritic- and orthography-insensitive key.

    Ghaemiyeh writes «عز و جل» where ablibrary writes «عزوجل», and it vocalises
    where ablibrary does not. CLAUDE.md's al-Faqih note is exact: comparing
    Arabic across these two sources with whitespace NORMALISED rather than
    REMOVED gives badly wrong answers three times running.
    """
    s = DIA.sub("", s)
    for a, b in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ى", "ي"), ("ة", "ه")):
        s = s.replace(a, b)
    return re.sub(r"[^\u0621-\u064a]", "", s)


def items_of(path):
    raw = open(path, encoding="utf-8").read()
    body = raw[raw.find("<BODY"):] if "<BODY" in raw else raw
    out = []
    for m in ELEM.finditer(body):
        cls, t = m.group(2), clean(m.group(3))
        if not t:
            continue
        hm = re.match(r"content_h(\d)$", cls)
        if hm:
            out.append(["h", int(hm.group(1)), LEAD.sub("", t)])
        elif RULE.match(t):
            out.append(["rule", 0, ""])
        else:
            out.append(["p", 0, t])
    return out


def reflow_markers(items, volume):
    pat = re.compile(TITLE.replace(" ", r"\s*") + r"\s*[،,]\s*(ج\s*%d|مقدمة)"
                     r"\s*[،,]\s*ص\s*:\s*(\d+)" % volume)
    out, i, joined = [], 0, 0
    while i < len(items):
        if items[i][0] != "p":
            out.append(items[i])
            i += 1
            continue
        hit = None
        for span in (1, 2, 3, 4):
            chunk = items[i:i + span]
            if len(chunk) < span or any(c[0] != "p" for c in chunk):
                break
            m = pat.search(" ".join(c[2] for c in chunk))
            if m and m.start() < len(chunk[0][2]) + 1:
                hit = (span, m)
                break
        if not hit:
            out.append(items[i])
            i += 1
            continue
        span, m = hit
        text = " ".join(c[2] for c in items[i:i + span])
        before, after = text[:m.start()].strip(), text[m.end():].strip()
        if before:
            out.append(["p", 0, before])
        out.append(["mark", int(m.group(2)),
                    "مقدمة" if "مقدمة" in m.group(1) else "main"])
        if after:
            out.append(["p", 0, after])
        joined += span > 1
        i += span
    return out, joined


def split_notes(lines):
    """Note paragraphs -> [{n, ar, k}] with k="fn" (anchored) or "src" (تخريج).

    A note wraps across paragraphs — «(2) في المصدر: أحمد بن عيسى،» continues
    in the next one — so a paragraph opening with neither form joins the one
    before it.
    """
    out = []
    for t in lines:
        m = N_FN.match(t)
        if m:
            out.append({"n": int(m.group(1)), "ar": t[m.end():].strip(), "k": "fn"})
            continue
        m = N_SRC.match(t)
        if m:
            out.append({"n": int(m.group(1)), "ar": t[m.end():].strip(), "k": "src"})
            continue
        if out:
            out[-1]["ar"] = (out[-1]["ar"] + " " + t).strip()
        else:
            out.append({"n": 0, "ar": t, "k": "src"})
    return [x for x in out if x["ar"]]


def raw_pages(path, volume):
    """Ghaemiyeh's own pages, plus whatever precedes its first marker."""
    items, joined = reflow_markers(items_of(path), volume)
    pages, cur, pre = [], None, []

    def put(t):
        if cur is None:
            pre.append(t)
        else:
            (cur["notes"] if cur["in_notes"] else cur["body"]).append(t)

    for kind, lvl, t in items:
        if kind == "rule":
            if cur:
                cur["in_notes"] = True
            continue
        if kind == "mark":
            if cur:
                pages.append(cur)
            cur = {"part": t, "n": lvl, "body": [], "notes": [], "in_notes": False}
            continue
        if kind == "p" and ((PROMO in t and len(t) < 4000)
                            or (cur is None and CATALOGUE.match(t))):
            continue
        # content_h3 is the SURAH-level division («سورة البقرة مدنية»,
        # «المستدرك (سورة آل عمران)»); h4 and h5 are the verse groups
        # within it («سورة البقرة(2): آية 195»). Collapsing all three to
        # one level — which is what Bihar's +1 mapping does here — leaves
        # the contents drawer as 400 undifferentiated verse rows with no
        # surah headings among them to navigate by.
        put(("H", 3 if lvl <= 3 else 4, t) if kind == "h" else t)
    if cur:
        pages.append(cur)
    return pages, pre, joined


def cut_in(page, key):
    """Split one over-long page where ablibrary says the next page opens.

    Returns (tail_body, tail_notes) moved off `page`, or None. The opening is
    looked for in the NOTES list as well as the body: when the header is gone
    the rule has already fired, so the next page's first paragraphs land in the
    previous page's footnotes — which is what made this look like lost text.
    """
    for fld in ("body", "notes"):
        for i, b in enumerate(page[fld]):
            if not key:
                continue
            # A surah-title page is a single H3 in this export («سورة الفرقان»
            # is all of printed page 107), so headings have to be candidates
            # too — skipping tuples leaves those pages unplaceable.
            f = fold(b[2] if isinstance(b, tuple) else b)
            if key not in f:
                continue
            if f.index(key) == 0:                      # clean paragraph break
                moved = page[fld][i:]
                page[fld] = page[fld][:i]
                if fld == "body":
                    tail = (moved + page["notes"], [])
                    page["notes"] = []
                    return tail
                return (moved, [])
            # the printed page breaks mid-paragraph: split the paragraph itself
            if isinstance(b, tuple):
                continue
            n, at = 0, None
            for j, ch in enumerate(b):
                if fold(ch):
                    if n == f.index(key):
                        at = j
                        break
                    n += 1
            if at is None:
                continue
            head, rest = b[:at].strip(), b[at:].strip()
            moved = ([rest] if rest else []) + page[fld][i + 1:]
            page[fld] = page[fld][:i] + ([head] if head else [])
            if fld == "body":
                tail = (moved + page["notes"], [])
                page["notes"] = []
                return tail
            return (moved, [])
    return None


def repair(pages, pre, abl, volume):
    """Add the pages Ghaemiyeh has no header for, using ablibrary's page list.

    Three kinds are added, and each is reported separately because they mean
    different things: a page recovered by splitting a merged one (real text
    that was on the wrong page), a page taken from the run before the export's
    first marker (the title page and the opening of volumes 2-5), and a page
    that is BLANK in the printed edition, which is published as a blank rather
    than left as a hole — CLAUDE.md's rule, so a citation never 404s.
    """
    by = {p["n"]: p for p in pages if p["part"] == "main"}
    fm = {p["n"]: p for p in pages if p["part"] == "مقدمة"}
    report = {"split": [], "pre": [], "blank": [], "unplaced": [], "fm": []}
    want = sorted(int(k) for k in abl if k.isdigit())

    # The foreword is paginated separately (مقدمة 7-66) and loses its own first
    # page the same way the main text does: page 7 opens before the export's
    # first «مقدمة، ص: 8» header, so nothing delimits it.
    fm_want = sorted(int(k.split()[1]) for k in abl
                     if k.startswith("مقدمة") and k.split()[-1].isdigit())

    # The run before the first marker holds SEVERAL pages — the title page and
    # then, in volumes 2-5, everything up to the export's first header. So its
    # cut points are all located first and the run sliced BETWEEN them. Taking
    # each page as "everything from its own opening onwards" and truncating,
    # which is the obvious way to write this, gives the first such page the
    # whole run and leaves every later one with nothing.
    pre_at, cur = {}, 0
    for L in want:
        if L in by:
            continue
        src = abl[str(L)]["body"].strip()
        if not src:
            continue
        k = fold(src.split(chr(10))[0])[:32]
        # The paragraph must BEGIN with the page's opening, not merely contain
        # it. ablibrary's v1 page 2 is «بسم الله الرحمن الرحيم» alone, and that
        # phrase also sits mid-sentence in the foreword's first paragraph — a
        # substring test handed the whole of مقدمة page 7 to printed page 2.
        hit = next((i for i in range(cur, len(pre))
                    if isinstance(pre[i], str) and k
                    and fold(pre[i]).startswith(k)), None)
        if hit is not None:
            pre_at[L] = hit
            cur = hit + 1
    order = sorted(pre_at, key=lambda L: pre_at[L])
    pre_slice = {}
    for j, L in enumerate(order):
        end = pre_at[order[j + 1]] if j + 1 < len(order) else len(pre)
        pre_slice[L] = pre[pre_at[L]:end]

    for L in want:
        if L in by:
            continue
        src = abl[str(L)]["body"].strip()
        if not src:
            by[L] = {"part": "main", "n": L, "body": [], "notes": [],
                     "in_notes": False, "blank": True}
            report["blank"].append(L)
            continue
        # Several opening lines, not just the first. Where a printed page
        # breaks mid-sentence the two editions spell the joint differently
        # («عز و جل» against «عزوجل»), so the first line can be unfindable
        # while the second is exact — which is the whole of the difference
        # between placing التهذيب-style page 349 and publishing it blank.
        prev = by.get(L - 1)
        got = None
        for ln in [x for x in src.split(chr(10)) if x.strip()][:6]:
            got = cut_in(prev, fold(ln)[:28]) if prev else None
            if got:
                break
        if got:
            by[L] = {"part": "main", "n": L, "body": got[0], "notes": got[1],
                     "in_notes": False}
            report["split"].append(L)
            continue
        if L in pre_slice:
            by[L] = {"part": "main", "n": L, "body": pre_slice[L],
                     "notes": [], "in_notes": False}
            report["pre"].append(L)
            continue
        # Printed page with no locatable Ghaemiyeh text: publish it blank
        # rather than leave a hole. Its text, where the export has any, stays
        # on the preceding page — so this is a page BOUNDARY that could not be
        # placed, not text that was lost, and the audit proves which.
        by[L] = {"part": "main", "n": L, "body": [], "notes": [],
                 "in_notes": False, "blank": True}
        report["unplaced"].append(L)
    for L in fm_want:
        if L in fm:
            continue
        src = abl["مقدمة %d" % L]["body"].strip()
        got = None
        for ln in [x for x in src.split(chr(10)) if x.strip()][:6]:
            got = cut_in(fm[L - 1], fold(ln)[:28]) if (L - 1) in fm else None
            if got:
                break
        if got is None and pre:
            k = fold(src.split(chr(10))[0])[:28] if src else ""
            hit = next((i for i in range(len(pre))
                        if isinstance(pre[i], str) and k
                        and fold(pre[i]).startswith(k)), None)
            if hit is not None:
                got = (pre[hit:], [])
        if got is None:
            continue
        fm[L] = {"part": "مقدمة", "n": L, "body": got[0], "notes": got[1],
                 "in_notes": False}
        report["fm"].append(L)

    out = [fm[n] for n in sorted(fm)]
    out += [by[n] for n in sorted(by)]
    return out, report


def finish(pages, volume):
    """Page dicts -> the JSON shape the builder reads."""
    done = []
    for p in pages:
        blocks, i = [], 0
        for b in p["body"]:
            if isinstance(b, tuple):
                blocks.append({"i": i, "tag": "h%d" % b[1], "ar": b[2]})
            else:
                blocks.append({"i": i, "tag": "p", "ar": b})
            i += 1
        # ALWAYS a string. The builders index `ids` and join it onto a
        # path, so an int id works everywhere until the first front-matter
        # page makes the list mixed.
        pid = ("fm-%d" % p["n"]) if p["part"] == "مقدمة" else str(p["n"])
        done.append({"id": pid, "n": p["n"], "blocks": blocks,
                     "notes": split_notes([x for x in p["notes"]
                                           if isinstance(x, str)])})
    return {"volume": volume, "pages": done}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("export")
    ap.add_argument("volume", type=int)
    ap.add_argument("--abl", help="directory holding burhan_v<N>.json from ablibrary")
    ap.add_argument("--out")
    a = ap.parse_args()

    pages, pre, joined = raw_pages(a.export, a.volume)
    rep = None
    if a.abl:
        abl = json.loads((pathlib.Path(a.abl) / f"burhan_v{a.volume}.json")
                         .read_text(encoding="utf-8"))
        pages, rep = repair(pages, pre, abl, a.volume)
    data = finish(pages, a.volume)

    n_bl = sum(len(p["blocks"]) for p in data["pages"])
    n_fn = sum(1 for p in data["pages"] for x in p["notes"] if x["k"] == "fn")
    n_sr = sum(1 for p in data["pages"] for x in p["notes"] if x["k"] == "src")
    n_hd = sum(1 for p in data["pages"] for b in p["blocks"] if b["tag"] != "p")
    print(f"v{a.volume}: {len(data['pages'])} pages  {n_bl} blocks  {n_hd} headings  "
          f"{n_fn} fn + {n_sr} src notes   (split headers rejoined: {joined})")
    if rep:
        print(f"   repaired: {len(rep['split'])} split from a merged page, "
              f"{len(rep['pre'])} before the first marker, "
              f"{len(rep['blank'])} blank in print, "
              f"{len(rep['fm'])} front matter, "
              f"{len(rep['unplaced'])} UNPLACED {rep['unplaced'][:10]}")
    if a.out:
        pathlib.Path(a.out).write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return 1 if rep and rep["unplaced"] else 0


if __name__ == "__main__":
    sys.exit(main())
