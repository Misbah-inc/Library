#!/usr/bin/env python3
"""Build جامع المقدمات reading pages from jame_pages.json.

  jame_build.py jame_pages.json --out ../jame-al-muqaddimat

URL shape follows Bihar, which is the library's model for a multi-volume book:

  /jame-al-muqaddimat/            volume selector
  /jame-al-muqaddimat/1/          volume 1 contents (its 9 treatises)
  /jame-al-muqaddimat/1/<page>/   a printed page, 1..609
  /jame-al-muqaddimat/2/<page>/   1..607

The TOC drawer is per volume, so each volume owns its assets/toc.json and its
pages carry data-book="..", which resolves to the volume folder. A single
book-level toc.json could not describe both volumes.

Language: the edition is a Persian commentary around Arabic matn, so the page
is fa and each block carries its own lang. That is what lets the Arabic set in
the Arabic face and the Persian in the UI face — they are interleaved down to
the line in this text, which is exactly why per-block tagging is worth the
trouble.

data-standalone="1" as on Bayt al-Ahzan: the book lives at its own top-level
slug rather than under /fa/, so reader.js must not prefix its links.

Deliberately NOT using class="vols"/"vol" for the volume grid — reader.js
rewrites those hrefs to <lang>/<slug>/<v>/ with no standalone guard, which
would point every volume link at a path that does not exist. class="chaps"
without data-langpath is left alone.
"""
import argparse, html, json, pathlib, re, sys

SITE = "https://library.misbah-inc.com"
SLUG = "jame-al-muqaddimat"
# Keep in step with the other builders — every page in the library links the
# same assets/reader.css and assets/reader.js, so they must all move together
# or a reader gets one book's stylesheet while browsing another's.
ASSETS_V = "6"
SRC = "fa"
FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"

TITLE = {"fa": "جامع المقدمات", "ar": "جامع المقدمات",
         "ur": "جامع المقدمات", "en": "Jami' al-Muqaddimat"}
VOL_LABEL = {"fa": "جلد", "ar": "المجلد", "ur": "جلد", "en": "Volume"}


def loc_num(n):
    return "".join(FA_DIGITS[int(c)] if c.isdigit() else c for c in str(n))


def esc(s):
    return html.escape(str(s), quote=True)


def page_url(v, n):
    return f"{SITE}/{SLUG}/{v}/{n}/"


TASHKIL = {}          # "vol:page:block" -> vocalised text, loaded in main()


def body_html(vol_n, page):
    """Flat h2/h3/p carrying data-i and a per-block lang, the shape the Bihar
    and Bayt al-Ahzan pages use, so it inherits the existing .body rules.

    A block with a vocalised variant also carries data-tashkil; reader.js keeps
    the printed text in data-plain and swaps between the two. The page ships
    the plain form, so with JavaScript off a reader still sees the printed
    text rather than an editorial reconstruction of it."""
    rows = []
    for i, b in enumerate(page["blocks"]):
        tag = b["tag"] if b["tag"] in ("h2", "h3") else "p"
        voc = TASHKIL.get(f'{vol_n}:{page["n"]}:{i}')
        extra = f' data-tashkil="{esc(voc)}"' if voc else ""
        rows.append(f'<{tag} lang="{b["lang"]}" data-i="{i}"{extra}>'
                    f'{esc(b["t"])}</{tag}>')
    return "".join(rows) or '<p class="blank-page">&nbsp;</p>'


def has_tashkil(vol_n, page):
    return any(f'{vol_n}:{page["n"]}:{i}' in TASHKIL
               for i in range(len(page["blocks"])))


def describe(vol, page):
    ch = page.get("chapter") or TITLE["fa"]
    return (f'{TITLE["fa"]} — {VOL_LABEL["fa"]} {loc_num(vol)}، '
            f'صفحهٔ {loc_num(page["n"])}. {ch}')


HEAD_BAR = '''<header class="bar"><div class="bar-in">
  <a class="brand" href="{R}/"><b data-i18n="libName"></b><small>Misbah Library</small></a>
  <div class="spacer"></div>
  {toc_btn}
  <button class="tbtn icon-only" id="btn-smaller" data-i18n-label="smaller">ا−</button>
  <button class="tbtn icon-only" id="btn-bigger" data-i18n-label="bigger">ا+</button>
  <a class="tbtn" href="{R}/"><svg class="ic" viewBox="0 0 24 24"><path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/></svg><span class="lbl" data-i18n="home"></span></a>
  <button class="tbtn icon-only" id="btn-menu" data-i18n-label="menu">
    <svg class="ic" viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h16"/></svg></button>
  <div class="langs" role="group">
    <button data-lang="ar">ع</button><button data-lang="fa">فا</button>
    <button data-lang="ur">اردو</button><button data-lang="en">EN</button>
  </div>
  <button class="tbtn" id="btn-theme" aria-pressed="false"></button>
</div></header>'''

