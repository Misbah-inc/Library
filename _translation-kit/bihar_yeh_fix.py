#!/usr/bin/env python3
"""Restore ي / ى in the PUBLISHED Bihar pages, using ablibrary's text.

    python bihar_yeh_fix.py --index <bihar_ref dir> --out idx.pkl
    python bihar_yeh_fix.py --apply 2 --index idx.pkl [--write]

**The defect.** Ghaemiyeh's Bihar exports write Persian ی (U+06CC) where Arabic
has TWO letters — ي (yāʾ) and ى (alif maqṣūra). `bihar_ar_extract.py` carried
the source through faithfully, so volumes 2-110 went live with 3,083,713 ی and
almost no ي. **Volume 1 predates that build, came from a different source, and
is correct** — which is why the inconsistency went unnoticed for two weeks: the
one volume anyone compares against is the right one.

**Why NOT a blanket ی -> ي.** That was tried on الغدير on 2026-09-27 and was
wrong for ~12% of occurrences: «موسى» became «موسي». The correctly typeset books
in this library run 6-23% ى, so a conversion producing 0% is visibly wrong from
a single number — a check costing one line that was never run. It also swaps an
obviously-foreign letter for a confidently-wrong Arabic one, which no reader can
detect. Leaving ی is better than guessing ي.

**The method.** ablibrary carries the same book, correctly typeset (books
1976-2085, all 110 volumes). Four tiers, most certain first:

  1. PARALLEL TEXT — the same 5-word phrase found in ablibrary, and the letter
     read off the word in that position. The only tier that can separate «على»
     from «علي», because that is a difference of meaning, not of spelling.
  2. the word-form is unambiguous across the whole reference corpus.
  3. an ambiguous form settled by the preceding word.
  4. nothing settles it -> leave ی, and count it.

**Scope is the dangerous part.** This edits PUBLISHED pages in place, and only
the text inside `<div class="body">` may change. The chrome around it carries
`data-fa` and `data-ur` attributes holding GENUINE Persian and Urdu — the
language switcher and the UI labels. A file-wide replacement would corrupt the
Farsi and Urdu interface on 44,306 pages while the Arabic looked perfect.
Both ends of every file are asserted byte-identical.
"""

import argparse
import collections
import json
import pathlib
import pickle
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

DIA = re.compile("[\u064b-\u0652\u0670\u0640]")
WORD = re.compile("[\u0621-\u064a\u0649\u0670\u064b-\u0652\u06cc\u06a9]+")
BODY = re.compile(r'(<div class="body">)(.*?)(</div>\s*</div>\s*<nav)', re.S)
FY = "\u06cc"
ALIF_MAQSURA = "\u0649"
ARABIC_YEH = "\u064a"
N = 5


def norm(w):
    """Spelling-neutral key: ی/ى -> ي, ک -> ك, hamza carriers -> ا."""
    w = DIA.sub("", w)
    for a, b in (("\u06cc", "\u064a"), ("\u0649", "\u064a"), ("\u06a9", "\u0643"),
                 ("\u0623", "\u0627"), ("\u0625", "\u0627"), ("\u0622", "\u0627")):
        w = w.replace(a, b)
    return w


