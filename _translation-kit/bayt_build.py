#!/usr/bin/env python3
"""Build Bayt al-Ahzan as PRINTED pages, the same shape as Bihar.

  bayt_build.py bayt_pages.json --lang fa --out <dir>
  bayt_build.py bayt_pages.json --index --out <dir>
  bayt_build.py bayt_pages.json --toc   --out <dir>

  /bayt-al-ahzan/            cover (chapter grid + colophon) + assets/toc.json
  /bayt-al-ahzan/<n>/        reserved for Qummi's Arabic original, not yet sourced
  /<lang>/bayt-al-ahzan/<n>/ <n> is the PRINTED page number, verified against the
                             scanned Naser edition (PDF page = printed + 3)

Pagination comes from bayt_paginate.py; see that file for how the printed
page numbers were established and checked.

Numbering has 31 holes (5, 13, 14, 28-30, 55, ...). Those are the edition's
part-title and blank pages — verified in the scan, no text is missing. The
printed number is kept so a citation matches the paper book, and prev/next
step through the ORDERED page list rather than n±1, so a reader never lands
on a hole.

Four things here are load-bearing and were each got wrong once:

  * The cover grid is class "chaps", never "suras". reader.js rewrites
    ".suras a[data-n]" to /<lang>/quran/<n>/ — a hardcoded path.
  * data-book points at the cover (ROOT/bayt-al-ahzan), not "..". reader.js
    loads BOOK + "/assets/toc.json".
  * The jump form's template carries the language, or the box sends readers
    to the empty Arabic slot.
  * The credit line is class "book-credit", not "cite" — reader.css hides
    .cite on en/fa/ur by the owner's request.
"""
import argparse, html, json, pathlib, re, sys

SITE = "https://library.misbah-inc.com"
SLUG = "bayt-al-ahzan"
SRC = "fa"

LANGS = {"fa": {"dir": "rtl"}, "en": {"dir": "ltr"}, "ur": {"dir": "rtl"}}
DEPTH = "../../.."

TITLES = {
    "fa": "رنج‌ها و فریادهای فاطمه سلام‌الله‌علیها",
    "en": "The Sorrows of Fatima (Bayt al-Ahzan)",
    "ur": "رنج ہا و فریادہای فاطمہ سلام اللہ علیہا",
}
SHORT = {"fa": "بیت‌الاحزان", "en": "Bayt al-Ahzan", "ur": "بیت الاحزان"}
AUTHOR = {"ar": "الشيخ عباس القمي", "fa": "شیخ عباس قمی",
          "ur": "شیخ عباس قمی", "en": "Shaykh Abbas al-Qummi"}
TRANSLATOR_FA = "محمد محمدی اشتهاردی"
FOREWORD = "ناصر مکارم شیرازی"

FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
REF = re.compile(r'\[(\d+)\]')


def loc_num(n, lang):
    return "".join(FA_DIGITS[int(c)] for c in str(n)) if lang in ("fa", "ur") else str(n)


def esc(s):
    return html.escape(s, quote=True)


def abs_url(lang, n=None):
    return f"{SITE}/{lang}/{SLUG}/{f'{n}/' if n else ''}"


def credit_block():
    """Class is book-credit, NOT cite — .cite is display:none on en/fa/ur."""
    return (f'<p class="book-credit">'
            f'<span data-i18n="author"></span>: {esc(AUTHOR["fa"])} · '
            f'<span data-i18n="translator"></span>: {esc(TRANSLATOR_FA)} · '
            f'<span data-i18n="foreword"></span>: {esc(FOREWORD)} · '
            f'<span data-i18n="textFrom"></span> '
            f'<a href="https://www.ghaemiyeh.com" rel="noopener">قائمیه</a></p>')


