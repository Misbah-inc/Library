#!/usr/bin/env python3
"""Build مفاتیح الجنان from mafatih.json.

    mafatih_build.py mafatih.json --out ../mafatih

URL shape — the owner chose item pagination over printed-page pagination:

    /mafatih/                 cover: the book's own أبواب as browse tiles
    /mafatih/dua-kumayl/      a named piece
    /mafatih/137/             everything else, numbered in document order

One page is ONE PIECE — a duʿā, a ziyarat, a chapter — whole, top to bottom.
The printed edition's 1,871 page breaks are not page breaks here; they are
rendered inline as «ص ۱۶۵» markers, the way جامع المقدمات shows them. That
keeps citation exact without ever interrupting a supplication: a reader
reciting دعای کمیل never has to press Next in the middle of it, which
printed-page pagination would force six times.

Two doors, one text. The cover is the app-style browse (categories →
subcategories → pieces); prev/next chains every page in the book's own order
so it can also be read straight through. Both address the same pages, so
there is no second URL space to keep in sync.

Slugs: the 26 famous pieces get their Latin alias, everything else gets its
ordinal. A numeric slug can never collide with a Latin one. These are
navigation only — translations key to the frozen UNIT ids, not to URLs, so
renumbering a page can never re-point a translation.

Language: Arabic text with حسین انصاریان's Persian beneath it, the pairing the
export gives explicitly. data-standalone="1" as on Bayt al-Ahzan and جامع
المقدمات — the book lives at its own top-level slug, not under /fa/, so
reader.js must not prefix its links. English and Urdu land later as a data
drop keyed to unit ids; nothing here has to move for that.
"""
import argparse, html, json, pathlib, re, sys

sys.stdout.reconfigure(encoding="utf-8")

HERE = pathlib.Path(__file__).parent
SITE = "https://library.misbah-inc.com"
SLUG = "mafatih"
ASSETS_V = "7"          # in step with the rest of the tree
FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"

TITLE_FA = "مفاتیح الجنان"
AUTHOR_FA = "شیخ عبّاس قمی"
TRANSLATOR_FA = "ترجمهٔ حسین انصاریان"


def loc(n):
    return "".join(FA_DIGITS[int(c)] if c.isdigit() else c for c in str(n))


def esc(s):
    return html.escape(str(s), quote=True)


def page_url(slug):
    return f"{SITE}/{SLUG}/{slug}/"


# --------------------------------------------------------------- the page set

def collect(root):
    """Every titled section, in document order, with its depth and parent.

    A section with no text of its own is still a page: it is the book's own
    section heading, and it carries the list of what sits under it, which is
    what makes browsing work. Reading straight through passes over it exactly
    as a reader passes a section title in print."""
    out = []

    def walk(node, depth, parent):
        for c in node["children"]:
            if c.get("title") is None:
                walk(c, depth, parent)
                continue
            rec = {"node": c, "depth": depth, "parent": parent,
                   "title": c["title"], "id": c.get("id"),
                   "slug_named": c.get("slug"),
                   "text": has_text(c), "children": []}
            if parent is not None:
                parent["children"].append(rec)
            out.append(rec)
            walk(c, depth + 1, rec)

    walk(root, 0, None)
    return out


def has_text(node):
    return any(u["k"] in ("ar", "note") for u in node["units"])


def assign_slugs(pages):
    # the category slugs are reserved so a numbered page can never take one
    taken, n = set(c["id"] for c in CATEGORIES), 0
    for p in pages:
        if p["slug_named"]:
            p["slug"] = p["slug_named"]
            taken.add(p["slug"])
    for p in pages:
        if not p.get("slug"):
            n += 1
            while str(n) in taken:
                n += 1
            p["slug"] = str(n)
            taken.add(p["slug"])
    return pages


# ------------------------------------------------------------- categories

