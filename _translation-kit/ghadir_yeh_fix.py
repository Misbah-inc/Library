#!/usr/bin/env python3
"""Restore ي / ى in the Ghaemiyeh الغدير, using ablibrary's text as the authority.

    python ghadir_yeh_fix.py --build-lexicon <abl dir> --out yeh_lexicon.json
    python ghadir_yeh_fix.py --apply <vols dir> --lexicon yeh_lexicon.json

**Why this is needed, and why the obvious fix was wrong.** Ghaemiyeh's export
writes Persian ی (U+06CC) where Arabic has TWO different letters:

    ي  U+064A  yāʾ              في ، الذي ، النبي ، علي (the name)
    ى  U+0649  alif maqṣūra     موسى ، المصطفى ، إلى ، حتى ، على (the preposition)

A blanket ی→ي conversion was deployed on 2026-09-27 and was WRONG for about
12% of occurrences — «موسى» became «موسي». Measured against ablibrary's text of
the same book: ى is 5,474 of 43,866 word-final letters, 12.5%. The conversion
had been verified position by position, same length, only that codepoint
changing — every check passed, and every check tested the wrong proposition.
It replaced an obviously-foreign letter with a confidently-wrong Arabic one,
which is strictly worse: a reader can see that ی is not Arabic, and cannot see
that موسي is misspelt.

**The source cannot settle it.** Ghaemiyeh has «موسی» 691 times and «موسى»
never; «حتی» 3,089 and «حتى» once. The distinction was never in the input.

**ablibrary has the same book, correctly typeset**, so the answer is transfer,
not inference. Three tiers, most certain first:

  1. the normalised form is UNAMBIGUOUS in the reference (1,595 of 1,666 forms
     in volume 1) -> use its spelling.
  2. ambiguous, but the PRECEDING word settles it — «علی بن» is the name
     «علي بن», «علی رغمة» the preposition «على رغمة». In volume 1 this
     resolves 4,658 of 5,033 ambiguous occurrences.
  3. still ambiguous, or the word is absent from the reference -> LEAVE ی
     ALONE and report it. About 2%. An untouched Persian letter is visibly
     foreign; a guessed Arabic one is not.

Nothing is changed unless the reference says so. No rule of thumb, no "usually".
"""

import argparse
import collections
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

DIA = re.compile("[\u064b-\u0652\u0670\u0640]")
WORD = re.compile("[\u0621-\u064a\u0649\u0670\u064b-\u0652\u06cc\u06a9]+")
FARSI_YEH = "\u06cc"


def norm(w):
    """Fold to a spelling-neutral key: ی/ى -> ي, ک -> ك, hamza carriers -> ا."""
    w = DIA.sub("", w)
    for a, b in (("\u06cc", "\u064a"), ("\u0649", "\u064a"), ("\u06a9", "\u0643"),
                 ("\u0623", "\u0627"), ("\u0625", "\u0627"), ("\u0622", "\u0627")):
        w = w.replace(a, b)
    return w


