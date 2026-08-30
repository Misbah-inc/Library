#!/usr/bin/env python3
"""Assemble a translated page (en / fa / ur) for the Misbah Library.

Input JSON per page:
  {"page": 50, "total": 231,
   "nodes": [{"i":0,"tag":"p","ar":"...","<lang>":"..."}, ...],
   "notes": [{"id":"fn-0-0-1","n":"١","ar":"...","<lang>":"..."}, ...]}

Usage:
  build.py <batch.json> <outdir> --lang ur [--volume 1] [--total 231]
                                [--alts ar,en,fa,ur] [--no-draft]

The shell is reproduced exactly as the live pages have it, so generated pages
are indistinguishable in structure from the hand-made ones.

Two rules this file exists to enforce, because getting them wrong is invisible
until search engines quietly ignore the whole site:

  * canonical and hreflang URLs are ABSOLUTE. Google requires fully-qualified
    URLs for hreflang; relative ones are discarded.
  * the hreflang set is RECIPROCAL and SELF-REFERENTIAL. Every page in a
    language cluster lists every version including itself, and every one of
    those pages must point back. A one-directional cluster is ignored wholesale.

--alts declares which language versions actually exist for this volume. Never
list a language whose pages have not been published: an hreflang pointing at a
404 invalidates the cluster.
"""
import argparse, html, json, re, sys, pathlib

SITE = "https://library.misbah-inc.com"
R = "../../../.."          # depth of <lang>/bihar/<vol>/<page>/ below the Library root

LANGS = {
    "en": {"dir": "ltr",
           "title": "Bihar al-Anwar",
           "label": "Allama Muhammad Baqir al-Majlisi"},
    "fa": {"dir": "rtl",
           "title": "بحار الأنوار الجامعة لدرر أخبار الأئمة الأطهار",
           "label": "علامه محمدباقر مجلسی"},
    "ur": {"dir": "rtl",
           "title": "بحار الأنوار الجامعة لدرر أخبار الأئمة الأطهار",
           "label": "علامہ محمد باقر مجلسی"},
}

# the part-label carries every language's name as data-* so the switcher can
# swap it in place; only the visible text differs per page language
LABELS = ('data-ar="العلامة محمد باقر المجلسي" data-fa="علامه محمدباقر مجلسی" '
          'data-ur="علامہ محمد باقر مجلسی" data-en="Allama Muhammad Baqir al-Majlisi"')


def esc_attr(s):
    return html.escape(s, quote=True)


def abs_url(lang, vol, n):
    """Fully-qualified URL of a page. Arabic is the site root; others nest."""
    prefix = "" if lang == "ar" else f"/{lang}"
    return f"{SITE}{prefix}/bihar/{vol}/{n}/"


def description(nodes, lang):
    """First 150 chars of the first translated line, matching existing pages."""
    for n in nodes:
        t = re.sub(r"<[^>]+>", "", n.get(lang, "")).strip()
        t = html.unescape(t)
        if t:
            return esc_attr(t[:150])
    return ""


