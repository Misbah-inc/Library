"""Build Arabic «الغدير» reading pages for a volume.

    python ghadir_ar_build.py ghadir_v1.json --out ../ghadir/1            --pages-json ../ghadir/assets/pages-1.json

One builder per book, as everywhere here. Derived from `ghadir_ar_build.py`
because al-Ghadir's Ghaemiyeh export is the ordinary Bihar shape — `ص: N` page
markers, `<SPAN class=chapter>` segments, real `content_note` divs with
`content_notelink` anchors — so `bihar_ar_extract.py` reads it unmodified and
the notes need no special handling.

**Edition: تحقيق مركز الغدير للدراسات الإسلامية، قم، 1416 هـ / 1995 م**
(ghbook.ir book 9638), by العلامة عبد الحسين أحمد الأميني النجفي.

**The source was Persian-typeset, and the text is normalised before extraction.**
The export writes every Arabic yāʾ and kāf with the PERSIAN codepoint — 411,830
`ی` (U+06CC) and 103,778 `ک` (U+06A9) against ZERO `ي` (U+064A) and ZERO `ك`
(U+0643). Every other Arabic book in this library is the other way round, so
publishing it as-is would make الغدير the only one in Persian letter forms,
visible to any reader who copies a citation. 510,672 + 125,799 characters are
converted in the prep step, verified position by position: same length, only
those two codepoints differing, and `پ`/`چ`/`گ` — real Persian letters with no
Arabic equivalent, in nisbas like «الچلبي» and «الگلپايگاني» — left untouched.

> **That conversion silently disarmed a guard.** `bihar_ar_extract.py` drops the
> Ghaemiyeh blurb by matching the literal «تعريف مرکز» with a PERSIAN kāf; after
> normalisation the text reads «تعريف مركز» and no longer matches, so the
> publisher's donation appeal — bank account, Isfahan office address, telephone
> numbers — survived into volume 11. The prep step now cuts it explicitly. A fix
> in one place can disable a check in another that nothing connects them.
"""

import argparse
import html
import json
import pathlib
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

SITE = "https://library.misbah-inc.com"
ASSETS_V = "9"   # FROZEN — see CLAUDE.md. Never bump.
AR_DIGITS = "٠١٢٣٤٥٦٧٨٩"

SHORT_AR = "الغدير"
TITLE = {"ar": "الغدير", "fa": "الغدیر",
         "ur": "الغدیر", "en": "Al-Ghadir"}
AUTHOR = {"ar": "العلامة عبد الحسين أحمد الأميني النجفي",
          "fa": "علامه عبدالحسین احمد امینی نجفی",
          "ur": "علامہ عبدالحسین احمد امینی نجفی",
          "en": "Allama 'Abd al-Husayn Ahmad al-Amini al-Najafi"}
EDITION = {"ar": "تحقيق مركز الغدير للدراسات الإسلامية، قم",
           "fa": "تحقیق مرکز الغدیر للدراسات الإسلامیه، قم",
           "ur": "تحقیق مرکز الغدیر للدراسات الإسلامیہ، قم",
           "en": "ed. Markaz al-Ghadir li-l-Dirasat al-Islamiyya, Qum"}
FRONT = {"ar": "مقدمة", "fa": "مقدمه", "ur": "مقدمہ", "en": "Front matter"}

def ar_num(n):
    return "".join(AR_DIGITS[int(c)] for c in str(n))


def esc(s):
    return html.escape(s, quote=True)


def cite(vol, n, lang, fm=False):
    if lang == "ar":
        return (f"{SHORT_AR}، {AUTHOR['ar']}، المجلد {ar_num(vol)}، "
                f"{'المقدمة، ' if fm else ''}ص {ar_num(n)}.")
    if lang == "fa":
        return (f"{TITLE['fa']}، {AUTHOR['fa']}، جلد {vol}، "
                f"{'مقدمه، ' if fm else ''}ص {n}.")
    if lang == "ur":
        return (f"{TITLE['ur']}، {AUTHOR['ur']}، جلد {vol}، "
                f"{'مقدمہ، ' if fm else ''}ص {n}.")
    pre = "front matter, " if fm else ""
    return f"{TITLE['en']}, {AUTHOR['en']}, vol. {vol}, {pre}p. {n}."


REF = re.compile(r"\[(\d+)\]")

# This export writes each note's own number INTO its text — note 1 reads
# «1- أخرجه الحافظ...» — so rendering the builder's «(١)» in front of it shows
# the number twice: «(١) 1- أخرجه». It is true of 2,428 of volume 1's 2,428
# notes, and of every volume. Stripped only when the leading number EQUALS
# the note's own, so a note whose text genuinely opens with a different
# figure is left alone.
#
# al-Kafi and al-Faqih have the SAME doubling and are live with it — see the
# CHANGELOG. Fixing those means rebuilding two published books, which is its
# own job; it is not done here.
def note_text(x):
    m = re.match(r"\s*(\d+)\s*-\s*", x["ar"])
    if m and int(m.group(1)) == x["n"]:
        return x["ar"][m.end():]
    return x["ar"]


