#!/usr/bin/env python3
"""Finish the ي/ى repair OUTSIDE `<div class="body">`, where it was scoped out.

    python bihar_chrome_fix.py --vol N [--write]
    python bihar_chrome_fix.py --toc [--write]

`bihar_yeh_fix.py` deliberately edited nothing but the body, because the page
chrome carries `data-fa` and `data-ur` attributes holding GENUINE Persian and
Urdu — «علامه محمدباقر مجلسی» is Persian and its ی is correct. A file-wide
replacement would have corrupted the language switcher on 44,306 pages while
the Arabic looked perfect.

But three things outside the body are ARABIC and were left in the old spelling:

  1. `<meta name="description">` and `og:description` — an excerpt of the body.
  2. `bihar/assets/toc.json`, the contents drawer: 20,026 ی across 5,480 of
     6,771 Arabic `title` fields. Its `fa`/`ur`/`en` fields must NOT change.
  3. the 110 `bihar/<vol>/index.html` chapter lists.

**Nothing here is inferred.** Each is DERIVED from text that is already fixed:
the description is rebuilt from the page's own repaired body exactly as
`bihar_ar_build.description()` builds it, and a toc title is taken from the
heading on its own page. Measured before writing: 200/200 descriptions and
300/300 toc rows reproduce, 0 mismatches. A row that does not reproduce is
LEFT ALONE and counted — never guessed at.

It also closes two residues the four-tier pass could not settle, both decidable
from orthography rather than from context:

  * «شی» / «الشی» before «ء» is شيء. «شىء» is not an Arabic spelling.
  * «علی» before «بن» is the name عليّ, never the preposition على.

Everything else it left as ی stays ی — «روى»/«روي» and «أبي»/«أبى» are both
real words and a confident wrong guess is worse than a visibly foreign letter.
"""

import argparse
import collections
import concurrent.futures
import html
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

LIB = pathlib.Path(__file__).resolve().parent.parent
BODY = re.compile(r'(<div class="body">)(.*?)(</div>\s*</div>\s*<nav)', re.S)
NOTES = re.compile(r'<div class="notes">')
FNREF = re.compile(r'<a class="fnref"[^>]*>.*?</a>', re.S)
TAG = re.compile(r"<[^>]+>")
DESC = re.compile(r'(<meta name="description" content=")([^"]*)(")')
OGD = re.compile(r'(<meta property="og:description" content=")([^"]*)(")')
HEAD = re.compile(r"<h[2-6][^>]*>(.*?)</h[2-6]>", re.S)
LANGATTR = re.compile(r'data-(fa|ur|en)="([^"]*)"')
WORD = re.compile("[ء-يىًٰ-ْیک]+")
DIA = re.compile("[ً-ْٰـ]")

FY, PK, AY, AK = "ی", "ک", "ي", "ك"
HAMZA, BIN = "ء", "بن"
SHIN, ALSHIN = "ش", "الش"
AYNLAM = "عل"


def fold(s):
    """Spelling-neutral: the three yeh forms and the two kafs collapse.

    Every edit this script makes is invisible to `fold`, so `fold(new) ==
    fold(old)` is a total guard that no TEXT changed — only letter forms.
    """
    for a, b in ((FY, AY), ("ى", AY), (PK, AK)):
        s = s.replace(a, b)
    return s


def tfold(s):
    """As `fold`, but also drops diacritics and normalises hamza — for
    matching a toc title against the heading it was built from."""
    s = DIA.sub("", fold(TAG.sub("", s)))
    for a, b in (("أ", "ا"), ("إ", "ا"),
                 ("آ", "ا"), ("ة", "ه")):
        s = s.replace(a, b)
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------------- body residue

def fix_residue(text, stat):
    """The two cases orthography settles without any context lookup."""
    toks = list(WORD.finditer(text))
    nxt = {}
    for i, m in enumerate(toks):
        nxt[m.start()] = (DIA.sub("", toks[i + 1].group(0))
                          if i + 1 < len(toks) else "")

    def rep(m):
        w = m.group(0)
        bare = DIA.sub("", w)
        if not bare.endswith(FY):
            return w
        after = nxt.get(m.start(), "")
        stem = bare[:-1]
        key = None
        if after == HAMZA and stem in (SHIN, ALSHIN):
            key = "shay"
        elif after == BIN and stem == AYNLAM:
            key = "ali_bin"
        if key is None:
            return w
        stat[key] += 1
        i = w.rfind(FY)
        return w[:i] + AY + w[i + 1:]

    return WORD.sub(rep, text)


