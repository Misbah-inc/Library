#!/usr/bin/env python3
"""Assemble an en/ page for the Misbah Library from extracted + translated content.

Input JSON per page:
  {"page": 50, "total": 231,
   "nodes": [{"i":0,"tag":"p","ar":"...","en":"..."}, ...],
   "notes": [{"id":"fn-0-0-1","n":"١","ar":"...","en":"..."}, ...]}

The shell is reproduced exactly as the existing en/ pages have it, so generated
pages are indistinguishable in structure from pages 1-48 and 81-84.
"""
import html, json, re, sys, pathlib

R = "../../../.."  # depth of en/bihar/1/<page>/ below the Library root


def esc_attr(s):
    return html.escape(s, quote=True)


def description(nodes):
    """First 150 chars of the first English line, matching existing pages."""
    for n in nodes:
        en = re.sub(r"<[^>]+>", "", n.get("en", "")).strip()
        en = html.unescape(en)
        if en:
            return esc_attr(en[:150])
    return ""


def build(page):
    n_, total = page["page"], page.get("total", 231)
    nodes, notes = page["nodes"], page.get("notes", [])

    body = []
    for nd in nodes:
        tag = nd["tag"]
        body.append(f'<{tag} lang="ar" data-i="{nd["i"]}">{nd["ar"]}</{tag}>')
        body.append(f'<{tag} class="tr-line" lang="en">{nd["en"]}</{tag}>')
    body = "".join(body)

    if notes:
        parts = []
        for nt in notes:
            parts.append(
                f'<div class="note" lang="ar" id="{nt["id"]}">'
                f'<span class="note-n">({nt["n"]})</span>'
                f'<span>{nt["ar"]}'
                f'<span class="tr-note-line" lang="en">{nt["en"]}</span>'
                f'</span></div>')
        notes_html = '<div class="notes">' + "".join(parts) + "</div>"
    else:
        notes_html = ""

    prev_n, next_n = n_ - 1, n_ + 1
    link_prev = f'<link rel="prev" href="{R}/en/bihar/1/{prev_n}/">' if prev_n >= 1 else ""
    link_next = f'<link rel="next" href="{R}/en/bihar/1/{next_n}/">' if next_n <= total else ""

    pager_prev = (f'<a class="btn prev" href="{R}/en/bihar/1/{prev_n}/" rel="prev">'
                  f'<span data-i18n="prev"></span></a>') if prev_n >= 1 else \
                 '<span class="btn" aria-disabled="true"><span data-i18n="prev"></span></span>'
    pager_next = (f'<a class="btn next" href="{R}/en/bihar/1/{next_n}/" rel="next">'
                  f'<span data-i18n="next"></span></a>') if next_n <= total else \
                 '<span class="btn" aria-disabled="true"><span data-i18n="next"></span></span>'

    return f'''<!DOCTYPE html>
<html lang="en" dir="ltr" data-root="{R}" data-book="../../.." data-sitelang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bihar al-Anwar — p. {n_}</title>
<meta name="description" content="{description(nodes)}">
<link rel="alternate" hreflang="ar" href="{R}/bihar/1/{n_}/"><link rel="canonical" href="https://misbah-inc.github.io/Library/en/bihar/1/{n_}/"><link rel="alternate" hreflang="fa" href="{R}/fa/bihar/1/{n_}/"><link rel="alternate" hreflang="ur" href="{R}/ur/bihar/1/{n_}/">{link_prev}{link_next}
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
      <div class="part-label"><span data-ar="العلامة محمد باقر المجلسي" data-fa="علامه محمدباقر مجلسی" data-ur="علامہ محمد باقر مجلسی" data-en="Allama Muhammad Baqir al-Majlisi">Allama Muhammad Baqir al-Majlisi</span>
        <span><span data-i18n="volume"></span> <span data-num="1">1</span>
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
      <a class="btn " href="{R}/en/bihar/1/1/" rel="related"><span data-i18n="first"></span></a>{pager_prev}
      <form id="jump" data-tpl="bihar/1/{{p}}/" action="{R}/" method="get">
        <input id="jump-num" name="p" inputmode="numeric" data-i18n-label="page"
               data-num-val="{n_}" value="{n_}">
      </form>
      {pager_next}<a class="btn " href="{R}/en/bihar/1/{total}/" rel="related"><span data-i18n="last"></span></a>
    </nav>
  </article>
</main>
<div id="page-meta" hidden data-alt-ar="{R}/bihar/1/{n_}/" data-alt-fa="{R}/fa/bihar/1/{n_}/" data-alt-ur="{R}/ur/bihar/1/{n_}/" data-slug="bihar" data-pagenum="{n_}"
     data-volume="1" data-pos="{n_ - 1}" data-total="{total}"></div>
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


if __name__ == "__main__":
    data = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    outdir = pathlib.Path(sys.argv[2])
    pages = data if isinstance(data, list) else [data]
    for p in pages:
        d = outdir / f'{p["page"]}-draft'
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(build(p), encoding="utf-8")
        print(f'{d}/index.html  ({len(p["nodes"])} nodes, {len(p.get("notes", []))} notes)')
