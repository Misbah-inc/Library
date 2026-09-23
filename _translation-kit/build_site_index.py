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

Three files answer a query:

  assets/search/pages.json      every page: href, book, category, language,
                                volume, page label, chapter. ~0.6 MB gzipped,
                                fetched once, needed to render any result.
  assets/search/t-<NNN>.json    512 shards of word -> page ids. A word lands in
                                a shard by fnv1a(word) % 512, so the browser
                                computes the shard itself and no lookup table
                                is needed. ~34 KB gzipped each.
  <book>/assets/search-<vol>.json   already built, and used here only for
                                snippets and exact-phrase confirmation, fetched
                                lazily for the volumes actually on screen.

Postings are DELTA-ENCODED IN BASE 36 and joined with «.» — «0.4.1.2s» is pages
0, 4, 5, 53. Page ids ascend within a word, so the gaps are small and most
encode to one or two characters. Measured against plain JSON arrays of numbers
this is about a third of the size, and gzip does the rest.

Two things that will silently break search if they drift:

1. **Tokenisation here must match the browser's.** Both split on the same
   non-word class over the same folded text. A word split differently in the
   two places is a word that can never be found, with no error to say so.
2. **Page ids are POSITIONAL** — an index into pages.json. Rebuild both files
   together, always. A stale shard against a fresh page table does not fail;
   it silently returns the wrong pages, which is far worse than an error.
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shards", type=int, default=512)
    a = ap.parse_args()

    cat = json.loads((LIB / "catalog.json").read_text(encoding="utf-8"))
    category = {b["slug"]: b.get("category", "") for b in cat.get("books", [])}

    src = sources([b['slug'] for b in cat.get('books', []) if not b.get('placeholder')])
    if not src:
        sys.exit("no per-volume indexes found — run build_search_index.py --all first")

    t0 = time.time()
    pages = []                                  # positional: id -> row
    post = collections.defaultdict(list)        # word -> ascending page ids
    for path, book, lang, vol in src:
        rows = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
        for r in rows:
            pid = len(pages)
            pages.append([r["href"], book, category.get(book, ""), lang,
                          vol or "", r["p"],
                          (r.get("part") or {}).get("ar", "")])
            for w in {w for w in SPLIT.split(r["t"]) if len(w) >= MINLEN}:
                post[w].append(pid)
        print(f"  {pathlib.Path(path).relative_to(LIB).as_posix():<44} "
              f"{len(rows):>5} pages  [{lang}]")

    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("t-*.json"):            # a stale shard returns WRONG pages
        old.unlink()

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

    meta = {"shards": a.shards, "pages": len(pages), "words": len(post),
            "built": time.strftime("%Y-%m-%d")}
    (OUT / "pages.json").write_bytes(json.dumps(
        {"meta": meta, "rows": pages}, ensure_ascii=False,
        separators=(",", ":")).encode("utf-8"))

    pt = (OUT / "pages.json").stat().st_size
    # CloudFront auto-compresses only BELOW 10,000,000 bytes. pages.json is
    # fetched by every reader who searches; at 8.5 MB it arrives as 0.57 MB
    # gzipped, and one byte over the ceiling it arrives as 8.5 MB raw — a 15x
    # regression with no error anywhere to announce it. ~153 bytes per page,
    # so the ceiling is around 65,000 pages.
    #
    # The fix when it comes is to shard the page table the way the postings are
    # already sharded — a reader needs the rows for their hits, not all of them.
    CF_LIMIT = 10_000_000
    if pt > CF_LIMIT:
        print("")
        print(f"  ** pages.json is {pt:,} bytes, OVER CloudFront's "
              f"{CF_LIMIT:,}-byte compression ceiling. It will be served "
              f"UNCOMPRESSED. Shard it before deploying. **")
    elif pt > CF_LIMIT * 0.8:
        print("")
        print(f"  ! pages.json is at {100*pt/CF_LIMIT:.0f}% of CloudFront's "
              f"compression ceiling ({pt:,} of {CF_LIMIT:,} bytes) — about "
              f"{(CF_LIMIT-pt)//max(1, pt//len(pages)):,} more pages of headroom.")
    print(f"\n  {len(pages):,} pages, {len(post):,} words, {a.shards} shards")
    print(f"  assets/search/pages.json   {pt/1048576:6.2f} MB")
    print(f"  assets/search/t-*.json     {total/1048576:6.2f} MB "
          f"({total/a.shards/1024:.0f} KB average shard)")
    print(f"  {time.time()-t0:.0f}s")
    print("\n  NOT committed (.gitignore) — deploy_s3.py uploads them.")


if __name__ == "__main__":
    main()
