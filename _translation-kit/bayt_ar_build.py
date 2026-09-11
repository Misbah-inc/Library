#!/usr/bin/env python3
"""Build Arabic reading pages and book cover for Bayt al-Ahzan.

Usage:
  bayt_ar_build.py bayt_ar.json --out ../Library/bayt-al-ahzan
    writes reading pages, assets/pages.json, assets/toc.json, index.html

  bayt_ar_build.py bayt_ar.json --pages --out ../Library/bayt-al-ahzan
    writes only assets/pages.json + assets/toc.json

  bayt_ar_build.py bayt_ar.json --cover --out ../Library/bayt-al-ahzan
    writes only index.html (Arabic cover)

  --page N  write only one reading page (for testing)
"""

import argparse, html, json, pathlib, re, sys

# Windows defaults stdout to cp1252 and this script prints Arabic and an
# arrow; without this it dies on its own progress output.
sys.stdout.reconfigure(encoding='utf-8')

SITE  = "https://library.misbah-inc.com"
ASSETS_V = "7"   # bump when reader.css/js change, to break browser caches.
                 # Without it a returning reader keeps a stale stylesheet and
                 # never sees the fix — which is what happened to the Qur'an.
SLUG  = "bayt-al-ahzan"
LANG  = "ar"
TITLE = "بيت الأحزان في مصائب سيدة النسوان"
AUTH  = "الشيخ عباس القمي"
PUB   = "دار الحكمة، قم"

# Chapter starts in the Arabic edition (page number → display title)
CHAPTERS = {
    1:   "المقدمة",
    18:  "الباب الأول — في ولادتها وأسمائها وكناها",
    30:  "الباب الثاني — في فضلها وجلالها وزهدها وعلمها",
    55:  "الباب الثالث — في أخبار السقيفة وما جرى عليها",
    163: "الباب الرابع — في كثرة حزنها وبكائها على أبيها",
}

# Depth for reading pages: /bayt-al-ahzan/<n>/ → R = "../.."
# A translated page sits one level deeper, at /<lang>/bayt-al-ahzan/<n>/.
R = "../.."

# Set from --lang / --tr in main(). The Arabic build is the default and is
# unchanged by any of this; a translated build reuses every part of the same
# template, which is the only way the two stay in step. Bihar learned that the
# hard way — one template, four languages.
LANG = "ar"
TR = {}          # "<page>:<block i>" -> text, and "<page>:n<note>" -> text
DIR = {"ar": "rtl", "fa": "rtl", "ur": "rtl", "en": "ltr"}
TITLES = {"ar": "بيت الأحزان في مصائب سيدة النسوان",
          "en": "The Sorrows of Fatima (Bayt al-Ahzan)",
          "fa": "رنج‌ها و فریادهای فاطمه سلام‌الله‌علیها",
          "ur": "رنج ہا و فریادہای فاطمہ سلام اللہ علیہا"}
PAGEWORD = {"ar": "ص", "fa": "ص", "ur": "ص", "en": "p."}


def tr_of(page_n, key):
    return TR.get(f"{page_n}:{key}", "")

REF = re.compile(r'\[(\d+)\]')


def esc(s):
    return html.escape(s, quote=True)


def abs_url(n=None, lang=None):
    lang = lang or LANG
    pre = "" if lang == "ar" else f"{lang}/"
    base = f"{SITE}/{pre}{SLUG}/"
    return base if n is None else f"{base}{n}/"


def note_html(page):
    if not page['notes']:
        return ''
    def one(note):
        body = (f'<span>{esc(note["ar"])}</span>')
        if LANG != "ar":
            t = tr_of(page["n"], f'n{note["n"]}')
            body += f'<span class="tr-line" lang="{LANG}">{esc(t)}</span>'
        return (f'<div class="note" lang="ar" id="fn-{page["n"]}-{note["n"]}">'
                f'<span class="note-n">({esc(str(note["n"]))})</span>{body}</div>')

    items = ''.join(one(note) for note in page['notes'])
    return f'<div class="notes">{items}</div>'


