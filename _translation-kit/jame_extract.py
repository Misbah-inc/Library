#!/usr/bin/env python3
"""Extract جامع المقدمات (Ghaemiyeh HTML export) into printed pages.

  jame_extract.py vol1.htm vol2.htm > jame_pages.json

Shape of the export, same family as Bayt al-Ahzan but not identical:

  <H1 class=content_h1>   volume title, then a trailing "درباره مركز" section
                          that is Ghaemiyeh's own boilerplate and is dropped
  <H2 class=content_h2>   the treatises — 9 in vol 1, 6 in vol 2, plus the
                          colophon (مشخصات کتاب) and its اشاره
  <H3 class=content_h3>   فصل headings inside a treatise
  <P class=content_paragraph><SPAN class=content_text>  prose, and the page
                          markers, which look like "ص :137"

The marker CLOSES the page it names — text runs from the previous marker up to
and including its own. Established from the tail of both files: the last marker
is 609 (vol 1) and 607 (vol 2) with no content after it, which could not happen
if a marker opened its page. Both volumes number 1..N with no gaps, so unlike
Bayt al-Ahzan there is nothing to fill in.

Each block is tagged ar or fa. This edition is a Persian commentary wrapped
around Arabic matn, and the two need different fonts and different treatment —
tashkīl belongs only on the Arabic. Classification is deliberately biased
toward fa: mislabelling Persian as Arabic would set Persian in the Arabic
serif face and expose it to vocalisation, which is the worse failure.
"""
import argparse, html, json, pathlib, re, sys

# پ چ ژ گ exist only in Persian. The export writes Arabic with Persian
# letterforms (ی for ي, ک for ك), so those two are NOT usable as signals.
PERSIAN_ONLY = set("پچژگ")
ZWNJ = "‌"

FA_WORDS = set("""است هست بود باشد باشند شود شوند کند کنند کرد کردن کرده شده می نمی
که را از به این آن اینکه چون چنانکه هر یا نیز خود برای بر با تا هم گویند گفته
دارد دارند داشت یعنی وقتی زیرا اگر پس آنکه بی همه دیگر""".split())

AR_WORDS = set("""فی من علی إلی عن هو هي هما هم الذي التي قال قوله إن أن أنه ما لا
إلا کان کانت هذا هذه ذلک تلک ثم قد لم لن بل أو أي عند بعد قبل حين نحو مثل
والحاصل أيضا كذلک فإن لأن حتى""".split())


def clean(fragment):
    """HTML fragment -> plain text lines, keeping ZWNJ (Persian needs it)."""
    t = re.sub(r"(?is)<br\s*/?>", "\n", fragment)
    t = re.sub(r"(?s)<[^>]+>", "", t)
    t = html.unescape(t)
    t = re.sub(r"[ \t ]+", " ", t)
    return [ln.strip() for ln in t.split("\n") if ln.strip()]


def one(fragment):
    return " ".join(clean(fragment))


def classify(t):
    """'ar' or 'fa' for one block of text."""
    if any(ch in PERSIAN_ONLY for ch in t) or ZWNJ in t:
        return "fa"
    words = re.findall(r"[؀-ۿ‌]+", t)
    if not words:
        return "fa"
    fa = sum(1 for w in words if w in FA_WORDS)
    ar = sum(1 for w in words if w in AR_WORDS)
    if fa == 0 and ar > 0:
        return "ar"
    if ar > fa * 3:
        return "ar"
    # no Persian function word at all in a run of real length reads as matn
    if fa == 0 and len(words) >= 4:
        return "ar"
    return "fa"


PAGE_RE = re.compile(r"^ص\s*:?\s*([0-9۰-۹]+)$")
FA_DIG = "۰۱۲۳۴۵۶۷۸۹"


def toint(s):
    return int("".join(str(FA_DIG.index(c)) if c in FA_DIG else c for c in s))


