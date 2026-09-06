#!/usr/bin/env python3
"""Independent audit of the جامع المقدمات vocalisation overlay.

This deliberately does NOT import jame_tashkil_check.py. That module is what the
work was produced against; if it carries a wrong assumption, re-running it would
confirm the same wrong assumption. Everything here is reimplemented from the
source data, so agreement between the two is evidence rather than an echo.

Five audits:

  1  TEXT      strip every mark from the vocalised text; it must equal the
               printed text exactly, character for character.
  2  SPLICE    every run the SOURCE already vocalised (Qur'anic verses, a few
               cited lines) must survive byte-identical, not merely equivalent
               under Unicode normalisation.
  3  SHAPE     the marks must be orthographically possible: no two vowels on one
               letter, no shadda or sukun opening a word, no tanwīn mid-word, no
               mark sitting on punctuation or a space.
  4  WORDS     the same bare word vocalised two different ways somewhere in the
               book. Most are legitimate (ضربت is four different words); a rare
               variant beside a dominant one is where a slip would hide.
  5  DENSITY   blocks with suspiciously few marks for their length — the
               signature of a half-finished entry.

Audits 1-3 are decidable: they pass or they fail. Audits 4 and 5 only produce
candidates for a human to read.
"""
import json, pathlib, re, sys, unicodedata
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).parent

FATHA, DAMMA, KASRA = "َ", "ُ", "ِ"
SHADDA, SUKUN       = "ّ", "ْ"
FATHATAN, DAMMATAN, KASRATAN = "ً", "ٌ", "ٍ"
SUPER_ALEF          = "ٰ"

VOWELS  = {FATHA, DAMMA, KASRA}
TANWIN  = {FATHATAN, DAMMATAN, KASRATAN}
NUCLEUS = VOWELS | TANWIN | {SUKUN}
MARKS   = NUCLEUS | {SHADDA, SUPER_ALEF}

# every combining mark this corpus can legitimately contain
ALL_DIA = re.compile("[ً-ٰٕۖ-ۭ]")
# a base character that a mark may attach to: an Arabic letter
LETTER  = re.compile("[ء-غـ-يٮ-ۓۺ-ۿ]")


def strip(s):
    return ALL_DIA.sub("", s)


def load():
    d = json.loads((HERE / "jame_pages.json").read_text(encoding="utf-8"))
    t = json.loads((HERE / "jame_tashkil.json").read_text(encoding="utf-8"))
    src, lang, chap = {}, {}, {}
    for vi, v in enumerate(d["volumes"], 1):
        for p in v["pages"]:
            for i, b in enumerate(p["blocks"]):
                k = f'{vi}:{p["n"]}:{i}'
                src[k] = b["t"]
                lang[k] = b.get("lang")
                chap[k] = p.get("chapter", "")
    return src, lang, chap, t


def audit_text(src, t):
    bad = []
    for k, voc in t.items():
        if k not in src:
            bad.append((k, "key is not in jame_pages.json (stale overlay entry)"))
            continue
        # Strip BOTH sides. The printed text carries its own diacritics wherever
        # the source quotes a vocalised Qur'anic verse; comparing a stripped
        # overlay against an unstripped source can never match, and reads as a
        # catastrophic failure when nothing is wrong.
        if strip(voc) != strip(src[k]):
            a, b = strip(voc), strip(src[k])
            i = next((j for j in range(min(len(a), len(b))) if a[j] != b[j]),
                     min(len(a), len(b)))
            bad.append((k, f"differs at char {i}: "
                           f"mine …{a[max(0,i-30):i+20]}… / printed …{b[max(0,i-30):i+20]}…"))
    return bad


def runs(s):
    """maximal whitespace-separated spans in which every token carries a mark"""
    out, cur = [], None
    for m in re.finditer(r"\S+", s):
        if ALL_DIA.search(m.group()):
            cur = (cur[0], m.end()) if cur and cur[1] == m.start() - 1 else (m.start(), m.end())
        elif cur:
            out.append(cur); cur = None
    if cur:
        out.append(cur)
    return [s[a:b] for a, b in out]


def audit_splice(src, t):
    checked, bad = 0, []
    for k, voc in t.items():
        for r in runs(src.get(k, "")):
            if len(ALL_DIA.findall(r)) < 2:
                continue
            checked += 1
            if r in voc:
                continue
            # is it present but renormalised? that is the silent failure mode
            why = ("present only under NFC normalisation — combining order changed"
                   if unicodedata.normalize("NFC", r) in unicodedata.normalize("NFC", voc)
                   else "absent")
            bad.append((k, r[:60], why))
    return checked, bad


