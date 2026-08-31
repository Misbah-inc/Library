#!/usr/bin/env python3
"""Build Qur'an surah pages for the Misbah Library.

  quran_build.py --lang ar --out <dir> [--surah 1 2 ...] [--alts ar,en,fa,ur]

Structure mirrors the rest of the library so the shared reader, the hreflang
machinery and gen_sitemap.py all work unchanged:

  /quran/<surah>/           Arabic
  /<lang>/quran/<surah>/    Arabic + that language's translation(s)

Each ayah is wrapped in <div class="aya" id="a<n>"> so /quran/2/#a255 is a
stable deep link that works in every view mode. The wrapper is never hidden;
only the Arabic line and the translation lines inside it are toggled.

Bismillah has three cases, verified against the Tanzil text:
  * surah 1  - the basmala IS ayah 1, so it is numbered like any verse
  * surah 9  - has none
  * others   - not part of ayah 1, so it is rendered as an unnumbered heading
Note 27:30 contains the basmala inside a numbered verse; that is left alone.

Attribution is mandatory, not decorative: the Arabic text is Tanzil's under
CC BY 3.0, and Tanzil's translation terms require a link back when more than
three translations are used. Both are emitted on every page.
"""
import argparse, html, os, pathlib, re, sys
import xml.etree.ElementTree as ET

SITE = "https://library.misbah-inc.com"
SRC = pathlib.Path(__file__).parent / "quran-source"

# translations available per language; a language may carry more than one
TRANSLATIONS = {
    "en": [{"id": "shakir", "file": "en.shakir.xml",
            "name": "Shakir", "translator": "Mohammad Habib Shakir"}],
    "fa": [{"id": "fooladvand", "file": "fa.fooladvand.xml",
            "name": "فولادوند", "translator": "Mohammad Mahdi Fooladvand"}],
    "ur": [{"id": "jawadi", "file": "ur.jawadi.xml",
            "name": "علامہ جوادی", "translator": "Syed Zeeshan Haider Jawadi"}],
}

LANGS = {
    "ar": {"dir": "rtl", "title": "القرآن الكريم", "depth": "../.."},
    "en": {"dir": "ltr", "title": "The Holy Qur'an", "depth": "../../.."},
    "fa": {"dir": "rtl", "title": "قرآن کریم", "depth": "../../.."},
    "ur": {"dir": "rtl", "title": "قرآنِ کریم", "depth": "../../.."},
}

AR_DIGITS = "٠١٢٣٤٥٦٧٨٩"          # Arabic-Indic
FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"          # Eastern Arabic-Indic, used by Persian and Urdu
DIGITS = {"ar": AR_DIGITS, "fa": FA_DIGITS, "ur": FA_DIGITS}


def ar_num(n):
    return "".join(AR_DIGITS[int(d)] for d in str(n))


def loc_num(n, lang):
    d = DIGITS.get(lang)
    return "".join(d[int(c)] for c in str(n)) if d else str(n)


def describe(m, ayas, lang):
    """The meta description is static, so it cannot be filled by the reader at
    runtime — it has to be written in the page's own language here, or every
    Arabic page turns up in search results with an English summary."""
    meccan = (m["type"] == "Meccan")
    if lang == "ar":
        return (f'سورة {m["name"]} — {"مكية" if meccan else "مدنية"}، '
                f'{loc_num(ayas, "ar")} آية.')
    if lang == "fa":
        return (f'سورهٔ {m["name"]} — {"مکی" if meccan else "مدنی"}، '
                f'{loc_num(ayas, "fa")} آیه.')
    if lang == "ur":
        return (f'سورہ {m["name"]} — {"مکی" if meccan else "مدنی"}، '
                f'{loc_num(ayas, "ur")} آیات۔')
    return f'{m["tname"]} ({m["ename"]}) — {m["type"]}, {ayas} ayat.'


def load(path):
    raw = pathlib.Path(path).read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    # Tanzil translation headers contain '--' inside an XML comment, which is
    # illegal; strip comment blocks before parsing.
    return ET.fromstring(re.sub(r"<!--.*?-->", "", raw, flags=re.S))


