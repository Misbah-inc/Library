#!/usr/bin/env python3
"""Build the site-wide full-text search index — every book, every language.

    python build_site_index.py            # reads the per-volume text indexes
    python build_site_index.py --shards 512

Run `build_search_index.py --all` FIRST: this reads its `search-*.json` output
rather than the 53,000 pages themselves, which turns an hour of Google Drive
reads into a couple of minutes.

WHY THIS SHAPE. The old site search downloaded one whole index per book and
scanned it. That works at 231 pages and is impossible at 53,000 — the library's
text is about 165 MB, and no reader is going to download the library to search
it. So the text is inverted: for each WORD, the list of pages it appears on.
A reader searching «الصدقة» needs the entry for that one word, not the corpus.

Four files answer a query, and NONE of them is the whole corpus:

  assets/search/meta.json       shard counts and the SEGMENT TABLE: one row per
                                source file giving the id range it occupies and
                                its book, category, language and volume. ~130
                                rows. Fetched once; this is all that book and
                                category filtering needs.
  assets/search/t-<NNN>.json    512 shards of word -> page ids. A word lands in
                                a shard by fnv1a(word) % 512, so the browser
                                computes the shard itself and no lookup table
                                is needed. ~23 KB gzipped each.
  assets/search/p-<NNN>.json    page rows — name, printed label, chapter — in
                                blocks of 1,000 ids. Fetched only for the
                                results actually being displayed.
  <book>/assets/search-<vol>.json   used only by the per-book Search button.

**Why the page table is sharded.** It used to be one `pages.json` carrying
href/book/category/language/volume/label/chapter for every page. At 55,393
pages that reached 8,471,418 bytes — 85% of CloudFront's 10,000,000-byte
auto-compression ceiling. Crossing that ceiling is not an error: the file
simply starts arriving RAW, 8.5 MB instead of 0.57 MB gzipped, to every reader
who searches. Two changes removed the cliff rather than postponing it:

  * book, category, language and volume moved into the segment table, because
    each source file occupies a CONTIGUOUS run of ids and those fields are
    properties of the run, not of 55,000 separate pages;
  * what remains is split into blocks of 1,000, and a reader fetches only the
    blocks holding their own results.

The href is rebuilt from segment + name rather than stored. `main()` asserts
that the rebuild reproduces the original exactly for every page, because if it
ever stops doing so, every search result links to a 404.

Postings are DELTA-ENCODED IN BASE 36 and joined with «.» — «0.4.1.2s» is pages
0, 4, 5, 53. Page ids ascend within a word, so the gaps are small and most
encode to one or two characters. Measured against plain JSON arrays of numbers
this is about a third of the size, and gzip does the rest.

Two things that will silently break search if they drift:

1. **Tokenisation here must match the browser's.** Both split on the same
   non-word class over the same folded text. A word split differently in the
   two places is a word that can never be found, with no error to say so.
2. **Page ids are POSITIONAL** — an index into the concatenated run of source
   files. `t-*`, `p-*` and `meta.json` are one artefact in many files; rebuild
   them together, always. A stale shard against a fresh segment table does not
   fail, it silently returns the wrong pages, which is far worse than an error.
   The builder deletes every `t-*` and `p-*` before writing, so a shrunken set
   cannot leave orphans behind.
"""

import argparse
import collections
import json
import pathlib
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

LIB = pathlib.Path(__file__).resolve().parent.parent
OUT = LIB / "assets" / "search"

# Must match the browser's tokeniser: letters, digits and underscore are token
# characters, everything else separates. Python's \w is Unicode-aware, so it
# already covers Arabic, Persian and Urdu letters.
#
# Do NOT "help" it by adding ؀-ۿ. That block contains the Arabic
# COMMA (U+060C), SEMICOLON, QUESTION MARK and FULL STOP (U+06D4), so adding it
# makes «الصدقه،» a single token that a search for «الصدقه» can never match —
# and the only symptom is a word that quietly returns nothing.
#
# The browser cannot use \w for this: in JavaScript \w is ASCII-only and would
# split every Arabic word into nothing. It uses /[^\p{L}\p{N}_]+/u instead, and
# the two are checked against each other — see the tokeniser parity test.
SPLIT = re.compile(r"[^\w]+", re.UNICODE)
MINLEN = 2

B36 = "0123456789abcdefghijklmnopqrstuvwxyz"


def b36(n):
    if n == 0:
        return "0"
    s = ""
    while n:
        n, r = divmod(n, 36)
        s = B36[r] + s
    return s


def shard_of(word, shards):
    """FNV-1a 32 over the UTF-8 bytes, and it has to be this.

    The browser computes the shard itself so no word->shard table has to be
    shipped, and `crypto.subtle` offers SHA only — there is no MD5 in a browser.
    FNV-1a is four lines in both languages and gives identical results.
    """
    h = 0x811C9DC5
    for b in word.encode("utf-8"):
        h = ((h ^ b) * 0x01000193) & 0xFFFFFFFF
    return h % shards


def sources(slugs):
    """Every per-volume text index on disk, as (path, book, lang, volume).

    Enumerated from the catalogue's slugs, NOT by a recursive glob: the tree
    holds ~53,000 directories on a streamed Google Drive, and walking it all
    to find ~130 files took longer than reading them.

    `search-index.json` is the shape a book with no volumes uses — but Bihar
    also still carries one from before per-volume files existed, covering
    volume 1 alone. Indexing it beside `search-1.json` would enter all 231 of
    those pages TWICE, and a duplicate page id is not an error anywhere: it
    just shows the reader the same hit two times. So within one tree, a
    `search-index.json` is used only when there are no numbered files.
    """
    out = []
    trees = [(s, "ar", LIB / s) for s in slugs]
    trees += [(s, L, LIB / L / s) for s in slugs for L in ("en", "fa", "ur")]
    for slug, lang, d in trees:
        a = d / "assets"
        if not a.is_dir():
            continue
        numbered = sorted((f for f in a.glob("search-*.json")
                           if f.stem[len("search-"):].isdigit()),
                          key=lambda f: int(f.stem[len("search-"):]))
        flat = a / "search-index.json"
        files = numbered or ([flat] if flat.is_file() else [])
        for f in files:
            name = f.stem[len("search-"):]
            out.append((str(f), slug, lang, name if name != "index" else None))
    return out


