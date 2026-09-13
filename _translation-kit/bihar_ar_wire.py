#!/usr/bin/env python3
"""Wire newly built Bihar volumes into the site.

    python bihar_ar_wire.py bihar_v2.json bihar_v3.json

Does the four things a new volume needs beyond its reading pages:

  1. the volume's own index page at bihar/<v>/index.html
  2. its chapters appended to bihar/assets/toc.json
  3. its tile switched on in all four bihar/index.html volume selectors
  4. catalog.json's volumesPublished

A volume with no translation carries `data-langs="ar"` on its selector tile.
reader.js keeps such a tile pointing at the Arabic tree instead of rewriting it
to /<lang>/bihar/<v>/, which nobody has built — the same guard `.chaps` uses.
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


def chapters(data):
    """Chapter rows: the h3/h4 headings, skipping the volume and record titles."""
    rows, seen = [], set()
    for p in data["pages"]:
        for b in p["blocks"]:
            if b["tag"] not in ("h3", "h4"):
                continue
            t = b["ar"].strip()
            if not t or t.startswith("بحار الأنوار الجامعة") or t == "هوية الكتاب":
                continue
            if (t, p["n"]) in seen:
                continue
            seen.add((t, p["n"]))
            rows.append({"title": t, "p": p["n"]})
    return rows


def volume_index(data, tpl):
    v = data["volume"]
    pages = [p["n"] for p in data["pages"]]
    notes = sum(len(p["notes"]) for p in data["pages"])
    rows = chapters(data)
    toc = "".join(
        f'<a class="toc-i" href="{r["p"]}/"><span data-num="{r["p"]}">{ar_num(r["p"])}</span>'
        f'<span style="flex:1" data-ar="{esc(r["title"])}">{esc(r["title"])}</span></a>'
        for r in rows)

    s = tpl
    s = s.replace('data-num="1">1</span>', f'data-num="{v}">{v}</span>', 1)
    s = re.sub(r'<a class="btn solid" href="\d+/"',
               f'<a class="btn solid" href="{pages[0]}/"', s, count=1)
    s = re.sub(r'(<dt data-i18n="pages"></dt><dd data-num=")\d+(">)\d+(</dd>)',
               rf'\g<1>{len(pages)}\g<2>{len(pages)}\g<3>', s, count=1)
    s = re.sub(r'(<dt data-i18n="notes"></dt><dd data-num=")\d+(">)\d+(</dd>)',
               rf'\g<1>{notes}\g<2>{notes}\g<3>', s, count=1)
    # replace the contents list wholesale
    i = s.index('<h2 data-i18n="contents"></h2>')
    j = s.index("</main>", i)
    head = s[:i] + '<h2 data-i18n="contents"></h2>\n  ' + toc + "\n"
    return head + s[j:]


def wire_selector(path, published, langs_by_vol):
    s = pathlib.Path(path).read_text(encoding="utf-8")
    orig = s
    for v in published:
        dl = langs_by_vol.get(v, "")
        attr = f' data-langs="{dl}"' if dl else ""
        span = (f'<span class="vol off"><b data-num="{v}">{ar_num(v)}</b></span>')
        anch = (f'<a class="vol" href="{v}/" data-vol="{v}"{attr}>'
                f'<b data-num="{v}">{ar_num(v)}</b></a>')
        if span in s:
            s = s.replace(span, anch, 1)
        else:                        # already an anchor: refresh its attributes
            s = re.sub(rf'<a class="vol" href="{v}/"[^>]*>(<b data-num="{v}">[^<]*</b>)</a>',
                       lambda m: anch, s, count=1)
    s = re.sub(r'(<dt data-i18n="published"></dt><dd data-num=")\d+(">)\d+(</dd>)',
               rf'\g<1>{len(published)}\g<2>{len(published)}\g<3>', s, count=1)
    if s != orig:
        pathlib.Path(path).write_text(s, encoding="utf-8", newline="")
    return s != orig


def main():
    files = sys.argv[1:]
    if not files:
        sys.exit(__doc__)
    datas = [json.loads(pathlib.Path(f).read_text(encoding="utf-8")) for f in files]

    tpl = (LIB / "bihar/1/index.html").read_text(encoding="utf-8")
    toc_path = LIB / "bihar/assets/toc.json"
    toc = json.loads(toc_path.read_text(encoding="utf-8"))
    toc = [t for t in toc if not re.match(r"bihar/(?:%s)/" %
           "|".join(str(d["volume"]) for d in datas), t.get("href", ""))]

    for d in datas:
        v = d["volume"]
        out = LIB / f"bihar/{v}/index.html"
        out.write_text(volume_index(d, tpl), encoding="utf-8", newline="")
        print(f"  volume index -> {out.relative_to(LIB)}")
        for r in chapters(d):
            toc.append({"title": r["title"], "href": f"bihar/{v}/{r['p']}/",
                        "label": ar_num(r["p"]), "p": r["p"], "vol": v})
        print(f"    {len(chapters(d))} chapters added to toc.json")

    toc_path.write_text(json.dumps(toc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  toc.json -> {len(toc)} rows")

    published = [1] + sorted(d["volume"] for d in datas)
    langs = {1: "ar,en,fa,ur"}
    for d in datas:
        langs[d["volume"]] = "ar"
    for p in ("bihar/index.html", "en/bihar/index.html",
              "fa/bihar/index.html", "ur/bihar/index.html"):
        ch = wire_selector(LIB / p, published, langs)
        print(f"  selector {p}: {'updated' if ch else 'unchanged'}")

    cat_path = LIB / "catalog.json"
    cat = json.loads(cat_path.read_text(encoding="utf-8"))

    def walk(o):
        if isinstance(o, dict):
            if o.get("slug") == "bihar":
                o["volumesPublished"] = published
            for x in o.values():
                walk(x)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    walk(cat)
    cat_path.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print(f"  catalog.json volumesPublished -> {published}")


if __name__ == "__main__":
    main()