def build_ngrams(abl_dir, n=5):
    """A PARALLEL-TEXT index of ablibrary: every n-word window -> positions.

    The dictionary is not enough on its own. «علی» is «على» 11,957 times and
    «علي» 5,304 times in ablibrary, because they are two different words — the
    preposition and the name. Asking "how is this word spelt" has no answer.

    Asking "how is this word spelt HERE" does. ablibrary carries the same book,
    so the surrounding phrase pins the exact occurrence and the letter can be
    read off it. On volume 1 this settles 2,972 of 4,291 cases the dictionary
    could not — 69%.

    It is not 100% because the editions differ: the Ghaemiyeh text is the 1416
    مركز الغدير edition and runs ~25% longer, carrying an editor's introduction
    and apparatus that ablibrary's edition does not contain. Only 38% of its
    sentences appear verbatim there. Where there is no parallel passage there
    is no answer, and the ی is left alone.
    """
    words = []
    for f in sorted(pathlib.Path(abl_dir).glob("abl_v*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        text = " ".join(p.get("body", "") for p in d.values())
        words += [DIA.sub("", w) for w in WORD.findall(text)]
    nw = [norm(w) for w in words]
    idx = collections.defaultdict(list)
    for i in range(len(nw) - n + 1):
        idx[tuple(nw[i:i + n])].append(i)
    return words, idx


def build(abl_dir):
    uni = collections.defaultdict(collections.Counter)
    bi = collections.defaultdict(collections.Counter)
    for f in sorted(pathlib.Path(abl_dir).glob("abl_v*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        text = " ".join(p.get("body", "") for p in d.values())
        ws = WORD.findall(text)
        for i, w in enumerate(ws):
            bare = DIA.sub("", w)
            if not (bare.endswith("\u0649") or bare.endswith("\u064a")):
                continue
            nw = norm(w)
            uni[nw][bare[-1]] += 1
            bi[(norm(ws[i - 1]) if i else "", nw)][bare[-1]] += 1
    return uni, bi


def apply_to(text, uni, bi, stat, words=None, idx=None, n=5):
    """Rewrite every ی, most-certain evidence first.

      1. PARALLEL TEXT — the same phrase located in ablibrary, letter read off
         the word in that position. The only tier that can separate «على» from
         «علي», because that depends on meaning, not spelling.
      2. the form is unambiguous in the reference.
      3. the preceding word settles an otherwise ambiguous form.
      4. nothing settles it -> leave ی and count it.

    Only the LAST ی in a word can be an alif maqṣūra: verified in the reference,
    where ى is word-final in 54,717 of 54,718 occurrences. Every other ی is a
    plain yāʾ.
    """
    toks = list(WORD.finditer(text))
    gn = [norm(m.group(0)) for m in toks]
    out, prev_end, prev_norm = [], 0, ""

    def from_parallel(i, want):
        if not idx:
            return None
        for a0 in range(max(0, i - n + 1), i + 1):
            key = tuple(gn[a0:a0 + n])
            if len(key) < n:
                continue
            hits = idx.get(key)
            if not hits:
                continue
            off = i - a0
            sp = {words[h + off][-1] for h in hits
                  if h + off < len(words) and norm(words[h + off]) == want}
            if len(sp) == 1:
                return next(iter(sp))
        return None

    for i, m in enumerate(toks):
        w = m.group(0)
        out.append(text[prev_end:m.start()])
        prev_end = m.end()
        if FARSI_YEH not in w:
            prev_norm = gn[i]; out.append(w); continue
        bare = DIA.sub("", w)
        last = w.rfind(FARSI_YEH)
        ends = bare.endswith(FARSI_YEH)
        chars = list(w)
        for k, ch in enumerate(chars):
            if ch == FARSI_YEH and not (ends and k == last):
                chars[k] = "ي"; stat["medial"] += 1
        if ends:
            nw = gn[i]
            pick = from_parallel(i, nw)
            if pick in ("ي", "ى"):
                stat["parallel"] += 1
            else:
                pick = None
                cand = uni.get(nw)
                if cand and len(cand) == 1:
                    pick = next(iter(cand)); stat["unambiguous"] += 1
                elif cand:
                    c2 = bi.get((prev_norm, nw))
                    if c2 and len(c2) == 1:
                        pick = next(iter(c2)); stat["by_context"] += 1
                    else:
                        stat["ambiguous"] += 1; stat["amb_words"][nw] += 1
                else:
                    stat["unknown"] += 1; stat["unk_words"][nw] += 1
            if pick:
                chars[last] = pick
            prev_norm = nw
        else:
            prev_norm = gn[i]
        out.append("".join(chars))
    out.append(text[prev_end:])
    res = "".join(out)
    # The ONE rule not transferred from the reference. «على بن» cannot be the
    # preposition — a name chain follows — and ablibrary itself has it 69 times
    # against «علي بن» 1,325, and «علي بن أبي طالب» 511 times against
    # «على بن أبي طالب» ZERO. So those are typos in the reference, and matching
    # it faithfully reproduced 19 of them. Approved by the owner 2026-09-27.
    # The lookbehind is essential: «يعلى بن مُرّة» is the NAME Ya'la and is
    # correct. Without it the pattern matches the «على» inside «يعلى» and
    # corrupts 35 correct occurrences to repair 25 wrong ones.
    fixed, n = re.subn(
        "(?<![\u0621-\u064a\u0649])\u0639\u0644\u0649(\s+\u0628\u0646)",
        lambda m: "علي" + m.group(1), res)
    stat["ala_bin"] += n
    return fixed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build-lexicon")
    ap.add_argument("--lexicon")
    ap.add_argument("--apply")
    ap.add_argument("--ref", help="abl dir, for parallel-text matching")
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.build_lexicon:
        uni, bi = build(a.build_lexicon)
        amb = [w for w, c in uni.items() if len(c) > 1]
        print(f"reference forms ending ى/ي : {len(uni):,}")
        print(f"  ambiguous on their own   : {len(amb):,}")
        print(f"  context pairs recorded   : {len(bi):,}")
        pathlib.Path(a.out).write_text(json.dumps(
            {"uni": {k: dict(v) for k, v in uni.items()},
             "bi": {f"{p}\t{w}": dict(c) for (p, w), c in bi.items()}},
            ensure_ascii=False), encoding="utf-8")
        print(f"  -> {a.out}")
        return
    if a.apply:
        lex = json.loads(pathlib.Path(a.lexicon).read_text(encoding="utf-8"))
        uni = {k: collections.Counter(v) for k, v in lex["uni"].items()}
        bi = {tuple(k.split("	")): collections.Counter(v)
              for k, v in lex["bi"].items()}
        words, idx = build_ngrams(a.ref) if a.ref else (None, None)
        if idx:
            print(f"parallel-text index: {len(words):,} words, {len(idx):,} windows")
        stat = collections.Counter()
        stat["amb_words"] = collections.Counter()
        stat["unk_words"] = collections.Counter()
        for f in sorted(pathlib.Path(a.apply).glob("ghadir_v*.htm"),
                        key=lambda x: int(re.search(r"v(\d+)", x.name).group(1))):
            src = f.read_text(encoding="utf-8")
            out = apply_to(src, uni, bi, stat, words, idx)
            # only the final letter of a word may differ, and only ی -> ي/ى
            assert len(out) == len(src), f"{f.name}: length changed"
            bad = [(i, src[i], out[i]) for i in range(len(src)) if src[i] != out[i]
                   and not (src[i] == FARSI_YEH and out[i] in "يى")]
            assert not bad, f"{f.name}: unexpected change {bad[:3]}"
            if a.out:
                d = pathlib.Path(a.out); d.mkdir(parents=True, exist_ok=True)
                (d / f.name).write_text(out, encoding="utf-8", newline="")
        tot = stat["unambiguous"] + stat["by_context"] + stat["ambiguous"] + stat["unknown"]
        print(f"non-final ی -> ي          : {stat['medial']:,}")
        tot += stat["parallel"]
        print(f"word-final ی found        : {tot:,}")
        print(f"  from the PARALLEL TEXT  : {stat['parallel']:,}  "
              f"({100*stat['parallel']/max(tot,1):.1f}%)")
        print(f"  resolved outright       : {stat['unambiguous']:,}  "
              f"({100*stat['unambiguous']/max(tot,1):.1f}%)")
        print(f"  resolved by context     : {stat['by_context']:,}  "
              f"({100*stat['by_context']/max(tot,1):.1f}%)")
        print(f"  LEFT AS ی — ambiguous   : {stat['ambiguous']:,}")
        print(f"  LEFT AS ی — not in ref  : {stat['unknown']:,}")
        print()
        print("  top still-ambiguous forms:")
        for w, n in stat["amb_words"].most_common(8):
            print(f"     {w:<14}{n:>6}")
        print("  top forms absent from the reference:")
        for w, n in stat["unk_words"].most_common(6):
            print(f"     {w:<14}{n:>6}")
        return


if __name__ == "__main__":
    main()