def read_text(root):
    out = {}
    for s in root.findall(".//sura"):
        si = int(s.get("index"))
        out[si] = {int(a.get("index")): a.get("text") for a in s.findall("aya")}
    return out


def read_meta(root):
    suras = {}
    for s in root.findall(".//sura"):
        suras[int(s.get("index"))] = {
            "ayas": int(s.get("ayas")), "name": s.get("name"),
            "tname": s.get("tname"), "ename": s.get("ename"),
            "type": s.get("type"), "order": int(s.get("order")),
        }
    juz = [(int(j.get("index")), int(j.get("sura")), int(j.get("aya")))
           for j in root.findall(".//juz")]
    sajda = {(int(x.get("sura")), int(x.get("aya"))): x.get("type")
             for x in root.findall(".//sajda")}
    return suras, juz, sajda


def esc(s):
    return html.escape(s, quote=True)


def abs_url(lang, n):
    pre = "" if lang == "ar" else f"/{lang}"
    return f"{SITE}{pre}/quran/{n}/"


def build(n, lang, meta, ar_text, translations, alts, total=114):
    L = LANGS[lang]
    R = L["depth"]
    m = meta[n]
    ayas = m["ayas"]
    is_ar = (lang == "ar")

    # ---- body -------------------------------------------------------------
    parts = []
    if n != 1 and n != 9:
        parts.append(f'<p class="bismillah" lang="ar">{BASMALA}</p>')

    for a in range(1, ayas + 1):
        rows = [f'<p lang="ar" data-i="{a-1}">{ar_text[n][a]}'
                f'<span class="aya-n">۝{ar_num(a)}</span></p>']
        for t in translations:
            rows.append(
                f'<p class="tr-line" lang="{lang}" data-tr="{t["id"]}">'
                f'<span class="aya-b">{a}</span>{t["text"][n][a]}</p>')
        parts.append(f'<div class="aya" id="a{a}">' + "".join(rows) + "</div>")
    body = "".join(parts)

    # ---- head -------------------------------------------------------------
    canonical = f'<link rel="canonical" href="{abs_url(lang, n)}">'
    alt_links = "".join(
        f'<link rel="alternate" hreflang="{a}" href="{abs_url(a, n)}">' for a in alts)
    if "ar" in alts:
        alt_links += (f'<link rel="alternate" hreflang="x-default" '
                      f'href="{abs_url("ar", n)}">')
    link_prev = f'<link rel="prev" href="{R}/{"" if is_ar else lang + "/"}quran/{n-1}/">' if n > 1 else ""
    link_next = f'<link rel="next" href="{R}/{"" if is_ar else lang + "/"}quran/{n+1}/">' if n < total else ""

    seg = "" if is_ar else lang + "/"
    pager_prev = (f'<a class="btn prev" href="{R}/{seg}quran/{n-1}/" rel="prev">'
                  f'<span data-i18n="prev"></span></a>') if n > 1 else \
                 '<span class="btn" aria-disabled="true"><span data-i18n="prev"></span></span>'
    pager_next = (f'<a class="btn next" href="{R}/{seg}quran/{n+1}/" rel="next">'
                  f'<span data-i18n="next"></span></a>') if n < total else \
                 '<span class="btn" aria-disabled="true"><span data-i18n="next"></span></span>'

    alt_attrs = " ".join(
        f'data-alt-{a}="{R}{"" if a == "ar" else "/" + a}/quran/{n}/"'
        for a in alts if a != lang)

    # translation view controls only exist where there is a translation
    if translations:
        tr_bar = ('<div class="tr-bar" id="tr-bar"><div class="tr-modes">'
                  '<button data-mode="tr" data-i18n="viewTr" aria-pressed="true"></button>'
                  '<button data-mode="both" data-i18n="viewBoth" aria-pressed="false"></button>'
                  '<button data-mode="side" data-i18n="viewSide" aria-pressed="false"></button>'
                  '<button data-mode="ar" data-i18n="viewAr" aria-pressed="false"></button>'
                  '</div><span class="tr-who">'
                  + " · ".join(esc(t["translator"]) for t in translations)
                  + '</span></div>')
    else:
        tr_bar = ""

    title = f'{m["name"]} — {L["title"]}' if not is_ar else f'{m["name"]} — القرآن الكريم'
    desc = esc(describe(m, ayas, lang))

    # The surah name is an Arabic proper noun and stays Arabic in every
    # language. The Latin transliteration and the English gloss are only
    # meaningful to an English reader, so they appear on that page alone.
    meta_bits = []
    if lang == "en":
        meta_bits.append(esc(m["tname"]))
        meta_bits.append(esc(m["ename"]))
    meta_bits.append(f'<span data-i18n="{"meccan" if m["type"] == "Meccan" else "medinan"}"></span>')
    meta_bits.append(f'<span data-num="{ayas}">{ayas}</span> '
                     f'<span data-i18n="ayat"></span>')
    sura_meta = " · ".join(meta_bits)

    # verse picker: reader.js wires the jump; the options are static so the
    # control works before any script runs
    opts = "".join(f'<option value="{i}">{i}</option>' for i in range(1, ayas + 1))
    vpick = (f'<span class="vpick"><span class="lbl" data-i18n="verse"></span>'
             f'<select id="vsel" data-i18n-label="verse">{opts}</select></span>')

    credit = (f'<p class="cite quran-credit">'
              f'<span data-i18n="textFrom"></span> '
              f'<a href="https://tanzil.net" rel="noopener">Tanzil Project</a>'
              + (f' · <span data-i18n="transFrom"></span> '
                 f'<a href="https://tanzil.net/trans/" rel="noopener">tanzil.net/trans</a>'
                 if translations else "")
              + '</p>')

    return f'''<!DOCTYPE html>
<html lang="{lang}" dir="{L["dir"]}" data-root="{R}" data-book=".." data-sitelang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{desc}">
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
      <div class="part-label"><span class="sura-name">{m["name"]}</span>
        <span class="sura-meta">{sura_meta}</span></div>
      {tr_bar}
      <div class="body" data-tr-static="1" data-unit="aya">{body}</div>
      {credit}
    </div>
    <nav class="pager">
      <a class="btn " href="{R}/{seg}quran/1/" rel="related"><span data-i18n="first"></span></a>{pager_prev}
      <form id="jump" data-tpl="quran/{{p}}/" action="{R}/" method="get">
        <input id="jump-num" name="p" inputmode="numeric" data-i18n-label="surah"
               data-num-val="{n}" value="{n}">
      </form>
      {pager_next}<a class="btn " href="{R}/{seg}quran/{total}/" rel="related"><span data-i18n="last"></span></a>
    </nav>
    <nav class="vnav">{vpick}</nav>
  </article>
</main>
<div id="page-meta" hidden {alt_attrs} data-slug="quran" data-pagenum="{n}"
     data-surah="{n}" data-ayas="{ayas}" data-pos="{n-1}" data-total="{total}"></div>
<div class="scrim" id="scrim"></div>
<nav class="nav" id="nav" aria-hidden="true">
  <div class="nav-head"><b data-i18n="menu"></b>
    <button id="nav-close" data-i18n-label="close">✕</button></div>
  <ul>
    <li><a href="{R}/"><svg class="ic" viewBox="0 0 24 24"><path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/></svg><span data-i18n="home"></span></a></li>
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


def build_index(meta, published, total=114):
    """The book cover at /quran/. Like /bihar/, there is ONE cover for every
    language: the strings carry data-ar/fa/ur/en and the reader swaps them,
    so this page must never hardcode a single language."""
    cells = []
    for n in range(1, total + 1):
        m = meta[n]
        inner = (f'<b class="sn" data-num="{n}">{ar_num(n)}</b>'
                 f'<span class="snm">{m["name"]}</span>'
                 f'<span class="sct"><span data-num="{m["ayas"]}">{ar_num(m["ayas"])}</span> '
                 f'<span data-i18n="ayat"></span></span>')
        if n in published:
            cells.append(f'<a class="sura-cell" href="{n}/" data-n="{n}">{inner}</a>')
        else:
            cells.append(f'<span class="sura-cell off" data-n="{n}">{inner}</span>')

    return f'''<!DOCTYPE html>
