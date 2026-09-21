#!/usr/bin/env python3
"""Build Arabic Bihar al-Anwar reading pages for a volume.

    python bihar_ar_build.py bihar_v2.json --out ../bihar/2 --pages-json ../bihar/assets/pages-2.json

Volume 1 was not built by any script in this kit — `build.py` emits en/fa/ur
only. So that new volumes match it rather than merely resemble it, this builder
takes its invariant chrome (head, header bar, side nav, drawer, footer, script
tag) straight out of a published volume 1 page and regenerates only the parts
that differ per page.

**No edge rail.** Volume 1 ships 120 hardcoded tick links per page; reader.js
deletes them and builds a dropdown from them. That was 9.3 KB of the 20.4 KB
page — 45% — for markup no reader ever sees, and at 110 volumes in four
languages it is 1.5 GB of it. Emitting none makes reader.js take its other
path: it fetches `bihar/assets/pages-<vol>.json` and builds the dropdown from
that, which is what every translated page already does, and the dropdown then
offers EVERY page instead of 120 sampled ones. Volume 1 keeps its rail — it is
the source of record and the template, and is not restructured without the
owner's word. Crawlability does not depend on the rail: each volume index links
every chapter, so no page sits more than ~7 clicks deep, and prev/next plus the
sitemap cover the rest.

**Volumes without a translation** must NOT claim hreflang or data-alt-* for
en/fa/ur: a cluster that points at pages nobody built is ignored wholesale, and
the language switcher would offer a 404. They carry `data-trlangs=""`, which
tells reader.js to show the "not translated yet" notice at once instead of
fetching a translation file that cannot exist.

**Front matter.** Six volumes paginate the publisher's front matter 1..N before
al-Majlisi's text restarts at 1. Those pages take ids `fm-1..fm-N` so a citation
to «vol 29 p 5» still resolves to al-Majlisi's page 5. See `bihar_ar_extract.py`.
"""

import argparse
import html
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

SITE = "https://library.misbah-inc.com"
ASSETS_V = "9"   # FROZEN — do not bump. GitHub Pages serves reader.css/js with
                 # Cache-Control: max-age=600 + ETag, identically with or without
                 # this query string, so a stale copy self-corrects in 10 minutes.
                 # Bumping it rewrites every page in the repo to buy nothing.
AR_DIGITS = "٠١٢٣٤٥٦٧٨٩"

TITLE_AR = "بحار الأنوار الجامعة لدرر أخبار الأئمة الأطهار"
SHORT_AR = "بحار الأنوار"
AUTHOR = {"ar": "العلامة محمد باقر المجلسي",
          "fa": "علامه محمدباقر مجلسی",
          "ur": "علامہ محمد باقر مجلسی",
          "en": "Allama Muhammad Baqir al-Majlisi"}
FRONT = {"ar": "مقدمة الناشر", "fa": "مقدمه ناشر",
         "ur": "مقدمہ ناشر", "en": "Publisher&#x27;s introduction"}
CITE = {
    "ar": lambda v, n: f"{TITLE_AR}، {AUTHOR['ar']}، المجلد {ar_num(v)}، ص {ar_num(n)}.",
    "fa": lambda v, n: f"{TITLE_AR}، {AUTHOR['fa']}، جلد {v}، ص {n}.",
    "ur": lambda v, n: f"{TITLE_AR}، {AUTHOR['ur']}، جلد {v}، ص {n}.",
    "en": lambda v, n: f"Bihar al-Anwar, {AUTHOR['en']}, vol. {v}, p. {n}.",
}
CITE_FM = {
    "ar": lambda v, n: f"{TITLE_AR}، المجلد {ar_num(v)}، مقدمة الناشر، ص {ar_num(n)}.",
    "fa": lambda v, n: f"{TITLE_AR}، جلد {v}، مقدمه ناشر، ص {n}.",
    "ur": lambda v, n: f"{TITLE_AR}، جلد {v}، مقدمہ ناشر، ص {n}.",
    "en": lambda v, n: f"Bihar al-Anwar, vol. {v}, publisher&#x27;s introduction, p. {n}.",
}

# Volume 83 alone is the مؤسسة الوفاء text: ghbook.ir has no HTML edition of it
# (withdrawn at the publisher's request), so it comes from ablibrary. Its page
# numbering does NOT match the دار احياء التراث العربي edition used by every
# other volume, and a reader checking a citation against a printed copy must be
# told so on the page itself, not in a changelog.
WAFA_VOLS = {83}
WAFA_NOTE = {
    "ar": "هذا المجلد من طبعة مؤسسة الوفاء، وترقيم صفحاته يختلف عن طبعة "
          "دار إحياء التراث العربي المعتمدة في سائر المجلدات.",
    "fa": "این مجلد از چاپ مؤسسة الوفاء است و شماره‌گذاری صفحات آن با چاپ "
          "دار احیاء التراث العربی که در دیگر مجلدات به کار رفته تفاوت دارد.",
    "ur": "یہ جلد مؤسسۃ الوفاء کے ایڈیشن سے ہے؛ اس کے صفحات کی ترتیب "
          "دار احیاء التراث العربی کے اُس ایڈیشن سے مختلف ہے جو باقی جلدوں میں ہے۔",
    "en": "This volume is from the Mu&#x27;assasat al-Wafa edition. Its page "
          "numbering differs from the Dar Ihya al-Turath al-Arabi edition used "
          "in every other volume.",
}


