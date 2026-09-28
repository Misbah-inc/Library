#!/usr/bin/env python3
"""Refresh the chapter LABELS in Bihar's search indexes, without re-reading
61,000 pages.

    python bihar_search_relabel.py [--write]

A search record is `{href, p, part, t}`. The ي/ى repair changed the page text,
so the instinct is to rebuild every index — seven hours of Drive reads.

It is not necessary, and the reason is exact. `t` is the page text passed
through `fold()`, and `fold` maps ي, ى AND ی all to ی. Every edit the repair
made was between those three letters, so **every `t` in the index is already
byte-identical to what a rebuild would produce.** What did change is `part.ar`,
the chapter label, which is stored UNFOLDED for display and comes from
`toc.json` — one file, already corrected.

So this recomputes `part` from the corrected toc and leaves `t` untouched.

The argument above is checked, not trusted: `--write` first re-derives `t` from
the live pages for a sample and refuses to run if a single one disagrees.
"""

import argparse
import json
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")

import build_search_index as B  # noqa: E402

LIB = B.LIB
SAMPLE = 40


def check_t_unchanged(rel="bihar"):
    """Re-derive `t` from the live pages and compare to what is stored.

    This is the whole justification for not rebuilding. If it fails, the fold
    reasoning is wrong somewhere and the indexes must be rebuilt properly.
    """
    root = LIB / rel
    vols = [v for v, _ in B.volumes(root)]
    random.seed(5)
    checked = bad = 0
    for vol in random.sample(vols, min(6, len(vols))):
        p = root / "assets" / f"search-{vol}.json"
        if not p.is_file():
            continue
        recs = json.loads(p.read_text(encoding="utf-8"))
        for r in random.sample(recs, min(SAMPLE // 6 + 1, len(recs))):
            f = LIB / r["href"].strip("/") / "index.html"
            if not f.is_file():
                continue
            now = B.fold(B.page_text(f.read_text(encoding="utf-8")))
            checked += 1
            if now != r.get("t", ""):
                bad += 1
                if bad <= 2:
                    print(f"   !! {r['href']} differs")
                    a, b = r.get("t", ""), now
                    for i in range(min(len(a), len(b))):
                        if a[i] != b[i]:
                            print(f"      stored: …{a[max(0,i-30):i+30]}…")
                            print(f"      now   : …{b[max(0,i-30):i+30]}…")
                            break
    print(f"`t` re-derived from live pages: {checked} sampled, {bad} differ")
    return bad == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--rel", default="bihar")
    a = ap.parse_args()

    if not check_t_unchanged(a.rel):
        sys.exit("`t` is NOT stable under the repair — rebuild the indexes "
                 "properly instead of relabelling.")

    root = LIB / a.rel
    files = changed = rows = 0
    for vol, pages in B.volumes(root):
        p = root / "assets" / (f"search-{vol}.json" if vol else "search-index.json")
        if not p.is_file():
            continue
        recs = json.loads(p.read_text(encoding="utf-8"))
        toc_rows, fm_rows = B.chapter_map(root, vol)
        n_changed = 0
        for r in recs:
            name = r["href"].rstrip("/").rsplit("/", 1)[-1]
            fm_n = int(name[3:]) if name.startswith("fm-") and name[3:].isdigit() else None
            n = int(name) if name.isdigit() else None
            part = (B.part_for(fm_rows, fm_n) if fm_n is not None
                    else B.part_for(toc_rows, n))
            old = r.get("part")
            if part is None:
                if old is not None:
                    r.pop("part", None)
                    n_changed += 1
            elif old != part:
                r["part"] = part
                n_changed += 1
        files += 1
        rows += n_changed
        if n_changed:
            changed += 1
            if a.write:
                p.write_bytes(json.dumps(recs, ensure_ascii=False).encode("utf-8"))
    print(f"{a.rel}: {files} index files, {changed} updated, "
          f"{rows:,} chapter labels refreshed"
          f"{'' if a.write else '  (dry run)'}")


if __name__ == "__main__":
    main()
