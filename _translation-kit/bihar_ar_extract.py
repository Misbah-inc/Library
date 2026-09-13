#!/usr/bin/env python3
"""Ghaemiyeh Bihar al-Anwar export  ->  per-page JSON, one volume at a time.

    python bihar_ar_extract.py <export.htm> <volume-number> > bihar_v<N>.json

The export is one HTML file per volume, Dar Ihya al-Turath text, the same
source volume 1 was built from.

Structure of the export, learned by inspection:

    <SPAN class=chapter></SPAN>          <- separates pages, and falls AFTER
    <DIV>                                   the page's footnotes, so one
      <P class=content_paragraph>…</P>      segment = body + marker + notes
      <P class=content_paragraph>
        <SPAN class=content_text>ص: 3</SPAN>   <- the marker CLOSES its page
      </P>
    </DIV>
    <HR class=content_hr>
    <DIV id=content_note_3_1 class=content_note>1- …</DIV>

Two things the naive reading gets wrong:

  * The page marker is a paragraph whose whole content is «ص: N». Matching the
    bare string instead picks up cross-references inside the prose — volume 2
    has a «ص: 178» sitting in the middle of page 86.
  * Footnotes for page N appear AFTER marker N. Segmenting on the marker puts
    them at the head of page N+1; segmenting on <SPAN class=chapter> keeps them
    with the page they belong to.

Consecutive segments carrying the SAME printed label are merged. The export
opens with the bibliographic record and the first text page both labelled «1»,
which is how volume 1 is already published — its page 1 carries هوية الکتاب and
مقدمة المؤلف together.
"""

import html as htmlmod
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

CHAPTER = re.compile(r"<SPAN class=chapter>\s*</SPAN>", re.I)
MARKER = re.compile(
    r"<P class=content_paragraph>\s*<SPAN class=content_text>\s*ص\s*:\s*(\d+)\s*</SPAN>\s*</P>",
    re.I)
NOTE = re.compile(
    r'<DIV id=content_note_(\d+)_(\d+) class=content_note>(.*?)</DIV>', re.I | re.S)
NOTELINK = re.compile(
    r'<A [^>]*class=content_notelink[^>]*>\s*\((\d+)\)\s*</A>', re.I)
PARA = re.compile(r"<P class=content_paragraph>(.*?)</P>", re.I | re.S)
HEAD = re.compile(r"<(?:P|DIV|H\d)[^>]*class=content_h(\d)[^>]*>(.*?)</(?:P|DIV|H\d)>",
                  re.I | re.S)
# The Ghaemiyeh publisher blurb that opens every export. It carries no page
# marker of its own; dropped rather than published.
PROMO = "تعريف مرکز"


def clean(fragment):
    """Tag-stripped text, with footnote links preserved as [n]."""
    t = NOTELINK.sub(lambda m: f"[{m.group(1)}]", fragment)
    t = re.sub(r"<BR\s*/?>", " ", t, flags=re.I)
    t = re.sub(r"<[^>]+>", "", t)
    t = htmlmod.unescape(t)
    t = t.replace("‌", "‌")
    return re.sub(r"[ \t\r\n]+", " ", t).strip()


def _blocks_from(head):
    """Ordered body blocks of one page: paragraphs and headings, in document order."""
    items = []
    for hm in HEAD.finditer(head):
        t = clean(hm.group(2))
        if t:
            items.append((hm.start(), f"h{min(int(hm.group(1)) + 1, 4)}", t))
    covered = [(hm.start(), hm.end()) for hm in HEAD.finditer(head)]
    for pm in PARA.finditer(head):
        if any(a <= pm.start() < b for a, b in covered):
            continue                       # a heading already claimed this node
        t = clean(pm.group(1))
        if t:
            items.append((pm.start(), "p", t))
    items.sort(key=lambda x: x[0])
    return [{"i": i, "tag": tag, "ar": t} for i, (_pos, tag, t) in enumerate(items)]