# TWO different ways into the same book, which is the point.
#
# «شروع خواندن» follows the edition's own order, cover to cover. That order is
# the author's and is not touched.
#
# These CATEGORIES are the other way in — how a reader actually arrives: they
# want a ziyarat, or today's اعمال, or a mustahabb prayer. That is not how the
# book is bound; ادعیه is split across four أبواب and the weekly acts sit
# inside باب اول. So the mapping below is editorial, matched on section title
# rather than position so that re-running the extractor cannot silently
# re-point it. A section may appear under two categories — اعمال هفته belongs
# to both اعمال and ادعیه — exactly as it does in print.

CATEGORIES = [
    {"id": "amal", "name": "اعمال", "sub": "اعمال روز و شب، هفته، ماه و مناسبات",
     "icon": "M12 3l2.4 5 5.6.8-4 3.9 1 5.5L12 15.6 6.9 18.2l1-5.5-4-3.9L9.6 8z",
     "titles": ["فصل سوم: دعاهای ایام هفته نقل از ملحقات صحیفه سجادیه",
                "فصل چهارم: فضیلت و اعمام شب و روز جُمعه",
                "فصل پنجم: زیارات معصومین (عَلَيهِم السَّلَامُ) در ایام هفته",
                "باب اول: اعمال شب و روز",
                "باب دوم: اعمال سال"]},
    {"id": "ziyarat", "name": "زیارت", "sub": "زیارات معصومین، اولیاء و عتبات",
     "icon": "M12 2l7 4v6c0 4.4-3 8.3-7 10-4-1.7-7-5.6-7-10V6z",
     "titles": ["باب سوم: زیارات"]},
    {"id": "namaz", "name": "نماز", "sub": "نمازهای مستحبی و تعقیبات",
     "icon": "M4 20h16M6 20V9l6-5 6 5v11M10 20v-5h4v5",
     "titles": ["باب دوم: نمازهای مستحبه",
                "فصل اول: تعقیبات مشترک",
                "فصل دوم: تعقیبات هر یک از نماز ها",
                "نمازهای ایام هفته"]},
    {"id": "adiya", "name": "ادعیه", "sub": "دعاهای مشهور، احراز و عوذات",
     "icon": "M8 21c0-4 1.5-6 4-6s4 2 4 6M9 3v6a3 3 0 0 0 6 0V3",
     "titles": ["باب اول: ادعیه",
                "باب سوم: ادعیه وعوذات آلام و اسقام",
                "باب چهارم: ادعیه منتخبه از کتاب کافی",
                "باب پنجم: ذکر بعض احراز و ادعیه موجزه",
                "فهرست ملحقات مفاتیح الجنان"]},
    {"id": "quran", "name": "قرآن", "sub": "سوره‌های برگزیده و خواص آیات",
     "icon": "M4 5a2 2 0 0 1 2-2h12v18H6a2 2 0 0 1-2-2zM8 3v18",
     "titles": ["سوره های قرآن در مفاتیح الجنان",
                "باب ششم:خواص بعضی سوره و آیات وغیره"]},
]


def resolve_categories(pages):
    """Bind each category to real pages, and say loudly if a title stops
    matching — a silently empty category is worse than a build failure."""
    # matched on the FOLDED title: these titles carry honorifics whose exact
    # diacritics are impossible to retype reliably, and a single wrong mark
    # would silently empty a category
    by_title = {}
    for p in pages:
        by_title.setdefault(foldtxt(p["title"]), p)
    out, missing = [], []
    for c in CATEGORIES:
        items = []
        for t in c["titles"]:
            p = by_title.get(foldtxt(t))
            if p is None:
                missing.append(t); continue
            items.append(p)
        out.append(dict(c, items=items))
    return out, missing


# ------------------------------------------------------------------ rendering

