#!/usr/bin/env python3
"""Wire the built «الاستبصار» volumes into the site.

    python istibsar_ar_wire.py <dir holding istibsar_v1..4.json>

Same four jobs as the other book wiring scripts: the volume
selector, a volume index per volume, `toc.json`, and the catalogue row.

**The contents comes from the extraction JSON, not from the built pages.**
ablibrary's own table of contents lists every chapter; only some of those
titles are also written inline in the body — 72 of 72 in Tahdhib volume 4, but
23 of Tahdhib volume 6's are absent from the text entirely. The drawer lists
all of them regardless, and each row points at the page where `abl_extract.py`
actually found the title rather than at the page ablibrary's index claimed,
because that index is demonstrably wrong in several volumes.

Arabic only — `data-langs="ar"` on every tile, no `translated` array.
"""

import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

LIB = pathlib.Path(__file__).resolve().parent.parent
AR_DIGITS = "٠١٢٣٤٥٦٧٨٩"
ar_num = lambda n: "".join(AR_DIGITS[int(c)] for c in str(n))
esc = lambda s: (s.replace("&", "&amp;").replace("<", "&lt;")
                 .replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#x27;"))

TITLE = {"ar": "الاستبصار", "fa": "الاستبصار", "ur": "الاستبصار", "en": "Al-Istibsar"}
AUTHOR = {"ar": "شيخ الطائفة أبو جعفر محمد بن الحسن الطوسي",
          "fa": "شیخ الطائفه، ابوجعفر محمد بن حسن طوسی",
          "ur": "شیخ الطائفہ ابوجعفر محمد بن حسن طوسی",
          "en": "Shaykh al-Ta'ifa Abu Ja'far Muhammad b. al-Hasan al-Tusi"}
# Same editor for both of al-Tusi's books, and a different one again from
# al-Kafi and al-Faqih. Do not copy an edition line between these files.
EDITION = {"ar": "تحقيق حسن الموسوي الخرسان، دار الكتب الإسلامية، طهران",
           "fa": "تحقیق حسن الموسوی الخرسان، دار الکتب الإسلامیه، تهران",
           "ur": "تحقیق حسن الموسوی الخرسان، دار الکتب الإسلامیہ، تہران",
           "en": "ed. Hasan al-Musawi al-Khirsan, Dar al-Kutub al-Islamiyya, Tehran"}

ASSETS_V = 9  # frozen — never bump; see the ASSETS_V note in CLAUDE.md


def multi(d, cls=None, tag="span", extra=""):
    """A span carrying all four languages, swapped in place by reader.js."""
    a = " ".join(f'data-{L}="{esc(d[L])}"' for L in ("ar", "fa", "ur", "en"))
    c = f' class="{cls}"' if cls else ""
    return f"<{tag}{c} {a}{extra}>{esc(d['ar'])}</{tag}>"


def chrome(depth):
    """Header, nav drawer and footer. `depth` is how far below the site root."""
    up = "../" * depth
    return dict(
        head=f"""<header class="bar"><div class="bar-in">
  <a class="brand" href="{up}"><b data-i18n="libName"></b><small>Misbah Library</small></a>
  <div class="spacer"></div>
  <a class="tbtn" href="{up}"><svg class="ic" viewBox="0 0 24 24"><path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/></svg><span class="lbl" data-i18n="home"></span></a>
  <button class="tbtn icon-only" id="btn-menu" data-i18n-label="menu">
    <svg class="ic" viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h16"/></svg></button>
  <div class="langs" role="group">
    <button data-lang="ar">ع</button><button data-lang="fa">فا</button>
    <button data-lang="ur">اردو</button><button data-lang="en">EN</button>
  </div>
  <button class="tbtn" id="btn-theme" aria-pressed="false"></button>
</div></header>""",
        foot=f"""<div class="scrim" id="scrim"></div>
<nav class="nav" id="nav" aria-hidden="true">
  <div class="nav-head"><b data-i18n="menu"></b>
    <button id="nav-close" data-i18n-label="close">✕</button></div>
  <ul>
    <li><a href="{up}"><svg class="ic" viewBox="0 0 24 24"><path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/></svg><span data-i18n="home"></span></a></li>
    <li><a href="{up}#continue"><svg class="ic" viewBox="0 0 24 24"><path d="M4 5h7v15H4z"/><path d="M13 5h7v15h-7z"/></svg><span data-i18n="mylib"></span></a></li>
    <li><a href="{up}search/"><svg class="ic" viewBox="0 0 24 24"><circle cx="11" cy="11" r="6.5"/><path d="M16 16l4 4"/></svg><span data-i18n="search"></span></a></li>
    <li><a href="{up}books/"><svg class="ic" viewBox="0 0 24 24"><path d="M4 4h6a3 3 0 013 3v13a3 3 0 00-3-3H4z"/><path d="M20 4h-6a3 3 0 00-3 3v13a3 3 0 013-3h6z"/></svg><span data-i18n="allBooks"></span></a></li>
  </ul>
  <hr>
  <ul>
    <li><a href="{up}about/"><svg class="ic" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/></svg><span data-i18n="about"></span></a></li>
    <li><a href="{up}contact/"><svg class="ic" viewBox="0 0 24 24"><path d="M3 6h18v12H3z"/><path d="M3 7l9 6 9-6"/></svg><span data-i18n="contact"></span></a></li>
  </ul>
</nav>
<footer class="foot"><div class="foot-in">
  <div><h3 data-i18n="libName"></h3></div>
  <div><h3 data-i18n="browse"></h3><ul>
    <li><a href="{up}" data-i18n="home"></a></li>
    <li><a href="{up}books/" data-i18n="allBooks"></a></li>
    <li><a href="{up}search/" data-i18n="search"></a></li>
    <li><a href="{up}about/" data-i18n="about"></a></li>
    <li><a href="{up}contact/" data-i18n="contact"></a></li>
  </ul></div>
</div></footer>
<script src="{up}assets/reader.js?v={ASSETS_V}" defer></script>""")


def page(title, desc, canon, depth, book, main):
    up = "../" * depth
    c = chrome(depth)
    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl" data-root="{up.rstrip('/') or '.'}" data-book="{book}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canon}">
