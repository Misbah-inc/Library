#!/usr/bin/env python3
"""Segment Bayt al-Ahzan's Arabic into sentence blocks — once, and for good.

    bayt_ar_split.py            # bayt_ar.json -> bayt_ar_blocks.json

The AB Library export carries one <p class="page-text"> per printed page, so
`bayt_ar.json` has exactly one block per page — median 1,141 characters, up to
2,016. Bihar has about eight blocks a page, and that is precisely why Bihar
reads well: each Arabic paragraph is followed by its own translation. At one
block per page a translated page would be a wall of Arabic followed by a wall
of English, and `verify.py`'s node-count check would have nothing to align.

So the Arabic is split here into sentences. The TEXT IS NOT TOUCHED: the
whitespace in the source is already single-spaced throughout (checked — zero
exceptions across all 189 pages), so joining the parts back with one space
reproduces the original character for character. That is asserted for every
page, and the script refuses to write if it ever fails.

WHY THIS IS A FILE AND NOT A STEP IN THE BUILDER. English will be keyed to
`data-i`. If the segmentation were recomputed at build time, then any later
tweak to the splitting rule — one more punctuation mark, a different minimum
length — would renumber the blocks and silently re-point every translated line
onto the wrong Arabic. The same trap that unit ids posed in مفاتیح. So the
split is computed once, committed, and from then on treated as data: the
builder and the translation both read `bayt_ar_blocks.json`, and this script
should not be re-run over a book that already has translations.
"""
import json, pathlib, re, sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = pathlib.Path(__file__).parent

# Sentence end: the Arabic full stop as this edition writes it, plus the
# question and exclamation marks. Splitting happens AFTER the mark, which stays
# with the sentence it closes.
SPLIT = re.compile(r"(?<=[.؟!])\s+")

# A run shorter than this is not a sentence — it is «فصل .» or a stray «قال .»
# left over by the split, and giving it its own block (and its own English
# line) would be noise on the page. It is folded back into the block before it.
MIN = 40


def split_block(text):
    parts = [p for p in SPLIT.split(text) if p.strip()]
    out = []
    for p in parts:
        if out and len(p) < MIN:
            out[-1] += " " + p
        else:
            out.append(p)
    # a short opener has nothing before it to join, so it takes the next block
    while len(out) > 1 and len(out[0]) < MIN:
        out[0] = out[0] + " " + out[1]
        del out[1]
    return out or [text]


def main():
    src = json.loads((HERE / "bayt_ar.json").read_text(encoding="utf-8"))
    out = dict(src)
    pages = []
    before = after = 0

    for page in src["pages"]:
        blocks = []
        for b in page["blocks"]:
            before += 1
            for piece in split_block(b["ar"]):
                blocks.append({"i": len(blocks), "ar": piece})
        after += len(blocks)

        # the load-bearing assertion: the Arabic must come back unchanged
        rejoined = " ".join(b["ar"] for b in blocks)
        original = " ".join(b["ar"] for b in page["blocks"])
        if rejoined != original:
            sys.exit(f"page {page['n']}: split is not lossless — refusing to write\n"
                     f"  original {len(original)} chars, rejoined {len(rejoined)}")
        pages.append({"n": page["n"], "blocks": blocks, "notes": page["notes"]})

    out["pages"] = pages
    out["segmented"] = True
    (HERE / "bayt_ar_blocks.json").write_text(
        json.dumps(out, ensure_ascii=False), encoding="utf-8")

    sizes = sorted(len(b["ar"]) for p in pages for b in p["blocks"])
    print(f"pages            : {len(pages)}")
    print(f"blocks           : {before} -> {after}  ({after / len(pages):.1f} per page)")
    print(f"chars per block  : median {sizes[len(sizes) // 2]}, "
          f"p90 {sizes[int(.9 * len(sizes))]}, max {sizes[-1]}")
    print(f"every page rejoins to the original Arabic exactly")
    print(f"-> {HERE / 'bayt_ar_blocks.json'}")


if __name__ == "__main__":
    main()