def parse(path, volume):
    raw = open(path, encoding="utf-8").read()
    body = raw[raw.find("<BODY"):] if "<BODY" in raw else raw

    pages, dropped, recovered = [], 0, []
    # Text after a segment's LAST marker belongs to the NEXT page — its own
    # marker lives in the following segment. Volume 3 segment 0 ends with the
    # author's dedication to كتاب التوحيد after «ص: 1»; discarding the tail lost
    # it. Footnote <DIV>s in the tail are ignored here because neither PARA nor
    # HEAD matches them.
    carry = ""
    for seg in CHAPTER.split(body):
        marks = list(MARKER.finditer(seg))
        if not marks:
            # A page can lose its own «ص: N» marker. Volume 3 segment 36 carries
            # 1,950 characters of body text and no marker; its neighbours close
            # 36 and 38, so it IS page 37 and the text is present, not missing.
            # Dropping it would silently lose a page of the book.
            txt = clean(seg)
            if not txt or (PROMO in txt and len(txt) < 4000):
                dropped += 1
                continue
            if not pages:
                dropped += 1
                continue
            label = pages[-1]["n"] + 1
            blocks = _blocks_from(carry + seg)
            carry = ""
            # a marker-less page still carries its own footnotes
            notes = [{"n": int(nm.group(2)), "ar": clean(nm.group(3))}
                     for nm in NOTE.finditer(seg)]
            if blocks:
                pages.append({"n": label, "blocks": blocks, "notes": notes})
                recovered.append(label)
            else:
                dropped += 1
            continue
        # A segment can carry MORE THAN ONE marker: the bibliographic record and
        # the first text page both close with «ص: 1» inside a single segment.
        # Taking only the first marker silently drops everything after it, which
        # is how the whole of volume 2's page 1 vanished on the first run.
        notes_at = [(nm.start(), int(nm.group(2)), clean(nm.group(3)))
                    for nm in NOTE.finditer(seg)]
        prev_end = 0
        for k, m in enumerate(marks):
            label = int(m.group(1))
            head = seg[prev_end:m.start()]
            if k == 0 and carry:
                head = carry + head
                carry = ""
            blocks = _blocks_from(head)
            nxt = marks[k + 1].start() if k + 1 < len(marks) else len(seg)
            notes = [{"n": n, "ar": t} for pos, n, t in notes_at
                     if m.end() <= pos < nxt]
            prev_end = m.end()
            # A page with a marker but no content is BLANK in the printed
            # edition (volume 3 page 284). Keep it: dropping it puts a hole in
            # the pagination and a 404 on a page a citation can point at.
            # bayt-al-ahzan-fa publishes its 31 blank pages the same way.
            if blocks and PROMO in blocks[0]["ar"] and not pages:
                dropped += 1
                continue
            if pages and pages[-1]["n"] == label:     # same printed page, continued
                off = len(pages[-1]["blocks"])
                for b in blocks:
                    b["i"] += off
                pages[-1]["blocks"].extend(blocks)
                pages[-1]["notes"].extend(notes)
            else:
                pages.append({"n": label, "blocks": blocks, "notes": notes})
        carry = seg[prev_end:]

    return {"volume": volume, "pages": pages, "dropped_segments": dropped,
            "recovered_markers": recovered}


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    data = parse(sys.argv[1], int(sys.argv[2]))
    p = data["pages"]
    nums = [x["n"] for x in p]
    gaps = [i for i in range(nums[0], nums[-1] + 1) if i not in set(nums)]
    print(json.dumps(data, ensure_ascii=False), file=sys.stdout)
    print(f"volume {data['volume']}: {len(p)} pages  {nums[0]}–{nums[-1]}", file=sys.stderr)
    print(f"  blocks {sum(len(x['blocks']) for x in p)}  "
          f"notes {sum(len(x['notes']) for x in p)}  "
          f"chars {sum(len(b['ar']) for x in p for b in x['blocks']):,}", file=sys.stderr)
    print(f"  segments dropped (promo/empty): {data['dropped_segments']}", file=sys.stderr)
    if data.get("recovered_markers"):
        print(f"  pages recovered from a MISSING marker: {data['recovered_markers']}", file=sys.stderr)
    blank=[x["n"] for x in p if not x["blocks"] and not x["notes"]]
    if blank:
        print(f"  blank pages kept (no text in the edition): {blank}", file=sys.stderr)
    print(f"  duplicate labels merged: "
          f"{len(nums) - len(set(nums))}", file=sys.stderr)
    if gaps:
        print(f"  ** MISSING PAGE NUMBERS: {gaps} **", file=sys.stderr)


if __name__ == "__main__":
    main()