def body_html(page):
    have = {note['n'] for note in page['notes']}
    parts = []
    for block in page['blocks']:
        def ref_sub(m):
            k = int(m.group(1))
            if k not in have:
                return m.group(0)
            return f'<a class="fnref" href="#fn-{page["n"]}-{k}">{k}</a>'
        ar = REF.sub(ref_sub, esc(block['ar']))
        parts.append(f'<p lang="ar" data-i="{block["i"]}">{ar}</p>')
        if LANG != "ar":
            # Every Arabic block gets a line, even an empty one: verify.py
            # aligns the two lists by position, and a missing line would shift
            # every translation after it onto the wrong Arabic.
            t = tr_of(page["n"], block["i"])
            parts.append(f'<p class="tr-line" lang="{LANG}">{esc(t)}</p>')
    return ''.join(parts)


def excerpt(page):
    t = page['blocks'][0]['ar'] if page['blocks'] else TITLE
    return t[:157].rsplit(' ', 1)[0] + '…' if len(t) > 160 else t


PUB_LANGS = ["ar"]      # languages that actually have pages; set in main()


def tr_bar():
    """The mode switch and the machine-translation badge, exactly as Bihar's
    translated pages carry them — same classes, so the shared CSS and JS apply
    with nothing added. The badge is not optional: readers are told to cite the
    Arabic."""
    if LANG == "ar":
        return ""
    return ('<div class="tr-bar" id="tr-bar">'
            '<div class="tr-modes">'
            '<button data-mode="tr" data-i18n="viewTr" aria-pressed="true"></button>'
            '<button data-mode="both" data-i18n="viewBoth" aria-pressed="false"></button>'
            '<button data-mode="ar" data-i18n="viewAr" aria-pressed="false"></button>'
            '</div>'
            '<span class="tr-note machine">'
            '<svg class="ic" viewBox="0 0 24 24"><path d="M12 3v2M5 8h14v11H5z"/>'
            '<circle cx="9" cy="13" r="1.2"/><circle cx="15" cy="13" r="1.2"/></svg>'
            '<span data-i18n="machineTr"></span></span>'
            '</div>')


