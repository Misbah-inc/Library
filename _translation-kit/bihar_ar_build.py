#!/usr/bin/env python3
"""Build Arabic Bihar al-Anwar reading pages for a volume.

    python bihar_ar_build.py bihar_v2.json --out ../bihar/2 --index

Volume 1 was not built by any script in this kit — `build.py` emits en/fa/ur
only. So that new volumes match it rather than merely resemble it, this builder
takes its invariant chrome (head, header bar, side nav, drawer, footer, script
tag) straight out of a published volume 1 page and regenerates only the parts
that differ per page. If the shared template ever changes, rebuild volume 1's
neighbours and this follows automatically.

What differs per page: title/description/og, prev-next-canonical-hreflang, the
edge rail, the volume+folio label, the body, the footnotes, the pager, the cite
line, and #page-meta.

**Volumes 2 and 3 have no translations.** They must NOT claim hreflang or
data-alt-* for en/fa/ur: a cluster that points at pages nobody built is ignored
wholesale, and the language switcher would offer a 404. Volume 1 claims all
three because all three exist.
"""

import argparse
import html
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

SITE = "https://library.misbah-inc.com"
ASSETS_V = "9"
RAIL = 120                      # links in the edge rail; volume 1 uses 120
AR_DIGITS = "٠١٢٣٤٥٦٧٨٩"

TITLE_AR = "بحار الأنوار الجامعة لدرر أخبار الأئمة الأطهار"
SHORT_AR = "بحار الأنوار"
AUTHOR = {"ar": "العلامة محمد باقر المجلسي",
          "fa": "علامه محمدباقر مجلسی",
          "ur": "علامہ محمد باقر مجلسی",
          "en": "Allama Muhammad Baqir al-Majlisi"}
CITE = {
    "ar": lambda v, n: f"{TITLE_AR}، {AUTHOR['ar']}، المجلد {ar_num(v)}، ص {ar_num(n)}.",
    "fa": lambda v, n: f"{TITLE_AR}، {AUTHOR['fa']}، جلد {v}، ص {n}.",
    "ur": lambda v, n: f"{TITLE_AR}، {AUTHOR['ur']}، جلد {v}، ص {n}.",
    "en": lambda v, n: f"Bihar al-Anwar, {AUTHOR['en']}, vol. {v}, p. {n}.",
}


def ar_num(n):
    return "".join(AR_DIGITS[int(c)] for c in str(n))


def esc(s):
    return html.escape(s, quote=True)


REF = re.compile(r"\[(\d+)\]")


def rail(pages, cur, vol):
    total = len(pages)
    idx = sorted({pages[round(k * (total - 1) / (RAIL - 1))] for k in range(RAIL)} | {cur})
    out = []
    for n in idx:
        mark = ' aria-current="page"' if n == cur else ""
        out.append(f'<a href="../../../bihar/{vol}/{n}/" data-numbered="1" '
                   f'title="صفحة {ar_num(n)}"{mark}></a>')
    return "".join(out)


def body_html(page, vol):
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
    return t[:150] if t else TITLE_AR


def split_template(tpl):
    """Cut a published volume-1 page into the chunks that never change."""
    a = tpl.index('<link rel="stylesheet"')
    b = tpl.index('<div class="edgewrap">')
    c = tpl.index('<main class="wrap">')
    d = tpl.index('<div class="scrim"')
    return {"chrome_head": tpl[a:b], "tail": tpl[d:]}