# A parenthesised LATIN-digit group inside RTL text renders REVERSED.
# Measured on the live page before this was added: «(1 / 369)» drew as
# «)369 / 1(» and «(3 / 293)» as «/  3()293». The brackets are bidi-neutral
# and take the surrounding direction, so the HTML is correct and the page is
# still wrong — checking the JSON can never find this. <bdi> isolates the
# group so it resolves left-to-right as its own unit.
#
# LATIN digits only. Arabic-Indic ٠-٩ are bidi class AN and already resolve
# correctly, which is why Bihar, al-Kafi and al-Faqih — whose parentheses
# hold only «(١)»-style note numbers — never needed this. الغدير is the first
# Ghaemiyeh book here with «(1 / 369)» citations.
#
# The interior must be digits and separators ONLY. «( عليه السلام )»,
# «(المؤلف)» and «(ص 189)» hold strong RTL text, resolve correctly on their
# own, and must be left alone — see the التهذيب note in CLAUDE.md.
NUMGRP = re.compile(r"[\(\[](?=[^)\]]*[0-9])[\s0-9/،,.\-–:]+[\)\]]")

def bidi_nums(t):
    """Isolate a Latin-digit group with UNICODE isolates, not markup.

    U+2066 LEFT-TO-RIGHT ISOLATE ... U+2069 POP DIRECTIONAL ISOLATE. These are
    part of the Unicode Bidirectional Algorithm itself, so any conforming text
    engine honours them — there is no user-agent default to fall back on and no
    stylesheet to override.

    Three markup approaches failed on iOS Safari before this one, and all three
    looked correct in Chrome:

      <bdi>                       dir="auto"; the group has no STRONG character
                                  (brackets neutral, digits weak), so the spec
                                  says fall back to ltr. Chrome does; iOS falls
                                  back to the parent's rtl.
      <bdi dir="ltr">             ignored.
      .body bdi{direction:ltr;
                unicode-bidi:isolate}   ignored.

    Verified against the source: «ذكره له ابن شهرآشوب في المناقب [1] (1 / 458).»
    was drawing as «(458 / 1» on the phone — the numeric runs swapped, which is
    the signature of the group resolving right-to-left.

    The characters are invisible and are stripped by the search fold(), which
    keeps only letters and digits, so neither the index nor a citation copied
    off the page is affected.
    """
    return NUMGRP.sub(lambda m: "⁦" + m.group(0) + "⁩", t)


def body_html(page):
    have = {x["n"] for x in page["notes"]}
    pos = page["n"] - 1
    parts = []
    for b in page["blocks"]:
        def sub(m):
            k = int(m.group(1))
            if k not in have:
                return m.group(0)
            return f'<a class="fnref" href="#fn-0-{pos}-{k}">{ar_num(k)}</a>'
        txt = bidi_nums(REF.sub(sub, esc(b["ar"])))
        tag = b["tag"] if b["tag"] in ("h2", "h3", "h4") else "p"
        parts.append(f'<{tag} lang="ar" data-i="{b["i"]}">{txt}</{tag}>')
    out = "".join(parts)
    if page["notes"]:
        notes = "".join(
            f'<div class="note" lang="ar" id="fn-0-{pos}-{x["n"]}">'
            f'<span class="note-n">({ar_num(x["n"])})</span>'
            f'<span>{bidi_nums(esc(note_text(x)))}</span></div>' for x in page["notes"])
        out += f'<div class="notes">{notes}</div>'
    return out