DRAWER = '''<div class="scrim" id="scrim"></div>
<nav class="nav" id="nav" aria-hidden="true">
  <div class="nav-head"><b data-i18n="menu"></b>
    <button id="nav-close" data-i18n-label="close">✕</button></div>
  <ul>
    <li><a href="{R}/"><span data-i18n="home"></span></a></li>
    <li><a href="{R}/{SLUG}/"><span data-i18n="contents"></span></a></li>
    <li><a href="{R}/search/"><span data-i18n="search"></span></a></li>
    <li><a href="{R}/books/"><span data-i18n="allBooks"></span></a></li>
  </ul>
</nav>
<footer class="foot"><div class="foot-in">
  <div><h3 data-i18n="libName"></h3></div>
</div></footer>'''


def build_page(vol, page, order, idx):
    n = page["n"]
    R = "../../.."
    v = vol["v"]
    prev_n = order[idx - 1] if idx > 0 else None
    next_n = order[idx + 1] if idx + 1 < len(order) else None

    def rel(p):
        return f"{R}/{SLUG}/{v}/{p}/"

    prev_l = f'<link rel="prev" href="{page_url(v, prev_n)}">' if prev_n else ""
    next_l = f'<link rel="next" href="{page_url(v, next_n)}">' if next_n else ""
    pager_prev = (f'<a class="btn prev" href="{rel(prev_n)}" rel="prev">'
                  f'<span data-i18n="prev"></span></a>') if prev_n else \
                 '<span class="btn" aria-disabled="true"><span data-i18n="prev"></span></span>'
    pager_next = (f'<a class="btn next" href="{rel(next_n)}" rel="next">'
                  f'<span data-i18n="next"></span></a>') if next_n else \
                 '<span class="btn" aria-disabled="true"><span data-i18n="next"></span></span>'

    title = f'{TITLE["fa"]} — {VOL_LABEL["fa"]} {loc_num(v)}، ص {loc_num(n)}'
    desc = esc(describe(v, page))

    # citation strings, one per interface language (reader.js reads data-cite-<lang>)
    ch = page.get("chapter") or ""
    cite_ar = f'جامع المقدمات، {ch}، المجلد {loc_num(v)}، ص {loc_num(n)}.'
    cite_fa = f'جامع المقدمات، {ch}، جلد {loc_num(v)}، ص {loc_num(n)}.'
    cite_ur = f'جامع المقدمات، {ch}، جلد {loc_num(v)}، ص {loc_num(n)}.'
    cite_en = f'Jami’ al-Muqaddimat, vol. {v}, p. {n}.'

    # the vocalisation toggle only appears on pages that actually have one
    tashkil_bar = ('<div class="tashkil-bar"><button class="tashkil-btn" id="btn-tashkil" '
                   'type="button" aria-pressed="true">'
                   '<span data-i18n="tashkil"></span></button></div>'
                   ) if has_tashkil(v, page) else ""
    toc_btn = ('<button class="tbtn" id="btn-toc"><svg class="ic" viewBox="0 0 24 24">'
               '<path d="M4 6h16M4 12h16M4 18h10"/></svg>'
               '<span class="lbl" data-i18n="contents"></span></button>')

    return f'''<!DOCTYPE html>
<html lang="fa" dir="rtl" data-root="{R}" data-book=".." data-sitelang="fa"
      data-standalone="1" data-srclang="fa">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{desc}">
<link rel="canonical" href="{page_url(v, n)}">
<link rel="alternate" hreflang="fa" href="{page_url(v, n)}">
<link rel="alternate" hreflang="x-default" href="{page_url(v, n)}">{prev_l}{next_l}
<link rel="stylesheet" href="{R}/assets/reader.css?v={ASSETS_V}">
</head>
<body>
<a class="skip" href="#text">&rarr;</a>
{HEAD_BAR.format(R=R, toc_btn=toc_btn)}
<main class="wrap">
  <article>
    <div class="leaf" id="text">
      <div class="part-label">
        <a class="up-link" href="{R}/{SLUG}/{v}/">{esc(page.get("chapter") or "")}</a>
        <span class="folio"><span data-i18n="page"></span>
        <span data-num="{n}">{loc_num(n)}</span></span></div>
      {tashkil_bar}
      <div class="body" data-tr-static="1">{body_html(v, page)}</div>
    </div>
    <nav class="pager">
      <a class="btn" href="{rel(order[0])}" rel="related"><span data-i18n="first"></span></a>{pager_prev}
      <form id="jump" data-tpl="{SLUG}/{v}/{{p}}/" action="{R}/{SLUG}/{v}/" method="get">
        <input id="jump-num" name="p" inputmode="numeric" data-i18n-label="page"
               data-num-val="{n}" value="{loc_num(n)}">
      </form>
      {pager_next}<a class="btn" href="{rel(order[-1])}" rel="related"><span data-i18n="last"></span></a>
    </nav>
    <p class="cite" id="cite-text"
       data-cite-ar="{esc(cite_ar)}" data-cite-fa="{esc(cite_fa)}"
       data-cite-ur="{esc(cite_ur)}" data-cite-en="{esc(cite_en)}">
      <span data-i18n="citation"></span>:
      <button class="btn-cite" id="btn-cite" data-i18n="cite"></button></p>
  </article>
</main>
<div id="page-meta" hidden data-slug="{SLUG}" data-pagenum="{n}" data-volume="{v}"
     data-title-fa="{esc(TITLE["fa"])}" data-title-ar="{esc(TITLE["ar"])}"
     data-title-ur="{esc(TITLE["ur"])}" data-title-en="{esc(TITLE["en"])}"
     data-href="{SLUG}/{v}/{n}/"
     data-pos="{idx}" data-total="{len(order)}"></div>
{DRAWER.format(R=R, SLUG=SLUG)}
<script src="{R}/assets/reader.js?v={ASSETS_V}" defer></script>
</body>
</html>
'''