def build_page(page, pages, vol, tp):
    n = page["n"]
    i = pages.index(n)
    prev_n = pages[i - 1] if i else None
    next_n = pages[i + 1] if i + 1 < len(pages) else None
    desc = esc(description(page))
    title = f"{SHORT_AR} — ص {ar_num(n)}"
    url = f"{SITE}/bihar/{vol}/{n}/"

    links = ""
    if prev_n:
        links += f'<link rel="prev" href="../../../bihar/{vol}/{prev_n}/">'
    if next_n:
        links += f'<link rel="next" href="../../../bihar/{vol}/{next_n}/">'
    # Arabic only: this volume has no translations, so no other hreflang exists.
    links += (f'<link rel="canonical" href="{url}">'
              f'<link rel="alternate" hreflang="ar" href="{url}">'
              f'<link rel="alternate" hreflang="x-default" href="{url}">')

    first, last = pages[0], pages[-1]
    pv = (f'<a class="btn prev" href="../../../bihar/{vol}/{prev_n}/" rel="prev">'
          f'<span data-i18n="prev"></span></a>' if prev_n else
          '<span class="btn" aria-disabled="true"><span data-i18n="prev"></span></span>')
    nx = (f'<a class="btn next" href="../../../bihar/{vol}/{next_n}/" rel="next">'
          f'<span data-i18n="next"></span></a>' if next_n else
          '<span class="btn" aria-disabled="true"><span data-i18n="next"></span></span>')

    cites = " ".join(f'data-cite-{L}="{esc(f(vol, n))}"' for L, f in CITE.items())
    cspan = " ".join(f'data-{L}="{esc(f(vol, n))}"' for L, f in CITE.items())

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
{tp['chrome_head']}<div class="edgewrap"><nav class="edge" aria-label="pages">{rail(pages, n, vol)}</nav></div>
<main class="wrap">
  <article>
    <div class="leaf" id="text">
      <div class="part-label"><span data-ar="{esc(AUTHOR['ar'])}" data-fa="{esc(AUTHOR['fa'])}" data-ur="{esc(AUTHOR['ur'])}" data-en="{esc(AUTHOR['en'])}">{esc(AUTHOR['ar'])}</span>
        <span><span data-i18n="volume"></span>
        <span data-num="{vol}">{vol}</span>
        <span class="folio"><span data-i18n="page"></span> <span data-num="{n}">{ar_num(n)}</span></span></span></div>
      <div class="body">{body_html(page, vol)}</div>
    </div>
    <nav class="pager">
      <a class="btn " href="../../../bihar/{vol}/{first}/" rel="related"><span data-i18n="first"></span></a>{pv}
      <form id="jump" data-tpl="bihar/{vol}/{{p}}/" action="../../../" method="get">
        <input id="jump-num" name="p" inputmode="numeric" data-i18n-label="page"
               data-num-val="{n}" value="{ar_num(n)}">
      </form>
      {nx}<a class="btn " href="../../../bihar/{vol}/{last}/" rel="related"><span data-i18n="last"></span></a>
    </nav>
    <p class="cite" id="cite-text" {cites}><span data-i18n="citation"></span>:
      <span {cspan}></span>
      &nbsp;·&nbsp;<code>/bihar/{vol}/{n}/</code></p>
  </article>
</main>
<div id="page-meta" hidden data-slug="bihar" data-title-ar="{esc(SHORT_AR)}" data-title-fa="{esc(SHORT_AR)}" data-title-ur="{esc(SHORT_AR)}" data-title-en="Bihar al-Anwar" data-href="bihar/{vol}/{n}/"
     data-pagenum="{n}" data-volume="{vol}" data-pos="{i}" data-total="{len(pages)}"></div>
{tp['tail']}"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--template", default="../bihar/1/26/index.html")
    ap.add_argument("--pages-json", help="write assets/pages-<vol>.json here")
    args = ap.parse_args()

    data = json.loads(pathlib.Path(args.json).read_text(encoding="utf-8"))
    vol = data["volume"]
    tp = split_template(pathlib.Path(args.template).read_text(encoding="utf-8"))
    pages = [p["n"] for p in data["pages"]]
    out = pathlib.Path(args.out)

    for page in data["pages"]:
        d = out / str(page["n"])
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(build_page(page, pages, vol, tp),
                                      encoding="utf-8", newline="")
    print(f"  {len(pages)} pages -> {out}")

    if args.pages_json:
        p = pathlib.Path(args.pages_json)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(pages, ensure_ascii=False), encoding="utf-8")
        print(f"  pages json -> {p}")


if __name__ == "__main__":
    main()
