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


# The sitemap protocol allows at most 50,000 URLs and 50 MB per FILE. Past
# either, the whole file is rejected - not the surplus entries, the file.
# Bihar in Arabic alone takes this library to ~48,400 URLs, so a single
# sitemap.xml stops being valid at the very next thing added. Above the limit
# sitemap.xml becomes an INDEX listing sitemap-1.xml, sitemap-2.xml ... which
# is the protocol's own answer and needs nothing changed at Search Console:
# the submitted URL stays /sitemap.xml.
PER_FILE = 40000          # under 50,000, with room before resplitting


def build_xml(rels):
    urls = []
    for rel in rels:
        path = "" if str(rel) == "." else "/".join(rel.parts) + "/"
        urls.append(f"{SITE}/{path}")
    body = "".join(f"<url><loc>{u}</loc></url>" for u in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            + body + '</urlset>'), urls


def write_sitemaps(root, rels):
    """One sitemap.xml, or an index plus shards once past PER_FILE."""
    # Shards from a previous, larger run would no longer be listed by the index
    # but would still sit in the tree and be crawlable. Clear them first.
    for old in root.glob("sitemap-*.xml"):
        old.unlink()

    if len(rels) <= PER_FILE:
        urls = rels
        (root / "sitemap.xml").write_text(xml, encoding="utf-8", newline="")
        return len(urls), ["sitemap.xml"], False

    shards, total = [], 0
    for k in range(0, len(rels), PER_FILE):
        name = "sitemap-%d.xml" % (k // PER_FILE + 1)
        xml, urls = build_xml(rels[k:k + PER_FILE])
        (root / name).write_text(xml, encoding="utf-8", newline="")
        shards.append(name)
        total += len(urls)
    body = "".join("<sitemap><loc>%s/%s</loc></sitemap>" % (SITE, n) for n in shards)
    (root / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + body + '</sitemapindex>', encoding="utf-8", newline="")
    return total, ["sitemap.xml"] + shards, True


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

    total, files, is_index = write_sitemaps(root, rels)
    (root / "robots.txt").write_text(ROBOTS.format(site=SITE), encoding="utf-8")
    print()
    if is_index:
        print("wrote sitemap INDEX + %d shards (%s URLs, %s max per file)"
              % (len(files) - 1, format(total, ","), format(PER_FILE, ",")))
    for f in files:
        print("  " + str(root / f))
    print("wrote " + str(root / "robots.txt"))


if __name__ == "__main__":
    main()