PAGE_SHARD = 1000     # pages per p-*.json shard


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shards", type=int, default=512)
    ap.add_argument("--page-shard", type=int, default=PAGE_SHARD)
    a = ap.parse_args()

    cat = json.loads((LIB / "catalog.json").read_text(encoding="utf-8"))
    category = {b["slug"]: b.get("category", "") for b in cat.get("books", [])}

    src = sources([b['slug'] for b in cat.get('books', []) if not b.get('placeholder')])
    if not src:
        sys.exit("no per-volume indexes found — run build_search_index.py --all first")

    t0 = time.time()
    # Each source file contributes a CONTIGUOUS run of ids, which is what makes
    # the segment table possible: book, category, language and volume are
    # properties of the run, not of each page, so they are stored once per file
    # (~130 rows) instead of 55,000 times. That is most of the old page table.
    rows = []                                   # positional: id -> [name, p, chapter]
    segs = []                                   # [start, count, book, cat, lang, vol]
    post = collections.defaultdict(list)        # word -> ascending page ids
    for path, book, lang, vol in src:
        src_rows = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
        start = len(rows)
        for r in src_rows:
            pid = len(rows)
            name = r["href"].rstrip("/").rsplit("/", 1)[-1]
            # The reader rebuilds the href from segment + name. If that ever
            # stops reproducing the original exactly, every search result links
            # to a 404 — so it is asserted here, where it is cheap, rather than
            # discovered in the browser.
            rebuilt = (f"{lang + '/' if lang != 'ar' else ''}{book}/"
                       f"{vol + '/' if vol else ''}{name}/")
            if rebuilt != r["href"]:
                sys.exit(f"href cannot be rebuilt: {r['href']!r} -> {rebuilt!r}")
            rows.append([name, r["p"], (r.get("part") or {}).get("ar", "")])
            for w in {w for w in SPLIT.split(r["t"]) if len(w) >= MINLEN}:
                post[w].append(pid)
        segs.append([start, len(src_rows), book, category.get(book, ""),
                     lang, vol or ""])
        print(f"  {pathlib.Path(path).relative_to(LIB).as_posix():<44} "
              f"{len(src_rows):>5} pages  [{lang}]")

    OUT.mkdir(parents=True, exist_ok=True)
    # A stale shard of either kind returns WRONG pages rather than failing.
    for pat in ("t-*.json", "p-*.json"):
        for old in OUT.glob(pat):
            old.unlink()
    if (OUT / "pages.json").exists():           # the unsharded table this replaces
        (OUT / "pages.json").unlink()

    buckets = collections.defaultdict(dict)
    for w, ids in post.items():
        enc, prev = [], 0
        for i in ids:
            enc.append(b36(i - prev))
            prev = i
        buckets[shard_of(w, a.shards)][w] = ".".join(enc)

    total = 0
    for h in range(a.shards):
        b = json.dumps(buckets.get(h, {}), ensure_ascii=False,
                       separators=(",", ":")).encode("utf-8")
        (OUT / f"t-{h:03d}.json").write_bytes(b)
        total += len(b)

    nps = (len(rows) + a.page_shard - 1) // a.page_shard
    ptotal = biggest = 0
    for k in range(nps):
        chunk = rows[k * a.page_shard:(k + 1) * a.page_shard]
        b = json.dumps(chunk, ensure_ascii=False,
                       separators=(",", ":")).encode("utf-8")
        (OUT / f"p-{k:03d}.json").write_bytes(b)
        ptotal += len(b)
        biggest = max(biggest, len(b))

    meta = {"shards": a.shards, "pageShard": a.page_shard, "pageShards": nps,
            "pages": len(rows), "words": len(post), "segments": segs,
            "built": time.strftime("%Y-%m-%d")}
    (OUT / "meta.json").write_bytes(json.dumps(
        meta, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    mt = (OUT / "meta.json").stat().st_size

    # CloudFront auto-compresses only BELOW 10,000,000 bytes, and nothing warns
    # when a file crosses it — it just starts arriving raw. Sharding keeps every
    # file far under, and this check is kept so that stops being true loudly.
    CF_LIMIT = 10_000_000
    worst = max(mt, biggest, total // max(1, a.shards))
    if worst > CF_LIMIT * 0.8:
        print("")
        print(f"  ! largest search file is {worst:,} bytes, "
              f"{100*worst/CF_LIMIT:.0f}% of CloudFront's compression ceiling")

    print("")
    print(f"  {len(rows):,} pages, {len(post):,} words, "
          f"{len(segs)} segments")
    print(f"  assets/search/meta.json    {mt/1024:7.1f} KB   "
          f"(fetched once — was an 8.5 MB page table)")
    print(f"  assets/search/p-*.json     {ptotal/1048576:6.2f} MB in {nps} shards, "
          f"largest {biggest/1024:.0f} KB")
    print(f"  assets/search/t-*.json     {total/1048576:6.2f} MB in {a.shards} shards, "
          f"average {total/a.shards/1024:.0f} KB")
    print(f"  {time.time()-t0:.0f}s")
    print("")
    print("  NOT committed (.gitignore) — deploy_s3.py uploads them.")


if __name__ == "__main__":
    main()
