#!/usr/bin/env python3
"""Apply hand-verified صرف paradigms across the book, mechanically.

  jame_tashkil_auto.py [--apply] [--limit N]

Rounds 1-3 vocalised the paradigm tables by hand and checked every form against
the canonical شکل. Those same word-forms recur throughout صرف میر, شرح التصریف
and شرح الامثله — the book is a drill, so it repeats itself. This applies the
verified forms wherever the identical bare word appears, instead of retyping
them a thousand times.

The whole design is about not guessing:

* Forms are GENERATED from the six sound أبواب, not typed. One vowel pattern per
  باب, so a slip shows up in every form of that باب at once rather than hiding
  in one cell.

* Only UNAMBIGUOUS forms are applied on sight. Several bare spellings carry more
  than one reading and are never auto-applied alone:
      ضرب    3ms perfect ضَرَبَ  — or the masdar ضَرْب
      ضربا   3md ضَرَبَا        — or masdar accusative ضَرْبًا
      ضربت   ضَرَبَتْ / ضَرَبْتَ / ضَرَبْتِ / ضَرَبْتُ  (four readings)
      اضرب   1s اَضْرِبُ        — or the imperative اُضْرُبْ
  These are applied ONLY inside a segment already proven to be a paradigm list
  by two or more unambiguous forms of the same root — the drill context that
  settles the reading. Outside that, they are left bare.

* A word that already carries any mark is never touched.

* Persian is never touched: the substitution is whole-word against an Arabic
  verb-form table, and Persian function words are not in it.

Text preservation is still proved afterwards by jame_tashkil_check.py, which is
the real gate — this script only proposes.
"""
import argparse, json, pathlib, re, sys, unicodedata

HERE = pathlib.Path(__file__).parent
F, K, D, S, SH = "َ", "ِ", "ُ", "ْ", "ّ"   # ـَ ـِ ـُ ـْ ـّ
YEH = "ی"          # the source spells yeh Persian-style; match it exactly
DIA = re.compile(r"[ً-ْٓ-ٰٕ]")

# root, ع-vowel of the perfect, ع-vowel of the imperfect
ABWAB = [
    ("نصر", F, D),   # فَعَلَ یَفْعُلُ   اصول
    ("ضرب", F, K),   # فَعَلَ یَفْعِلُ   اصول
    ("علم", K, F),   # فَعِلَ یَفْعَلُ   اصول
    ("منع", F, F),   # فَعَلَ یَفْعَلُ   فروع
    ("حسب", K, K),   # فَعِلَ یَفْعِلُ   فروع
    ("شرف", D, D),   # فَعُلَ یَفْعُلُ   فروع
]


def paradigm(root, pv, qv):
    """{bare form: vocalised form} for one sound triliteral باب.

    Returns two dicts: unambiguous forms, and the ambiguous ones that need
    paradigm context before they may be applied.
    """
    a, b, c = root
    perf = a + F + b + pv + c              # ضَرَبـ  (stem, ع vowel varies)
    pstem = a + F + b + pv + c + S         # ضَرَبْـ  (before consonant endings)
    imp = a + S + b + qv + c               # ـضْرِبـ  (imperfect stem)

    sure = {
        # ── perfect ──
        root + "وا":   perf + D + "وا",            # ضَرَبُوا   3mp
        root + "ن":    pstem + "ن" + F,            # ضَرَبْنَ   3fp
        root + "تا":   perf + F + "ت" + F + "ا",   # ضَرَبَتَا  3fd
        root + "تما":  pstem + "ت" + D + "م" + F + "ا",   # ضَرَبْتُمَا 2md/2fd
        root + "تم":   pstem + "ت" + D + "م" + S,  # ضَرَبْتُمْ  2mp
        root + "تن":   pstem + "ت" + D + "ن" + SH + F,   # ضَرَبْتُنَّ 2fp
        root + "نا":   pstem + "ن" + F + "ا",      # ضَرَبْنَا  1p
        # ── imperfect ──
        YEH + root + "ان":     YEH + F + imp + F + "ان" + K, # یَضْرِبَانِ 3md
        YEH + root + "ون":     YEH + F + imp + D + "ون" + F, # یَضْرِبُونَ 3mp
        YEH + root + "ن":      YEH + F + a + S + b + qv + c + S + "ن" + F,  # یَضْرِبْنَ 3fp
        "ت" + root + "ان":     "ت" + F + imp + F + "ان" + K, # تَضْرِبَانِ 3fd/2md
        "ت" + root + "ون":     "ت" + F + imp + D + "ون" + F, # تَضْرِبُونَ 2mp
        "ت" + root + YEH + "ن": "ت" + F + imp + K + YEH + "ن" + F,  # تَضْرِبِینَ 2fs
        "ت" + root + "ن":      "ت" + F + a + S + b + qv + c + S + "ن" + F,  # تَضْرِبْنَ 2fp
    }
    # Need the drill context to settle which reading is meant.
    #
    # The three bare imperfects (یضرب تضرب نضرب) were in `sure` until a preview
    # caught them going wrong in running prose, twice over:
    #   "ان تضرب اضرب"      conditional ان takes the JUSSIVE تَضْرِبْ, not تَضْرِبُ
    #   "و یعلم من ذلک …"   PASSIVE یُعْلَمُ ("is known"), not active یَعْلَمُ
    # Indicative, jussive and passive are spelled identically in these three, so
    # only syntax decides — which a word-table cannot see. Inside a paradigm
    # list they are being cited as forms, not used in a sentence, and there the
    # indicative reading is the right one.
    risky = {
        root:         perf + F,                    # ضَرَبَ    3ms  (vs masdar)
        root + "ا":   perf + F + "ا",              # ضَرَبَا   3md  (vs ـًا)
        root + "ت":   pstem + "ت" + F,             # ضَرَبْتَ  2ms  (4 readings)
        YEH + root:   YEH + F + imp + D,           # یَضْرِبُ  3ms  (vs jussive/passive)
        "ت" + root:   "ت" + F + imp + D,           # تَضْرِبُ  3fs/2ms
        "ن" + root:   "ن" + F + imp + D,           # نَضْرِبُ  1p
    }
    return sure, risky


