#!/usr/bin/env python3
"""Re-sync the Arabic embedded in en/fa/ur Bihar volume 1 after the ي/ى repair.

    python bihar_v1_resync.py [--write]

Volume 1 is the only translated volume, and a translated page does not merely
link to the Arabic — it CARRIES it, as `<p lang="ar" data-i="N">` beside each
translated line, so the reader can switch between them in place. Repairing the
Arabic source therefore desynchronises three trees at once, and `verify.py`
aligns translations to the Arabic block by block, so it would fail.

**The corrected Arabic is COPIED from the source, never re-inferred.** Running
the four-tier pass over these pages again would be a second, independent guess
at the same words, free to disagree with the first — and on an `fa` or `ur`
page it would also be loose among genuine Persian and Urdu, where ی is correct
and must survive. Copying cannot do either.

Two structures differ between the trees and both are handled:

  * a HEADING is wrapped on the Arabic page in `<span data-ar= data-fa= …>` so
    reader.js can swap it in place; the translated page carries the bare text
    and prints its own translation on the next line. The span is unwrapped
    before comparing — this is the same case `verify.py`'s `unwrap_heading()`
    exists for.
  * a block is replaced only when it is already fold-identical to the source,
    i.e. differs in nothing but the letter forms. Anything else is left alone
    and counted, because a block that disagrees about its TEXT is a different
    problem and must not be papered over.

The guard blanks every region this script is allowed to touch and asserts the
two files are otherwise byte-identical, which is what keeps it away from the
Persian and Urdu translation lines.
"""

import argparse
import collections
import concurrent.futures
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

LIB = pathlib.Path(__file__).resolve().parent.parent
EL = re.compile(
    r'<(h[1-6]|p|div)\b([^>]*\blang="ar"[^>]*\bdata-i="(\d+)"[^>]*)>(.*?)</\1>',
    re.S)
SPAN = re.compile(r'^<span\b[^>]*>(.*)</span>$', re.S)
FY, AY, AM, PK, AK = "ی", "ي", "ى", "ک", "ك"


def fold(s):
    for a, b in ((FY, AY), (AM, AY), (PK, AK)):
        s = s.replace(a, b)
    return s


def unwrap(inner):
    m = SPAN.match(inner.strip())
    return m.group(1) if m else inner


def blocks(path):
    src = path.read_text(encoding="utf-8")
    return src, {m.group(3): m.group(4) for m in EL.finditer(src)}


def blank(s):
    """Punch out every Arabic block — the only thing this script may change."""
    return EL.sub(lambda m: f"<{m.group(1)}{m.group(2)}>\x00</{m.group(1)}>", s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--langs", default="en,fa,ur")
    a = ap.parse_args()

    ar_root = LIB / "bihar/1"
    pages = sorted((p for p in ar_root.iterdir() if p.is_dir()),
                   key=lambda p: (0, int(p.name)) if p.name.isdigit() else (1, 0))
    stat = collections.Counter()
    left_ex = []

    # Each page needs two reads and a write. Serial, over Drive, that is
    # ~20 minutes for work the CPU finishes in under a second — the same
    # mistake that made the earlier pass run 8x slower than it had to.
    for lang in a.langs.split(","):
        changed = 0

        def one(d, lang=lang):
            arf = d / "index.html"
            tf = LIB / lang / "bihar/1" / d.name / "index.html"
            if not arf.is_file() or not tf.is_file():
                stat[f"{lang}:absent"] += 1
                return 0
            _, src_b = blocks(arf)
            tsrc, tr_b = blocks(tf)

            out, pos = [], 0
            for m in EL.finditer(tsrc):
                n, cur = m.group(3), m.group(4)
                s = src_b.get(n)
                if s is None:
                    stat[f"{lang}:no_source_block"] += 1
                    continue
                pick = None
                for cand in (unwrap(s), s):
                    if fold(cur) == fold(cand):
                        pick = cand
                        break
                if pick is None:
                    stat[f"{lang}:left"] += 1
                    if len(left_ex) < 4:
                        left_ex.append((lang, d.name, n, cur[:70], s[:70]))
                    continue
                if pick == cur:
                    stat[f"{lang}:already"] += 1
                    continue
                stat[f"{lang}:fixed"] += 1
                out.append(tsrc[pos:m.start(4)])
                out.append(pick)
                pos = m.end(4)
            if not out:
                return 0
            out.append(tsrc[pos:])
            new = "".join(out)
            assert blank(new) == blank(tsrc), f"{tf}: text outside an Arabic block changed"
            if a.write:
                tf.write_text(new, encoding="utf-8", newline="")
            return 1

        with concurrent.futures.ThreadPoolExecutor(32) as ex:
            changed = sum(ex.map(one, pages))
        verb = "written" if a.write else "would change"
        print(f"{lang}/bihar/1: {changed} pages {verb}"
              f"   blocks re-synced {stat[f'{lang}:fixed']:,}"
              f"   already in step {stat[f'{lang}:already']:,}"
              f"   LEFT {stat[f'{lang}:left']:,}")

    if left_ex:
        print("\nblocks left alone (text differs, not just letter forms):")
        for lang, pg, n, cur, s in left_ex:
            print(f"  {lang} page {pg} block {n}\n    tr : {cur}\n    ar : {s}")


if __name__ == "__main__":
    main()