def chapter_starts(vol):
    """First printed page of each treatise."""
    starts = {}
    for p in vol["pages"]:
        cn = p.get("chapter_n") or 0
        if cn and cn not in starts and p["blocks"]:
            starts[cn] = p["n"]
    return starts


def build_toc(data):
    """One book-level assets/toc.json covering BOTH volumes.

    It has to live at the book root, not per volume: reader.js rewrites
    BOOK to ROOT + '/' + data-slug on any page carrying data-sitelang, so a
    per-volume assets/toc.json is never fetched and the drawer comes up empty.
    Spanning both volumes is also the better listing — all 15 treatises in one
    place, so a reader can cross from volume 1 to volume 2 without backing out.
    """
    items = []
    for vol in data["volumes"]:
        starts = chapter_starts(vol)
        for c in vol["chapters"]:
            p = starts.get(c["n"])
            if p is None:
                continue
            items.append({"href": f'{SLUG}/{vol["v"]}/{p}/',
                          "title": f'{VOL_LABEL["fa"]} {loc_num(vol["v"])} · {c["title"]}',
                          "p": p})
    return json.dumps(items, ensure_ascii=False, separators=(",", ":"))


def build_vol_index(vol):
    """Volume contents page — the treatises, each linking to its first page."""
    R = "../.."
    v = vol["v"]
    starts = chapter_starts(vol)
    pages = [p["n"] for p in vol["pages"]]
    cells = []
    for c in vol["chapters"]:
        p = starts.get(c["n"])
        inner = (f'<b class="sn" data-num="{c["n"]}">{loc_num(c["n"])}</b>'
                 f'<span class="snm">{esc(c["title"])}</span>'
                 f'<span class="sct"><span data-i18n="page"></span> '
                 f'<span data-num="{p}">{loc_num(p)}</span></span>') if p else ""
        if p:
            cells.append(f'<a class="chap-cell" href="{p}/">{inner}</a>')
    title = f'{TITLE["fa"]} — {VOL_LABEL["fa"]} {loc_num(v)}'
    toc_btn = ('<button class="tbtn" id="btn-toc"><svg class="ic" viewBox="0 0 24 24">'
               '<path d="M4 6h16M4 12h16M4 18h10"/></svg>'
               '<span class="lbl" data-i18n="contents"></span></button>')
    return f'''<!DOCTYPE html>
<html lang="fa" dir="rtl" data-root="{R}" data-book="." data-sitelang="fa"
      data-standalone="1" data-srclang="fa">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(title)} — {loc_num(len(pages))} صفحه، {loc_num(len(cells))} کتاب.">
<link rel="canonical" href="{SITE}/{SLUG}/{v}/">
<link rel="stylesheet" href="{R}/assets/reader.css?v={ASSETS_V}">
</head>
<body>
<a class="skip" href="#text">&rarr;</a>
{HEAD_BAR.format(R=R, toc_btn=toc_btn)}
<main class="cover" id="text">
  <h1>{esc(title)}</h1>
  <p class="by">{loc_num(len(cells))} کتاب · {loc_num(len(pages))} صفحه</p>
  <div class="rule"></div>
  <p class="cover-go"><a class="btn go" href="{pages[0]}/"><span data-i18n="start"></span></a></p>
  <h2 data-i18n="chapters"></h2>
  <div class="chaps">{"".join(cells)}</div>
</main>
{DRAWER.format(R=R, SLUG=SLUG)}
<script src="{R}/assets/reader.js?v={ASSETS_V}" defer></script>
</body>
</html>
'''


