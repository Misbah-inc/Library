#!/usr/bin/env python3
"""Regenerate sitemap.xml and robots.txt from what is actually on disk.

  gen_sitemap.py --root "G:/My Drive/Misbah Library/Library" [--dry-run]

The URL list is derived by walking the tree for directories that contain an
index.html, so it can never drift from what is published. Add a volume, run
this, and the sitemap is correct.

Skipped: the kit itself, anything beginning with "_" or ".", and "<n>-draft"
folders, which are unreviewed and must never be advertised to search engines.
"""
import argparse, pathlib, sys

SITE = "https://library.misbah-inc.com"

ROBOTS = """User-agent: *
Allow: /
Sitemap: {site}/sitemap.xml
"""


def skip(name):
    return name.startswith("_") or name.startswith(".") or name.endswith("-draft")


def page_dirs(root):
    """Every directory under root that publishes an index.html."""
    out = []
    for p in sorted(root.rglob("index.html")):
        rel = p.parent.relative_to(root)
        if any(skip(part) for part in rel.parts):
            continue
        out.append(rel)
    return out


def sort_key(rel):
    """Group by section, then sort numeric path segments numerically."""
    parts = rel.parts
    return tuple((1, int(x)) if x.isdigit() else (0, x) for x in parts)


def build_xml(rels):
    urls = []
    for rel in rels:
        path = "" if str(rel) == "." else "/".join(rel.parts) + "/"
        urls.append(f"{SITE}/{path}")
    body = "".join(f"<url><loc>{u}</loc></url>" for u in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            + body + '</urlset>'), urls


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    root = pathlib.Path(a.root)
    if not (root / "index.html").exists():
        sys.exit(f"{root} does not look like the Library root (no index.html)")

    rels = sorted(page_dirs(root), key=sort_key)
    xml, urls = build_xml(rels)

    # a quick breakdown so a bad run is obvious at a glance
    counts = {}
    for rel in rels:
        top = rel.parts[0] if rel.parts else "(root)"
        counts[top] = counts.get(top, 0) + 1
    print(f"{len(urls)} URLs")
    for k in sorted(counts):
        print(f"  {k:<12} {counts[k]}")

    if a.dry_run:
        print("\n--dry-run: nothing written")
        return

    (root / "sitemap.xml").write_text(xml, encoding="utf-8")
    (root / "robots.txt").write_text(ROBOTS.format(site=SITE), encoding="utf-8")
    print(f"\nwrote {root/'sitemap.xml'}")
    print(f"wrote {root/'robots.txt'}")


if __name__ == "__main__":
    main()
