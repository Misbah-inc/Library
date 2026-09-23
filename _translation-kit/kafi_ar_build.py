#!/usr/bin/env python3
"""Build Arabic al-Kafi reading pages for a volume.

    python kafi_ar_build.py kafi_v1.json --out ../kafi/1 --pages-json ../kafi/assets/pages-1.json

Derived from `bihar_ar_build.py` and deliberately kept as a separate file, which
is this project's established shape — one builder per book (`bayt_build.py`,
`mafatih_build.py`, `jame_build.py`, `quran_build.py`). A fix made here that is
also a fault there must be applied to both; they share a lineage, not code.

**Edition: دار التعارف للمطبوعات، بيروت ١٤١١ق، ضبطه وصححه محمّد جعفر شمس الدين**,
via the Ghaemiyeh export. Chosen over al-Ghaffari's دار الكتب الإسلامية printing
because the matn carries the editor's own tashkil — 425,870 marks at 9.9%
density — and no reconstruction can stand in for an editor's judgement. The two
editions paginate differently and must never be mixed; see CLAUDE.md.

**The book has three named parts, not eight uniform volumes.** Scholars cite
«أصول الكافي ج ١» and «الروضة من الكافي», not «الكافي ج ١», so the part is what
the page label and the citation line carry. Volume boundaries were verified
against al-Ghaffari's independent edition and agree exactly.

**No translations.** Every page carries `data-trlangs=""`, so reader.js shows the
"not translated yet" notice at once instead of fetching a file that cannot exist.

**No edge rail**, same as Bihar volumes 2-110: reader.js falls through to
`kafi/assets/pages-<vol>.json` and the dropdown then offers every page.
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

SHORT_AR = "الكافي"
AUTHOR = {"ar": "ثقة الإسلام محمد بن يعقوب الكليني",
          "fa": "ثقة‌الاسلام محمد بن یعقوب کلینی",
          "ur": "ثقۃ الاسلام محمد بن یعقوب کلینی",
          "en": "Thiqat al-Islam Muhammad b. Ya'qub al-Kulayni"}

# Which part each volume belongs to, read off this edition's own volume
# headings (دار التعارف للمطبوعات، بيروت): vols 1-2 say «أصول الكافي»,
# 3-7 «فُروعُ الكافي», 8 «روضة الكافي». The seams agree with the openings —
# vol 2 كتاب الإيمان والكفر, 3 كتاب الطهارة, 4 أبواب الصدقة, 5 كتاب الجهاد,
# 6 كتاب العقيقة, 7 كتاب الوصايا, 8 كتاب الروضة.
PART = {
    1: {"ar": "أصول الكافي", "fa": "اصول کافی", "ur": "اصولِ کافی", "en": "Usul al-Kafi"},
    2: {"ar": "أصول الكافي", "fa": "اصول کافی", "ur": "اصولِ کافی", "en": "Usul al-Kafi"},
    3: {"ar": "فروع الكافي", "fa": "فروع کافی", "ur": "فروعِ کافی", "en": "Furu al-Kafi"},
    4: {"ar": "فروع الكافي", "fa": "فروع کافی", "ur": "فروعِ کافی", "en": "Furu al-Kafi"},
    5: {"ar": "فروع الكافي", "fa": "فروع کافی", "ur": "فروعِ کافی", "en": "Furu al-Kafi"},
    6: {"ar": "فروع الكافي", "fa": "فروع کافی", "ur": "فروعِ کافی", "en": "Furu al-Kafi"},
    7: {"ar": "فروع الكافي", "fa": "فروع کافی", "ur": "فروعِ کافی", "en": "Furu al-Kafi"},
    8: {"ar": "الروضة من الكافي", "fa": "روضه کافی", "ur": "روضۂ کافی", "en": "Al-Rawda min al-Kafi"},
}
FRONT = {"ar": "مقدمة الناشر", "fa": "مقدمه ناشر",
         "ur": "مقدمہ ناشر", "en": "Publisher's introduction"}


def ar_num(n):
    return "".join(AR_DIGITS[int(c)] for c in str(n))


def esc(s):
    return html.escape(s, quote=True)


def cite(vol, n, lang, fm=False):
    p = PART[vol][lang]
    if lang == "ar":
        mid = f"{p}، {AUTHOR['ar']}، المجلد {ar_num(vol)}"
        return f"{mid}، {'مقدمة الناشر، ' if fm else ''}ص {ar_num(n)}."
    if lang == "fa":
        return f"{p}، {AUTHOR['fa']}، جلد {vol}، {'مقدمه ناشر، ' if fm else ''}ص {n}."
    if lang == "ur":
        return f"{p}، {AUTHOR['ur']}، جلد {vol}، {'مقدمہ ناشر، ' if fm else ''}ص {n}."
    pre = "publisher's introduction, " if fm else ""
    return f"{p}, {AUTHOR['en']}, vol. {vol}, {pre}p. {n}."


REF = re.compile(r"\[(\d+)\]")


def body_html(page):
    have = {x["n"] for x in page["notes"]}
    pos = page["n"] - 1
    parts = []
    for b in page["blocks"]:
        def sub(m):
            k = int(m.group(1))
            if k not in have:
                return m.group(0)
            return f'<a class="fnref" href="#fn-0-{pos}-{k}">{ar_num(k)}</a>'
        txt = REF.sub(sub, esc(b["ar"]))
        tag = b["tag"] if b["tag"] in ("h2", "h3", "h4") else "p"
        parts.append(f'<{tag} lang="ar" data-i="{b["i"]}">{txt}</{tag}>')
    out = "".join(parts)
    if page["notes"]:
        notes = "".join(
            f'<div class="note" lang="ar" id="fn-0-{pos}-{x["n"]}">'
            f'<span class="note-n">({ar_num(x["n"])})</span>'
            f'<span>{esc(x["ar"])}</span></div>' for x in page["notes"])
        out += f'<div class="notes">{notes}</div>'
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
    part = PART[vol]
    title = (f"{part['ar']} — {FRONT['ar']} ص {ar_num(n)}" if fm
             else f"{part['ar']} — ص {ar_num(n)}")
    url = f"{SITE}/kafi/{vol}/{pid}/"

    links = ""
    if prev_id:
        links += f'<link rel="prev" href="../../../kafi/{vol}/{prev_id}/">'
    if next_id:
        links += f'<link rel="next" href="../../../kafi/{vol}/{next_id}/">'
    links += (f'<link rel="canonical" href="{url}">'
              f'<link rel="alternate" hreflang="ar" href="{url}">'
              f'<link rel="alternate" hreflang="x-default" href="{url}">')

    first, last = ids[0], ids[-1]
    pv = (f'<a class="btn prev" href="../../../kafi/{vol}/{prev_id}/" rel="prev">'
          f'<span data-i18n="prev"></span></a>' if prev_id else
          '<span class="btn" aria-disabled="true"><span data-i18n="prev"></span></span>')
    nx = (f'<a class="btn next" href="../../../kafi/{vol}/{next_id}/" rel="next">'
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

    partspan = (f'<span data-ar="{esc(part["ar"])}" data-fa="{esc(part["fa"])}"'
                f' data-ur="{esc(part["ur"])}" data-en="{esc(part["en"])}">{esc(part["ar"])}</span>')

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
      <a class="btn " href="../../../kafi/{vol}/{first}/" rel="related"><span data-i18n="first"></span></a>{pv}
      <form id="jump" data-tpl="kafi/{vol}/{{p}}/" action="../../../" method="get">
        <input id="jump-num" name="p" inputmode="numeric" data-i18n-label="page"
               data-num-val="{n}" value="{ar_num(n)}">
      </form>
      {nx}<a class="btn " href="../../../kafi/{vol}/{last}/" rel="related"><span data-i18n="last"></span></a>
    </nav>
    <p class="cite" id="cite-text" {cites}><span data-i18n="citation"></span>:
      <span {cspan}></span>
      &nbsp;·&nbsp;<code>/kafi/{vol}/{pid}/</code></p>
  </article>
</main>
<div id="page-meta" hidden data-trlangs="" data-slug="kafi" data-title-ar="{esc(SHORT_AR)}" data-title-fa="الکافی" data-title-ur="الکافی" data-title-en="Al-Kafi" data-href="kafi/{vol}/{pid}/"
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
