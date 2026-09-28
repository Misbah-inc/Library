#!/usr/bin/env python3
"""Build the in-book search indexes a reader's browser searches.

    python build_search_index.py bihar kafi
    python build_search_index.py --all
    python build_search_index.py en/bihar --force

There is no search engine behind this site. When a reader opens a book, clicks
Search and types a word, `reader.js` downloads that book's index and scans it in
the browser — so the index has to BE the book's text. That is the whole reason
these files are large, and the reason they are per volume.

**One file per volume, never one per book.** Bihar as a single file is 126 MB,
and CloudFront's automatic compression stops at 10,000,000 bytes, so a
single-file index would also arrive uncompressed. Per volume each file is about
1 MB and lands around 250 KB gzipped — measured, not assumed. `reader.js` asks
for `search-<vol>.json` when the page declares `data-volume`, and falls back to
`search-index.json` for books that have no volumes.

**A translated page indexes its own language.** `reader.js` pins `BOOK` to the
Arabic root so `toc.json` resolves, so it cannot be used to find the English
text; the search loader resolves `<lang>/<slug>` first and falls back to the
Arabic. Run this over `en/bihar` the same way you run it over `bihar`.

**The text includes footnotes**, which is what the hand-made Bihar index did:
on `bihar/1/26/` it carries 1,400 folded characters against 1,269 for the body
alone. The editor's notes are where a rare word is usually explained, so they
are worth finding.

**Folding must match `fold()` in reader.js exactly.** The reader's query is
folded by that function and matched with `indexOf`, so any disagreement here is
a word that can never be found — silently, with no error anywhere. FOLD and
DROP below are transcribed from it; change them only together.

These files are NOT committed — see the `.gitignore` entry. They are derived
from the published HTML in one command, they would add ~130 MB to a repository
that already struggles to push, and `aws s3 sync` does not read `.gitignore`,
so `deploy_s3.py` uploads them regardless. The cost is that a fresh clone has
no indexes until this is run; that is written down in DEPLOY.md.
"""

import argparse
import html
import json
import pathlib
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

LIB = pathlib.Path(__file__).resolve().parent.parent

# Transcribed from reader.js — keep in step or a folded query stops matching.
FOLD = {"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ی",
        "ي": "ی", "ك": "ک", "ة": "ه", "ؤ": "و", "ئ": "ی"}
DROP = re.compile("[ؐ-ًؚ-ْٰۖ-ۭـ]")  # combining marks + tatweel

TAG = re.compile(r"<[^>]+>")
FNREF = re.compile(r'<a class="fnref"[^>]*>.*?</a>', re.S)
WS = re.compile(r"\s+")

# The Qur'an and مفاتیح have in-book search of their own — qnav.js searches
# verses, mafatih.js has a two-index scheme — and neither reads these files.
# They are still indexed, because SITE-WIDE search is built from these files
# and the reader expects /search/ to cover the whole library. Writing them is
# therefore harmless to those books and necessary to the site.
OWN_SEARCH = set()


def fold(s):
    return "".join(FOLD.get(c, c.lower()) for c in DROP.sub("", s))


def page_text(src):
    """The page's readable text — body and footnotes, markup gone.

    Match `<div class="body` WITHOUT the closing quote: مفاتیح writes
    `class="body mafatih"`, so requiring the quote silently produced 694
    empty rows — a whole book that returned no search hit and no error.
    """
    try:
        art = src[src.index('<div class="body'):src.index("</article>")]
    except ValueError:
        return ""
    # strip the footnote REFERENCE numerals (the markers), keep the notes
    art = FNREF.sub(" ", art)
    # Drop the Unicode bidi isolates الغدير's builder puts around Latin-digit
    # citation groups (U+2066 … U+2069). They are invisible and carry no
    # meaning, but fold() keeps them — it only strips diacritics — so without
    # this they would sit inside the indexed text and a phrase crossing one
    # could never match, since a reader's query will never contain them.
    art = art.translate({0x2066: None, 0x2067: None, 0x2068: None,
                         0x2069: None, 0x200E: None, 0x200F: None})
    return WS.sub(" ", html.unescape(TAG.sub(" ", art))).strip()


def page_dirs(d):
    """Sub-directories of `d` that hold a reading page, in on-disk order."""
    out = []
    for p in d.iterdir():
        if p.is_dir() and (p / "index.html").is_file():
            out.append(p)
    return out


def volumes(root):
    """[(volume-or-None, [page dirs])] — one entry per index file to write."""
    vols = sorted((p for p in root.iterdir()
                   if p.is_dir() and p.name.isdigit()), key=lambda p: int(p.name))
    # A numeric directory is a VOLUME only if it holds page directories of its
    # own. Bayt al-Ahzan's `12/` is page 12 and holds no sub-pages, so a book
    # whose numeric dirs are all leaves is not a multi-volume book.
    real = [v for v in vols if page_dirs(v)]
    if real:
        return [(v.name, page_dirs(v)) for v in real]
    pages = page_dirs(root)
    return [(None, pages)] if pages else []


