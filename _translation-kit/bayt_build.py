#!/usr/bin/env python3
"""Build Bayt al-Ahzan chapter pages for the Misbah Library.

  bayt_build.py <bayt.json> --lang fa --out <dir> [--chapter N ...]
  bayt_build.py <bayt.json> --index --out <dir> [--published 1,2,...]

  /bayt-al-ahzan/<n>/        reserved for Qummi's Arabic original (not yet sourced)
  /<lang>/bayt-al-ahzan/<n>/ Persian source, plus a translation where one exists

This book is the library's first whose source of record is NOT Arabic: the
original Arabic is Qummi's, but what we hold is Ishtihardi's Persian rendering.
So the Persian sits in /fa/ from the outset, leaving the root slot free for the
Arabic when it is sourced — no migration, no broken URLs later.

For the same reason the reader must not label the source view "Arabic": pages
carry data-srclang so the button names the language actually shown.
"""
import argparse, html, json, pathlib, re, sys

SITE = "https://library.misbah-inc.com"
ASSETS_V = "3"
SLUG = "bayt-al-ahzan"
SRC = "fa"                       # language of the text we hold

LANGS = {
    "fa": {"dir": "rtl", "depth": "../../.."},
    "en": {"dir": "ltr", "depth": "../../.."},
    "ur": {"dir": "rtl", "depth": "../../.."},
}

TITLES = {
    "fa": "رنج‌ها و فریادهای فاطمه سلام‌الله‌علیها",
    "en": "The Sorrows of Fatima (Bayt al-Ahzan)",
    "ur": "رنج ہا و فریادہای فاطمہ سلام اللہ علیہا",
}
AUTHOR = {"ar": "الشيخ عباس القمي", "fa": "شیخ عباس قمی",
          "ur": "شیخ عباس قمی", "en": "Shaykh Abbas al-Qummi"}
TRANSLATOR_FA = "محمد محمدی اشتهاردی"
FOREWORD = "ناصر مکارم شیرازی"

FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"


def loc_num(n, lang):
    return "".join(FA_DIGITS[int(c)] for c in str(n)) if lang in ("fa", "ur") else str(n)


def esc(s):
    return html.escape(s, quote=True)


def abs_url(lang, n=None):
    tail = f"{n}/" if n else ""
    return f"{SITE}/{lang}/{SLUG}/{tail}"


def credit_block():
    """Every party whose work is on the page, named. The Ghaemiyeh centre
    distributes this text freely; crediting them and the translator is both
    correct and the thing that makes relying on that distribution defensible."""
    return (f'<p class="cite book-credit">'
            f'<span data-i18n="author"></span>: {esc(AUTHOR["fa"])} · '
            f'<span data-i18n="translator"></span>: {esc(TRANSLATOR_FA)} · '
            f'<span data-i18n="foreword"></span>: {esc(FOREWORD)} · '
            f'<span data-i18n="textFrom"></span> '
            f'<a href="https://www.ghaemiyeh.com" rel="noopener">قائمیه</a></p>')


