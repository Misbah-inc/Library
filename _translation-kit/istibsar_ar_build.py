#!/usr/bin/env python3
"""Build Arabic «الاستبصار» reading pages for a volume.

    python istibsar_ar_build.py istibsar_v1.json --out ../istibsar/1 --pages-json ../istibsar/assets/pages-1.json

Derived from `faqih_ar_build.py`. One builder per book is this project's shape.

**Source: ablibrary.net, not Ghaemiyeh** — the only book family here that is.
Both Ghaemiyeh exports of this book carry NO footnotes at all (zero note divs,
zero anchors across all fourteen volumes of the two books), and Ghaemiyeh's
الاستبصار has no printed-page markers either, only hadith ids. A library that
addresses every page by its printed number cannot be built from that. The
editor's apparatus and the pagination both come from ablibrary; see
`abl_extract.py` for what had to be rebuilt to get there.

**Edition: تحقيق حسن الموسوي الخرسان، دار الكتب الإسلامية، طهران.** The same
editor for both books — and a different one again from al-Kafi (شمس الدين، دار
التعارف) and al-Faqih (الغفاري، مؤسسة النشر الإسلامي). Four canonical books,
three editors; do not copy an edition line between these builders.

**The vocalisation was given up deliberately and can be added later.** Ghaemiyeh
is 82% vocalised for Tahdhib and 63% for Istibsar against ablibrary's 0, but the
two sources agree page for page, so the marks can be layered on as an overlay
without disturbing the text or the notes.

**Footnotes here carry no inline markers.** ablibrary's notes are keyed to a
hadith number — «* 315 - 316 الاستبصار ج 1 ص 109» — not to a `(1)` in the body,
so there is nothing to anchor a superscript to. They render as a list at the
foot of the page, which is what the edition itself does.

**No translations.** `data-trlangs=""` on every page.
"""

import argparse
import html
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

SITE = "https://library.misbah-inc.com"
ASSETS_V = "9"   # FROZEN — see CLAUDE.md. Never bump.
AR_DIGITS = "٠١٢٣٤٥٦٧٨٩"

SHORT_AR = "الاستبصار"
TITLE = {"ar": "الاستبصار", "fa": "الاستبصار", "ur": "الاستبصار", "en": "Al-Istibsar"}
AUTHOR = {"ar": "شيخ الطائفة أبو جعفر محمد بن الحسن الطوسي", "fa": "شیخ الطائفه، ابوجعفر محمد بن حسن طوسی", "ur": "شیخ الطائفہ ابوجعفر محمد بن حسن طوسی", "en": "Shaykh al-Ta'ifa Abu Ja'far Muhammad b. al-Hasan al-Tusi"}
EDITION = {"ar": "تحقيق حسن الموسوي الخرسان، دار الكتب الإسلامية، طهران", "fa": "تحقیق حسن الموسوی الخرسان، دار الکتب الإسلامیه، تهران", "ur": "تحقیق حسن الموسوی الخرسان، دار الکتب الإسلامیہ، تہران", "en": "ed. Hasan al-Musawi al-Khirsan, Dar al-Kutub al-Islamiyya, Tehran"}
FRONT = {"ar": "مقدمة", "fa": "مقدمه", "ur": "مقدمہ", "en": "Front matter"}

def ar_num(n):
    return "".join(AR_DIGITS[int(c)] for c in str(n))


def esc(s):
    return html.escape(s, quote=True)


def cite(vol, n, lang, fm=False):
    if lang == "ar":
        return (f"{SHORT_AR}، {AUTHOR['ar']}، المجلد {ar_num(vol)}، "
                f"{'المقدمة، ' if fm else ''}ص {ar_num(n)}.")
    if lang == "fa":
        return (f"{TITLE['fa']}، {AUTHOR['fa']}، جلد {vol}، "
                f"{'مقدمه، ' if fm else ''}ص {n}.")
    if lang == "ur":
        return (f"{TITLE['ur']}، {AUTHOR['ur']}، جلد {vol}، "
                f"{'مقدمہ، ' if fm else ''}ص {n}.")
    pre = "front matter, " if fm else ""
    return f"{TITLE['en']}, {AUTHOR['en']}, vol. {vol}, {pre}p. {n}."


REF = re.compile(r"\[(\d+)\]")
NUMGRP = re.compile(r"[\(\[]\s*\d+\s*[\)\]]")