def build_reading_page(page, order, idx):
    n = page['n']
    prev_n = order[idx - 1] if idx > 0 else None
    next_n = order[idx + 1] if idx + 1 < len(order) else None
    total  = len(order)

    canonical = f'<link rel="canonical" href="{abs_url(n)}">'
    # Farsi is NOT a translation of this book — it is a different edition
    # (Ishtihardi) living at its own slug, and the two share no pagination, so
    # it is linked at cover level only. Everything else is page-for-page.
    alts = f'<link rel="alternate" hreflang="ar" href="{abs_url(n, "ar")}">'
    for L in PUB_LANGS:
        if L != "ar":
            alts += f'<link rel="alternate" hreflang="{L}" href="{abs_url(n, L)}">'
    alts += (f'<link rel="alternate" hreflang="fa" href="{SITE}/bayt-al-ahzan-fa/">'
             f'<link rel="alternate" hreflang="x-default" href="{abs_url(n, "ar")}">')
    prev_l = f'<link rel="prev" href="{abs_url(prev_n)}">' if prev_n else ''
    next_l = f'<link rel="next" href="{abs_url(next_n)}">' if next_n else ''

    pager_prev = (
        f'<a class="btn prev" href="{abs_url(prev_n)}" rel="prev">'
        f'<span data-i18n="prev"></span></a>'
        if prev_n else
        '<span class="btn" aria-disabled="true"><span data-i18n="prev"></span></span>'
    )
    pager_next = (
        f'<a class="btn next" href="{abs_url(next_n)}" rel="next">'
        f'<span data-i18n="next"></span></a>'
        if next_n else
        '<span class="btn" aria-disabled="true"><span data-i18n="next"></span></span>'
    )

    title_str = f'{TITLES[LANG]} — {PAGEWORD[LANG]} {n}'
    SITELANG = "" if LANG == "ar" else f' data-sitelang="{LANG}"'
    TRSTATIC = "" if LANG == "ar" else ' data-tr-static="1"'
    ALT_AR = "" if LANG == "ar" else f'\n     data-alt-ar="{R}/{SLUG}/{n}/"'
    FA_EDITION = ("../../bayt-al-ahzan-fa/" if LANG == "ar"
                  else f"{R}/bayt-al-ahzan-fa/")
    desc      = esc(excerpt(page))

    return f"""<!DOCTYPE html>
<html lang="{LANG}" dir="{DIR[LANG]}" data-root="{R}" data-book="{R}/{SLUG}"{SITELANG}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title_str)}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{esc(title_str)}">
<meta property="og:description" content="{desc}">
{canonical}{alts}{prev_l}{next_l}
<link rel="stylesheet" href="{R}/assets/reader.css?v={ASSETS_V}">
</head>
<body>
<a class="skip" href="#text">&rarr;</a>
<header class="bar"><div class="bar-in">
  <a class="brand" href="{R}/"><b data-i18n="libName"></b><small>Misbah Library</small></a>
  <div class="spacer"></div>
  <button class="tbtn" id="btn-toc"><svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 6h16M4 12h16M4 18h10"/></svg><span class="lbl" data-i18n="contents"></span></button>
  <button class="tbtn icon-only" id="btn-smaller" aria-label="Smaller text">ا−</button>
  <button class="tbtn icon-only" id="btn-bigger" aria-label="Larger text">ا+</button>
  <a class="tbtn" href="{R}/"><svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/></svg><span class="lbl" data-i18n="home"></span></a>
  <button class="tbtn icon-only" id="btn-menu" aria-label="Menu">
    <svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 7h16M4 12h16M4 17h16"/></svg></button>
  <div class="langs" role="group">
    <button data-lang="ar">ع</button><button data-lang="fa">فا</button><button data-lang="ur">اردو</button><button data-lang="en">EN</button>
  </div>
  <button class="tbtn" id="btn-theme" aria-pressed="false"></button>
</div></header>
<main class="wrap">
  <article>
    <div class="leaf" id="text">
      <div class="part-label"><span>{esc(AUTH)}</span>
        <span class="folio"><span data-i18n="page"></span> <span data-num="{n}">{n}</span></span>
      </div>
      {tr_bar()}<div class="body"{TRSTATIC}>{body_html(page)}</div>
      {note_html(page)}
    </div>
    <nav class="pager">
      <a class="btn" href="{abs_url(order[0])}" rel="related"><span data-i18n="first"></span></a>{pager_prev}
      <form id="jump" data-tpl="{SLUG}/{{p}}/" action="{R}/{SLUG}/" method="get">
        <input id="jump-num" name="p" inputmode="numeric" aria-label="Page"
               data-num-val="{n}" value="{n}">
      </form>
      {pager_next}<a class="btn" href="{abs_url(order[-1])}" rel="related"><span data-i18n="last"></span></a>
    </nav>
  </article>
</main>
<div id="page-meta" hidden{ALT_AR}
     data-alt-fa="{FA_EDITION}"
     data-slug="{SLUG}" data-pagenum="{n}"
     data-pos="{idx}" data-total="{total}"
     data-title-ar="{esc(TITLE)}"
     data-title-fa="رنج‌ها و فریادهای فاطمه سلام‌الله‌علیها"
     data-title-en="The Sorrows of Fatima (Bayt al-Ahzan)"
     data-title-ur="رنج ہا و فریادہای فاطمہ سلام اللہ علیہا"></div>
<div class="scrim" id="scrim"></div>
<aside class="drawer" id="drawer" aria-hidden="true">
  <div class="drawer-head"><h2 id="drawer-title"></h2>
    <button id="drawer-close" aria-label="Close">✕</button></div>
  <div class="drawer-body" id="drawer-body"></div>
</aside>
<nav class="nav" id="nav" aria-hidden="true">
  <div class="nav-head"><b data-i18n="menu"></b>
    <button id="nav-close" aria-label="Close">✕</button></div>
  <ul>
    <li><a href="{R}/"><span data-i18n="home"></span></a></li>
    <li><a href="{R}/{SLUG}/"><span data-i18n="contents"></span></a></li>
    <li><a href="{R}/search/"><span data-i18n="search"></span></a></li>
    <li><a href="{R}/books/"><span data-i18n="allBooks"></span></a></li>
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
<script src="{R}/assets/reader.js?v={ASSETS_V}" defer></script>
</body>
</html>"""