def build_chapter(ch, chapters, lang, alts):
    L = LANGS[lang]
    R = L["depth"]
    n = ch["n"]
    total = len(chapters)
    is_src = (lang == SRC)

    rows = []
    for b in ch["blocks"]:
        tag = b["tag"]
        txt = b.get(SRC, "")
        if tag in ("h3", "h4"):
            rows.append(f'<div class="sec" id="s{b["i"]}">'
                        f'<{tag} lang="{SRC}" data-i="{b["i"]}">{esc(txt)}</{tag}>'
                        + (f'<{tag} class="tr-line" lang="{lang}">{esc(b[lang])}</{tag}>'
                           if not is_src and lang in b else "")
                        + '</div>')
        else:
            rows.append(f'<div class="blk" id="s{b["i"]}">'
                        f'<p lang="{SRC}" data-i="{b["i"]}">{esc(txt)}</p>'
                        + (f'<p class="tr-line" lang="{lang}">{esc(b[lang])}</p>'
                           if not is_src and lang in b else "")
                        + '</div>')
    body = "".join(rows)

    canonical = f'<link rel="canonical" href="{abs_url(lang, n)}">'
    alt_links = "".join(
        f'<link rel="alternate" hreflang="{a}" href="{abs_url(a, n)}">' for a in alts)
    alt_links += (f'<link rel="alternate" hreflang="x-default" '
                  f'href="{abs_url(SRC, n)}">')

    prev_l = f'<link rel="prev" href="{R}/{lang}/{SLUG}/{n-1}/">' if n > 1 else ""
    next_l = f'<link rel="next" href="{R}/{lang}/{SLUG}/{n+1}/">' if n < total else ""
    pager_prev = (f'<a class="btn prev" href="{R}/{lang}/{SLUG}/{n-1}/" rel="prev">'
                  f'<span data-i18n="prev"></span></a>') if n > 1 else \
                 '<span class="btn" aria-disabled="true"><span data-i18n="prev"></span></span>'
    pager_next = (f'<a class="btn next" href="{R}/{lang}/{SLUG}/{n+1}/" rel="next">'
                  f'<span data-i18n="next"></span></a>') if n < total else \
                 '<span class="btn" aria-disabled="true"><span data-i18n="next"></span></span>'

    alt_attrs = " ".join(f'data-alt-{a}="{R}/{a}/{SLUG}/{n}/"' for a in alts if a != lang)

    # a translated page gets the view controls; the source page has nothing to toggle
    tr_bar = ('<div class="tr-bar" id="tr-bar"><div class="tr-modes">'
              '<button data-mode="tr" data-i18n="viewTr" aria-pressed="true"></button>'
              '<button data-mode="both" data-i18n="viewBoth" aria-pressed="false"></button>'
              '<button data-mode="side" data-i18n="viewSide" aria-pressed="false"></button>'
              '<button data-mode="ar" data-i18n="viewSrc" aria-pressed="false"></button>'
              '</div><span class="tr-note machine">'
              '<svg class="ic" viewBox="0 0 24 24"><path d="M12 3v2M5 8h14v11H5z"/>'
              '<circle cx="9" cy="13" r="1.2"/><circle cx="15" cy="13" r="1.2"/></svg>'
              '<span data-i18n="machineTr"></span></span></div>') if not is_src else ""

    desc = esc(f'{ch["title"]} — {TITLES.get(lang, TITLES[SRC])}')

    return f'''<!DOCTYPE html>
<html lang="{lang}" dir="{L["dir"]}" data-root="{R}" data-book=".." data-sitelang="{lang}"
      data-srclang="{SRC}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(ch["title"])} — {esc(TITLES.get(lang, TITLES[SRC]))}</title>
<meta name="description" content="{desc}">
{canonical}{alt_links}{prev_l}{next_l}
<link rel="stylesheet" href="{R}/assets/reader.css?v={ASSETS_V}">
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
      <div class="part-label"><span class="ch-name">{esc(ch["title"])}</span>
        <span class="ch-meta"><span data-i18n="chapter"></span>
        <span data-num="{n}">{loc_num(n, lang)}</span> /
        <span data-num="{total}">{loc_num(total, lang)}</span></span></div>
      {tr_bar}
      <div class="body" data-tr-static="1" data-unit="blk">{body}</div>
      {credit_block()}
    </div>
    <nav class="pager">
      <a class="btn " href="{R}/{lang}/{SLUG}/1/" rel="related"><span data-i18n="first"></span></a>{pager_prev}
      <form id="jump" data-tpl="{SLUG}/{{p}}/" action="{R}/" method="get">
        <input id="jump-num" name="p" inputmode="numeric" data-i18n-label="chapter"
               data-num-val="{n}" value="{n}">
      </form>
      {pager_next}<a class="btn " href="{R}/{lang}/{SLUG}/{total}/" rel="related"><span data-i18n="last"></span></a>
    </nav>
  </article>
</main>
<div id="page-meta" hidden {alt_attrs} data-slug="{SLUG}" data-pagenum="{n}"
     data-pos="{n-1}" data-total="{total}"></div>
<div class="scrim" id="scrim"></div>
<nav class="nav" id="nav" aria-hidden="true">
  <div class="nav-head"><b data-i18n="menu"></b>
    <button id="nav-close" data-i18n-label="close">✕</button></div>
  <ul>
    <li><a href="{R}/"><span data-i18n="home"></span></a></li>
    <li><a href="{R}/search/"><span data-i18n="search"></span></a></li>
    <li><a href="{R}/books/"><span data-i18n="allBooks"></span></a></li>
  </ul>
</nav>
<footer class="foot"><div class="foot-in">
  <div><h3 data-i18n="libName"></h3></div>
</div></footer>
<script src="{R}/assets/reader.js?v={ASSETS_V}" defer></script>
</body>
</html>
'''