# A parenthesised NUMBER inside right-to-left text comes out visually reversed —
# «( 21 ) 4 -» renders as «) 21 (» — because the brackets are bidi-neutral and
# take the surrounding direction. Measured on the page: reading left to right
# the glyphs landed in the order «) 21 (». Wrapping the group in <bdi> isolates
# it, so it renders left to right as its own unit and reads «( 21 )», which is
# what ablibrary shows. Only NUMBER groups are wrapped: «( عليه السلام )» holds
# strong RTL text, resolves correctly on its own, and must be left alone.
def bidi_nums(t):
    return NUMGRP.sub(lambda m: "<bdi>" + m.group(0) + "</bdi>", t)



def body_html(page):
    # Only the NUMBERED footnotes can be linked. A k="src" note is the editor's
    # تخريج, keyed to a hadith number rather than to a marker in the text, so it
    # has no anchor and must not be given a fabricated one — numbering it would
    # invent a «(2)» the reader can never find in the page.
    fn = [x for x in page["notes"] if x.get("k", "fn") == "fn"]
    src = [x for x in page["notes"] if x.get("k") == "src"]
    have = {x["n"] for x in fn}
    pos = page["n"] - 1
    parts = []
    for b in page["blocks"]:
        def sub(m):
            k = int(m.group(1))
            if k not in have:
                return m.group(0)
            return f'<a class="fnref" href="#fn-0-{pos}-{k}">{ar_num(k)}</a>'
        txt = bidi_nums(REF.sub(sub, esc(b["ar"])))
        tag = b["tag"] if b["tag"] in ("h2", "h3", "h4") else "p"
        parts.append(f'<{tag} lang="ar" data-i="{b["i"]}">{txt}</{tag}>')
    out = "".join(parts)
    if fn or src:
        rows = "".join(
            f'<div class="note" lang="ar" id="fn-0-{pos}-{x["n"]}">'
            f'<span class="note-n">({ar_num(x["n"])})</span>'
            f'<span>{bidi_nums(esc(x["ar"]))}</span></div>' for x in fn)
        rows += "".join(
            f'<div class="note" lang="ar">'
            f'<span class="note-n">*</span>'
            f'<span>{bidi_nums(esc(x["ar"]))}</span></div>' for x in src)
        out += f'<div class="notes">{rows}</div>'
    return out