def body_html(node):
    """Arabic with its Persian beneath, Qummi's instructions as prose, and the
    printed page numbers inline rather than as breaks.

    ONE PAIRING MAY SPAN TWO UNITS. Where the print edition breaks a phrase
    across a page, the export splits it in two and hangs the footnote — the
    whole phrase's translation — on the SECOND half. Rendered naively the first
    half appears untranslated, which is how the opening of مناجات ششم came to
    sit on the page with nothing under it. 41 of the 72 untranslated units are
    this, including one split at «وَ كُلَّ / شَيْءٍ أَحْصَيْنَاهُ».

    They are joined here, at render time, and deliberately NOT in the data:
    merging units would renumber every unit id after them in the section, and
    those ids are frozen because English and Urdu will be keyed to them. Each
    half keeps its own id and stays independently linkable.
    """
    rows, i, us = [], 0, node["units"]

    def page_mark(u):
        return (f'<div class="folio-mark" aria-hidden="true">'
                f'<span>ص {loc(u["n"])}</span></div>')

    while i < len(us):
        u = us[i]
        if u["k"] == "page":
            rows.append(page_mark(u)); i += 1; continue
        if u["k"] == "note":
            rows.append(f'<p class="rub" lang="fa">{esc(u["fa"])}</p>'); i += 1; continue

        if u.get("rub"):
            rows.append(f'<p class="rub" lang="fa">{esc(u["rub"])}</p>')

        tr = (u.get("tr") or {}).get("fa", "")
        parts = [u]
        j = i + 1
        if not tr:
            # look past any page markers for the half that carries the footnote
            between, k = [], j
            while k < len(us) and us[k]["k"] == "page":
                between.append(us[k]); k += 1
            if k < len(us) and us[k]["k"] == "ar" and not us[k].get("rub")                and (us[k].get("tr") or {}).get("fa"):
                parts.append(("page", between))
                parts.append(us[k])
                tr = (us[k]["tr"] or {}).get("fa", "")
                j = k + 1

        inner = ""
        for part in parts:
            if isinstance(part, tuple):
                inner += "".join(page_mark(p) for p in part[1])
                continue
            cls = "unit mixed" if part.get("mixed") else "unit"
            inner += (f'<p class="u-ar" lang="ar" id="u-{esc(part["id"])}" '
                      f'data-p="{part.get("p","")}">{esc(part["ar"])}</p>')
        if tr:
            inner += f'<p class="u-tr" lang="fa">{esc(tr)}</p>'
        # the id lives on the paragraph, not the wrapper: a joined pairing has
        # two Arabic halves and each must stay independently addressable, and
        # two elements cannot share one id
        cls = "unit mixed" if u.get("mixed") else "unit"
        rows.append(f'<div class="{cls}" data-p="{u.get("p","")}">{inner}</div>')
        i = j

    return "".join(rows)


def child_list(rec, pages_by_id):
    if not rec["children"]:
        return ""
    li = []
    for c in rec["children"]:
        n_ar = sum(1 for u in c["node"]["units"] if u["k"] == "ar")
        meta = f'<span class="ch-n">{loc(n_ar)} بند</span>' if n_ar else ""
        trail, q = [], c["parent"]
        while q is not None:
            trail.append(q["title"] or ""); q = q["parent"]
        day, eve = weekday_of(c["title"], trail)
        attr = (f' data-weekday="{day}"' + (' data-eve="1"' if eve else "")) if day is not None else ""
        li.append(f'<li{attr}><a href="../{esc(c["slug"])}/">'
                  f'<span>{esc(c["title"])}</span>{meta}</a></li>')
    return f'<ul class="sec-list">{"".join(li)}</ul>'


HEAD_BAR = '''<header class="bar"><div class="bar-in">
  <a class="brand" href="{R}/"><b data-i18n="libName"></b><small>Misbah Library</small></a>
  <div class="spacer"></div>
  <button class="tbtn" id="btn-msearch"><svg class="ic" viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg><span class="lbl" data-i18n="search"></span></button>
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
</div></header>'''