<link rel="alternate" hreflang="ar" href="{canon}">
<link rel="alternate" hreflang="x-default" href="{canon}">
<link rel="stylesheet" href="{up}assets/reader.css?v={ASSETS_V}">
</head>
<body>
{c['head']}
{main}
{c['foot']}
</body>
</html>
"""


# «اشارة» is the export's "a note follows" marker and «هوية الكتاب» is the
# publisher's catalogue record — neither is a chapter. Both are spelled with
# Persian letters in some volumes and Arabic in others, so compare folded.
def fold(s):
    return (s.replace("ی", "ي").replace("ک", "ك").replace("ۀ", "ة")
             .replace("‌", "").strip())


SKIP = {fold(x) for x in ("اشارة", "إشارة", "هوية الكتاب", "الفهرس", "فهرس")}


def chapters(data):
    """Every chapter ablibrary's own table of contents lists.

    Taken from the extraction's `toc`, NOT from the h3 blocks in the pages.
    Only some chapter titles are written inline in ablibrary's body text — all
    72 of Tahdhib volume 4's are, but 23 of volume 6's appear nowhere in the
    text at all. Reading the drawer off the emitted headings would silently
    drop those chapters from the contents of the volumes that need them most.

    `abl_extract.py` has already corrected each row's page to where the title
    was actually found, so `p` points at the text rather than at ablibrary's
    index field, which is wrong in several volumes.
    """
    ids = {p["n"]: p.get("id", str(p["n"])) for p in data["pages"]}
    rows, seen = [], set()
    for t in data.get("toc", []):
        title = t["title"].strip()
        page = t.get("page", "")
        if not title or fold(title) in SKIP:
            continue
        # A row whose title was never located carries ablibrary's page claim,
        # which is demonstrably wrong — «كلمة الناشر» claims page 5 and would
        # label every body page after it. Drop it rather than mislead.
        if t.get("located") is False:
            continue
        n = int(page) if str(page).isdigit() else None
        key = (fold(title), page)
        if key in seen:
            continue
        seen.add(key)
        rows.append({"title": title, "p": n if n is not None else page,
                     "id": ids.get(n, str(page))})
    return [r for r in rows if isinstance(r["p"], int)]


def volume_index(data):
    v = data["volume"]
    ids = [p.get("id", str(p["n"])) for p in data["pages"]]
    numbered = [p for p in data["pages"] if not str(p.get("id", "")).startswith("fm-")]
    notes = sum(len(p["notes"]) for p in data["pages"])
    rows = chapters(data)
    toc = "".join(
        f'<a class="toc-i" href="{r["id"]}/"><span data-num="{r["p"]}">{ar_num(r["p"])}</span>'
        f'<span style="flex:1" data-ar="{esc(r["title"])}">{esc(r["title"])}</span></a>'
        for r in rows)
    main = f"""<main class="cover">
  <p class="crumb"><a href="../" {" ".join(f'data-{L}="{esc(TITLE[L])}"' for L in ("ar","fa","ur","en"))}>{esc(TITLE['ar'])}</a></p>
  <h1><span data-i18n="volume"></span> <span data-num="{v}">{v}</span></h1>
  <p class="by" {" ".join(f'data-{L}="{esc(AUTHOR[L])}"' for L in ("ar","fa","ur","en"))}>{esc(AUTHOR['ar'])}</p>
  <div class="rule"></div>
  <div class="start"><a class="btn solid" href="{ids[0]}/" data-i18n="start"></a>
    <a class="btn" href="../" data-i18n="otherVolumes"></a></div>
  <dl>
    <dt data-i18n="pages"></dt><dd data-num="{len(data['pages'])}">{len(data['pages'])}</dd>
    <dt data-i18n="notes"></dt><dd data-num="{notes}">{notes}</dd>
    <dt data-i18n="edition"></dt><dd {" ".join(f'data-{L}="{esc(EDITION[L])}"' for L in ("ar","fa","ur","en"))}></dd>
  </dl>
  <h2 data-i18n="contents"></h2>
  {toc}