def body_html(page, lang):
    """Flat h3/p carrying data-i, the shape the Bihar pages use, so it inherits
    the .body and .body [lang="fa"] rules already in the stylesheet. Inline
    [n] citations become footnote links to the notes block below."""
    have = {n["n"] for n in page["notes"]}

    def ref(m):
        k = int(m.group(1))
        if k not in have:
            return m.group(0)
        return (f'<a class="fnref" href="#fn-{page["n"]}-{k}">'
                f'{loc_num(k, SRC)}</a>')

    rows = []
    for i, b in enumerate(page["blocks"]):
        tag = "h3" if b["tag"] in ("h3", "h4") else "p"
        rows.append(f'<{tag} lang="{SRC}" data-i="{i}">'
                    f'{REF.sub(ref, esc(b["fa"]))}</{tag}>')
    return "".join(rows)


def notes_html(page):
    if not page["notes"]:
        return ""
    items = "".join(
        f'<div class="note" lang="{SRC}" id="fn-{page["n"]}-{n["n"]}">'
        f'<span class="note-n">({loc_num(n["n"], SRC)})</span>'
        f'<span>{esc(n["fa"])}</span></div>'
        for n in page["notes"])
    return f'<div class="notes">{items}</div>'


def describe(page):
    for b in page["blocks"]:
        if b["tag"] == "p" and len(b["fa"]) > 60:
            return b["fa"][:157].rsplit(" ", 1)[0] + "…"
    return f'{page["chapter"]} — {TITLES[SRC]}'


def build_page(page, order, idx, lang, alts):
    n = page["n"]
    R = DEPTH
    prev_n = order[idx - 1] if idx > 0 else None
    next_n = order[idx + 1] if idx + 1 < len(order) else None
    total = len(order)

    canonical = f'<link rel="canonical" href="{abs_url(lang, n)}">'
    alt_links = "".join(f'<link rel="alternate" hreflang="{a}" href="{abs_url(a, n)}">'
                        for a in alts)
    alt_links += f'<link rel="alternate" hreflang="x-default" href="{abs_url(SRC, n)}">'

    prev_l = f'<link rel="prev" href="{R}/{lang}/{SLUG}/{prev_n}/">' if prev_n else ""
    next_l = f'<link rel="next" href="{R}/{lang}/{SLUG}/{next_n}/">' if next_n else ""
    pager_prev = (f'<a class="btn prev" href="{R}/{lang}/{SLUG}/{prev_n}/" rel="prev">'
                  f'<span data-i18n="prev"></span></a>') if prev_n else \
                 '<span class="btn" aria-disabled="true"><span data-i18n="prev"></span></span>'
    pager_next = (f'<a class="btn next" href="{R}/{lang}/{SLUG}/{next_n}/" rel="next">'
                  f'<span data-i18n="next"></span></a>') if next_n else \
                 '<span class="btn" aria-disabled="true"><span data-i18n="next"></span></span>'

    alt_attrs = " ".join(f'data-alt-{a}="{R}/{a}/{SLUG}/{n}/"' for a in alts if a != lang)
    desc = esc(describe(page))
    title = f'{SHORT.get(lang, SHORT[SRC])} — ص {loc_num(n, lang)}'

    return f'''<!DOCTYPE html>
<html lang="{lang}" dir="{LANGS[lang]["dir"]}" data-root="{R}" data-book="{R}/{SLUG}"
      data-sitelang="{lang}" data-srclang="{SRC}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{desc}">
{canonical}{alt_links}{prev_l}{next_l}
<link rel="stylesheet" href="{R}/assets/reader.css">
</head>
<body>
<a class="skip" href="#text">&rarr;</a>
<header class="bar"><div class="bar-in">
  <a class="brand" href="{R}/"><b data-i18n="libName"></b><small>Misbah Library</small></a>
  <div class="spacer"></div>
  <button class="tbtn" id="btn-toc"><svg class="ic" viewBox="0 0 24 24"><path d="M4 6h16M4 12h16M4 18h10"/></svg><span class="lbl" data-i18n="contents"></span></button>
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
</div></header>
<main class="wrap">
  <article>
    <div class="leaf" id="text">
      <div class="part-label"><span>{esc(page["chapter"])}</span>
        <span class="folio"><span data-i18n="page"></span>
        <span data-num="{n}">{loc_num(n, lang)}</span></span></div>
      <div class="body" data-tr-static="1">{body_html(page, lang)}</div>
      {notes_html(page)}
    </div>
    <nav class="pager">
      <a class="btn" href="{R}/{lang}/{SLUG}/{order[0]}/" rel="related"><span data-i18n="first"></span></a>{pager_prev}
      <form id="jump" data-tpl="{lang}/{SLUG}/{{p}}/" action="{R}/{lang}/{SLUG}/" method="get">
        <input id="jump-num" name="p" inputmode="numeric" data-i18n-label="page"
               data-num-val="{n}" value="{loc_num(n, lang)}">
      </form>
      {pager_next}<a class="btn" href="{R}/{lang}/{SLUG}/{order[-1]}/" rel="related"><span data-i18n="last"></span></a>
    </nav>
  </article>
</main>
<div id="page-meta" hidden {alt_attrs} data-slug="{SLUG}" data-pagenum="{n}"
     data-pos="{idx}" data-total="{total}"></div>
<div class="scrim" id="scrim"></div>
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
</div></footer>
<script src="{R}/assets/reader.js" defer></script>
</body>
</html>
'''