<html lang="ar" dir="rtl" data-root=".." data-book=".">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>القرآن الكريم</title>
<meta name="description" content="القرآن الكريم — {ar_num(total)} سورة، مع الترجمة.">
<link rel="canonical" href="{SITE}/quran/">
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
  <h1 data-ar="القرآن الكريم" data-fa="قرآن کریم" data-ur="قرآنِ کریم"
      data-en="The Holy Qur&#x27;an">القرآن الكريم</h1>
  <p class="by" data-ar="كلام الله تعالى" data-fa="کلام الله تعالی"
     data-ur="کلامِ اللہ تعالیٰ" data-en="The Word of God">كلام الله تعالى</p>
  <div class="rule"></div>
  <dl>
    <dt data-i18n="surahs"></dt><dd data-num="{total}">{ar_num(total)}</dd>
    <dt data-i18n="published"></dt><dd data-num="{len(published)}">{ar_num(len(published))}</dd>
    <dt data-i18n="edition"></dt><dd data-ar="مشروع تنزيل" data-fa="پروژهٔ تنزیل"
        data-ur="تنزیل پروجیکٹ" data-en="Tanzil Project"></dd>
  </dl>
  <h2 data-i18n="pickSurah"></h2>
  <div class="suras" data-langpath="quran">{"".join(cells)}</div>
  <p class="note-msg" data-i18n="volsNote"></p>