</main>"""
    return page(f"{TITLE['ar']} — المجلد {ar_num(v)}",
                f"{TITLE['ar']} — {AUTHOR['ar']} — المجلد {v}، "
                f"{len(numbered)} صفحة، {EDITION['ar']}",
                f"https://library.misbah-inc.com/istibsar/{v}/", 2, "..", main), len(rows)


def selector(datas):
    tiles = "".join(
        f'<a class="vol" href="{d["volume"]}/" data-vol="{d["volume"]}" data-langs="ar">'
        f'<b data-num="{d["volume"]}">{ar_num(d["volume"])}</b></a>'
        for d in datas)
    pages = sum(len(d["pages"]) for d in datas)
    main = f"""<main class="cover">
  <h1 {" ".join(f'data-{L}="{esc(TITLE[L])}"' for L in ("ar","fa","ur","en"))}>{esc(TITLE['ar'])}</h1>
  <p class="by" {" ".join(f'data-{L}="{esc(AUTHOR[L])}"' for L in ("ar","fa","ur","en"))}>{esc(AUTHOR['ar'])}</p>
  <div class="rule"></div>
  <dl>
    <dt data-i18n="volumes"></dt><dd data-num="{len(datas)}">{len(datas)}</dd>
    <dt data-i18n="published"></dt><dd data-num="{len(datas)}">{len(datas)}</dd>
    <dt data-i18n="pages"></dt><dd data-num="{pages}">{pages}</dd>
    <dt data-i18n="edition"></dt><dd {" ".join(f'data-{L}="{esc(EDITION[L])}"' for L in ("ar","fa","ur","en"))}></dd>
  </dl>
  <h2 data-i18n="pickVolume"></h2>
  <div class="vols">{tiles}</div>
</main>"""
    return page(f"{TITLE['ar']} — {AUTHOR['ar']}",
                f"{TITLE['ar']} — {AUTHOR['ar']}، {len(datas)} مجلدات، "
                f"{pages} صفحة، {EDITION['ar']}",
                "https://library.misbah-inc.com/istibsar/", 1, ".", main)


def main():
    src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1
                       else pathlib.Path(__file__).parent)
    files = [src / f"istibsar_v{v}.json" for v in range(1, 5)]
    missing = [f.name for f in files if not f.exists()]
    if missing:
        sys.exit("missing extraction json: " + ", ".join(missing))
    datas = [json.loads(f.read_text(encoding="utf-8")) for f in files]

    toc = []
    for d in datas:
        v = d["volume"]
        out = LIB / f"istibsar/{v}/index.html"
        html, n = volume_index(d)
        out.write_text(html, encoding="utf-8", newline="")
        for r in chapters(d):
            toc.append({"title": r["title"], "href": f"istibsar/{v}/{r['id']}/",
                        "label": ar_num(r["p"]), "p": r["p"], "vol": v})
        print(f"  istibsar/{v}/index.html   {n} chapters")

    (LIB / "istibsar/index.html").write_text(selector(datas), encoding="utf-8", newline="")
    print(f"  istibsar/index.html       {len(datas)} volume tiles")

    tp = LIB / "istibsar/assets/toc.json"
    tp.write_text(json.dumps(toc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  istibsar/assets/toc.json  {len(toc)} rows")

    cp = LIB / "catalog.json"
    cat = json.loads(cp.read_text(encoding="utf-8"))
    hit = 0
    for b in cat.get("books", []):
        if b.get("slug") == "istibsar":
            b.pop("placeholder", None)
            b["href"] = "istibsar/"
            b["volumes"] = len(datas)
            b["volumesPublished"] = [d["volume"] for d in datas]
            hit += 1
    if hit != 1:
        sys.exit(f"catalog.json: expected exactly one istibsar entry, found {hit}")
    cp.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n",
                  encoding="utf-8")
    print(f"  catalog.json          istibsar published, volumes 1-{len(datas)}")


if __name__ == "__main__":
    main()
