#!/usr/bin/env python3
"""Publish the library to S3 behind CloudFront.

    python deploy_s3.py --bucket library-misbah-inc --dist E1234ABCDEF
    python deploy_s3.py --bucket library-misbah-inc --dry-run

Why this exists rather than `git push`. GitHub Pages caps a published site at
1 GB and times a deployment out after 10 minutes, and a deployment rebuilds the
WHOLE site rather than the diff. At ~48,600 files the library is past what that
can carry, so GitHub keeps the files, the history and the push workflow, and S3
serves the pages.

Three things this does that a bare `aws s3 sync` does not:

1. **It does not publish the workshop.** `_translation-kit/` is 192 MB of build
   scripts and source JSON and is, today, served live — so is `CLAUDE.md`.
   Harmless while the repo is public; the moment the repo goes private, serving
   them would leak exactly what was closed.

   **`--delete` does NOT remove something you add to EXCLUDE.** The filters
   apply to the DESTINATION listing as well as the source, so an excluded key
   is not considered for deletion — it is simply invisible to sync. Adding a
   pattern here stops future uploads and nothing more. Anything already in the
   bucket has to be removed by hand, once:

       aws s3 rm s3://<bucket>/<prefix>/ --recursive

   This was learned the hard way: `.claude/launch.json` was served live and
   survived a deploy that excluded it.

2. **Cache headers per file type**, which GitHub Pages does not allow at all.
   The pages are short-lived, the fonts never change. This is the proper fix for
   the problem `ASSETS_V` was invented for: with an invalidation on every deploy
   a changed reader.js reaches everyone at once, so the frozen `?v=9` stays
   frozen and never needs to be thought about again.

3. **One CloudFront invalidation per deploy.** A wildcard counts as a single
   path against the 1,000-per-month free allowance, so `/*` costs nothing and
   removes every "why is it still showing the old version" question.

The S3 bucket must have **static website hosting enabled with index document
`index.html`**, and CloudFront's origin must be the bucket's *website* endpoint
(`<bucket>.s3-website-<region>.amazonaws.com`), NOT the REST endpoint. Only the
website endpoint resolves `/bihar/4/50/` to `bihar/4/50/index.html`; with the
REST endpoint every directory URL on the site 404s. This is the single most
common way to get this setup wrong.
"""

import argparse
import pathlib
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")

# NOT published. Everything else under the Library root is. A deny-list is the
# right shape here because the tree is mostly content: naming the four things a
# reader must never receive is shorter and far less likely to silently drop a
# new book than an allow-list that must be edited every time one is added.
#
# Adding a pattern here stops the upload; it does NOT delete what is already in
# the bucket, because sync's filters hide the key from the delete pass too.
# Remove those by hand once — see the module docstring.
EXCLUDE = [
    "_translation-kit/*",   # 192 MB of build scripts and source JSON
    ".git/*", ".github/*", ".gitattributes", ".gitignore",
    ".claude/*",            # agent config; launch.json was live until 2026-09-22
    "*.md",                 # CLAUDE.md, CHANGELOG.md, README
    "*.py", "*.ps1", "*.sh",
    ".DS_Store", "desktop.ini", "Thumbs.db",
]

# Everything gets the short cache first, then assets are re-uploaded with longer
# ones. Two reasons it is done in this order rather than per-directory: a pass
# per file type would rescan all 48,000 files once per type, which over Google
# Drive is the difference between minutes and an hour; and `aws s3 sync` skips
# unchanged files, so it would not rewrite headers on a second visit anyway —
# only `cp --metadata-directive REPLACE` does, which is why assets use `cp`.
PAGE_CACHE = "public,max-age=600"          # what GitHub Pages serves today
ASSET_CACHE = [
    ("fonts & images", "public,max-age=31536000,immutable",
     ["woff2", "woff", "ttf", "otf", "png", "jpg", "jpeg", "gif", "svg", "ico", "webp"]),
    # Ten minutes, NOT a day. `ASSETS_V` is frozen, so the URL never changes
    # and a browser's own cache is the only thing deciding when a reader gets
    # new JS — a CloudFront invalidation cannot reach into it. At max-age=86400
    # a returning reader could run yesterday's reader.js for a full day, which
    # makes CLAUDE.md's rule ("ship the JS change on its own, it is live within
    # ten minutes") simply untrue. These are 77 KB and 66 KB and revalidate to
    # a ~200-byte 304, and the edge is invalidated on every deploy anyway.
    ("css & js", "public,max-age=600", ["css", "js"]),
]