TAIL = '''<div class="scrim" id="scrim"></div>
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


# ------------------------------------------------------- اعمال ایام هفته

# JS getDay() numbering, so the client needs no table: 0 Sunday … 6 Saturday.
# Longest first — یکشنبه, سه شنبه and پنجشنبه all END in شنبه, so a naive scan
# labels every one of them Saturday.
WEEKDAYS = [("پنجشنبه", 4), ("پنج شنبه", 4), ("چهارشنبه", 3), ("چهار شنبه", 3),
            ("سه شنبه", 2), ("سه‌شنبه", 2), ("دوشنبه", 1), ("دو شنبه", 1),
            ("یکشنبه", 0), ("یک شنبه", 0), ("شنبه", 6),
            ("جمعه", 5), ("جُمعه", 5)]

# The observance is weekly only in these settings. Without the gate «سوره
# جُمعه» — a sura of the Qur'an — becomes a Friday devotion, and «نماز روز یک
# شنبه» under ذی القعده becomes a weekly one when it belongs to that month.
WEEKLY_CTX = ("ایام هفته", "شب و روز جُمعه", "نمازهای مستحبه")


def weekday_of(title, trail):
    """(day, is_eve) or (None, False).

    is_eve marks a «شب» section. The Islamic day begins at maghrib, so
    «اعمال شب جُمعه» is Thursday evening, not Friday's — it has to surface a
    day EARLIER than its name says, which is the whole reason this is tracked
    separately rather than folded into the day number."""
    t = title or ""
    if "سوره" in t:                       # سوره جُمعه is not a Friday devotion
        return None, False
    ctx = " ".join([t] + list(trail))
    if not any(k in ctx for k in WEEKLY_CTX):
        return None, False
    for word, day in WEEKDAYS:
        if word in t:
            return day, ("شب" in t)
    return None, False


def quran_note(rec, R):
    """Mafātīḥ carries only the handful of suras Qummi selected. A reader who
    lands here looking for a sura the book does not include should be told
    where the whole Qur'an is rather than concluding the library lacks it."""
    KEY = "سوره های قرآن"
    here = rec["title"] or ""
    up = (rec["parent"]["title"] or "") if rec["parent"] else ""
    # the section itself, and the suras directly under it — not every page that
    # happens to say «سوره», which would put it on خواص سوره قَدر and friends
    if KEY not in here and KEY not in up:
        return ""
    return ('<p class="xbook-note">این بخش تنها سوره‌های برگزیدهٔ مفاتیح است. '
            f'<a href="{R}/quran/">متن کامل قرآن کریم با ترجمه ←</a></p>')


def view_bar(node):
    """Arabic / Persian / both. Only where there is actually a pairing to
    toggle — a section of pure Persian rubric has nothing to switch off."""
    if not any(u["k"] == "ar" and (u.get("tr") or {}).get("fa")
               for u in node["units"]):
        return ""
    return ('<div class="view-bar" role="group">'
            '<button class="vbtn" data-view="both" aria-pressed="true" data-i18n="viewBoth"></button>'
            '<button class="vbtn" data-view="ar" aria-pressed="false" data-i18n="viewAr"></button>'
            '<button class="vbtn" data-view="tr" aria-pressed="false" data-i18n="viewTr"></button>'
            '</div>')


def build_page(rec, order, idx, pages_by_id):
    R = "../.."
    slug = rec["slug"]
    node = rec["node"]
    prev = order[idx - 1] if idx > 0 else None
    nxt = order[idx + 1] if idx + 1 < len(order) else None

    def rel(p):
        return f'../{esc(p["slug"])}/'

    prev_l = f'<link rel="prev" href="{page_url(prev["slug"])}">' if prev else ""
    next_l = f'<link rel="next" href="{page_url(nxt["slug"])}">' if nxt else ""
    pager_prev = (f'<a class="btn prev" href="{rel(prev)}" rel="prev">'
                  f'<span data-i18n="prev"></span></a>') if prev else \
        '<span class="btn" aria-disabled="true"><span data-i18n="prev"></span></span>'
    pager_next = (f'<a class="btn next" href="{rel(nxt)}" rel="next">'
                  f'<span data-i18n="next"></span></a>') if nxt else \
        '<span class="btn" aria-disabled="true"><span data-i18n="next"></span></span>'

    trail = []
    p = rec["parent"]
    while p is not None:
        trail.append(p)
        p = p["parent"]
    trail.reverse()
    crumb = " · ".join(f'<a href="{rel(t)}">{esc(t["title"])}</a>' for t in trail)

    first_p = next((u.get("p") for u in node["units"] if u.get("p")), None)
    title = f'{rec["title"]} — {TITLE_FA}'
    plain = re.sub(r"\s+", " ", " ".join(
        (u.get("rub") or "") + " " + (u.get("fa") or (u.get("tr") or {}).get("fa", ""))
        for u in node["units"]))[:180].strip()
    desc = esc(f'{rec["title"]} — {TITLE_FA}، {AUTHOR_FA}. {plain}'[:300])

    cite = f'{TITLE_FA}، {rec["title"]}' + (f'، ص {loc(first_p)}' if first_p else "") + '.'

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
<link rel="canonical" href="{page_url(slug)}">
<link rel="alternate" hreflang="fa" href="{page_url(slug)}">
<link rel="alternate" hreflang="x-default" href="{page_url(slug)}">{prev_l}{next_l}
<link rel="stylesheet" href="{R}/assets/reader.css?v={ASSETS_V}">
</head>
<body>
<a class="skip" href="#text">&rarr;</a>
{HEAD_BAR.format(R=R)}
<main class="wrap">
  <article>
    <div class="leaf" id="text">
      <div class="part-label">
        <span class="crumb">{crumb or f'<a href="{R}/{SLUG}/">{esc(TITLE_FA)}</a>'}</span>
        {f'<span class="folio"><span data-i18n="page"></span> <span>{loc(first_p)}</span></span>' if first_p else ''}
      </div>
      <h1 class="piece-title">{esc(rec["title"])}</h1>
      {quran_note(rec, R)}
      {view_bar(node)}
      <div class="body mafatih" data-tr-static="1">{body_html(node)}</div>
      {child_list(rec, pages_by_id)}
    </div>
    <nav class="pager">
      <a class="btn" href="{rel(order[0])}" rel="related"><span data-i18n="first"></span></a>{pager_prev}
      {pager_next}<a class="btn" href="{rel(order[-1])}" rel="related"><span data-i18n="last"></span></a>
    </nav>
    <p class="cite" id="cite-text" data-cite-ar="{esc(cite)}" data-cite-fa="{esc(cite)}"
       data-cite-ur="{esc(cite)}" data-cite-en="{esc(cite)}">
      <span data-i18n="citation"></span>:
      <button class="btn-cite" id="btn-cite" data-i18n="cite"></button></p>
  </article>
</main>
<div id="page-meta" hidden data-slug="{SLUG}" data-piece="{esc(slug)}"></div>
{TAIL.format(R=R, SLUG=SLUG)}
<script src="{R}/assets/reader.js?v={ASSETS_V}" defer></script>
<script src="{R}/{SLUG}/assets/mafatih.js?v={ASSETS_V}" defer></script>
</body>
</html>
'''