# ------------------------------------------------------------- description

def derive_desc(body):
    """Exactly `bihar_ar_build.description()`, read off the repaired page."""
    m = NOTES.search(body)
    t = body[:m.start()] if m else body
    t = html.unescape(TAG.sub(" ", FNREF.sub("", t)))
    t = re.sub(r"\[\d+\]", "", t)
    return re.sub(r"\s+", " ", t).strip()[:150]


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def audit_lang_attrs(body, stat):
    """Volume 1 wraps its headings in a span carrying data-fa / data-ur, and
    that span sits INSIDE the body — inside the region the yeh passes edited.
    Those attributes hold genuine Persian and Urdu.

    Both passes only ever WRITE ي or ى, so a Persian/Urdu attribute containing
    either is proof one was damaged. Nothing else in this file can detect that,
    and the pages are already written, so this is the check that closes it.
    """
    for lang, val in LANGATTR.findall(body):
        if lang == "en":
            continue
        stat["langattr"] += 1
        if "ى" in val or "ي" in val:
            stat["langattr_DAMAGED"] += 1
            print(f"   !! data-{lang} carries an Arabic yeh: {val[:70]}")


def do_page(src, stat):
    m = BODY.search(src)
    if not m:
        stat["no_body"] += 1
        return src
    audit_lang_attrs(m.group(2), stat)
    body = fix_residue(m.group(2), stat)
    new = src[:m.start(2)] + body + src[m.end(2):]

    want = derive_desc(body)
    for pat in (DESC, OGD):
        dm = pat.search(new)
        if not dm:
            continue
        cur = html.unescape(dm.group(2))
        if cur == want:
            stat["desc_already"] += 1
        elif fold(cur) == fold(want):
            new = new[:dm.start(2)] + esc(want) + new[dm.end(2):]
            stat["desc_fixed"] += 1
        else:
            # The derivation disagrees about the TEXT, not just the letters.
            # Leave it: a description is not worth inventing.
            stat["desc_left"] += 1
    return new


def blank(s):
    """Punch out the three regions this script is allowed to touch."""
    s = BODY.sub(lambda m: m.group(1) + "\x00" + m.group(3), s, count=1)
    s = DESC.sub(lambda m: m.group(1) + "\x00" + m.group(3), s)
    s = OGD.sub(lambda m: m.group(1) + "\x00" + m.group(3), s)
    return s


def guard(old, new):
    """Prove only letter forms changed, and only where intended.

    `fold` is blind to every edit made here, so an inequality means real text
    moved. The second assertion is what stops a stray regex from reaching
    `data-fa` — those bytes must survive untouched.
    """
    assert fold(old) == fold(new), "TEXT changed, not just letter forms"
    assert blank(old) == blank(new), "chrome outside the edited regions changed"


# --------------------------------------------------------------------- toc

def page_headings(href):
    f = LIB / href.strip("/") / "index.html"
    try:
        src = f.read_text(encoding="utf-8")
    except OSError:
        return {}
    m = BODY.search(src)
    if not m:
        return {}
    out = {}
    for h in HEAD.findall(m.group(2)):
        out.setdefault(tfold(h), re.sub(r"\s+", " ", TAG.sub("", h)).strip())
    return out


def do_toc(write):
    p = LIB / "bihar/assets/toc.json"
    rows = json.loads(p.read_text(encoding="utf-8"))
    fa0 = sum(r.get("fa", "").count(FY) for r in rows)
    ur0 = sum(r.get("ur", "").count(FY) for r in rows)
    stat = collections.Counter()
    # Every row needs the headings of its own page, and these reads are the
    # whole cost of this pass — serial, over Drive, they dominate everything.
    need = sorted({r.get("href", "") for r in rows
                   if FY in r.get("title", "") or PK in r.get("title", "")})
    print(f"   reading {len(need):,} pages for their headings...", flush=True)
    with concurrent.futures.ThreadPoolExecutor(32) as ex:
        cache = dict(zip(need, ex.map(page_headings, need)))
    for r in rows:
        t = r.get("title", "")
        if FY not in t and PK not in t:
            stat["clean"] += 1
            continue
        href = r.get("href", "")
        hit = cache[href].get(tfold(t))
        if hit and fold(hit) == fold(t):
            if hit != t:
                r["title"] = hit
                stat["fixed"] += 1
            else:
                stat["clean"] += 1
        else:
            stat["left"] += 1
    print(f"toc.json: {len(rows):,} rows")
    print(f"   titles already correct        {stat['clean']:>6,}")
    print(f"   titles taken from their page  {stat['fixed']:>6,}")
    print(f"   LEFT (no heading matched)     {stat['left']:>6,}")
    print(f"   ی left in Arabic titles       "
          f"{sum(r.get('title', '').count(FY) for r in rows):>6,}")
    fa1 = sum(r.get("fa", "").count(FY) for r in rows)
    ur1 = sum(r.get("ur", "").count(FY) for r in rows)
    print(f"   ی in fa/ur fields: {fa0}/{ur0} before, {fa1}/{ur1} after")
    assert (fa0, ur0) == (fa1, ur1), "Persian/Urdu toc fields were altered"
    if write:
        p.write_text(json.dumps(rows, ensure_ascii=False, indent=1),
                     encoding="utf-8", newline="")
        print("   written")