def build_index(data, starts):
    """The cover. Language-neutral: the chapter grid points at whichever
    language actually has pages (data-langs), so no reader lands on the empty
    Arabic slot. Class is chaps, not suras — see the module docstring."""
    cells = []
    for c in data["chapters"]:
        p = starts[c["n"]]
        inner = (f'<b class="sn" data-num="{p}">{loc_num(p, "fa")}</b>'
                 f'<span class="snm">{esc(c["title"])}</span>')
        cells.append(f'<a class="chap-cell" href="../{SRC}/{SLUG}/{p}/" '
                     f'data-n="{p}">{inner}</a>')

    colo = "".join(f'<p>{esc(x)}</p>' for x in data["colophon"])
    pages = data["pages"]

    return f'''<!DOCTYPE html>
<html lang="fa" dir="rtl" data-root=".." data-book="." data-srclang="{SRC}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(TITLES["fa"])}</title>
<meta name="description" content="{esc(TITLES['fa'])} — ترجمهٔ بیت‌الاحزان اثر {esc(AUTHOR['fa'])}، به قلم {esc(TRANSLATOR_FA)}.">
<meta property="og:title" content="{esc(TITLES['fa'])}">
<link rel="canonical" href="{SITE}/{SLUG}/">
<link rel="stylesheet" href="../assets/reader.css">
</head>
<body>
<a class="skip" href="#text">&rarr;</a>
<header class="bar"><div class="bar-in">
  <a class="brand" href="../"><b data-i18n="libName"></b><small>Misbah Library</small></a>
  <div class="spacer"></div>
  <a class="tbtn" href="../"><svg class="ic" viewBox="0 0 24 24"><path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/></svg><span class="lbl" data-i18n="home"></span></a>
  <button class="tbtn icon-only" id="btn-menu" data-i18n-label="menu">
    <svg class="ic" viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h16"/></svg></button>
  <div class="langs" role="group">
    <button data-lang="ar">ع</button><button data-lang="fa">فا</button>
    <button data-lang="ur">اردو</button><button data-lang="en">EN</button>
  </div>
  <button class="tbtn" id="btn-theme" aria-pressed="false"></button>
</div></header>
<main class="cover" id="text">
  <h1 data-ar="بيت الأحزان" data-fa="{esc(TITLES["fa"])}"
      data-ur="{esc(TITLES["ur"])}" data-en="{esc(TITLES["en"])}">{esc(TITLES["fa"])}</h1>
  <p class="by" data-ar="{esc(AUTHOR["ar"])}" data-fa="{esc(AUTHOR["fa"])}"
     data-ur="{esc(AUTHOR["ur"])}" data-en="{esc(AUTHOR["en"])}">{esc(AUTHOR["fa"])}</p>
  <p class="book-sub" lang="fa">ترجمهٔ بیت‌الاحزان</p>
  <div class="rule"></div>
  <dl>
    <dt data-i18n="pages"></dt><dd data-num="{len(pages)}">{loc_num(len(pages), "fa")}</dd>
    <dt data-i18n="chapters"></dt><dd data-num="{len(data["chapters"])}">{loc_num(len(data["chapters"]), "fa")}</dd>
    <dt data-i18n="translator"></dt><dd>{esc(TRANSLATOR_FA)}</dd>
    <dt data-i18n="foreword"></dt><dd>{esc(FOREWORD)}</dd>
  </dl>
  <p class="cover-go"><a class="btn" href="../{SRC}/{SLUG}/{pages[0]["n"]}/"><span data-i18n="start"></span></a></p>
  <h2 data-i18n="pickChapter"></h2>
  <div class="chaps" data-langpath="{SLUG}" data-langs="{SRC}">{"".join(cells)}</div>
</main>
<nav class="nav" id="nav" aria-hidden="true">
  <div class="nav-head"><b data-i18n="menu"></b>
    <button id="nav-close" data-i18n-label="close">✕</button></div>
  <ul>
    <li><a href="../"><span data-i18n="home"></span></a></li>
    <li><a href="../search/"><span data-i18n="search"></span></a></li>
    <li><a href="../books/"><span data-i18n="allBooks"></span></a></li>
  </ul>
</nav>
<div class="scrim" id="scrim"></div>
<footer class="foot"><div class="foot-in">
  <div><h3 data-i18n="libName"></h3></div>
  <div><h3 data-i18n="browse"></h3><ul>
    <li><a href="../" data-i18n="home"></a></li>
    <li><a href="../books/" data-i18n="allBooks"></a></li>
    <li><a href="../search/" data-i18n="search"></a></li>
    <li><a href="../about/" data-i18n="about"></a></li>
    <li><a href="../contact/" data-i18n="contact"></a></li>
  </ul></div>
</div></footer>
<script src="../assets/reader.js" defer></script>
</body>
</html>
'''


