#!/usr/bin/env python3
"""ablibrary.net  ->  per-page JSON, the same shape the Ghaemiyeh extractor emits.

    python abl_extract.py tahdhib 1 6026 > tahdhib_v1.json
    python abl_extract.py --cache <dir> istibsar 1 2437 > istibsar_v1.json

WHY THIS EXISTS. Every book in the library so far came from a Ghaemiyeh HTML
export through `bihar_ar_extract.py`. تهذيب الأحكام and الاستبصار do not, for two
reasons found by measuring rather than assuming:

  * **Neither Ghaemiyeh export has any footnotes.** Zero `content_note` divs,
    zero anchors, zero `<HR>` across all fourteen volumes. ablibrary carries the
    editor's full apparatus — ~543k characters for Tahdhib, ~252k for Istibsar.
  * **Ghaemiyeh's الاستبصار has no page markers at all.** It is segmented by
    hadith id (`-روایت-1-728`), not by printed page. This library addresses and
    cites every page by its printed number, so there is nothing to build a URL
    from. That is a constraint, not a preference.

The cost is the vocalisation: Ghaemiyeh's Tahdhib is 82% vocalised and
Istibsar 63%, ablibrary 0%. Adding it back as an overlay is possible later
precisely because the two sources agree page for page — see the README in each
`Claude outputs/<book>-ghbook-html/` folder.

WHAT ABLIBRARY GIVES, AND WHAT HAS TO BE REBUILT

`Contents` returns one text blob per page plus one notes blob. There are no
paragraphs, no headings, no structure of any kind — and the text is HARD
WRAPPED at roughly eighty characters, so a newline is a line break in the
printed page, NOT a paragraph boundary. Joining on newlines would glue the end
of every line to the start of the next; splitting on them would shatter every
sentence. The reflow here joins the lines and re-splits on the one boundary the
text actually marks: a hadith opening `( 316 ) 7`.

`TableOfContents` returns the chapter list with, per entry, a sequence number, a
printed page, and a title. The body repeats the title inline prefixed by that
sequence number — «2 باب الطهارة من الاحداث» — which is what lets a heading be
marked without guessing.

**Match the title by WORD COUNT, not by string equality.** The table of
contents and the body do not always agree: chapter 3 of Tahdhib volume 1 is
«باب آداب الاحداث الموجبة للطهارة» in the contents and «…للطهارات» in the body.
Requiring equality drops the heading silently; taking the contents' word count
from the body keeps the body's own wording, which is what a citation should
resolve to.

NOTHING IS DROPPED. `check()` re-joins every emitted block and asserts the
result is character-for-character the source body with whitespace collapsed.
That is the equivalent of `bihar_ar_audit.py` for this path, and it runs on
every volume, every time — an extractor nobody has watched fail is not evidence.
"""

import argparse
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

WS = re.compile(r"\s+")

# ablibrary hard-wraps its text, but a BLOCK always begins at a line start —
# so a newline mid-block is a wrap and a newline before one of these is a real
# boundary. Treating every newline as a wrap is what ran a whole page together
# into one paragraph; treating every newline as a break would shatter every
# sentence. Both books are covered:
#   التهذيب v1    «( 316 ) 7 وأخبرني…»          parentheses
#   التهذيب v3    «* ( 125 ) * 76 - وروى…»      starred parentheses
#   الاستبصار v2  «[ 28 ] 4 - فأما ما رواه…»     square brackets
#   الاستبصار v1  «176 - 1 أخبرني…»             bare number
# FOUR forms across two books. Missing one does not fail — it merges
# every hadith on the page into the previous paragraph, which is what
# shipped: Istibsar v1 had 0 splits and 251 pages that were one block.
# The bare-number form is why HEAD_LINE must be tested FIRST, or
# «25 - باب مقدار الصاع» reads as hadith 25 part 1.
HADITH_LINE = re.compile(r"^\s*\*?\s*(?:\[\s*\d+\s*\]|\(\s*\d+\s*\)|\d+)\s*\*?\s*-?\s*\d+\s*-?\s")
# «25 - باب مقدار الصاع», «2 باب الطهارة من الاحداث», «كتاب الزكاة», «أبواب…»
# and — الاستبصار volume 3 only — bracketed: «[ 1 - باب من يستحق أن يقسم… ]».
# Without the optional «[» that volume found 2 headings instead of 219, and
# every one of them was silently glued onto the previous paragraph.
HEAD_LINE = re.compile(r"^\s*\[?\s*(?:\d+\s*-?\s*)?(?:باب|كتاب|أبواب)\b")
# A numbered footnote in the notes blob: «( 1 ) المظنون قويا…». Everything else
# there is a تخريج line keyed to a hadith number — «- 163 - التهذيب ج 1 ص 372».
NOTE_NUM = re.compile(r"^\s*\(\s*(\d+)\s*\)\s*")
SRC_LINE = re.compile(r"^\s*[*\-\u2022]")
# a footnote marker in the BODY, and its anchored form
MARKER = re.compile(r"\(\s*(\d{1,3})\s*\)")
MARKER_REF = re.compile(r"\[(\d{1,3})\]")
# a heading that carries its own number is trusted outright
NUMBERED_HEAD = re.compile(r"^\s*\[?\s*\d+\s*-?\s*(?:باب|كتاب|أبواب)\b")
# a hadith marker found MID-LINE, where a heading and its first hadith share one line
MARK_MID = re.compile(r"(?:\[\s*\d+\s*\]|\(\s*\d+\s*\))\s*\d+\s*-?\s")
LEAD_NUM = re.compile(r"^\s*\d+\s*-?\s*")