def ar_num(n):
    return "".join(AR_DIGITS[int(c)] for c in str(n))


def esc(s):
    return html.escape(s, quote=True)


REF = re.compile(r"\[(\d+)\]")


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
    url = f"{SITE}/bihar/{vol}/{pid}/"

    links = ""
    if prev_id:
        links += f'<link rel="prev" href="../../../bihar/{vol}/{prev_id}/">'
    if next_id:
        links += f'<link rel="next" href="../../../bihar/{vol}/{next_id}/">'
    # Arabic only: this volume has no translations, so no other hreflang exists.
    links += (f'<link rel="canonical" href="{url}">'
              f'<link rel="alternate" hreflang="ar" href="{url}">'
              f'<link rel="alternate" hreflang="x-default" href="{url}">')

    first, last = ids[0], ids[-1]
    pv = (f'<a class="btn prev" href="../../../bihar/{vol}/{prev_id}/" rel="prev">'
          f'<span data-i18n="prev"></span></a>' if prev_id else
          '<span class="btn" aria-disabled="true"><span data-i18n="prev"></span></span>')
    nx = (f'<a class="btn next" href="../../../bihar/{vol}/{next_id}/" rel="next">'
          f'<span data-i18n="next"></span></a>' if next_id else
          '<span class="btn" aria-disabled="true"><span data-i18n="next"></span></span>')

    table = CITE_FM if fm else CITE
    cites = " ".join(f'data-cite-{L}="{esc(f(vol, n))}"' for L, f in table.items())
    cspan = " ".join(f'data-{L}="{esc(f(vol, n))}"' for L, f in table.items())

    if fm:
        folio = ('<span class="folio"><span data-ar="' + esc(FRONT["ar"]) +
                 '" data-fa="' + esc(FRONT["fa"]) + '" data-ur="' + esc(FRONT["ur"]) +
                 '" data-en="' + FRONT["en"] + '">' + esc(FRONT["ar"]) + '</span> '
                 f'<span data-num="{n}">{ar_num(n)}</span></span>')
    else:
        folio = ('<span class="folio"><span data-i18n="page"></span> '
                 f'<span data-num="{n}">{ar_num(n)}</span></span>')

    note = ""
    if vol in WAFA_VOLS:
        note = ('<p class="book-credit" data-ar="' + esc(WAFA_NOTE["ar"]) +
                '" data-fa="' + esc(WAFA_NOTE["fa"]) + '" data-ur="' + esc(WAFA_NOTE["ur"]) +
                '" data-en="' + WAFA_NOTE["en"] + '">' + esc(WAFA_NOTE["ar"]) + '</p>')

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
      <div class="part-label"><span data-ar="{esc(AUTHOR['ar'])}" data-fa="{esc(AUTHOR['fa'])}" data-ur="{esc(AUTHOR['ur'])}" data-en="{esc(AUTHOR['en'])}">{esc(AUTHOR['ar'])}</span>
        <span><span data-i18n="volume"></span>
        <span data-num="{vol}">{vol}</span>
        {folio}</span></div>
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
      &nbsp;·&nbsp;<code>/bihar/{vol}/{pid}/</code></p>{note}
  </article>
</main>
<div id="page-meta" hidden data-trlangs="" data-slug="bihar" data-title-ar="{esc(SHORT_AR)}" data-title-fa="{esc(SHORT_AR)}" data-title-ur="{esc(SHORT_AR)}" data-title-en="Bihar al-Anwar" data-href="bihar/{vol}/{pid}/"
     data-pagenum="{pid}" data-volume="{vol}" data-pos="{i}" data-total="{len(ids)}"></div>
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
    print(f"  {len(ids)} pages -> {out}" + (f"  ({fmn} front matter)" if fmn else ""))

    if args.pages_json:
        # The dropdown is a PAGE picker, so it lists al-Majlisi's own pages only.
        # reader.js reads these as numbers; an "fm-5" among them would break it.
        nums = [p["n"] for p in data["pages"] if not p["id"].startswith("fm-")]
        p = pathlib.Path(args.pages_json)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(nums, ensure_ascii=False), encoding="utf-8")
        print(f"  pages json -> {p} ({len(nums)} numbered pages)")


if __name__ == "__main__":
    main()
