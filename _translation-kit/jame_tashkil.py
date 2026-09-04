#!/usr/bin/env python3
"""Vocalise the Arabic paradigm words of جامع المقدمات.

  jame_tashkil.py jame_pages.json --out jame_tashkil.json [--show]

Scope: کتاب الامثله (vol 1, pp. 11-14), the ضرب paradigm every student learns
first. It is the treatise where vocalisation actually carries the lesson, and
its forms are fully determined by the paradigm rather than by interpretation,
so they can be got right and checked.

TWO SAFETY RULES, both enforced by verify() below.

1. ADD MARKS ONLY — never substitute a letter. The source writes اضرب with a
   bare alef and ضاربه with ه, not أضرب and ضاربة. "Correcting" those would be
   editing the text, not vocalising it. So the invariant is:

       strip_diacritics(vocalised) == original,  exactly.

   Any letter change, dropped word or typo breaks it and the build fails loudly.

2. VOCALISE POSITIONALLY, never by word lookup. In the ماضی block ضربت occurs
   four times and is a different word each time —

       ضَرَبَتْ   she struck        (غائب مؤنث)
       ضَرَبْتَ   you m. struck     (مخاطب مذکر)
       ضَرَبْتِ   you f. struck     (مخاطب مؤنث)
       ضَرَبْتُ   I struck          (متکلم)

   A word→word map would get three of the four wrong, and wrong in the way that
   matters most: silently, to the reader who came to learn exactly this. Each
   entry below is therefore a whole phrase, replaced in document order.

Output is an overlay keyed "vol:page:block", never a rewrite of the source —
the printed text stays the text, and the reader toggles the vocalised layer on.
"""
import argparse, json, pathlib, re, sys, unicodedata

DIAC = re.compile(r"[ً-ْٰ]")


def strip(s):
    return DIAC.sub("", s)


# (vol, page, block) -> [(bare phrase, vocalised phrase)], applied in order,
# each consuming the next not-yet-replaced occurrence.
TABLE = {
    (1, 11, 1): [
        ("بسم الله الرحمن الرحیم", "بِسْمِ اللهِ الرَّحْمٰنِ الرَّحیمِ"),
    ],
    # ماضی — 14 forms
    (1, 11, 3): [
        ("ضرب ضربا ضربوا",      "ضَرَبَ ضَرَبَا ضَرَبُوا"),
        ("ضربت ضربتا ضربن",     "ضَرَبَتْ ضَرَبَتَا ضَرَبْنَ"),
        ("ضربت ضربتما ضربتم",   "ضَرَبْتَ ضَرَبْتُمَا ضَرَبْتُمْ"),
        ("ضربت ضربتما ضربتن",   "ضَرَبْتِ ضَرَبْتُمَا ضَرَبْتُنَّ"),
        ("ضربت ضربنا",          "ضَرَبْتُ ضَرَبْنَا"),
    ],
    # مستقبل — opens on p11, finishes on p12
    (1, 11, 4): [
        ("یضرب یضربان یضربون",  "یَضْرِبُ یَضْرِبَانِ یَضْرِبُونَ"),
        ("تضرب تضربان یضربن",   "تَضْرِبُ تَضْرِبَانِ یَضْرِبْنَ"),
    ],
    (1, 12, 0): [
        ("تضرب تضربان تضربون",  "تَضْرِبُ تَضْرِبَانِ تَضْرِبُونَ"),
        ("تضربین تضربان تضربن", "تَضْرِبِینَ تَضْرِبَانِ تَضْرِبْنَ"),
        ("اضرب نضرب",           "اَضْرِبُ نَضْرِبُ"),
    ],
    # اسم فاعل
    (1, 12, 1): [
        ("ضارب ضاربان ضاربون",   "ضَارِبٌ ضَارِبَانِ ضَارِبُونَ"),
        ("ضاربه ضاربتان ضاربات", "ضَارِبَهٌ ضَارِبَتَانِ ضَارِبَاتٌ"),
    ],
    # اسم مفعول
    (1, 12, 2): [
        ("مضروب مضروبان مضروبون",   "مَضْرُوبٌ مَضْرُوبَانِ مَضْرُوبُونَ"),
        ("مضروبه مضروبتان مضروبات", "مَضْرُوبَهٌ مَضْرُوبَتَانِ مَضْرُوبَاتٌ"),
    ],
    # امر — jussive after لام الأمر, then the bare imperative
    (1, 12, 3): [
        ("لیضرب لیضربا لیضربوا", "لِیَضْرِبْ لِیَضْرِبَا لِیَضْرِبُوا"),
        ("لتضرب لتضربا لیضربن",  "لِتَضْرِبْ لِتَضْرِبَا لِیَضْرِبْنَ"),
        ("اضرب اضربا اضربوا",    "اِضْرِبْ اِضْرِبَا اِضْرِبُوا"),
        ("اضربی اضربا اضربن",    "اِضْرِبِی اِضْرِبَا اِضْرِبْنَ"),
        ("لاضرب لنضرب",          "لِاَضْرِبْ لِنَضْرِبْ"),
    ],
    # نهی — لا الناهیة + jussive; runs onto p13
    (1, 12, 4): [
        ("لا یضرب لا یضربا لا یضربوا", "لَا یَضْرِبْ لَا یَضْرِبَا لَا یَضْرِبُوا"),
        ("لا تضرب لا تضربا لا یضربن",  "لَا تَضْرِبْ لَا تَضْرِبَا لَا یَضْرِبْنَ"),
        ("لا تضرب لا تضربا لا تضربوا", "لَا تَضْرِبْ لَا تَضْرِبَا لَا تَضْرِبُوا"),
        ("لا تضربی لا تضربا لا تضربن", "لَا تَضْرِبِی لَا تَضْرِبَا لَا تَضْرِبْنَ"),
    ],
    (1, 13, 0): [
        ("لا اضرب لا نضرب", "لَا اَضْرِبْ لَا نَضْرِبْ"),
    ],
    # جحد — لم + jussive
    (1, 13, 1): [
        ("لم یضرب لم یضربا لم یضربوا", "لَمْ یَضْرِبْ لَمْ یَضْرِبَا لَمْ یَضْرِبُوا"),
        ("لم تضرب لم تضربا لم یضربن",  "لَمْ تَضْرِبْ لَمْ تَضْرِبَا لَمْ یَضْرِبْنَ"),
        ("لم تضرب لم تضربا لم تضربوا", "لَمْ تَضْرِبْ لَمْ تَضْرِبَا لَمْ تَضْرِبُوا"),
        ("لم تضربی لم تضربا لم تضربن", "لَمْ تَضْرِبِی لَمْ تَضْرِبَا لَمْ تَضْرِبْنَ"),
        ("لم اضرب لم نضرب",            "لَمْ اَضْرِبْ لَمْ نَضْرِبْ"),
    ],
    # نفی — لا النافیة + indicative, so the endings stay مرفوع
    (1, 13, 2): [
        ("لا یضرب لا یضربان لا یضربون", "لَا یَضْرِبُ لَا یَضْرِبَانِ لَا یَضْرِبُونَ"),
        ("لا تضرب لا تضربان لا یضربن",  "لَا تَضْرِبُ لَا تَضْرِبَانِ لَا یَضْرِبْنَ"),
        ("لا تضرب لا تضربان لا تضربون", "لَا تَضْرِبُ لَا تَضْرِبَانِ لَا تَضْرِبُونَ"),
        ("لا تضربین لا تضربان لا تضربن","لَا تَضْرِبِینَ لَا تَضْرِبَانِ لَا تَضْرِبْنَ"),
        ("لا اضرب لا نضرب",             "لَا اَضْرِبُ لَا نَضْرِبُ"),
    ],
    # استفهام — هل + indicative; runs onto p14
    (1, 13, 3): [
        ("هل یضرب هل یضربان هل یضربون", "هَلْ یَضْرِبُ هَلْ یَضْرِبَانِ هَلْ یَضْرِبُونَ"),
        ("هل تضرب هل تضربان هل یضربن",  "هَلْ تَضْرِبُ هَلْ تَضْرِبَانِ هَلْ یَضْرِبْنَ"),
        ("هل تضرب هل تضربان هل تضربون", "هَلْ تَضْرِبُ هَلْ تَضْرِبَانِ هَلْ تَضْرِبُونَ"),
    ],
    (1, 14, 0): [
        ("تضربین هل تضربان هل تضربن", "تَضْرِبِینَ هَلْ تَضْرِبَانِ هَلْ تَضْرِبْنَ"),
        ("هل اضرب هل نضرب",           "هَلْ اَضْرِبُ هَلْ نَضْرِبُ"),
    ],
}


