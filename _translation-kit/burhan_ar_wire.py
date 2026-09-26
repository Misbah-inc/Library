"""Wire «البرهان في تفسير القرآن» into the site: volume selector, volume
indexes, `burhan/assets/toc.json`, and the catalog row.

    python burhan_ar_wire.py <dir holding burhan_v1..5.json>

Unlike `burhan_ar_wire.py`, the contents are read from the HEADINGS IN THE
PAGES, not from a separate table of contents — because this export has them and
ablibrary's does not. That is the whole reason this book comes from Ghaemiyeh:
2,221 headings against ablibrary's zero. Every row's page is therefore true by
construction, since the row IS the heading on that page.

Two levels are kept apart and both matter. `h3` is the surah division
(«سورة البقرة مدنية», «المستدرك (سورة آل عمران)»); `h4` is the verse group
inside it («سورة البقرة(2): آية 195»). Volume 5 alone has 72 surah headings
because it carries the short surahs من الدخان إلى الناس, while volume 1 covers
only الفاتحة والبقرة وآل عمران — so a volume with few `h3` rows is the book's
own shape, not a fault.
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

TITLE = {"ar": "البرهان في تفسير القرآن", "fa": "البرهان في تفسير القرآن",
         "ur": "البرہان فی تفسیر القرآن", "en": "Al-Burhan fi Tafsir al-Qur'an"}
AUTHOR = {"ar": "السيد هاشم بن سليمان الحسيني البحراني",
          "fa": "سید هاشم بن سلیمان حسینی بحرانی",
          "ur": "سید ہاشم بن سلیمان حسینی بحرانی",
          "en": "Sayyid Hashim b. Sulayman al-Husayni al-Bahrani"}
EDITION = {"ar": "تحقيق قسم الدراسات الإسلامية، مؤسسة البعثة، قم",
           "fa": "تحقیق قسم الدراسات الإسلامیه، مؤسسه البعثه، قم",
           "ur": "تحقیق قسم الدراسات الإسلامیہ، مؤسسہ البعثہ، قم",
           "en": "ed. Qism al-Dirasat al-Islamiyya, Mu'assasat al-Bi'tha, Qum"}

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
    """Contents rows, read off the h3/h4 headings the export actually carries.

    A row's page is true by construction — the row IS a heading on that page —
    so nothing here has to trust an external index the way التهذيب does.
    """
    rows, seen = [], set()
    for p in data["pages"]:
        for b in p["blocks"]:
            if b["tag"] not in ("h3", "h4"):
                continue
            t = b["ar"].strip()
            f = fold(t)
            if not f or f in SKIP:
                continue
            if (f, p["n"]) in seen:
                continue
            seen.add((f, p["n"]))
            rows.append({"title": t, "p": p["n"],
                         "id": str(p.get("id", p["n"])), "lvl": b["tag"]})
    return rows


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
                f"https://library.misbah-inc.com/burhan/{v}/", 2, "..", main), len(rows)


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
                "https://library.misbah-inc.com/burhan/", 1, ".", main)


def main():
    src = pathlib.Path(sys.argv[1] if len(sys.argv) > 1
                       else pathlib.Path(__file__).parent)
    files = [src / f"burhan_v{v}.json" for v in range(1, 6)]
    missing = [f.name for f in files if not f.exists()]
    if missing:
        sys.exit("missing extraction json: " + ", ".join(missing))
    datas = [json.loads(f.read_text(encoding="utf-8")) for f in files]

    toc = []
    for d in datas:
        v = d["volume"]
        out = LIB / f"burhan/{v}/index.html"
        html, n = volume_index(d)
        out.write_text(html, encoding="utf-8", newline="")
        for r in chapters(d):
            toc.append({"title": r["title"], "href": f"burhan/{v}/{r['id']}/",
                        "label": ar_num(r["p"]), "p": r["p"], "vol": v,
                        "lvl": r["lvl"]})
        print(f"  burhan/{v}/index.html   {n} chapters")

    (LIB / "burhan/index.html").write_text(selector(datas), encoding="utf-8", newline="")
    print(f"  burhan/index.html       {len(datas)} volume tiles")

    tp = LIB / "burhan/assets/toc.json"
    tp.write_text(json.dumps(toc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  burhan/assets/toc.json  {len(toc)} rows")

    cp = LIB / "catalog.json"
    cat = json.loads(cp.read_text(encoding="utf-8"))
    hit = 0
    for b in cat.get("books", []):
        if b.get("slug") == "burhan":
            b.pop("placeholder", None)
            b["href"] = "burhan/"
            b["volumes"] = len(datas)
            b["volumesPublished"] = [d["volume"] for d in datas]
            # DERIVED, never typed. The home page's counter reads this and
            # nothing checks it: Bihar's said 231 — volume 1 alone — while
            # the site served about 49,000, for as long as it took someone
            # to notice. See the note under al-Kafi in CLAUDE.md.
            b["pages"] = sum(len(d["pages"]) for d in datas)
            hit += 1
    if hit != 1:
        sys.exit(f"catalog.json: expected exactly one burhan entry, found {hit}")
    cp.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n",
                  encoding="utf-8")
    print(f"  catalog.json          burhan published, volumes 1-{len(datas)}")


if __name__ == "__main__":
    main()