def flat(s):
    return WS.sub(" ", s).strip()


def toc_key(t):
    """First three words, number stripped — how a heading candidate is
    matched against the contents."""
    w = LEAD_NUM.sub("", t.strip().lstrip("[").strip()).split()
    return " ".join(w[:3])


def split_notes(blob):
    """The notes blob -> [{n, ar, k}].

    Two different things share it, and they are not interchangeable:

      k="fn"   «( 1 ) المظنون قويا ابدال الستة بالأربعة…»  a numbered footnote
               with a matching «( 1 )» marker in the body, so it is anchored
               and the reader can click through to it.
      k="src"  «- 163 - التهذيب ج 1 ص 372 الكافي ج 1 ص 211» the editor's تخريج,
               keyed to a HADITH number, not to any marker in the text. It has
               nothing to anchor to and is rendered without a number.

    Treating all of them as unanchored — which is what this did at first — left
    every «( 1 )» in the body as dead text pointing nowhere, when the same
    marker is clickable in Bihar.
    """
    b = blob.strip()
    if not b:
        return []
    out = []
    state = {"cur": [], "kind": None, "num": None}

    def flush():
        if state["cur"]:
            t = flat(" ".join(state["cur"]))
            if t:
                out.append({"n": state["num"] if state["kind"] == "fn" else 0,
                            "ar": t, "k": state["kind"] or "src"})
        state["cur"] = []

    for line in b.split(chr(10)):
        m = NOTE_NUM.match(line)
        if m:
            flush()
            state.update(cur=[line[m.end():]], kind="fn", num=int(m.group(1)))
        elif SRC_LINE.match(line) or not state["cur"]:
            flush()
            state.update(cur=[line], kind="src", num=None)
        else:
            state["cur"].append(line)
    flush()
    return [x for x in out if x["ar"]]


def blocks_for(body, notes, toc_keys=()):
    """Reflow one page into blocks, using ablibrary's own line starts.

    Continuation lines join with a space; a line matching HADITH_LINE or a
    confirmed HEAD_LINE opens a new block.

    **A heading is exactly one line.** Letting it absorb continuation lines the
    way a paragraph does swallowed whole passages: the ziyara after
    «9 - باب وداع أمير المؤمنين» became part of the heading in التهذيب v6, and a
    full hadith did the same in الاستبصار v4 — and both then appeared in the
    contents drawer as a "chapter title" hundreds of characters long.

    **An UNNUMBERED candidate must be confirmed against the contents.** A
    wrapped continuation line often begins with باب/كتاب/أبواب by accident —
    «كتاب حريز أنه قال : إني نسيت…» is the middle of hadith 1418, «كتاب الله عز
    وجل» is a quotation, «أبواب كندة في الصحن» is a place. Each of those became
    a false chapter. A candidate carrying its own number is trusted; one
    without has to appear in ablibrary's table of contents.
    """
    if not body.strip():
        return []
    have = {x["n"] for x in notes if x["k"] == "fn"}
    keys = set(toc_keys)
    blocks = []
    state = {"cur": [], "kind": "p"}

    def flush():
        if state["cur"]:
            t = flat(" ".join(state["cur"]))
            if t:
                blocks.append({"tag": "h3" if state["kind"] == "h" else "p",
                               "ar": t})
        state["cur"] = []

    def is_heading(line):
        if not HEAD_LINE.match(line):
            return False
        if NUMBERED_HEAD.match(line):
            return True
        return toc_key(line) in keys

    for line in body.split(chr(10)):
        if is_heading(line):
            flush()
            # The heading and the first hadith of its chapter can share one
            # source line — «33 - باب علامة أول يوم من شهر رمضان [ 199 ] 1 - …»
            # so split at the marker instead of publishing the pair as a title.
            m = MARK_MID.search(line, 1)
            head, rest = (line[:m.start()], line[m.start():]) if m else (line, "")
            state.update(cur=[head], kind="h")
            flush()
            state.update(cur=[rest] if rest.strip() else [], kind="p")
        elif HADITH_LINE.match(line):
            flush()
            state.update(cur=[line], kind="p")
        else:
            state["cur"].append(line)
    flush()

    # Anchor the footnote markers, and ONLY those whose note exists. «( 316 ) 7»
    # opens a hadith in التهذيب and must never become a footnote link, so a
    # marker is converted only when a numbered note actually carries that number
    # and the match is not the block's own opening.
    def anchor(t):
        def sub(m):
            if m.start() == 0 or int(m.group(1)) not in have:
                return m.group(0)
            return "[" + m.group(1) + "]"
        return MARKER.sub(sub, t)

    for bl in blocks:
        bl["ar"] = anchor(bl["ar"])
    return [{"i": i, "tag": x["tag"], "ar": x["ar"]}
            for i, x in enumerate(blocks)]