def build_cover(data):
    """Volume selector at /jame-al-muqaddimat/."""
    R = ".."
    cells = []
    for vol in data["volumes"]:
        v = vol["v"]
        npages = len(vol["pages"])
        nch = len(chapter_starts(vol))
        cells.append(
            f'<a class="chap-cell" href="{v}/">'
            f'<b class="sn" data-num="{v}">{loc_num(v)}</b>'
            f'<span class="snm">{esc(VOL_LABEL["fa"])} {loc_num(v)}</span>'
            f'<span class="sct"><span data-num="{nch}">{loc_num(nch)}</span> کتاب · '
            f'<span data-num="{npages}">{loc_num(npages)}</span> صفحه</span></a>')
    total = sum(len(v["pages"]) for v in data["volumes"])
    return f'''<!DOCTYPE html>
<html lang="fa" dir="rtl" data-root="{R}" data-book="." data-sitelang="fa"
      data-standalone="1" data-srclang="fa">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(TITLE["fa"])}</title>
<meta name="description" content="{esc(TITLE["fa"])} — مجموعهٔ متون مقدماتی صرف و نحو و منطق، در {loc_num(len(data["volumes"]))} جلد و {loc_num(total)} صفحه.">
<link rel="canonical" href="{SITE}/{SLUG}/">
<link rel="stylesheet" href="{R}/assets/reader.css?v={ASSETS_V}">
</head>
<body>
<a class="skip" href="#text">&rarr;</a>
{HEAD_BAR.format(R=R, toc_btn="")}
<main class="cover" id="text">
  <h1>{esc(TITLE["fa"])}</h1>
  <p class="by">مجموعهٔ متون مقدماتی صرف، نحو و منطق</p>
  <div class="rule"></div>
  <h2 data-i18n="pickVolume"></h2>
  <div class="chaps">{"".join(cells)}</div>
</main>
{DRAWER.format(R=R, SLUG=SLUG)}
<script src="{R}/assets/reader.js?v={ASSETS_V}" defer></script>
</body>
</html>
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pages")
    ap.add_argument("--out", required=True)
    ap.add_argument("--tashkil", help="vocalisation overlay from jame_tashkil.py")
    a = ap.parse_args()

    data = json.loads(pathlib.Path(a.pages).read_text(encoding="utf-8"))

    if a.tashkil:
        tp = pathlib.Path(a.tashkil)
        if tp.exists():
            TASHKIL.update(json.loads(tp.read_text(encoding="utf-8")))
            print(f"vocalisation overlay: {len(TASHKIL)} blocks")

    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    (out / "index.html").write_text(build_cover(data), encoding="utf-8")
    (out / "assets").mkdir(parents=True, exist_ok=True)
    (out / "assets" / "toc.json").write_text(build_toc(data), encoding="utf-8")

    made = 0
    for vol in data["volumes"]:
        v = vol["v"]
        vdir = out / str(v)
        vdir.mkdir(parents=True, exist_ok=True)
        (vdir / "index.html").write_text(build_vol_index(vol), encoding="utf-8")

        order = [p["n"] for p in vol["pages"]]
        # feeds reader.js's page dropdown (the sitewide replacement for the
        # tick-mark edge bar); it looks for assets/pages-<vol>.json at the
        # BOOK root, so both volumes' files live together under assets/
        (out / "assets" / f"pages-{v}.json").write_text(
            json.dumps(order, separators=(",", ":")), encoding="utf-8")
        for idx, page in enumerate(vol["pages"]):
            d = vdir / str(page["n"])
            d.mkdir(parents=True, exist_ok=True)
            (d / "index.html").write_text(
                build_page(vol, page, order, idx), encoding="utf-8")
            made += 1
        print(f"volume {v}: {len(order)} pages + contents + toc.json -> {vdir}")
    print(f"cover -> {out}/index.html")
    print(f"{made} reading pages total")


if __name__ == "__main__":
    main()