def do_vindex(write):
    """The 110 volume index pages carry their chapter rows inline, as
    `<span data-ar="TITLE">TITLE</span>` — the title twice per row. They are
    the same strings as toc.json's, so the CORRECTED toc is the lookup and
    nothing is inferred a second time.

    Four `data-fa` / `data-ur` per page hold genuine Persian and Urdu. They
    survive because a replacement only ever fires on a string that folds equal
    to an Arabic toc title, and is counted before and after regardless.
    """
    rows = json.loads((LIB / "bihar/assets/toc.json").read_text(encoding="utf-8"))
    by_vol = collections.defaultdict(dict)
    for r in rows:
        t = r.get("title", "")
        if t:
            by_vol[r.get("vol")].setdefault(fold(t), t)
    stat = collections.Counter()
    for vol in range(1, 111):
        f = LIB / "bihar" / str(vol) / "index.html"
        if not f.is_file():
            continue
        src = f.read_text(encoding="utf-8")
        fa0 = sum(v.count(FY) for k, v in LANGATTR.findall(src) if k != "en")
        new = src
        for m in set(re.findall(r'data-ar="([^"]*)"', src)):
            if FY not in m and PK not in m:
                continue
            good = by_vol.get(vol, {}).get(fold(m))
            if good and good != m:
                new = new.replace(m, good)
                stat["rows"] += 1
        if new == src:
            continue
        assert fold(new) == fold(src), f"vol {vol}: text changed, not letters"
        fa1 = sum(v.count(FY) for k, v in LANGATTR.findall(new) if k != "en")
        assert fa0 == fa1, f"vol {vol}: a Persian/Urdu attribute was altered"
        stat["pages"] += 1
        if write:
            f.write_text(new, encoding="utf-8", newline="")
    left = 0
    for vol in range(1, 111):
        f = LIB / "bihar" / str(vol) / "index.html"
        if f.is_file():
            for t in re.findall(r'data-ar="([^"]*)"', f.read_text(encoding="utf-8")):
                left += t.count(FY)
    print(f"volume index pages: {stat['pages']} changed, "
          f"{stat['rows']:,} distinct titles corrected")
    print(f"   ی left in their data-ar titles: {left:,}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vol", type=int)
    ap.add_argument("--vindex", action="store_true")
    ap.add_argument("--toc", action="store_true")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()

    if a.toc:
        do_toc(a.write)
        return

    if a.vindex:
        do_vindex(a.write)
        return

    stat = collections.Counter()
    root = LIB / "bihar" / str(a.vol)
    pages = sorted((p for p in root.iterdir() if p.is_dir()),
                   key=lambda p: (0, int(p.name)) if p.name.isdigit() else (1, 0))
    changed = 0
    for d in pages:
        f = d / "index.html"
        if not f.is_file():
            continue
        src = f.read_text(encoding="utf-8")
        new = do_page(src, stat)
        if new == src:
            continue
        guard(src, new)
        changed += 1
        if a.write:
            f.write_text(new, encoding="utf-8", newline="")
    verb = "written" if a.write else "would change"
    print(f"volume {a.vol}: {len(pages)} pages, {changed} {verb}")
    print(f"  «شی ء»  -> «شي ء»      : {stat['shay']:,}")
    print(f"  «علی بن» -> «علي بن»   : {stat['ali_bin']:,}")
    print(f"  description re-derived : {stat['desc_fixed']:,}")
    print(f"  description already ok : {stat['desc_already']:,}")
    print(f"  description LEFT alone : {stat['desc_left']:,}")
    print(f"  data-fa/ur in body     : {stat['langattr']:,}"
          f"   DAMAGED {stat['langattr_DAMAGED']:,}")
    assert not stat["langattr_DAMAGED"], "a Persian/Urdu attribute was corrupted"


if __name__ == "__main__":
    main()
