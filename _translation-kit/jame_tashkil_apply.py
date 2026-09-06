#!/usr/bin/env python3
"""Apply a batch of vocalisations, refusing any entry that alters the text.

    from jame_tashkil_apply import apply_batch
    apply_batch({"1:233:0": "…"})

jame_tashkil_check.py catches an altered letter *after* it has been written and
the book rebuilt. That is one step too late: the bad entry is already in the
data file and in 1,216 pages. This validates first and writes only if every
entry survives, so a mistake never reaches disk.

It exists because the same error kept recurring — writing the *standard* form of
a word instead of the printed one:

    الان  → الآن     an alef given a madda
    راؤن  → راؤون    a wāw supplied
    قید   → قیدت     a tāʾ supplied for feminine agreement
    بالاخر → بالآخر   the madda again

Every one is me knowing better than the page, and none is visible on screen.
"""
import json, pathlib, re, sys

HERE = pathlib.Path(__file__).parent
DIA = re.compile(r"[ً-ٰٕۖ-ۭ]")


def bare(s):
    return DIA.sub("", s)


def load_index(pages_path=None):
    d = json.loads((pathlib.Path(pages_path) if pages_path
                    else HERE / "jame_pages.json").read_text(encoding="utf-8"))
    idx = {}
    for vol in d["volumes"]:
        for pg in vol["pages"]:
            for i, b in enumerate(pg["blocks"]):
                idx[f'{vol["v"]}:{pg["n"]}:{i}'] = b["t"]
    return idx


def apply_batch(batch, tashkil_path=None, pages_path=None, quiet=False):
    """Validate every entry, then write. Returns the new total.

    Raises SystemExit(1) with a per-entry diff if anything would alter the text.
    """
    idx = load_index(pages_path)
    P = pathlib.Path(tashkil_path) if tashkil_path else HERE / "jame_tashkil.json"
    t = json.loads(P.read_text(encoding="utf-8"))

    problems = []
    for key, voc in batch.items():
        if key not in idx:
            problems.append((key, "no such block", "", ""))
            continue
        o, v = bare(idx[key]), bare(voc)
        if o == v:
            continue
        # locate the first divergence so the message is actionable
        i = next((j for j in range(min(len(o), len(v))) if o[j] != v[j]), min(len(o), len(v)))
        problems.append((
            key,
            f"text altered at char {i}",
            f"printed: …{o[max(0, i-32):i+26]}…",
            f"mine   : …{v[max(0, i-32):i+26]}…",
        ))

    if problems:
        print(f"REFUSED — {len(problems)} of {len(batch)} entries alter the text:\n",
              file=sys.stderr)
        for key, what, a, b in problems:
            print(f"  {key}: {what}", file=sys.stderr)
            if a:
                print(f"    {a}\n    {b}", file=sys.stderr)
        print("\nNothing was written.", file=sys.stderr)
        sys.exit(1)

    t.update(batch)
    P.write_text(json.dumps(t, ensure_ascii=False, indent=1), encoding="utf-8")
    if not quiet:
        print(f"applied {len(batch)}; total now {len(t)}")
    return len(t)