def build_toc_json(data):
    pages  = data['pages']
    nums   = [p['n'] for p in pages]
    starts = {}
    last   = None
    for p in pages:
        if p['n'] in CHAPTERS:
            last = p['n']
        if last is not None:
            starts.setdefault(last, p['n'])

    chapters = []
    chap_list = sorted(CHAPTERS)
    for i, cstart in enumerate(chap_list):
        cend = chap_list[i + 1] - 1 if i + 1 < len(chap_list) else nums[-1]
        first_page = starts.get(cstart, cstart)
        # count pages in this chapter
        count = sum(1 for n in nums if cstart <= n <= cend)
        chapters.append({
            'n':    i + 1,
            'ar':   CHAPTERS[cstart],
            'href': f'{SLUG}/{first_page}/',
            'pages': count,
        })
    return chapters


def build_arabic_cover(data, out_dir):
    pages = data['pages']
    nums  = [p['n'] for p in pages]
    first = nums[0]

    chap_list = sorted(CHAPTERS)
    # Build chapter start-page map (first page that belongs to each chapter)
    page_set = set(nums)
    def first_page_of(cstart):
        for n in range(cstart, cstart + 100):
            if n in page_set:
                return n
        return cstart

    chap_cells = []
    for i, cstart in enumerate(chap_list):
        cend  = chap_list[i + 1] - 1 if i + 1 < len(chap_list) else nums[-1]
        fp    = first_page_of(cstart)
        count = sum(1 for n in nums if cstart <= n <= cend)
        label = CHAPTERS[cstart]
        chap_cells.append(
            f'<a class="chap-cell" href="{fp}/" data-n="{fp}">'
            f'<span class="chap-n">{i+1}</span>'
            f'<span class="chap-title" lang="ar">{esc(label)}</span>'
            f'<span class="chap-pages">{count} ص</span></a>'
        )
    chaps_grid = '\n'.join(chap_cells)

    canonical = f'<link rel="canonical" href="{abs_url()}">'
    alts = (f'<link rel="alternate" hreflang="ar" href="{abs_url()}">'
            f'<link rel="alternate" hreflang="fa" href="{SITE}/bayt-al-ahzan-fa/">'
            f'<link rel="alternate" hreflang="x-default" href="{abs_url()}">')

    html_out = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl" data-root=".." data-book=".">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(TITLE)}</title>
<meta name="description" content="{esc(TITLE)} — {esc(AUTH)} — {esc(PUB)}">
{canonical}{alts}
<link rel="stylesheet" href="../assets/reader.css?v={ASSETS_V}">
</head>
<body class="cover">
<a class="skip" href="#main">&rarr;</a>
<header class="bar"><div class="bar-in">
  <a class="brand" href="../"><b data-i18n="libName"></b><small>Misbah Library</small></a>
  <div class="spacer"></div>
  <a class="tbtn" href="../"><svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/></svg><span class="lbl" data-i18n="home"></span></a>
  <button class="tbtn icon-only" id="btn-menu" aria-label="Menu">
    <svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 7h16M4 12h16M4 17h16"/></svg></button>
  <div class="langs" role="group">
    <button data-lang="ar">ع</button><button data-lang="fa">فا</button><button data-lang="ur">اردو</button><button data-lang="en">EN</button>
  </div>
  <button class="tbtn" id="btn-theme" aria-pressed="false"></button>
</div></header>
<main class="wrap" id="main">
  <div class="cover-hero">
    <p class="by" lang="ar">{esc(AUTH)}</p>
    <h1 class="book-title" lang="ar">{esc(TITLE)}</h1>
    <p class="book-sub" lang="ar">{esc(PUB)}</p>
    <a class="btn start" href="{first}/" data-i18n="startReading"></a>
  </div>
  <section class="chaps" data-langpath="{SLUG}" data-langs="ar,fa">
    {chaps_grid}
  </section>
</main>
<nav class="nav" id="nav" aria-hidden="true">
  <div class="nav-head"><b data-i18n="menu"></b>
    <button id="nav-close" aria-label="Close">✕</button></div>
  <ul>
    <li><a href="../"><span data-i18n="home"></span></a></li>
    <li><a href="../books/"><span data-i18n="allBooks"></span></a></li>
    <li><a href="../search/"><span data-i18n="search"></span></a></li>
  </ul>