def build_index(chapters, published):
    cells = []
    for c in chapters:
        n = c["n"]
        inner = (f'<b class="sn" data-num="{n}">{loc_num(n, "fa")}</b>'
                 f'<span class="snm">{esc(c["title"])}</span>')
        if n in published:
            cells.append(f'<a class="sura-cell" href="../{SRC}/{SLUG}/{n}/" '
                         f'data-n="{n}">{inner}</a>')
        else:
            cells.append(f'<span class="sura-cell off" data-n="{n}">{inner}</span>')

    return f'''<!DOCTYPE html>
<html lang="fa" dir="rtl" data-root=".." data-book="." data-srclang="{SRC}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(TITLES["fa"])}</title>
<meta name="description" content="{esc(TITLES['fa'])} — ترجمهٔ بیت‌الاحزان، {esc(AUTHOR['fa'])}.">
<link rel="canonical" href="{SITE}/{SLUG}/">
<link rel="stylesheet" href="../assets/reader.css?v={ASSETS_V}">
</head>
<body>
<a class="skip" href="#text">&rarr;</a>
<header class="bar"><div class="bar-in">
  <a class="brand" href="../"><b data-i18n="libName"></b><small>Misbah Library</small></a>
  <div class="spacer"></div>
  <a class="tbtn" href="../"><svg class="ic" viewBox="0 0 24 24"><path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/></svg><span class="lbl" data-i18n="home"></span></a>
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
  <div class="rule"></div>
  <dl>
    <dt data-i18n="chapters"></dt><dd data-num="{len(chapters)}">{loc_num(len(chapters), "fa")}</dd>
    <dt data-i18n="translator"></dt><dd>{esc(TRANSLATOR_FA)}</dd>
    <dt data-i18n="edition"></dt><dd data-ar="قائمیه" data-fa="قائمیه"
        data-ur="قائمیہ" data-en="Ghaemiyeh"></dd>
  </dl>
  <h2 data-i18n="pickChapter"></h2>
  <div class="suras" data-langpath="{SLUG}">{"".join(cells)}</div>
</main>
<footer class="foot"><div class="foot-in">
  <div><h3 data-i18n="libName"></h3></div>
</div></footer>
<script src="../assets/reader.js?v={ASSETS_V}" defer></script>
</body>
</html>
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("batch")
    ap.add_argument("--out", required=True)
    ap.add_argument("--lang", choices=sorted(LANGS))
    ap.add_argument("--chapter", nargs="*", type=int)
    ap.add_argument("--alts", default="fa")
    ap.add_argument("--index", action="store_true")
    ap.add_argument("--published", default="")
    a = ap.parse_args()

    data = json.loads(pathlib.Path(a.batch).read_text(encoding="utf-8"))
    chapters = data["chapters"]
    out = pathlib.Path(a.out)

    if a.index:
        pub = {int(x) for x in a.published.split(",") if x.strip()}
        out.mkdir(parents=True, exist_ok=True)
        (out / "index.html").write_text(build_index(chapters, pub), encoding="utf-8")
        print(f"cover -> {out}/index.html  ({len(pub)} of {len(chapters)} published)")
        return

    if not a.lang:
        sys.exit("--lang is required unless --index")
    alts = [x.strip() for x in a.alts.split(",") if x.strip()]
    if a.lang not in alts:
        sys.exit(f"--alts must include {a.lang}; hreflang sets are self-referential")

    todo = a.chapter if a.chapter else [c["n"] for c in chapters]
    for c in chapters:
        if c["n"] not in todo:
            continue
        d = out / str(c["n"])
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(
            build_chapter(c, chapters, a.lang, alts), encoding="utf-8")
    print(f"{len(todo)} chapters -> {out}  (lang={a.lang}, alts={alts})")


if __name__ == "__main__":
    main()
