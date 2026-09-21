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
   them would leak exactly what was closed. `--delete` on the first pass means
   running this against a bucket populated before these rules existed REMOVES
   them, rather than merely stopping their upload.

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
# `--delete` on the first pass means anything already on S3 and excluded here is
# REMOVED from the CDN, which is what makes this safe to run against a bucket
# that was populated before these rules existed.
EXCLUDE = [
    "_translation-kit/*",   # 192 MB of build scripts and source JSON
    ".git/*", ".github/*", ".gitattributes", ".gitignore",
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
    ("css & js", "public,max-age=86400", ["css", "js"]),
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