</nav>
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
<script src="../assets/reader.js?v={ASSETS_V}" defer></script>
</body>
</html>"""

    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    enc = 'utf-8'
    p = out / 'index.html'
    p.write_text(html_out, encoding=enc)
    print(f'  cover → {p}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('json')
    ap.add_argument('--out',   required=True, help='Output folder (bayt-al-ahzan/)')
    ap.add_argument('--pages', action='store_true', help='Write assets/pages.json + toc.json only')
    ap.add_argument('--cover', action='store_true', help='Write index.html only')
    ap.add_argument('--page',  type=int,            help='Write one reading page only')
    ap.add_argument('--lang',  default='ar', choices=['ar', 'en', 'fa', 'ur'],
                    help='Language of the pages to write. ar is the source of record.')
    ap.add_argument('--tr',    help='Translation JSON for --lang: '
                               '{"<page>:<block>": "...", "<page>:n<note>": "..."}')
    ap.add_argument('--alts',  default='ar',
                    help='Languages that actually HAVE pages, for hreflang. '
                         'Listing one that is not published points the cluster '
                         'at a 404 and invalidates all of it.')
    args = ap.parse_args()

    global LANG, TR, R, PUB_LANGS
    LANG = args.lang
    PUB_LANGS = [x.strip() for x in args.alts.split(',') if x.strip()]
    if LANG not in PUB_LANGS:
        sys.exit(f'--alts must include --lang ({LANG}); hreflang sets are self-referential')
    if LANG != 'ar':
        # /<lang>/bayt-al-ahzan/<n>/ is one level deeper than /bayt-al-ahzan/<n>/
        R = '../../..'
        if not args.tr:
            sys.exit('--tr is required when --lang is not ar')
        TR = {k: v for k, v in
              json.loads(pathlib.Path(args.tr).read_text(encoding='utf-8')).items()}
        print(f'  translation: {len(TR):,} strings for {LANG}')

    data  = json.loads(pathlib.Path(args.json).read_text(encoding='utf-8'))
    pages = data['pages']
    order = [p['n'] for p in pages]

    out_dir = pathlib.Path(args.out)
    enc     = 'utf-8'

    # ── assets ──────────────────────────────────────────────────────────────
    if (args.pages or not (args.cover or args.page)) and LANG == 'ar':
        assets = out_dir / 'assets'
        assets.mkdir(parents=True, exist_ok=True)

        # pages.json
        pj = assets / 'pages.json'
        pj.write_text(json.dumps(order, ensure_ascii=False), encoding=enc)
        print(f'  pages.json → {pj}')

        # toc.json
        toc = build_toc_json(data)
        tj  = assets / 'toc.json'
        tj.write_text(json.dumps(toc, ensure_ascii=False, indent=2), encoding=enc)
        print(f'  toc.json → {tj}  ({len(toc)} chapters)')

    # ── Arabic cover ─────────────────────────────────────────────────────────
    if (args.cover or not (args.pages or args.page)) and LANG == 'ar':
        build_arabic_cover(data, out_dir)

    # ── reading pages ────────────────────────────────────────────────────────
    if args.page:
        idxmap = {p['n']: i for i, p in enumerate(pages)}
        if args.page not in idxmap:
            sys.exit(f'Page {args.page} not found')
        pages_to_build = [(pages[idxmap[args.page]], idxmap[args.page])]
    elif not (args.pages or args.cover):
        pages_to_build = [(p, i) for i, p in enumerate(pages)]
    else:
        pages_to_build = []

    for page, idx in pages_to_build:
        html_out = build_reading_page(page, order, idx)
        page_dir = out_dir / str(page['n'])
        page_dir.mkdir(parents=True, exist_ok=True)
        p = page_dir / 'index.html'
        p.write_text(html_out, encoding=enc)
        if args.page or idx % 20 == 0:
            print(f'  page {page["n"]:3d} → {p}')

    if pages_to_build and not args.page:
        print(f'  {len(pages_to_build)} reading pages written')


if __name__ == '__main__':
    main()