def description(page):
    t = " ".join(b["ar"] for b in page["blocks"])
    t = re.sub(r"\[\d+\]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:150] if t else SHORT_AR


def split_template(tpl):
    """Chrome lifted from a published Bihar page — same folder depth, so the
    relative links resolve identically. Only data-slug/data-book differ, and
    those are written fresh below."""
    a = tpl.index('<link rel="stylesheet"')
    b = tpl.index('<div class="edgewrap">')
    d = tpl.index('<div class="scrim"')
    return {"chrome_head": tpl[a:b], "tail": tpl[d:]}


def build_page(page, ids, vol, tp):
    pid = page["id"]
    n = page["n"]
    fm = pid.startswith("fm-")
    i = ids.index(pid)
    prev_id = ids[i - 1] if i else None
    next_id = ids[i + 1] if i + 1 < len(ids) else None
    desc = esc(description(page))
    title = (f"{SHORT_AR} — {FRONT['ar']} ص {ar_num(n)}" if fm
             else f"{SHORT_AR} — ص {ar_num(n)}")
    url = f"{SITE}/istibsar/{vol}/{pid}/"

    links = ""
    if prev_id:
        links += f'<link rel="prev" href="../../../istibsar/{vol}/{prev_id}/">'
    if next_id:
        links += f'<link rel="next" href="../../../istibsar/{vol}/{next_id}/">'
    links += (f'<link rel="canonical" href="{url}">'
              f'<link rel="alternate" hreflang="ar" href="{url}">'
              f'<link rel="alternate" hreflang="x-default" href="{url}">')

    first, last = ids[0], ids[-1]
    pv = (f'<a class="btn prev" href="../../../istibsar/{vol}/{prev_id}/" rel="prev">'
          f'<span data-i18n="prev"></span></a>' if prev_id else
          '<span class="btn" aria-disabled="true"><span data-i18n="prev"></span></span>')
    nx = (f'<a class="btn next" href="../../../istibsar/{vol}/{next_id}/" rel="next">'
          f'<span data-i18n="next"></span></a>' if next_id else
          '<span class="btn" aria-disabled="true"><span data-i18n="next"></span></span>')

    cites = " ".join(f'data-cite-{L}="{esc(cite(vol, n, L, fm))}"' for L in ("ar", "fa", "ur", "en"))
    cspan = " ".join(f'data-{L}="{esc(cite(vol, n, L, fm))}"' for L in ("ar", "fa", "ur", "en"))

    if fm:
        folio = ('<span class="folio"><span data-ar="' + esc(FRONT["ar"]) +
                 '" data-fa="' + esc(FRONT["fa"]) + '" data-ur="' + esc(FRONT["ur"]) +
                 '" data-en="' + esc(FRONT["en"]) + '">' + esc(FRONT["ar"]) + '</span> '
                 f'<span data-num="{n}">{ar_num(n)}</span></span>')
    else:
        folio = ('<span class="folio"><span data-i18n="page"></span> '
                 f'<span data-num="{n}">{ar_num(n)}</span></span>')

    # This book has no named parts, so the slot carries its own title.
    partspan = (f'<span data-ar="{esc(TITLE["ar"])}" data-fa="{esc(TITLE["fa"])}"'
                f' data-ur="{esc(TITLE["ur"])}" data-en="{esc(TITLE["en"])}">'
                f'{esc(TITLE["ar"])}</span>')

    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl" data-root="../../.." data-book="../..">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{desc}">
{links}
{tp['chrome_head']}<main class="wrap">
  <article>
    <div class="leaf" id="text">
      <div class="part-label">{partspan}
        <span><span data-i18n="volume"></span>
        <span data-num="{vol}">{vol}</span>
        {folio}</span></div>
      <div class="body">{body_html(page)}</div>
    </div>
    <nav class="pager">
      <a class="btn " href="../../../istibsar/{vol}/{first}/" rel="related"><span data-i18n="first"></span></a>{pv}
      <form id="jump" data-tpl="istibsar/{vol}/{{p}}/" action="../../../" method="get">
        <input id="jump-num" name="p" inputmode="numeric" data-i18n-label="page"
               data-num-val="{n}" value="{ar_num(n)}">
      </form>
      {nx}<a class="btn " href="../../../istibsar/{vol}/{last}/" rel="related"><span data-i18n="last"></span></a>
    </nav>
    <p class="cite" id="cite-text" {cites}><span data-i18n="citation"></span>:
      <span {cspan}></span>
      &nbsp;·&nbsp;<code>/istibsar/{vol}/{pid}/</code></p>
  </article>
</main>
<div id="page-meta" hidden data-trlangs="" data-slug="istibsar" data-title-ar="{esc(SHORT_AR)}" data-title-fa="الاستبصار" data-title-ur="الاستبصار" data-title-en="Al-Istibsar" data-href="istibsar/{vol}/{pid}/"
     data-pagenum="{pid}" data-volume="{vol}" data-pos="{i}" data-total="{len(ids)}"></div>
{tp['tail']}"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--template", default="../bihar/1/26/index.html")
    ap.add_argument("--pages-json")
    args = ap.parse_args()

    data = json.loads(pathlib.Path(args.json).read_text(encoding="utf-8"))
    vol = data["volume"]
    tp = split_template(pathlib.Path(args.template).read_text(encoding="utf-8"))
    for p in data["pages"]:
        p.setdefault("id", str(p["n"]))
    ids = [p["id"] for p in data["pages"]]
    out = pathlib.Path(args.out)

    for page in data["pages"]:
        d = out / page["id"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(build_page(page, ids, vol, tp),
                                      encoding="utf-8", newline="")
    fmn = sum(1 for x in ids if x.startswith("fm-"))
    print(f"  vol {vol}: {len(ids)} pages -> {out}" + (f"  ({fmn} front matter)" if fmn else ""))

    if args.pages_json:
        nums = [p["n"] for p in data["pages"] if not p["id"].startswith("fm-")]
        p = pathlib.Path(args.pages_json)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(nums, ensure_ascii=False), encoding="utf-8")
        print(f"    pages json -> {p.name} ({len(nums)} numbered pages)")


if __name__ == "__main__":
    main()