def unanchor(t):
    """Undo anchor() so the round-trip can compare against the source."""
    return MARKER_REF.sub(lambda m: "( " + m.group(1) + " )", t)


def check(pages, raw_bodies):
    """Every block, re-joined and un-anchored, must be the source body exactly.

    `unanchor()` is essential: the blocks carry «[1]» where the source carries
    «( 1 )», so comparing them raw would report every page with a footnote as
    corrupt and hide any real fault in the noise.
    """
    bad = []
    for p, src in zip(pages, raw_bodies):
        got = unanchor(" ".join(b["ar"] for b in p["blocks"]))
        want = flat(src)
        if got != want:
            bad.append((p["id"], want, got))
    return bad


def fetch(book_id, cache):
    """(pages, toc) from ablibrary, or from a cached Contents dump."""
    import abl
    from pb import frames, walk

    def subs(b, f):
        return [v for pp, w, v in walk(b) if pp == (f,) and w == 2]

    def sub1(b, f):
        s = subs(b, f)
        return s[0] if s else None

    def txt(m, f):
        v = sub1(m, f)
        return v.decode("utf-8", "replace") if isinstance(v, (bytes, bytearray)) else None

    pages = None
    if cache and pathlib.Path(cache).is_file():
        pages = json.loads(pathlib.Path(cache).read_text(encoding="utf-8"))
    if pages is None:
        raw = abl.call("Contents", book_id, timeout=400)
        pl = [p for f, p in frames(raw) if f == 0][0]
        pages = {}
        for r in subs(sub1(pl, 1), 1):
            lab = txt(r, 4)
            body, notes = [], []
            for f7 in subs(r, 7):
                h = sub1(f7, 24)
                if h is not None:
                    t = txt(h, 1)
                    if t:
                        body.append(t)
                for f10 in subs(f7, 10):
                    for f24 in subs(f10, 24):
                        t = txt(f24, 1)
                        if t:
                            notes.append(t)
            pages[lab] = {"body": "\n".join(body), "notes": "\n".join(notes)}

    raw = abl.call("TableOfContents", book_id, timeout=300)
    pl = [p for f, p in frames(raw) if f == 0][0]
    toc = []
    for it in subs(pl, 1):
        seq, page, title = txt(it, 1), txt(it, 8), txt(it, 6)
        if seq and page and title:
            toc.append({"seq": seq, "page": page,
                        "title": flat(title.split("\n")[0])})
    return pages, toc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("volume", type=int)
    ap.add_argument("book_id", type=int)
    ap.add_argument("--cache", help="a cached Contents dump for this volume")
    a = ap.parse_args()

    raw_pages, toc = fetch(a.book_id, a.cache)

    toc_keys = {toc_key(t['title']) for t in toc if t.get('title')}
    pages, raw_bodies, fm = [], [], 0
    for lab in raw_pages:
        rec = raw_pages[lab]
        if lab.isdigit():
            n, pid = int(lab), lab
        else:
            fm += 1
            n, pid = fm, f"fm-{fm}"
        notes = split_notes(rec["notes"])
        pages.append({"n": n, "id": pid,
                      "blocks": blocks_for(rec["body"], notes, toc_keys),
                      "notes": notes})
        raw_bodies.append(rec["body"])

    # The contents rows are now taken from the headings actually found in the
    # text, which carry a page that is true by construction. ablibrary's own
    # page pointer is not used at all: both fields it offers are wrong in
    # several volumes, and a contents row that sends a reader to an unrelated
    # page is worse than one that is absent.
    toc = [{"title": b["ar"], "page": p["id"], "n": p["n"], "located": True}
           for p in pages for b in p["blocks"] if b["tag"] != "p"]

    bad = check(pages, raw_bodies)
    heads = sum(1 for p in pages for b in p["blocks"] if b["tag"] != "p")
    notes = sum(len(p["notes"]) for p in pages)
    print(f"  {a.slug} vol {a.volume} (ablibrary {a.book_id}): {len(pages)} pages "
          f"({fm} front matter), {heads} headings of {len(toc)} in the contents, "
          f"{notes:,} notes", file=sys.stderr)
    if bad:
        print(f"  ** {len(bad)} pages do not round-trip — first: {bad[0][0]}",
              file=sys.stderr)
        print(f"     want: {bad[0][1][:140]}", file=sys.stderr)
        print(f"     got : {bad[0][2][:140]}", file=sys.stderr)
        sys.exit(1)
    print("  round-trip: every block re-joins to the source exactly",
          file=sys.stderr)
    json.dump({"volume": a.volume, "source": "ablibrary", "book_id": a.book_id,
               "pages": pages, "toc": toc, "front_matter": fm},
              sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