def chapter_map(root, vol):
    """page id -> chapter title, from the book's toc.json if it has one.

    A language tree has no toc.json of its own — only the Arabic root does,
    which is exactly why reader.js pins BOOK there. Fall back to it, or every
    translated hit loses its chapter label.
    """
    tp = root / "assets" / "toc.json"
    if not tp.is_file():
        tp = LIB / root.name / "assets" / "toc.json"
    if not tp.is_file():
        return ([], [])
    try:
        toc = json.loads(tp.read_text(encoding="utf-8"))
    except Exception:
        return ([], [])
    rows = [r for r in toc if isinstance(r, dict) and r.get("p") is not None]
    if vol is not None:
        rows = [r for r in rows if str(r.get("vol", vol)) == str(vol)]
    if not rows:
        return ([], [])
    rows.sort(key=lambda r: r["p"])
    # Front matter and the author's own text are TWO page-number spaces, and
    # they overlap. Six Bihar volumes, al-Kafi 1, al-Faqih 1 and البرهان 1 all
    # paginate a publisher's foreword 1..N before the text restarts at 1, so a
    # toc row for fm page 10 and a reading page numbered 10 are different pages
    # with the same number. Matching on the number alone put a front-matter
    # heading on 45 main pages of Bihar 29, 25 of البرهان 1 and 15 of al-Faqih 1,
    # and left every fm page with no chapter label at all — its own rows were
    # never reachable, because an fm page's `n` is None.
    return ([r for r in rows if "/fm-" not in r.get("href", "")],
            [r for r in rows if "/fm-" in r.get("href", "")])


def part_for(rows, n):
    """The last chapter that starts at or before page n."""
    title = None
    for r in rows:
        if n is None or r["p"] > n:
            break
        title = r.get("title")
    return {"ar": title} if title else None


def build(rel, force=False):
    root = LIB / rel
    if not root.is_dir():
        print(f"  {rel}: no such directory — skipped")
        return 0, 0
    slug = pathlib.PurePosixPath(rel).name
    if slug in OWN_SEARCH:
        print(f"  {rel}: ships its own search — skipped")
        return 0, 0
    groups = volumes(root)
    if not groups:
        print(f"  {rel}: no reading pages found — skipped")
        return 0, 0
    assets = root / "assets"
    assets.mkdir(exist_ok=True)
    files = total = 0
    for vol, pages in groups:
        out = assets / (f"search-{vol}.json" if vol else "search-index.json")
        rows, fm_rows = chapter_map(root, vol)
        recs = []
        for p in pages:
            n = int(p.name) if p.name.isdigit() else None
            # An fm page carries its own number in its own space.
            fm_n = int(p.name[3:]) if p.name.startswith("fm-") and p.name[3:].isdigit() else None
            recs.append({"href": f"{rel}/{vol + '/' if vol else ''}{p.name}/",
                         "p": n if n is not None else p.name,
                         "part": (part_for(fm_rows, fm_n) if fm_n is not None
                                  else part_for(rows, n)),
                         "t": fold(page_text((p / "index.html").read_text(encoding="utf-8")))})
        recs.sort(key=lambda r: (r["p"] if isinstance(r["p"], int) else -1, str(r["p"])))
        for r in recs:
            if r["part"] is None:
                del r["part"]
        # A page that yields nothing is a bug in the extractor, not a fact
        # about the book, and it is invisible in the output size of a big run.
        empty = [r["href"] for r in recs if not r["t"]]
        if empty:
            print(f"    ** {len(empty)} of {len(recs)} pages extracted NO TEXT "
                  f"— first: {empty[0]}")
        blob = json.dumps(recs, ensure_ascii=False).encode("utf-8")
        out.write_bytes(blob)
        files += 1
        total += len(blob)
        print(f"    {out.relative_to(LIB).as_posix():<44} "
              f"{len(recs):>5} pages  {len(blob)/1048576:6.2f} MB")
    return files, total


def discover():
    """Every book tree with reading pages: Arabic roots and language trees."""
    out = []
    cat = json.loads((LIB / "catalog.json").read_text(encoding="utf-8"))
    slugs = [b["slug"] for b in cat.get("books", [])
             if not b.get("placeholder") and b.get("href")]
    for s in slugs:
        if s in OWN_SEARCH:
            continue
        if (LIB / s).is_dir():
            out.append(s)
        for L in ("en", "fa", "ur"):
            if (LIB / L / s).is_dir() and volumes(LIB / L / s):
                out.append(f"{L}/{s}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("books", nargs="*", help="book roots, e.g. bihar kafi en/bihar")
    ap.add_argument("--all", action="store_true", help="every published book tree")
    a = ap.parse_args()
    targets = discover() if a.all or not a.books else a.books
    print(f"indexing {len(targets)} book tree(s)\n")
    t0 = time.time()
    files = total = 0
    for rel in targets:
        print(f"  {rel}")
        f, n = build(rel)
        files += f
        total += n
    print(f"\n{files} index files, {total/1048576:.1f} MB on disk, "
          f"{time.time()-t0:.0f}s")
    print("NOT committed — .gitignore covers them; deploy_s3.py uploads them anyway.")


if __name__ == "__main__":
    main()