</main>
<div class="scrim" id="scrim"></div>
<nav class="nav" id="nav" aria-hidden="true">
  <div class="nav-head"><b data-i18n="menu"></b>
    <button id="nav-close" data-i18n-label="close">✕</button></div>
  <ul>
    <li><a href="../"><span data-i18n="home"></span></a></li>
    <li><a href="../search/"><span data-i18n="search"></span></a></li>
    <li><a href="../books/"><span data-i18n="allBooks"></span></a></li>
  </ul>
</nav>
<footer class="foot"><div class="foot-in">
  <div><h3 data-i18n="libName"></h3></div>
</div></footer>
<script src="../assets/reader.js" defer></script>
</body>
</html>
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", required=True, choices=sorted(LANGS))
    ap.add_argument("--out", required=True)
    ap.add_argument("--surah", nargs="*", type=int)
    ap.add_argument("--alts", default="ar,en,fa,ur")
    ap.add_argument("--src", default=str(SRC))
    ap.add_argument("--index", action="store_true",
                    help="build the book cover at /quran/index.html instead of surah pages")
    ap.add_argument("--published", default="",
                    help="comma-separated surahs that are live; the rest render "
                         "as placeholders on the cover, as unpublished Bihar volumes do")
    a = ap.parse_args()

    src = pathlib.Path(a.src)
    alts = [x.strip() for x in a.alts.split(",") if x.strip()]
    if a.lang not in alts:
        sys.exit(f"--alts must include {a.lang}; hreflang sets are self-referential")

    meta, juz, sajda = read_meta(load(src / "quran-data.xml"))
    ar_text = read_text(load(src / "quran-uthmani.xml"))

    global BASMALA
    BASMALA = ar_text[1][1]        # canonical basmala, from the same source

    if a.index:
        published = {int(x) for x in a.published.split(",") if x.strip()}
        out = pathlib.Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "index.html").write_text(build_index(meta, published), encoding="utf-8")
        print(f"cover -> {out}/index.html  ({len(published)} of 114 published)")
        return

    translations = []
    for t in TRANSLATIONS.get(a.lang, []):
        t = dict(t)
        t["text"] = read_text(load(src / t["file"]))
        translations.append(t)

    todo = a.surah if a.surah else range(1, 115)
    out = pathlib.Path(a.out)
    for n in todo:
        d = out / str(n)
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(
            build(n, a.lang, meta, ar_text, translations, alts), encoding="utf-8")
    print(f"{len(list(todo))} surah pages -> {out}  (lang={a.lang}, "
          f"translations={[t['id'] for t in translations] or 'none'})")


if __name__ == "__main__":
    main()
