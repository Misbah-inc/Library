#!/usr/bin/env python3
"""Verify every vocalised block in jame_tashkil.json.

  jame_tashkil_check.py [--verbose]

Vocalising a صرف/نحو text is the one place in this library where a quiet error
does real damage: a wrong ḥaraka does not look wrong, it teaches the opposite
rule, and the reader who would notice is exactly the reader who came to learn
it. So the vocalised text is never trusted on inspection alone.

The check that can be made absolute is that NOTHING BUT MARKS WAS ADDED. Strip
every diacritic from the vocalised form and from the printed form; the two must
be byte-identical. That catches the dangerous failure — a letter silently
changed, a word dropped, a phrase "corrected" — which is far worse than a
debatable vowel, because it alters the text itself.

What it cannot catch is a wrong-but-well-formed vowel. That still needs reading,
which is why batches stay small and matn is done before commentary.

Exits non-zero if any block fails, so it can gate a build.
"""
import argparse, json, pathlib, re, sys

HERE = pathlib.Path(__file__).parent
DIA = re.compile(r"[ً-ْٓ-ٰٕۖ-ۭ]")
# The Persian commentary stays bare — only the Arabic matn and the صرف paradigms
# inside it get marks. Two independent tells that a mark has leaked into Persian:
# a word built from a Persian-only letter, or a Persian function word.
PERSIAN_ONLY = set("پچژگ")
FA_WORDS = set("""است هست بود باشد باشند شود شوند کند کنند کرد کردن کرده شده شد
می نمی که را از به این آن اینکه چون چنانکه هر یا نیز خود برای بر با تا هم
گویند گفته دارد دارند داشت یعنی وقتی زیرا اگر پس آنکه بی همه دیگر بودن
وجه باز چهارده شش سه دو یک مذکر مؤنث""".split())

# A few words are spelled identically in both languages, so the bare form cannot
# settle which one it is — but the marks can. Persian بِه is "be"; Arabic بِهِ
# carries the pronoun's own kasra and could not be the Persian preposition. So
# the exception is the *vocalised* form, not the bare word: this stays narrow and
# a genuine slip on Persian به is still caught.
ARABIC_HOMOGRAPHS = {
    "بِهِ",      # bi-hi — "by Him", as in و به نستعین
    "بِهَا",     # bi-hā
    "لَهُ", "لَهَا",
    "مِنْ", "مَنْ",
}


def bare(s):
    return DIA.sub("", s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", default=str(HERE / "jame_pages.json"))
    ap.add_argument("--tashkil", default=str(HERE / "jame_tashkil.json"))
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()

    d = json.loads(pathlib.Path(a.pages).read_text(encoding="utf-8"))
    t = json.loads(pathlib.Path(a.tashkil).read_text(encoding="utf-8"))

    index = {}
    for vol in d["volumes"]:
        for pg in vol["pages"]:
            for i, b in enumerate(pg["blocks"]):
                index[f'{vol["v"]}:{pg["n"]}:{i}'] = (b, pg.get("chapter") or "?")

    altered, orphan, persian, unchanged = [], [], [], []
    marks_added = 0

    for key, voc in t.items():
        if key not in index:
            orphan.append(key)
            continue
        blk, chapter = index[key]
        orig = blk["t"]

        if bare(voc) != bare(orig):
            altered.append((key, chapter, orig, voc))
            continue
        if bare(voc) == voc:
            unchanged.append(key)          # nothing actually added
        marks_added += len(DIA.findall(voc)) - len(DIA.findall(orig))

        for word in re.findall(r"\S+", voc):
            if not DIA.search(word):
                continue
            clean = word.strip("─،.:؛()«»\"'")
            if clean in ARABIC_HOMOGRAPHS:
                continue
            stem = bare(clean)
            if any(c in PERSIAN_ONLY for c in word) or stem in FA_WORDS:
                persian.append((key, chapter, word))
                break

    total_ar = sum(1 for vol in d["volumes"] for pg in vol["pages"]
                   for b in pg["blocks"] if b["lang"] == "ar")

    print(f"vocalised blocks : {len(t)}")
    print(f"marks added      : {marks_added:,}")
    print(f"text preserved   : {len(t) - len(altered) - len(orphan)}/{len(t)}")
    print(f"coverage         : {len(t)} of {total_ar} Arabic-tagged blocks "
          f"({100.0 * len(t) / max(1, total_ar):.1f}%)")

    ok = True
    if altered:
        ok = False
        print(f"\nFAIL — {len(altered)} block(s) changed the text, not just the marks:")
        for key, chapter, orig, voc in altered[:10]:
            print(f"  {key}  ({chapter})")
            print(f"    printed  : {bare(orig)[:90]}")
            print(f"    vocalised: {bare(voc)[:90]}")
    if orphan:
        ok = False
        print(f"\nFAIL — {len(orphan)} key(s) match no block (stale after a re-extract):")
        for k in orphan[:10]:
            print("  " + k)
    if persian:
        print(f"\nWARN — {len(persian)} block(s) put marks on a Persian word:")
        for key, chapter, word in persian[:10]:
            print(f"  {key}  ({chapter})  {word}")
    if unchanged:
        print(f"\nWARN — {len(unchanged)} block(s) add no marks at all "
              f"(they only cost a data-tashkil attribute): {unchanged[:5]}")

    if ok and not persian:
        print("\nAll clear.")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