def audit_shape(t):
    """Is each mark cluster something Arabic orthography can actually produce?"""
    bad = []
    for k, voc in t.items():
        for w in voc.split():
            if not ALL_DIA.search(w):
                continue
            bare_i = -1                       # index of the base char in this word
            cluster, base = [], None
            def flush():
                if not cluster:
                    return None
                c = "".join(cluster)
                if base is None:
                    return "mark with nothing to sit on"
                if not LETTER.match(base):
                    return f"mark on {base!r}, which is not a letter"
                if sum(ch in NUCLEUS for ch in cluster) > 1:
                    return "two vowels/sukun on one letter"
                if cluster.count(SHADDA) > 1:
                    return "doubled shadda"
                if SUKUN in cluster and any(ch in VOWELS | TANWIN for ch in cluster):
                    return "sukun together with a vowel"
                if bare_i == 0 and SHADDA in cluster:
                    return "shadda on the first letter of the word"
                # A sukun CAN open a token here: this edition writes lām al-amr
                # and the connective wāw as separate tokens (وَ لْیَقْضُوا,
                # وَ أْمُرْ, فُلَانٌ بْنُ فُلَانٍ), so the first letter really is silent.
                return None
            for ch in w:
                if ch in MARKS:
                    cluster.append(ch)
                else:
                    msg = flush()
                    if msg:
                        bad.append((k, w, msg))
                    cluster, base, bare_i = [], ch, bare_i + 1
            msg = flush()
            if msg:
                bad.append((k, w, msg))
            # tanwīn may only sit on the last letter, or the one before a final ا/ی
            letters = [c for c in w if c not in MARKS]
            for m in re.finditer("[" + "".join(TANWIN) + "]", w):
                n = sum(1 for c in w[:m.start()] if c not in MARKS) - 1
                # the block separator ─ and the name delimiters ؟ " ride along
                # on the token; they are not letters and must not count as tail
                # Only the letter immediately after matters. Allowed: the alif of
                # fathatān, a final ی/ه, the silent wāw of عَمْرٍو, and the block
                # separator where the export glued two words together.
                nxt = letters[n + 1] if n + 1 < len(letters) else ""
                # `"` closes a proper name in this export (؟بَنِی تَمِیمٍ")
                if nxt not in ("", "ا", "ی", "ى", "ه", "و", "─", '"'):
                    bad.append((k, w, f"tanwīn followed by {nxt!r}"))
    return bad


def audit_words(t, min_count=6):
    """Same bare word, more than one vocalisation. Ranked so that a lone variant
    beside a dominant one — the shape a typo takes — sorts to the top."""
    forms = defaultdict(Counter)
    for voc in t.values():
        for w in voc.split():
            if not ALL_DIA.search(w):
                continue
            w = w.strip("─")
            if len(strip(w)) < 3:
                continue
            forms[strip(w)][w] += 1
    out = []
    for bare, c in forms.items():
        if len(c) < 2 or sum(c.values()) < min_count:
            continue
        ranked = c.most_common()
        top, topn = ranked[0]
        for variant, n in ranked[1:]:
            if n == 1 and topn >= 5:          # one-off beside an established form
                out.append((topn / 1.0, bare, top, topn, variant, n))
    out.sort(key=lambda x: -x[0])
    return out


def audit_stub(src, lang, t):
    """Overlay entries that add almost no marks of their own. In Persian
    commentary that is correct — one Arabic paradigm word is vocalised and the
    Persian around it is not. In an ARABIC block it means the entry is present
    but the prose was never done, which silently inflates any count that asks
    only whether the key exists."""
    out = []
    for k, voc in t.items():
        if lang.get(k) != "ar":
            continue
        added = len(ALL_DIA.findall(voc)) - len(ALL_DIA.findall(src.get(k, "")))
        letters = len([c for c in strip(voc) if LETTER.match(c)])
        if letters >= 60 and added / max(letters, 1) < 0.05:
            out.append((k, letters, added))
    return sorted(out)


def audit_density(src, t):
    odd = []
    for k, voc in t.items():
        letters = len([c for c in strip(voc) if LETTER.match(c)])
        marks = len(ALL_DIA.findall(voc))
        if letters >= 60 and marks / letters < 0.30:
            odd.append((k, letters, marks, round(marks / letters, 2)))
    return sorted(odd, key=lambda x: x[3])


def main():
    src, lang, chap, t = load()
    print(f"overlay entries : {len(t)}")
    print(f"marks           : {sum(len(ALL_DIA.findall(v)) for v in t.values()):,}")
    print()

    bad = audit_text(src, t)
    print(f"1  TEXT     {len(t) - len(bad)}/{len(t)} blocks strip back to the printed text exactly")
    for k, m in bad[:10]:
        print(f"            FAIL {k}  {m}")

    n, sb = audit_splice(src, t)
    print(f"2  SPLICE   {n - len(sb)}/{n} pre-vocalised source runs survive byte-identical")
    for k, r, why in sb[:10]:
        print(f"            FAIL {k}  {r}  ({why})")

    shb = audit_shape(t)
    print(f"3  SHAPE    {len(shb)} impossible mark clusters")
    for k, w, m in shb[:20]:
        print(f"            {k}  {w}  — {m}")

    wb = audit_words(t)
    print(f"4  WORDS    {len(wb)} one-off spellings beside an established form")
    for _, bare, top, topn, var, n in wb[:25]:
        print(f"            {bare:<16} {top} ×{topn:<4} but {var} ×{n}")

    st = audit_stub(src, lang, t)
    print(f"5  STUB     {len(st)} Arabic blocks in the overlay but not vocalised")
    for k, l, a in st:
        print(f"            {k:<10} {chap.get(k,''):<22} {l} letters, {a} marks added")
    if st:
        print("            (an early automated pass vocalised the ضرب/نصر paradigm")
        print("             book-wide, which puts a key in the overlay for a block")
        print("             whose prose is still untouched — so any progress count")
        print("             that asks only \"is the key present?\" overstates itself.")
        print("             A stub in a treatise reported COMPLETE is a real fault;")
        print("             one in a treatise still in progress is just work to do.)")

    print()
    hard = len(bad) + len(sb) + len(shb)
    print("VERDICT  " + ("no mechanical fault found" if hard == 0
                         else f"{hard} mechanical faults — fix before shipping")
          + f"; {len(st)} blocks still to vocalise")
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