def category_page(cat, order):
    """One category: the sections mapped into it, as cards.

    Deliberately one level only. A reader picking «زیارت» wants the handful of
    divisions under it, not 15 sections x their children flattened into 200
    links — the tap that follows is what narrows it. That is also how the
    printed book and the apps present it.
    """
    R = "../.."
    # When a category is one section — زیارت is all of باب سوم — that single
    # card is not a choice. Its children are the level the reader wants, and
    # they are the four divisions the printed book itself offers. Categories
    # that already map to several sections are left at that level.
    items = cat["items"]
    if len(items) == 1 and items[0]["children"]:
        items = items[0]["children"]
    cards = []
    for it in items:
        kids = len(it["children"])
        n = kids or sum(1 for u in it["node"]["units"] if u["k"] == "ar")
        unit = "بخش" if kids else "بند"
        cards.append(
            '<a class="mcat-card" href="../' + esc(it["slug"]) + '/">'
            '<span class="mcat-t">' + esc(it["title"]) + '</span>'
            '<span class="mcat-n">' + loc(n) + ' ' + unit + '</span></a>')
    desc = esc(cat["name"] + " — " + cat["sub"] + ". " + TITLE_FA + "، " + AUTHOR_FA + ".")
    url = SITE + "/" + SLUG + "/" + cat["id"] + "/"
    title = esc(cat["name"]) + " — " + esc(TITLE_FA)
    return (
        '<!DOCTYPE html>\n'
        '<html lang="fa" dir="rtl" data-root="' + R + '" data-book=".." '
        'data-sitelang="fa" data-standalone="1" data-srclang="fa">\n'
        '<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<title>' + title + '</title>\n'
        '<meta name="description" content="' + desc + '">\n'
        '<meta property="og:title" content="' + title + '">\n'
        '<meta property="og:description" content="' + desc + '">\n'
        '<link rel="canonical" href="' + url + '">\n'
        '<link rel="alternate" hreflang="fa" href="' + url + '">\n'
        '<link rel="alternate" hreflang="x-default" href="' + url + '">\n'
        '<link rel="stylesheet" href="' + R + '/assets/reader.css?v=' + ASSETS_V + '">\n'
        '</head>\n<body>\n'
        '<a class="skip" href="#text">&rarr;</a>\n'
        + HEAD_BAR.format(R=R) +
        '\n<main class="cover mcat" id="text">\n'
        '  <p class="mcat-up"><a href="../">' + esc(TITLE_FA) + '</a></p>\n'
        '  <h1>' + esc(cat["name"]) + '</h1>\n'
        '  <div class="rule"></div>\n'
        '  <p class="book-credit">' + esc(cat["sub"]) + '</p>\n'
        '  <div class="mcat-grid">' + "".join(cards) + '</div>\n'
        '</main>\n'
        '<div id="page-meta" hidden data-slug="' + SLUG + '"></div>\n'
        + TAIL.format(R=R, SLUG=SLUG) +
        '\n<script src="' + R + '/assets/reader.js?v=' + ASSETS_V + '" defer></script>\n'
        '<script src="' + R + '/' + SLUG + '/assets/mafatih.js?v=' + ASSETS_V + '" defer></script>\n'
        '</body>\n</html>\n')