def run(cmd, dry):
    print("   $ " + " ".join(cmd[:9]) + (" …" if len(cmd) > 9 else ""))
    if dry:
        return 0
    return subprocess.call(cmd)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bucket", required=True)
    ap.add_argument("--dist", help="CloudFront distribution id, to invalidate")
    ap.add_argument("--root", default=str(pathlib.Path(__file__).resolve().parent.parent))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    root = pathlib.Path(a.root)
    if not (root / "index.html").exists():
        sys.exit(f"{root} does not look like the Library root (no index.html)")
    if not shutil.which("aws") and not a.dry_run:
        sys.exit("the AWS CLI is not installed — see DEPLOY.md, step 1")

    # The search indexes are NOT in git (see .gitignore) — they are derived and
    # too large to commit. `aws s3 sync --delete` therefore has a trap: deploying
    # from a clone that has never run build_search_index.py would DELETE them off
    # S3, and every book's Search button would start answering "Could not load."
    # with nothing in this output to say why. Refuse instead.
    # Per VOLUME, not per book: bihar/assets/search-index.json is the old
    # volume-1-only file and still exists, so "the book has some index" would
    # pass while 109 volumes had none.
    missing = []
    for b in ("bihar", "kafi"):
        if not (root / b).is_dir():
            continue
        vols = [d.name for d in (root / b).iterdir()
                if d.is_dir() and d.name.isdigit()]
        gap = [v for v in vols if not (root / b / "assets" / f"search-{v}.json").is_file()]
        if gap:
            missing.append(f"{b} ({len(gap)} of {len(vols)} volumes)")
    # The site-wide index is the one readers actually reach from /search/.
    # Its shards hold POSITIONS into pages.json, so a half-present set is
    # worse than none: it answers with confidently wrong pages.
    sd = root / "assets" / "search"
    if not (sd / "pages.json").is_file() or len(list(sd.glob("t-*.json"))) < 2:
        missing.append("site-wide index (assets/search/)")
    if missing and not a.dry_run:
        print("no search indexes for: " + ", ".join(missing))
        print("they are gitignored and must be built before deploying:")
        print("    python _translation-kit/build_search_index.py --all")
        print("    python _translation-kit/build_site_index.py")
        print("(--dry-run skips this check)")
        return 1

    rc = 0
    print("")
    print(f"== whole site  ({PAGE_CACHE})   [--delete: removes what is excluded]")
    cmd = ["aws", "s3", "sync", str(root), f"s3://{a.bucket}",
           "--cache-control", PAGE_CACHE, "--delete", "--only-show-errors"]
    for pat in EXCLUDE:
        cmd += ["--exclude", pat]
    rc |= run(cmd, a.dry_run)

    for label, cache, exts in ASSET_CACHE:
        print("")
        print(f"== re-stamp {label}  ({cache})")
        cmd = ["aws", "s3", "cp", str(root / "assets"), f"s3://{a.bucket}/assets",
               "--recursive", "--metadata-directive", "REPLACE",
               "--cache-control", cache, "--only-show-errors", "--exclude", "*"]
        for e in exts:
            cmd += ["--include", f"*.{e}"]
        rc |= run(cmd, a.dry_run)

    if a.dist:
        print("\n== invalidate CloudFront")
        rc |= run(["aws", "cloudfront", "create-invalidation",
                   "--distribution-id", a.dist, "--paths", "/*"], a.dry_run)

    print("\nDRY RUN — nothing uploaded" if a.dry_run else
          ("\ndone" if rc == 0 else f"\n** one or more steps failed (rc={rc}) **"))
    return rc


if __name__ == "__main__":
    sys.exit(main())
