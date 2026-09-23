#!/usr/bin/env python3
"""Build Arabic «من لا يحضره الفقيه» reading pages for a volume.

    python faqih_ar_build.py faqih_v1.json --out ../faqih/1 --pages-json ../faqih/assets/pages-1.json

Derived from `kafi_ar_build.py`, itself from `bihar_ar_build.py`, and kept as a
separate file — one builder per book is this project's established shape. A fix
made here that is also a fault there must be applied to both; they share a
lineage, not code.

**Edition: تحقيق علي أكبر الغفاري، مؤسسة النشر الإسلامي / جماعة المدرسين، قم**,
via the Ghaemiyeh export (ghbook.ir book 19340). ablibrary carries the SAME
edition with the SAME pagination — verified at pages 100/200/300/400 in every
volume and at 98.75-99.75% coverage on sampled character runs — so the choice
between them is narrow, and it is NOT the tashkil argument that settled al-Kafi:

    Bihar vol 10   54.88% of letters carry a mark
    al-Kafi vol 1  10.83%
    al-Faqih v1     0.69%   <- essentially unvocalised
    al-Faqih v3     0.51%

This export is vocalised only incidentally, where the editor disambiguates a
word. Ghaemiyeh is chosen for duller reasons: it includes the back-matter
فهارس that ablibrary drops, and it is the format `bihar_ar_extract.py` and
`bihar_ar_audit.py` already read, so the book arrives through the same audited
pipeline as every other. ablibrary's one advantage is a fuller editor's
introduction in volume 1.

**Four uniform volumes, no named parts.** Unlike al-Kafi, which is cited as
«أصول الكافي ج ١», al-Faqih is cited plainly by volume, so the part-label slot
carries the book's own title rather than a part name.

**Hadith numbering runs continuously across the four volumes** — vol 1 ends at
1573, vol 2 at 3215, vol 3 at 4967, vol 4 at 5829 — and is identical in both
sources, so a citation resolves against either.

**No translations.** Every page carries `data-trlangs=""`, so reader.js shows the
"not translated yet" notice at once instead of fetching a file that cannot exist.

**No edge rail**, same as Bihar volumes 2-110 and al-Kafi: reader.js falls
through to `faqih/assets/pages-<vol>.json` and the dropdown offers every page.
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

SHORT_AR = "من لا يحضره الفقيه"
TITLE = {"ar": "من لا يحضره الفقيه", "fa": "من لا يحضره الفقيه",
         "ur": "من لا يحضره الفقيه", "en": "Man la Yahduruhu al-Faqih"}
AUTHOR = {"ar": "الشيخ الصدوق محمد بن علي بن بابويه القمي",
          "fa": "شیخ صدوق، محمد بن علی بن بابویه قمی",
          "ur": "شیخ صدوق محمد بن علی بن بابویہ قمی",
          "en": "Al-Shaykh al-Saduq Muhammad b. Ali b. Babawayh al-Qummi"}
# Named by each volume's own هوية الكتاب block. Do NOT write دار التعارف here —
# that is al-Kafi's edition in this library, a different book and a different
# publisher; the two builders sit next to each other and are easy to confuse.
EDITION = {"ar": "تحقيق علي أكبر الغفاري، مؤسسة النشر الإسلامي، قم",
           "fa": "تحقیق علی‌اکبر غفاری، مؤسسة النشر الإسلامی، قم",
           "ur": "تحقیق علی اکبر غفاری، مؤسسۃ النشر الإسلامی، قم",
           "en": "ed. Ali Akbar al-Ghaffari, Mu'assasat al-Nashr al-Islami, Qum"}
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
    title = (f"{SHORT_AR} — {FRONT['ar']} ص {ar_num(n)}" if fm
             else f"{SHORT_AR} — ص {ar_num(n)}")
    url = f"{SITE}/faqih/{vol}/{pid}/"

    links = ""
    if prev_id:
        links += f'<link rel="prev" href="../../../faqih/{vol}/{prev_id}/">'
    if next_id:
        links += f'<link rel="next" href="../../../faqih/{vol}/{next_id}/">'
    links += (f'<link rel="canonical" href="{url}">'
              f'<link rel="alternate" hreflang="ar" href="{url}">'
              f'<link rel="alternate" hreflang="x-default" href="{url}">')

    first, last = ids[0], ids[-1]
    pv = (f'<a class="btn prev" href="../../../faqih/{vol}/{prev_id}/" rel="prev">'
          f'<span data-i18n="prev"></span></a>' if prev_id else
          '<span class="btn" aria-disabled="true"><span data-i18n="prev"></span></span>')
    nx = (f'<a class="btn next" href="../../../faqih/{vol}/{next_id}/" rel="next">'
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

    # al-Faqih has no named parts, so this slot carries the book's own title.
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
      <a class="btn " href="../../../faqih/{vol}/{first}/" rel="related"><span data-i18n="first"></span></a>{pv}
      <form id="jump" data-tpl="faqih/{vol}/{{p}}/" action="../../../" method="get">
        <input id="jump-num" name="p" inputmode="numeric" data-i18n-label="page"
               data-num-val="{n}" value="{ar_num(n)}">
      </form>
      {nx}<a class="btn " href="../../../faqih/{vol}/{last}/" rel="related"><span data-i18n="last"></span></a>
    </nav>
    <p class="cite" id="cite-text" {cites}><span data-i18n="citation"></span>:
      <span {cspan}></span>
      &nbsp;·&nbsp;<code>/faqih/{vol}/{pid}/</code></p>
  </article>
</main>
<div id="page-meta" hidden data-trlangs="" data-slug="faqih" data-title-ar="{esc(SHORT_AR)}" data-title-fa="من لا يحضره الفقيه" data-title-ur="من لا يحضره الفقيه" data-title-en="Man la Yahduruhu al-Faqih" data-href="faqih/{vol}/{pid}/"
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