def tokenize(path):
    s = pathlib.Path(path).read_text(encoding="utf-8-sig", errors="replace")
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", "", s)

    m = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", s)
    vol_title = one(m.group(1)) if m else ""

    # drop Ghaemiyeh's "درباره مركز" trailer — it is their advert, not the book
    for needle in ("درباره مركز", "درباره مرکز"):
        cut = s.find(needle)
        if cut > 0:
            s = s[:cut]
            break

    toks = []
    pat = re.compile(r"(?is)<(h2|h3)[^>]*>(.*?)</\1>"
                     r"|<p\s+class=content_paragraph[^>]*>(.*?)</p>")
    for m in pat.finditer(s):
        if m.group(1):
            txt = one(m.group(2)).strip().strip('"').strip()
            if txt:
                toks.append((m.group(1).lower(), txt))
        else:
            for line in clean(m.group(3)):
                pm = PAGE_RE.match(line)
                if pm:
                    toks.append(("PAGE", toint(pm.group(1))))
                elif line and line != "ص :":
                    toks.append(("p", line))
    return vol_title, toks


def build_volume(v, path):
    vol_title, toks = tokenize(path)

    chapters, chap_title, chap_n = [], "", 0
    pages, cur = [], []
    page_chapter, page_chapter_n = "", 0

    def flush(pageno):
        """Close the accumulated blocks as printed page `pageno`."""
        pages.append({
            "n": pageno,
            "chapter": page_chapter,
            "chapter_n": page_chapter_n,
            "blocks": cur[:],
        })

    for kind, val in toks:
        if kind == "PAGE":
            flush(val)
            cur = []
            # the next page opens in whatever chapter is current
            page_chapter, page_chapter_n = chap_title, chap_n
        elif kind == "h2":
            chap_n += 1
            chap_title = val
            chapters.append({"n": chap_n, "title": val})
            if not cur:                       # page opens on this treatise
                page_chapter, page_chapter_n = chap_title, chap_n
            cur.append({"tag": "h2", "lang": classify(val), "t": val})
        elif kind == "h3":
            if not cur:
                page_chapter, page_chapter_n = chap_title, chap_n
            cur.append({"tag": "h3", "lang": classify(val), "t": val})
        else:
            if not cur:
                page_chapter, page_chapter_n = chap_title, chap_n
            cur.append({"tag": "p", "lang": classify(val), "t": val})

    if cur:                                    # trailing text with no marker
        flush(pages[-1]["n"] + 1 if pages else 1)

    return {"v": v, "title": vol_title, "chapters": chapters, "pages": pages}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sources", nargs="+")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--out", help="write here instead of stdout; PowerShell's '>' "
                                  "prepends a UTF-8 BOM that json.load then rejects")
    a = ap.parse_args()

    vols = [build_volume(i + 1, p) for i, p in enumerate(a.sources)]
    out = {"title": "جامع المقدمات", "volumes": vols}

    if a.stats:
        for vol in vols:
            ps = vol["pages"]
            nums = [p["n"] for p in ps]
            blocks = sum(len(p["blocks"]) for p in ps)
            ar = sum(1 for p in ps for b in p["blocks"] if b["lang"] == "ar")
            fa = blocks - ar
            arch = sum(len(b["t"]) for p in ps for b in p["blocks"] if b["lang"] == "ar")
            fach = sum(len(b["t"]) for p in ps for b in p["blocks"] if b["lang"] == "fa")
            print(f"volume {vol['v']}: {vol['title']}", file=sys.stderr)
            print(f"  pages    : {len(ps)}  ({min(nums)}..{max(nums)})  "
                  f"sequential={nums == list(range(min(nums), max(nums)+1))}",
                  file=sys.stderr)
            print(f"  empty    : {sum(1 for p in ps if not p['blocks'])}", file=sys.stderr)
            print(f"  chapters : {len(vol['chapters'])}", file=sys.stderr)
            print(f"  blocks   : {blocks}   ar={ar} ({arch:,} ch)  fa={fa} ({fach:,} ch)",
                  file=sys.stderr)
            for c in vol["chapters"]:
                n = sum(1 for p in ps for b in p["blocks"] if p["chapter_n"] == c["n"])
                print(f"     {c['n']:>2}. {c['title'][:44]:<46} blocks={n}", file=sys.stderr)

    blob = json.dumps(out, ensure_ascii=False)
    if a.out:
        pathlib.Path(a.out).write_text(blob, encoding="utf-8")
    else:
        print(blob)


if __name__ == "__main__":
    main()
