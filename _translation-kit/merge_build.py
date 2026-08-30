#!/usr/bin/env python3
"""Merge a translation module into the extracted Arabic and build the pages.

  merge_build.py <tr_module> <outdir> --lang ur [--volume 1] [--total N]
                 [--alts ar,en,fa,ur] [--no-draft] <arabic index.html ...>

The translation module supplies:
  PAGES = {page_number: [line, line, ...]}   one line per data-i node, in order
  NOTES = {"fn-0-12-1": "translated note", ...}

Both are checked against the extracted Arabic before anything is written: a
count mismatch or a missing note is a hard exit, never a silently short page.
"""
import argparse, importlib, pathlib, sys
import extract as E, build as B


def escape_tr(s):
    """Convert plain quotes to the entities the live pages use."""
    return s.replace("&", "&amp;").replace("'", "&#x27;").replace('"', "&quot;")


def run(trmod, ar_paths, outdir, lang, vol, total, alts, draft=True):
    tr = importlib.import_module(trmod)
    built = []
    for p in ar_paths:
        page = E.extract(p)
        n = page["page"]

        if n not in tr.PAGES:
            sys.exit(f"page {n}: no entry in {trmod}.PAGES")
        lines = tr.PAGES[n]
        if len(lines) != len(page["nodes"]):
            sys.exit(f"page {n}: {len(lines)} translations vs "
                     f"{len(page['nodes'])} nodes")

        for nd, line in zip(page["nodes"], lines):
            nd[lang] = escape_tr(line)
        for nt in page["notes"]:
            if nt["id"] not in tr.NOTES:
                sys.exit(f"page {n}: missing translation for note {nt['id']}")
            nt[lang] = escape_tr(tr.NOTES[nt["id"]])

        pg_total = total if total is not None else page.get("total", 231)
        name = f"{n}" if not draft else f"{n}-draft"
        d = pathlib.Path(outdir) / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(
            B.build(page, lang, vol, pg_total, alts), encoding="utf-8")
        built.append((n, len(page["nodes"]), len(page["notes"])))
    return built


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("module", help="translation module, e.g. tr_ur_49_58")
    ap.add_argument("outdir")
    ap.add_argument("arabic", nargs="+", help="Arabic source index.html files")
    ap.add_argument("--lang", required=True, choices=sorted(B.LANGS))
    ap.add_argument("--volume", type=int, default=1)
    ap.add_argument("--total", type=int, default=None)
    ap.add_argument("--alts", default="ar,en,fa,ur",
                    help="language versions that EXIST for this volume")
    ap.add_argument("--no-draft", action="store_true")
    a = ap.parse_args()

    alts = [x.strip() for x in a.alts.split(",") if x.strip()]
    if a.lang not in alts:
        sys.exit(f"--alts must include {a.lang}; hreflang sets are self-referential")

    for n, nn, nt in run(a.module, a.arabic, a.outdir, a.lang, a.volume,
                         a.total, alts, draft=not a.no_draft):
        print(f"  p.{n:>3}  {nn} nodes, {nt} notes")


if __name__ == "__main__":
    main()