def nfc(s):
    """Canonical order for the combining marks.

    ـُّ can be encoded shadda-then-vowel or vowel-then-shadda. Both render
    identically, so the difference is invisible on screen and in a diff — but
    they are different bytes, and mixing them would make the same word fail to
    match itself. NFC puts them in combining-class order (fatha 30 before
    shadda 33), which is what hand-typed text normalises to anyway.
    """
    return unicodedata.normalize("NFC", s)


SURE, RISKY, ROOT_OF = {}, {}, {}
for r, pv, qv in ABWAB:
    s, k = paradigm(r, pv, qv)
    SURE.update({b: nfc(v) for b, v in s.items()})
    RISKY.update({b: nfc(v) for b, v in k.items()})
    for bare in list(s) + list(k):
        ROOT_OF[bare] = r

WORD = re.compile(r"[^\s─،.:؛()«»\"']+")


def vocalise_segment(seg):
    """Substitute inside one ─-delimited segment. Returns (text, n_applied)."""
    # which roots does this segment prove are being drilled?
    proven = {}
    for m in WORD.finditer(seg):
        w = m.group(0)
        if DIA.search(w):
            continue
        if w in SURE:
            proven[ROOT_OF[w]] = proven.get(ROOT_OF[w], 0) + 1
    drilled = {r for r, n in proven.items() if n >= 2}

    out, last, applied = [], 0, 0
    for m in WORD.finditer(seg):
        w = m.group(0)
        if DIA.search(w):                 # already marked — never re-touch
            continue
        rep = SURE.get(w)
        if rep is None and w in RISKY and ROOT_OF[w] in drilled:
            rep = RISKY[w]                # safe: this segment is a paradigm list
        if rep is None:
            continue
        out.append(seg[last:m.start()]); out.append(rep)
        last = m.end(); applied += 1
    out.append(seg[last:])
    return "".join(out), applied


def vocalise(text):
    parts = text.split("─")
    total = 0
    for i, seg in enumerate(parts):
        parts[i], n = vocalise_segment(seg)
        total += n
    return "─".join(parts), total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", default=str(HERE / "jame_pages.json"))
    ap.add_argument("--tashkil", default=str(HERE / "jame_tashkil.json"))
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="stop after N blocks")
    a = ap.parse_args()

    d = json.loads(pathlib.Path(a.pages).read_text(encoding="utf-8"))
    tp = pathlib.Path(a.tashkil)
    t = json.loads(tp.read_text(encoding="utf-8")) if tp.exists() else {}

    added = marks = 0
    touched_pages = set()
    for vol in d["volumes"]:
        for pg in vol["pages"]:
            for i, b in enumerate(pg["blocks"]):
                key = f'{vol["v"]}:{pg["n"]}:{i}'
                if key in t:
                    continue
                voc, n = vocalise(b["t"])
                if n == 0:
                    continue
                t[key] = voc
                added += 1; marks += n
                touched_pages.add((vol["v"], pg["n"]))
                if a.limit and added >= a.limit:
                    break
            if a.limit and added >= a.limit: break
        if a.limit and added >= a.limit: break

    print(f"blocks {'vocalised' if a.apply else 'that would be vocalised'}: {added}")
    print(f"forms substituted : {marks:,}")
    print(f"pages touched     : {len(touched_pages)}")
    print(f"total blocks now  : {len(t)}")
    if a.apply:
        tp.write_text(json.dumps(t, ensure_ascii=False, indent=1), encoding="utf-8")
        print("written — now run jame_tashkil_check.py")
    else:
        print("(dry run — pass --apply to write)")


if __name__ == "__main__":
    main()