# ---------------------------------------------------------------------- cover

def cover(cats, order):
    """The landing page is a chooser, not a table of contents.

    The book's own order lives behind «شروع خواندن» and in the contents
    drawer; nobody arriving at Mafatih is looking for «باب پنجم». They want a
    ziyarat, a mustahabb prayer, or today's acts — so the page leads with those
    five, then with what today actually is, and keeps the linear edition as a
    quiet second door.
    """
    R = ".."
    tiles = []
    for c in cats:
        tiles.append(
            '<a class="mtile" href="' + esc(c["id"]) + '/">'
            '<span class="mtile-ic" aria-hidden="true">'
            '<svg viewBox="0 0 24 24"><path d="' + c["icon"] + '"/></svg></span>'
            '<span class="mtile-t">' + esc(c["name"]) + '</span>'
            '<span class="mtile-s">' + esc(c["sub"]) + '</span></a>')
    desc = esc(TITLE_FA + " — " + AUTHOR_FA
               + ". مجموعهٔ ادعیه، زیارات و اعمال، با " + TRANSLATOR_FA + ".")
    home = SITE + "/" + SLUG + "/"
    return (
        '<!DOCTYPE html>\n'
        '<html lang="fa" dir="rtl" data-root="' + R + '" data-book="." '
        'data-sitelang="fa" data-standalone="1" data-srclang="fa">\n'
        '<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<title>' + esc(TITLE_FA) + '</title>\n'
        '<meta name="description" content="' + desc + '">\n'
        '<meta property="og:title" content="' + esc(TITLE_FA) + '">\n'
        '<meta property="og:description" content="' + desc + '">\n'
        '<link rel="canonical" href="' + home + '">\n'
        '<link rel="alternate" hreflang="fa" href="' + home + '">\n'
        '<link rel="alternate" hreflang="x-default" href="' + home + '">\n'
        '<link rel="stylesheet" href="' + R + '/assets/reader.css?v=' + ASSETS_V + '">\n'
        '</head>\n<body>\n'
        '<a class="skip" href="#text">&rarr;</a>\n'
        + HEAD_BAR.format(R=R) +
        '\n<main class="mhome" id="text">\n'
        '  <header class="mhero">\n'
        '    <h1>' + esc(TITLE_FA) + '</h1>\n'
        '    <p class="mhero-by">' + esc(AUTHOR_FA) + ' <span>·</span> '
        + esc(TRANSLATOR_FA) + '</p>\n'
        '    <div class="mhero-search">\n'
        '      <svg class="mhero-ic" viewBox="0 0 24 24" aria-hidden="true">'
        '<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>\n'
        '      <input id="mcover-q" type="search" autocomplete="off" spellcheck="false" '
        'placeholder="نام دعا، زیارت یا جمله‌ای از متن…" aria-label="جستجو در مفاتیح">\n'
        '      <button class="btn solid" id="mcover-go" type="button">جستجو</button>\n'
        '    </div>\n'
        '    <p class="mhero-hint">مثال: «دعای کمیل» · «اعمال ماه رمضان» · «من لی غیرک»</p>\n'
        '  </header>\n'
        '  <nav class="mtiles" aria-label="بخش‌ها">' + "".join(tiles) + '</nav>\n'
        '  <section id="mweek" class="mweek" hidden></section>\n'
        '  <section class="mread">\n'
        '    <div><h2>خواندن پیوستهٔ کتاب</h2>\n'
        '    <p>متن کامل، به ترتیب خودِ کتاب، از آغاز تا پایان.</p></div>\n'
        '    <a class="btn solid" href="' + esc(order[0]["slug"]) + '/">شروع خواندن</a>\n'
        '  </section>\n'
        '</main>\n'
        '<div id="page-meta" hidden data-slug="' + SLUG + '"></div>\n'
        + TAIL.format(R=R, SLUG=SLUG) +
        '\n<script src="' + R + '/assets/reader.js?v=' + ASSETS_V + '" defer></script>\n'
        '<script src="' + R + '/' + SLUG + '/assets/mafatih.js?v=' + ASSETS_V + '" defer></script>\n'
        '</body>\n</html>\n')