def build_toc(data, starts):
    """reader.js renders ROOT + '/' + LANG + '/' + x.href on translated pages,
    so hrefs must NOT carry the language prefix — that would double it."""
    return [{"title": c["title"], "fa": c["title"], "p": starts[c["n"]],
             "href": f"{SLUG}/{starts[c['n']]}/"} for c in data["chapters"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pages")
    ap.add_argument("--out", required=True)
    ap.add_argument("--lang", choices=sorted(LANGS))
    ap.add_argument("--alts", default="fa")
    ap.add_argument("--index", action="store_true")
    ap.add_argument("--toc", action="store_true")
    a = ap.parse_args()

    data = json.loads(pathlib.Path(a.pages).read_text(encoding="utf-8"))
    pages = data["pages"]
    order = [p["n"] for p in pages]
    starts = {}
    for p in pages:
        starts.setdefault(p["chapter_n"], p["n"])
    out = pathlib.Path(a.out)

    if a.index:
        out.mkdir(parents=True, exist_ok=True)
        (out / "index.html").write_text(build_index(data, starts), encoding="utf-8")
        print(f"cover -> {out}/index.html")
        return

    if a.toc:
        (out / "assets").mkdir(parents=True, exist_ok=True)
        (out / "assets" / "toc.json").write_text(
            json.dumps(build_toc(data, starts), ensure_ascii=False), encoding="utf-8")
        print(f"toc -> {out}/assets/toc.json ({len(data['chapters'])} chapters)")
        return

    if not a.lang:
        sys.exit("--lang is required unless --index or --toc")
    alts = [x.strip() for x in a.alts.split(",") if x.strip()]
    if a.lang not in alts:
        sys.exit(f"--alts must include {a.lang}; hreflang sets are self-referential")

    for i, p in enumerate(pages):
        d = out / str(p["n"])
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(
            build_page(p, order, i, a.lang, alts), encoding="utf-8")
    print(f"{len(pages)} pages -> {out}  (lang={a.lang}, printed {order[0]}–{order[-1]})")


if __name__ == "__main__":
    main()
