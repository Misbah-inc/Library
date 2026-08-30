#!/usr/bin/env python3
"""Check a built translated page against its Arabic source of record.

  verify.py --lang ur [--root AR_ROOT] [--out OUT_DIR] [--volume 1]
            [--total 231] [--alts ar,en,fa,ur] [--no-draft] <page ...>

Must report 0 failures before anything is committed. It checks that the Arabic
is byte-identical to source, that data-i is contiguous, that every node has
exactly one translation line, that footnote refs and note blocks agree, that
every note carries a translation, that the page/volume numbers are right, that
the SEO head is correct, and that Arabic-only chrome has not leaked in.
"""
import argparse, os, pathlib, re, sys
import extract as E
import build as B

SITE = B.SITE
FAIL = 0


def bad(msg):
    global FAIL
    FAIL += 1
    print("  FAIL:", msg)


def check(ar_path, out_path, lang, vol, total, alts):
    if not pathlib.Path(ar_path).exists():
        bad(f"arabic source not found: {ar_path}")
        return
    if not pathlib.Path(out_path).exists():
        bad(f"built page not found: {out_path}")
        return
    src = E.extract(ar_path)
    out = pathlib.Path(out_path).read_text(encoding="utf-8")
    n = src["page"]
    L = B.LANGS[lang]

    ar_nodes = re.findall(r'<(p|h3) lang="ar" data-i="(\d+)">(.*?)</\1>', out, re.S)
    tr_nodes = re.findall(r'<(p|h3) class="tr-line" lang="' + lang + r'">(.*?)</\1>',
                          out, re.S)

    if len(ar_nodes) != len(src["nodes"]):
        bad(f"p{n}: ar node count {len(ar_nodes)} != {len(src['nodes'])}")
    if len(tr_nodes) != len(src["nodes"]):
        bad(f"p{n}: {lang} line count {len(tr_nodes)} != {len(src['nodes'])}")
    if [int(i) for _, i, _ in ar_nodes] != list(range(len(ar_nodes))):
        bad(f"p{n}: data-i not contiguous")

    for (tag, i, txt), s in zip(ar_nodes, src["nodes"]):
        if txt != s["ar"]:
            bad(f"p{n}: arabic altered at data-i={i}")
        if tag != s["tag"]:
            bad(f"p{n}: tag mismatch at data-i={i} ({tag} vs {s['tag']})")

    for tag, txt in tr_nodes:
        if not txt.strip():
            bad(f"p{n}: empty {lang} line")
        # Urdu and Farsi are written in the Arabic script, so this only makes
        # sense for English.
        if lang == "en" and re.search(r'[؀-ۿ]', re.sub(r'<[^>]+>', '', txt)):
            bad(f"p{n}: arabic left inside an english line")

    # ---- footnotes ----------------------------------------------------------
    refs = set(re.findall(r'href="#(fn-[\d-]+)"', out))
    notes = set(re.findall(r'class="note" lang="ar" id="(fn-[\d-]+)"', out))
    if refs != notes:
        bad(f"p{n}: fnref/note mismatch refs={sorted(refs)} notes={sorted(notes)}")
    if len(notes) != len(src["notes"]):
        bad(f"p{n}: note count {len(notes)} != {len(src['notes'])}")
    for nt in src["notes"]:
        if f'id="{nt["id"]}"' not in out:
            bad(f"p{n}: note {nt['id']} missing")
    if src["notes"] and out.count(f'class="tr-note-line" lang="{lang}"') != len(src["notes"]):
        bad(f"p{n}: translated-note count wrong")

    # ---- SEO head: absolute, self-referential, no stale domain --------------
    canonical = f'<link rel="canonical" href="{SITE}/{lang}/bihar/{vol}/{n}/">'
    if canonical not in out:
        bad(f"p{n}: canonical wrong or not absolute")
    for a in alts:
        pre = "" if a == "ar" else f"/{a}"
        if f'<link rel="alternate" hreflang="{a}" href="{SITE}{pre}/bihar/{vol}/{n}/">' not in out:
            bad(f"p{n}: missing/!absolute hreflang {a}")
    if lang not in alts:
        bad(f"p{n}: hreflang set is not self-referential")
    if "ar" in alts and f'hreflang="x-default" href="{SITE}/bihar/{vol}/{n}/"' not in out:
        bad(f"p{n}: missing x-default")
    for a in ("ar", "en", "fa", "ur"):
        if a not in alts and f'hreflang="{a}"' in out:
            bad(f"p{n}: hreflang {a} present but not published")
    if "github.io" in out:
        bad(f"p{n}: stale github.io URL")

    # ---- shell sanity -------------------------------------------------------
    for must in [f'data-pagenum="{n}"', f'data-pos="{n-1}"', f'data-total="{total}"',
                 f'data-volume="{vol}"', f'<span data-num="{n}">{n}</span>',
                 'data-tr-static="1"', f'lang="{lang}" dir="{L["dir"]}"',
                 f'<title>{L["title"]} — p. {n}</title>']:
        if must not in out:
            bad(f"p{n}: missing {must!r}")
    if 'class="edge"' in out or 'id="cite-text"' in out or 'id="drawer"' in out:
        bad(f"p{n}: arabic-only chrome leaked in")
    if re.search(r'lang="ar"[^>]*>\s*</(p|h3)>', out):
        bad(f"p{n}: empty arabic node")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pages", nargs="+", type=int)
    ap.add_argument("--lang", required=True, choices=sorted(B.LANGS))
    ap.add_argument("--root", default=os.environ.get(
        "AR_ROOT", "/mnt/user-data/uploads/Library"))
    ap.add_argument("--out", default=os.environ.get("OUT_DIR", "/home/claude/work/out"))
    ap.add_argument("--volume", type=int, default=1)
    ap.add_argument("--total", type=int, default=231)
    ap.add_argument("--alts", default="ar,en,fa,ur")
    ap.add_argument("--no-draft", action="store_true")
    a = ap.parse_args()

    alts = [x.strip() for x in a.alts.split(",") if x.strip()]
    suffix = "" if a.no_draft else "-draft"
    for p in a.pages:
        check(f"{a.root}/bihar/{a.volume}/{p}/index.html",
              f"{a.out}/{p}{suffix}/index.html",
              a.lang, a.volume, a.total, alts)

    print(f"\n{len(a.pages)} pages checked — {FAIL} failures")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