def apply(original, pairs):
    out = original
    for bare, voc in pairs:
        if bare not in out:
            raise ValueError(f"phrase not found: {bare!r}")
        out = out.replace(bare, voc, 1)
    return out


def verify(original, vocalised):
    """Only combining marks may differ. Returns None or a description."""
    if strip(vocalised) != original:
        a, b = original, strip(vocalised)
        for i, (x, y) in enumerate(zip(a, b)):
            if x != y:
                return (f"letters changed at {i}: "
                        f"{a[max(0,i-18):i+18]!r} -> {b[max(0,i-18):i+18]!r}")
        return f"length differs after stripping: {len(a)} vs {len(b)}"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pages")
    ap.add_argument("--out")
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args()

    data = json.loads(pathlib.Path(a.pages).read_text(encoding="utf-8"))
    index = {}
    for vol in data["volumes"]:
        for p in vol["pages"]:
            for i, b in enumerate(p["blocks"]):
                index[(vol["v"], p["n"], i)] = b["t"]

    overlay, errors, marks = {}, [], 0
    for key, pairs in sorted(TABLE.items()):
        if key not in index:
            errors.append(f"{key}: no such block")
            continue
        original = index[key]
        try:
            voc = apply(original, pairs)
        except ValueError as e:
            errors.append(f"{key}: {e}")
            continue
        bad = verify(original, voc)
        if bad:
            errors.append(f"{key}: {bad}")
            continue
        added = len(DIAC.findall(voc)) - len(DIAC.findall(original))
        marks += added
        overlay[f"{key[0]}:{key[1]}:{key[2]}"] = voc
        if a.show:
            print(f"--- {key}  (+{added} marks)", file=sys.stderr)
            print("    " + voc[:150], file=sys.stderr)

    print(f"blocks vocalised : {len(overlay)}", file=sys.stderr)
    print(f"marks added      : {marks}", file=sys.stderr)
    print(f"verified         : strip(vocalised) == original for all "
          f"{len(overlay)} blocks", file=sys.stderr)
    if errors:
        print(f"\nFAILED ({len(errors)}):", file=sys.stderr)
        for e in errors:
            print("  " + e, file=sys.stderr)
        sys.exit(1)

    if a.out:
        pathlib.Path(a.out).write_text(
            json.dumps(overlay, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"wrote {a.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