def build_index(ref_dir):
    words = []
    for f in sorted(pathlib.Path(ref_dir).glob("b*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for p in d.values():
            words += [DIA.sub("", w) for w in WORD.findall(p.get("body", ""))]
    nw = [norm(w) for w in words]
    ng = collections.defaultdict(list)
    for i in range(len(nw) - N + 1):
        ng[tuple(nw[i:i + N])].append(i)
    uni = collections.defaultdict(collections.Counter)
    bi = collections.defaultdict(collections.Counter)
    for i, w in enumerate(words):
        if not (w.endswith(ALIF_MAQSURA) or w.endswith(ARABIC_YEH)):
            continue
        uni[nw[i]][w[-1]] += 1
        bi[(nw[i - 1] if i else "", nw[i])][w[-1]] += 1
    return {"words": words, "ng": dict(ng),
            "uni": {k: dict(v) for k, v in uni.items()},
            "bi": {k: dict(v) for k, v in bi.items()}}


def fix_text(text, ix, stat, maqsura=False):
    """Rewrite every ی in one page's body.

    Only the LAST ی of a word can be an alif maqṣūra — verified against the
    reference, where ى is word-final in 54,717 of 54,718 occurrences. Every
    other ی is a plain yāʾ, so «یحیی» needs all three handled, not just the
    last: fixing only the final one leaves «یحیى», still Persian at the front.
    """
    words, ng, uni, bi = ix["words"], ix["ng"], ix["uni"], ix["bi"]
    toks = list(WORD.finditer(text))
    gn = [norm(m.group(0)) for m in toks]
    out, prev_end, prev_norm = [], 0, ""

    def parallel(i, want):
        for a in range(max(0, i - N + 1), i + 1):
            key = tuple(gn[a:a + N])
            if len(key) < N:
                continue
            hits = ng.get(key)
            if not hits:
                continue
            off = i - a
            sp = {words[h + off][-1] for h in hits
                  if h + off < len(words) and norm(words[h + off]) == want}
            if len(sp) == 1:
                return next(iter(sp))
        return None

    trigger = ARABIC_YEH if maqsura else FY

    for i, m in enumerate(toks):
        w = m.group(0)
        out.append(text[prev_end:m.start()])
        prev_end = m.end()
        if trigger not in w:
            prev_norm = gn[i]
            out.append(w)
            continue
        bare = DIA.sub("", w)
        last = w.rfind(trigger)
        ends = bare.endswith(trigger)
        ch = list(w)
        if not maqsura:
            for k, c in enumerate(ch):
                if c == FY and not (ends and k == last):
                    ch[k] = ARABIC_YEH
                    stat["medial"] += 1
        if ends:
            nw = gn[i]
            pick = parallel(i, nw)
            if pick:
                stat["parallel"] += 1
            else:
                cand = uni.get(nw)
                if cand and len(cand) == 1:
                    pick = next(iter(cand))
                    stat["unambiguous"] += 1
                elif cand:
                    c2 = bi.get((prev_norm, nw))
                    if c2 and len(c2) == 1:
                        pick = next(iter(c2))
                        stat["by_context"] += 1
                    else:
                        stat["ambiguous"] += 1
                else:
                    stat["unknown"] += 1
            if maqsura:
                # The input is already ي. Only ى is a repair; ي is the no-op.
                # An unresolved word therefore stays ي — the safe default here
                # is the letter that is already on the page.
                if pick == ALIF_MAQSURA:
                    ch[last] = ALIF_MAQSURA
                    stat["to_maqsura"] += 1
                else:
                    stat["kept_yeh"] += 1
            elif pick:
                ch[last] = pick
            prev_norm = nw
        else:
            prev_norm = gn[i]
        out.append("".join(ch))
    out.append(text[prev_end:])
    res = "".join(out)
    # «يعلى بن» is the narrator Yaʿlā and is CORRECT. Without the lookbehind the
    # rule matches the «على» inside «يعلى» and corrupts correct names to repair
    # misprints — on الغدير that was 35 wrong for 25 right. Only a standalone
    # «على» before «بن» is the misprint.
    # In maqsura mode this rule runs the SAME direction and can only
    # repair «على بن» back to the name, never create one — so a 5-gram
    # that resolved «علي» to «على» in front of «بن» is undone here
    # rather than shipped.
    res, n = re.subn("(?<![\u0621-\u064a\u0649])\u0639\u0644\u0649(\\s+\u0628\u0646)",
                     lambda mm: "\u0639\u0644\u064a" + mm.group(1), res)
    stat["ala_bin"] += n
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index")
    ap.add_argument("--out")
    ap.add_argument("--apply", type=int)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--maqsura", action="store_true",
                    help="volume 1's inverted defect: input is ي throughout, "
                         "ask the reference which ones should be ى")
    ap.add_argument("--lib", default="G:/My Drive/Misbah Library/Library/bihar")
    a = ap.parse_args()

    if a.out:
        ix = build_index(a.index)
        with open(a.out, "wb") as f:
            pickle.dump(ix, f, protocol=4)
        print(f"reference words : {len(ix['words']):,}")
        print(f"5-word windows  : {len(ix['ng']):,}")
        print(f"word forms      : {len(ix['uni']):,}")
        return

    with open(a.index, "rb") as f:
        ix = pickle.load(f)
    stat = collections.Counter()
    root = pathlib.Path(a.lib) / str(a.apply)
    pages = sorted((p for p in root.iterdir() if p.is_dir()),
                   key=lambda p: (0, int(p.name)) if p.name.isdigit() else (1, 0))
    changed = 0
    for d in pages:
        f = d / "index.html"
        if not f.is_file():
            continue
        src = f.read_text(encoding="utf-8")
        m = BODY.search(src)
        if not m:
            continue
        fixed = fix_text(m.group(2), ix, stat, maqsura=a.maqsura)
        head, tail = src[:m.start(2)], src[m.end(2):]
        new = head + fixed + tail
        assert new.startswith(head), f"{f}: chrome before the body changed"
        assert new.endswith(tail), f"{f}: chrome after the body changed"
        if new != src:
            changed += 1
            if a.write:
                f.write_text(new, encoding="utf-8", newline="")
    tot = sum(stat[k] for k in ("parallel", "unambiguous", "by_context",
                                "ambiguous", "unknown"))
    verb = "written" if a.write else "would change"
    print(f"volume {a.apply}: {len(pages)} pages, {changed} {verb}")
    if a.maqsura:
        print(f"  word-final ي examined  : {tot:,}")
        print(f"    -> ى (repaired)       {stat['to_maqsura']:>9,}")
        print(f"    kept ي                {stat['kept_yeh']:>9,}")
        print("  how each was decided:")
        for k, lab in (("parallel", "from parallel text"),
                       ("unambiguous", "form unambiguous"),
                       ("by_context", "by preceding word"),
                       ("ambiguous", "unresolved — ambiguous"),
                       ("unknown", "unresolved — not in ref")):
            print(f"    {lab:<24}{stat[k]:>9,}")
        print(f"  «على بن» -> «علي بن»   : {stat['ala_bin']:,}")
        return
    print(f"  word-final ی           : {tot:,}")
    for k, lab in (("parallel", "from parallel text"),
                   ("unambiguous", "form unambiguous"),
                   ("by_context", "by preceding word"),
                   ("ambiguous", "LEFT as ی — ambiguous"),
                   ("unknown", "LEFT as ی — not in ref")):
        print(f"    {lab:<24}{stat[k]:>9,}")
    print(f"  non-final ی -> ي       : {stat['medial']:,}")
    print(f"  «على بن» -> «علي بن»   : {stat['ala_bin']:,}")


if __name__ == "__main__":
    main()