def build(page, lang, vol, total, alts):
    n_ = page["page"]
    nodes, notes = page["nodes"], page.get("notes", [])
    L = LANGS[lang]

    body = []
    for nd in nodes:
        tag = nd["tag"]
        body.append(f'<{tag} lang="ar" data-i="{nd["i"]}">{nd["ar"]}</{tag}>')
        body.append(f'<{tag} class="tr-line" lang="{lang}">{nd[lang]}</{tag}>')
    body = "".join(body)

    if notes:
        parts = []
        for nt in notes:
            parts.append(
                f'<div class="note" lang="ar" id="{nt["id"]}">'
                f'<span class="note-n">({nt["n"]})</span>'
                f'<span>{nt["ar"]}'
                f'<span class="tr-note-line" lang="{lang}">{nt[lang]}</span>'
                f'</span></div>')
        notes_html = '<div class="notes">' + "".join(parts) + "</div>"
    else:
        notes_html = ""

    # ---- absolute canonical + full reciprocal hreflang set -------------------
    canonical = f'<link rel="canonical" href="{abs_url(lang, vol, n_)}">'
    alt_links = "".join(
        f'<link rel="alternate" hreflang="{a}" href="{abs_url(a, vol, n_)}">'
        for a in alts)
    if "ar" in alts:   # Arabic is the source of record, so it is the default
        alt_links += (f'<link rel="alternate" hreflang="x-default" '
                      f'href="{abs_url("ar", vol, n_)}">')

    prev_n, next_n = n_ - 1, n_ + 1
    link_prev = f'<link rel="prev" href="{R}/{lang}/bihar/{vol}/{prev_n}/">' if prev_n >= 1 else ""
    link_next = f'<link rel="next" href="{R}/{lang}/bihar/{vol}/{next_n}/">' if next_n <= total else ""

    pager_prev = (f'<a class="btn prev" href="{R}/{lang}/bihar/{vol}/{prev_n}/" rel="prev">'
                  f'<span data-i18n="prev"></span></a>') if prev_n >= 1 else \
                 '<span class="btn" aria-disabled="true"><span data-i18n="prev"></span></span>'
    pager_next = (f'<a class="btn next" href="{R}/{lang}/bihar/{vol}/{next_n}/" rel="next">'
                  f'<span data-i18n="next"></span></a>') if next_n <= total else \
                 '<span class="btn" aria-disabled="true"><span data-i18n="next"></span></span>'

    # #page-meta drives the language switcher: data-alt-<lang> makes the button
    # navigate to the real translated URL instead of re-rendering in place
    alt_attrs = " ".join(f'data-alt-{a}="{R}{"" if a == "ar" else "/" + a}/bihar/{vol}/{n_}/"'
                         for a in alts if a != lang)

    return f'''<!DOCTYPE html>
<html lang="{lang}" dir="{L["dir"]}" data-root="{R}" data-book="../../.." data-sitelang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{L["title"]} — p. {n_}</title>
<meta name="description" content="{description(nodes, lang)}">
{canonical}{alt_links}{link_prev}{link_next}
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
      <div class="part-label"><span {LABELS}>{L["label"]}</span>
        <span><span data-i18n="volume"></span> <span data-num="{vol}">{vol}</span>
        <span class="folio"><span data-i18n="page"></span>
        <span data-num="{n_}">{n_}</span></span></span></div>
      <div class="tr-bar" id="tr-bar">
        <div class="tr-modes">
          <button data-mode="tr" data-i18n="viewTr" aria-pressed="true"></button>
          <button data-mode="both" data-i18n="viewBoth" aria-pressed="false"></button>
          <button data-mode="ar" data-i18n="viewAr" aria-pressed="false"></button>
        </div>
        <span class="tr-note machine">
          <svg class="ic" viewBox="0 0 24 24"><path d="M12 3v2M5 8h14v11H5z"/>
          <circle cx="9" cy="13" r="1.2"/><circle cx="15" cy="13" r="1.2"/></svg>
          <span data-i18n="machineTr"></span></span>
      </div>
      <div class="body" data-tr-static="1">{body}</div>
      {notes_html}
    </div>
    <nav class="pager">
      <a class="btn " href="{R}/{lang}/bihar/{vol}/1/" rel="related"><span data-i18n="first"></span></a>{pager_prev}
      <form id="jump" data-tpl="bihar/{vol}/{{p}}/" action="{R}/" method="get">
        <input id="jump-num" name="p" inputmode="numeric" data-i18n-label="page"
               data-num-val="{n_}" value="{n_}">
      </form>
      {pager_next}<a class="btn " href="{R}/{lang}/bihar/{vol}/{total}/" rel="related"><span data-i18n="last"></span></a>
    </nav>
  </article>
</main>
<div id="page-meta" hidden {alt_attrs} data-slug="bihar" data-pagenum="{n_}"
     data-volume="{vol}" data-pos="{n_ - 1}" data-total="{total}"></div>
<div class="scrim" id="scrim"></div>
<nav class="nav" id="nav" aria-hidden="true">
  <div class="nav-head"><b data-i18n="menu"></b>
    <button id="nav-close" data-i18n-label="close">✕</button></div>
  <ul>
    <li><a href="{R}/"><svg class="ic" viewBox="0 0 24 24"><path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/></svg><span data-i18n="home"></span></a></li>
    <li><a href="{R}/#continue"><svg class="ic" viewBox="0 0 24 24"><path d="M4 5h7v15H4z"/><path d="M13 5h7v15h-7z"/></svg><span data-i18n="mylib"></span></a></li>
    <li><a href="{R}/search/"><svg class="ic" viewBox="0 0 24 24"><circle cx="11" cy="11" r="6.5"/><path d="M16 16l4 4"/></svg><span data-i18n="search"></span></a></li>
    <li><a href="{R}/books/"><svg class="ic" viewBox="0 0 24 24"><path d="M4 4h6a3 3 0 013 3v13a3 3 0 00-3-3H4z"/><path d="M20 4h-6a3 3 0 00-3 3v13a3 3 0 013-3h6z"/></svg><span data-i18n="allBooks"></span></a></li>
  </ul>
  <hr>
  <ul>
    <li><a href="{R}/about/"><svg class="ic" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/></svg><span data-i18n="about"></span></a></li>
    <li><a href="{R}/contact/"><svg class="ic" viewBox="0 0 24 24"><path d="M3 6h18v12H3z"/><path d="M3 7l9 6 9-6"/></svg><span data-i18n="contact"></span></a></li>
  </ul>
</nav>
<footer class="foot"><div class="foot-in">
  <div><h3 data-i18n="libName"></h3></div>
  <div><h3 data-i18n="browse"></h3><ul>
    <li><a href="{R}/" data-i18n="home"></a></li>
    <li><a href="{R}/books/" data-i18n="allBooks"></a></li>
    <li><a href="{R}/search/" data-i18n="search"></a></li>
    <li><a href="{R}/about/" data-i18n="about"></a></li>
    <li><a href="{R}/contact/" data-i18n="contact"></a></li>
  </ul></div>
</div></footer>
<script src="{R}/assets/reader.js" defer></script>
</body>
</html>
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("batch")
    ap.add_argument("outdir")
    ap.add_argument("--lang", required=True, choices=sorted(LANGS))
    ap.add_argument("--volume", type=int, default=1)
    ap.add_argument("--total", type=int, default=None,
                    help="pages in the volume; defaults to each page's own 'total'")
    ap.add_argument("--alts", default="ar,en,fa,ur",
                    help="language versions that EXIST for this volume. Listing one "
                         "that is not published yet points hreflang at a 404 and "
                         "invalidates the whole cluster.")
    ap.add_argument("--no-draft", action="store_true",
                    help="write <n>/ instead of <n>-draft/")
    a = ap.parse_args()

    alts = [x.strip() for x in a.alts.split(",") if x.strip()]
    for x in alts:
        if x not in ("ar", "en", "fa", "ur"):
            sys.exit(f"unknown language in --alts: {x}")
    if a.lang not in alts:
        sys.exit(f"--alts must include the page's own language ({a.lang}); "
                 "hreflang sets are self-referential")

    data = json.loads(pathlib.Path(a.batch).read_text(encoding="utf-8"))
    outdir = pathlib.Path(a.outdir)
    pages = data if isinstance(data, list) else [data]

    for p in pages:
        total = a.total if a.total is not None else p.get("total", 231)
        name = f'{p["page"]}' if a.no_draft else f'{p["page"]}-draft'
        d = outdir / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(
            build(p, a.lang, a.volume, total, alts), encoding="utf-8")
        print(f'{d}/index.html  ({len(p["nodes"])} nodes, '
              f'{len(p.get("notes", []))} notes)')


if __name__ == "__main__":
    main()