# ------------------------------------------------------------------- search

FOLD_MAP = {"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
            "ى": "ی", "ي": "ی", "ك": "ک", "ة": "ه",
            "ؤ": "و", "ئ": "ی"}
DROP_RE = re.compile("[\u0610-\u061A\u064B-\u0652\u0670\u06D6-\u06ED\u0640\u200c]")
FA_AR_DIGITS = {ord(c): str(i) for i, c in enumerate("۰۱۲۳۴۵۶۷۸۹")}
FA_AR_DIGITS.update({ord(c): str(i) for i, c in enumerate("٠١٢٣٤٥٦٧٨٩")})


def foldtxt(t):
    """The same normalisation reader.js does, plus ZWNJ and digits.

    Everything a reader types differs from what the edition prints: they type
    ی where the text has ي, ک for ك, and no diacritics at all. Without this a
    search for the opening of دعای کمیل finds nothing, which is the single
    most likely thing anyone will search for."""
    t = DROP_RE.sub("", t.translate(FA_AR_DIGITS))
    return re.sub(r"\s+", " ", "".join(FOLD_MAP.get(c, c) for c in t)).strip().lower()


def build_search(pages, out):
    """Two indexes, because there are two kinds of search.

    NAMES are what someone reaches for first, and there are only 689 of them,
    so that index is small enough to answer as the reader types. TEXT is the
    half-remembered line: 4,073 Arabic units plus their Persian, fetched only
    when a name search has not already answered the question."""
    titles, body = [], []
    for p in pages:
        trail, q = [], p["parent"]
        while q is not None:
            trail.append(q["title"] or "")
            q = q["parent"]
        trail.reverse()
        first = next((u.get("p") for u in p["node"]["units"] if u.get("p")), None)
        n_ar = sum(1 for u in p["node"]["units"] if u["k"] == "ar")
        n_note = sum(1 for u in p["node"]["units"] if u["k"] == "note")
        # 92 sections are titled «إشارَة:» — headings that say nothing. The
        # زیارت اربعین is one of them: its title is useless, but its opening
        # line names it exactly. Indexing that line as an alias is what lets a
        # search by name find the section that actually holds it.
        opener = ""
        for u in p["node"]["units"]:
            t = u.get("rub") or (u.get("fa") if u["k"] == "note" else "")
            if t:
                opener = t[:140]
                break
        row = {"s": p["slug"], "t": p["title"], "f": foldtxt(p["title"]),
               "b": " · ".join(trail[1:]) if len(trail) > 1 else "",
               "p": first, "n": n_ar, "x": n_note, "c": len(p["children"])}
        if opener:
            row["h"] = foldtxt(opener)
            row["hd"] = opener[:90]
        titles.append(row)
        # rows are arrays, not objects: 5,750 repetitions of five key names is
        # a quarter of a megabyte of nothing. [slug, unitId, arabic, persian, page]
        for u in p["node"]["units"]:
            if u["k"] == "ar":
                fa = (u.get("tr") or {}).get("fa", "")
                rub = u.get("rub", "")
                body.append([p["slug"], u["id"], u["ar"],
                             (rub + " ⟨ " + fa) if rub and fa else (rub or fa),
                             u.get("p")])
            elif u["k"] == "note":
                body.append([p["slug"], "", "", u["fa"], u.get("p")])
    a = out / "assets"
    a.mkdir(exist_ok=True)
    (a / "search-titles.json").write_text(
        json.dumps(titles, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (a / "search-body.json").write_text(
        json.dumps(body, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return len(titles), len(body)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", nargs="?", default=str(HERE / "mafatih.json"))
    ap.add_argument("--out", default=str(HERE.parent / SLUG))
    a = ap.parse_args()

    root = json.loads(pathlib.Path(a.src).read_text(encoding="utf-8"))
    pages = assign_slugs(collect(root))
    by_id = {p["id"]: p for p in pages if p["id"]}
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    for i, rec in enumerate(pages):
        d = out / rec["slug"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(build_page(rec, pages, i, by_id),
                                      encoding="utf-8")

    # the cover's tiles are the book's own top-level divisions
    cats, missing = resolve_categories(pages)
    if missing:
        raise SystemExit("category titles no longer match the book: " + repr(missing))
    for c in cats:
        d = out / c["id"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(category_page(c, pages), encoding="utf-8")

    (out / "index.html").write_text(cover(cats, pages), encoding="utf-8")

    # contents drawer: reader.js fetches <book>/assets/toc.json
    (out / "assets").mkdir(exist_ok=True)
    # reader.js reads title / href / p, and href is resolved against the site
    # root, not the page. p is the printed page the piece opens on, which is
    # what makes the drawer usable as an index of the physical edition.
    toc = []
    for p in pages:
        first = next((u.get("p") for u in p["node"]["units"] if u.get("p")), None)
        toc.append({"title": ("— " * (p["depth"] - 1)) + p["title"],
                    "href": f'{SLUG}/{p["slug"]}/', "p": first})
    (out / "assets" / "toc.json").write_text(
        json.dumps(toc, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8")

    nt, nb = build_search(pages, out)

    # اعمال هفته: what belongs to each day of the week
    week = []
    for p in pages:
        trail, q = [], p["parent"]
        while q is not None:
            trail.append(q["title"] or ""); q = q["parent"]
        day, eve = weekday_of(p["title"], trail)
        if day is None:
            continue
        n_ar = sum(1 for u in p["node"]["units"] if u["k"] == "ar")
        if not n_ar:
            continue
        week.append({"d": day, "e": 1 if eve else 0, "s": p["slug"],
                     "t": p["title"], "g": trail[0] if trail else "", "n": n_ar})
    (out / "assets" / "weekday.json").write_text(
        json.dumps(week, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    print(f"pages written : {len(pages):,}  (+ cover)")
    print(f"search index  : {nt:,} names, {nb:,} text rows")
    print(f"weekday map   : {len(week)} observances across "
          f"{len(set(w['d'] for w in week))} days"
          f" ({sum(1 for w in week if w['e'])} of them شب)")
    print(f"  with text   : {sum(1 for p in pages if p['text']):,}")
    print(f"  named slugs : {sum(1 for p in pages if p['slug_named'])}")
    print(f"  categories  : {len(cats)} landing pages, "
          f"{sum(len(c['items']) for c in cats)} sections mapped")
    print(f"-> {out}")


if __name__ == "__main__":
    main()
