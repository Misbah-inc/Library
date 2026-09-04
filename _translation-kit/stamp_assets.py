#!/usr/bin/env python3
"""Stamp ?v=<N> onto unversioned reader.css / reader.js references.

  stamp_assets.py --root .. --version 5 [--apply]

Bihar, both Bayt al-Ahzan books and the six root pages link the shared assets
with no version, so they depend on ordinary HTTP cache expiry: edit
assets/reader.css and a returning reader keeps the stale copy for as long as
their browser feels like it. The Qur'an pages had exactly that bug — the ا+/ا−
and mobile fixes shipped, and no returning reader could see them.

This only rewrites the asset URL. Nothing else in the page may move, and that
is checked rather than assumed: putting the version back must reproduce the
original file byte for byte, or the file is left alone and reported.

Works on BYTES, deliberately. Every page here is CRLF, and Python's text mode
would rewrite all of them to LF on the way out — 1,391 files showing as fully
changed for a five-character edit. Bytes also sidestep any encoding round-trip
over the Arabic and cannot introduce a BOM.

Dry-run by default; pass --apply to write.
"""
import argparse, pathlib, re, sys

# matches a reference with or without an existing ?v=N, so this both stamps
# first-time references and moves an already-stamped one to a new version
REF = re.compile(rb'(reader\.(?:css|js))(?:\?v=\d+)?(?=")')


def normalize(data):
    """Strip the version from every reference — the comparison baseline."""
    return REF.sub(rb"\1", data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--version", required=True)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    root = pathlib.Path(a.root).resolve()
    ver = a.version.encode()
    files = [p for p in root.rglob("*.html")
             if "_translation-kit" not in p.parts and ".claude" not in p.parts]

    changed, already, norefs, failed = 0, 0, 0, []
    for f in files:
        original = f.read_bytes()
        if not REF.search(original):
            norefs += 1
            continue
        patched = REF.sub(rb"\1?v=" + ver, original)
        if patched == original:
            already += 1                        # already on this version
            continue

        # the whole safety argument: with versions removed, the two files are
        # identical — so nothing but the version string can have moved
        if normalize(patched) != normalize(original):
            failed.append(f"{f.relative_to(root)}: content changed, not just the version")
            continue
        if patched.count(b"\r\n") != original.count(b"\r\n"):
            failed.append(f"{f.relative_to(root)}: line endings changed")
            continue

        if a.apply:
            f.write_bytes(patched)
        changed += 1

    print(f"{'restamped' if a.apply else 'would restamp'} to v={a.version}: {changed}")
    print(f"already on v={a.version}: {already}")
    print(f"no reader asset reference: {norefs}")
    if failed:
        print(f"\nFAILED {len(failed)} — not written:")
        for x in failed[:20]:
            print("  " + x)
        sys.exit(1)


if __name__ == "__main__":
    main()