def description(page):
    t = " ".join(b["ar"] for b in page["blocks"])
    t = re.sub(r"\[\d+\]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t[:150] if t else SHORT_AR


def split_template(tpl):
    """Chrome lifted from a published Bihar page — same folder depth, so the
    relative links resolve identically. Only data-slug/data-book differ, and
    those are written fresh below."""
    a = tpl.index('<link rel="stylesheet"')
    b = tpl.index('<div class="edgewrap">')
    d = tpl.index('<div class="scrim"')
    return {"chrome_head": tpl[a:b], "tail": tpl[d:]}


def build_page(page, ids, vol, tp):
    pid = page["id"]
    n = page["n"]
    fm = pid.startswith("fm-")
    i = ids.index(pid)
    prev_id = ids[i - 1] if i else None
    next_id = ids[i + 1] if i + 1 < len(ids) else None
    desc = esc(description(page))
    title = (f"{SHORT_AR} — {FRONT['ar']} ص {ar_num(n)}" if fm
             else f"{SHORT_AR} — ص {ar_num(n)}")
    url = f"{SITE}/ghadir/{vol}/{pid}/"

    links = ""
    if prev_id:
        links += f'<link rel="prev" href="../../../ghadir/{vol}/{prev_id}/">'
    if next_id:
        links += f'<link rel="next" href="../../../ghadir/{vol}/{next_id}/">'
    links += (f'<link rel="canonical" href="{url}">'
              f'<link rel="alternate" hreflang="ar" href="{url}">'
              f'<link rel="alternate" hreflang="x-default" href="{url}">')

    first, last = ids[0], ids[-1]
    pv = (f'<a class="btn prev" href="../../../ghadir/{vol}/{prev_id}/" rel="prev">'
          f'<span data-i18n="prev"></span></a>' if prev_id else
          '<span class="btn" aria-disabled="true"><span data-i18n="prev"></span></span>')
    nx = (f'<a class="btn next" href="../../../ghadir/{vol}/{next_id}/" rel="next">'
          f'<span data-i18n="next"></span></a>' if next_id else
          '<span class="btn" aria-disabled="true"><span data-i18n="next"></span></span>')

    cites = " ".join(f'data-cite-{L}="{esc(cite(vol, n, L, fm))}"' for L in ("ar", "fa", "ur", "en"))
    cspan = " ".join(f'data-{L}="{esc(cite(vol, n, L, fm))}"' for L in ("ar", "fa", "ur", "en"))

    if fm:
        folio = ('<span class="folio"><span data-ar="' + esc(FRONT["ar"]) +
                 '" data-fa="' + esc(FRONT["fa"]) + '" data-ur="' + esc(FRONT["ur"]) +
                 '" data-en="' + esc(FRONT["en"]) + '">' + esc(FRONT["ar"]) + '</span> '
                 f'<span data-num="{n}">{ar_num(n)}</span></span>')
    else:
        folio = ('<span class="folio"><span data-i18n="page"></span> '
                 f'<span data-num="{n}">{ar_num(n)}</span></span>')

    # al-Faqih has no named parts, so this slot carries the book's own title.
    partspan = (f'<span data-ar="{esc(TITLE["ar"])}" data-fa="{esc(TITLE["fa"])}"'
                f' data-ur="{esc(TITLE["ur"])}" data-en="{esc(TITLE["en"])}">'
                f'{esc(TITLE["ar"])}</span>')

    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl" data-root="../../.." data-book="../..">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{desc}">
{links}
{tp['chrome_head']}<main class="wrap">
  <article>
    <div class="leaf" id="text">
      <div class="part-label">{partspan}
        <span><span data-i18n="volume"></span>
        <span data-num="{vol}">{vol}</span>
        {folio}</span></div>
      <div class="body">{body_html(page)}</div>
    </div>
    <nav class="pager">
      <a class="btn " href="../../../ghadir/{vol}/{first}/" rel="related"><span data-i18n="first"></span></a>{pv}
      <form id="jump" data-tpl="ghadir/{vol}/{{p}}/" action="../../../" method="get">
        <input id="jump-num" name="p" inputmode="numeric" data-i18n-label="page"
               data-num-val="{n}" value="{ar_num(n)}">
      </form>
      {nx}<a class="btn " href="../../../ghadir/{vol}/{last}/" rel="related"><span data-i18n="last"></span></a>
    </nav>
    <p class="cite" id="cite-text" {cites}><span data-i18n="citation"></span>:
      <span {cspan}></span>
      &nbsp;·&nbsp;<code>/ghadir/{vol}/{pid}/</code></p>
  </article>
</main>
<div id="page-meta" hidden data-trlangs="" data-slug="ghadir" data-title-ar="{esc(SHORT_AR)}" data-title-fa="الغدیر" data-title-ur="الغدیر" data-title-en="Al-Ghadir" data-href="ghadir/{vol}/{pid}/"
     data-pagenum="{pid}" data-volume="{vol}" data-pos="{i}" data-total="{len(ids)}"></div>
{tp['tail']}"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--template", default="../bihar/1/26/index.html")
    ap.add_argument("--pages-json")
    args = ap.parse_args()

    data = json.loads(pathlib.Path(args.json).read_text(encoding="utf-8"))
    vol = data["volume"]
    tp = split_template(pathlib.Path(args.template).read_text(encoding="utf-8"))
    for p in data["pages"]:
        p.setdefault("id", str(p["n"]))
    ids = [p["id"] for p in data["pages"]]
    out = pathlib.Path(args.out)

    for page in data["pages"]:
        d = out / page["id"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(build_page(page, ids, vol, tp),
                                      encoding="utf-8", newline="")
    fmn = sum(1 for x in ids if x.startswith("fm-"))
    print(f"  vol {vol}: {len(ids)} pages -> {out}" + (f"  ({fmn} front matter)" if fmn else ""))

    if args.pages_json:
        nums = [p["n"] for p in data["pages"] if not p["id"].startswith("fm-")]
        p = pathlib.Path(args.pages_json)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(nums, ensure_ascii=False), encoding="utf-8")
        print(f"    pages json -> {p.name} ({len(nums)} numbered pages)")


if __name__ == "__main__":
    main()
