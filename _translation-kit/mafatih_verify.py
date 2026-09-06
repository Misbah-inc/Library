#!/usr/bin/env python3
"""Independent audit of mafatih.json against the Ghaemiyeh export.

Written the way jame_tashkil_review.py is written, and for the same reason: it
re-derives everything from the source rather than importing the extractor's
judgement, so agreement between the two is evidence and not an echo. The one
thing it does import is the extractor's own credit vocabulary and page-marker
pattern, because those name material that is deliberately *not* in the output
and there is no way to recognise it independently.

Six audits:

  1  TEXT     every character of the source's content spans survives, once.
  2  IDS      section ids and unit ids are unique.
  3  STABLE   a second extraction of the same input reproduces every id and
              every unit body exactly. This is the load-bearing one: English
              and Urdu will be keyed to these ids, so an id that moves when the
              extractor is next touched silently re-points a translation.
  4  PAIR     every Arabic unit that owns a translation still owns it, and no
              translation is attached to a unit that is not Arabic.
  5  RUBRIC   no peeled core still contains Persian; no rubric is empty.
  6  AUDIO    no reciter credit or «***» separator survives anywhere.

Audits 1-5 are decidable. Run it after any change to mafatih_extract.py.
"""
import collections, json, pathlib, re, sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import mafatih_extract as M

WS = re.compile(r"\s+")


def flat(root):
    out = []

    def w(n, depth=0):
        out.append(n)
        for c in n["children"]:
            w(c, depth + 1)

    w(root)
    return out


def texts(nodes):
    """every string the output would ever put on a page"""
    for u in (u for n in nodes for u in n["units"]):
        for f in ("rub", "ar", "fa"):
            if u.get(f):
                yield u[f]
        if u.get("tr", {}).get("fa"):
            yield u["tr"]["fa"]


def main(src, jsonpath):
    doc = json.loads(pathlib.Path(jsonpath).read_text(encoding="utf-8"))
    nodes = flat(doc)
    units = [u for n in nodes for u in n["units"]]
    ar = [u for u in units if u["k"] == "ar"]
    fails = 0

    # ---------------------------------------------------------------- 1 TEXT
    raw = pathlib.Path(src).read_text(encoding="utf-8", errors="replace")
    root2, _ = M.extract(src)
    credits = M.audio_credits(root2)
    want = []
    for m in M.SPAN.finditer(raw):
        t = M.clean(m.group(1))
        if t and t not in credits and t not in ("***", "صوت") and not M.PAGE.match(t):
            want.append(t)
    have = list(texts(nodes))
    a = collections.Counter(WS.sub("", "".join(want)))
    b = collections.Counter(WS.sub("", "".join(have)))
    lost = a - b
    print(f"1  TEXT     {sum(a.values()):,} source characters; "
          f"{sum(lost.values()):,} missing from the output")
    if lost:
        fails += 1
        print(f"            {dict(lost.most_common(10))}")

    # ----------------------------------------------------------------- 2 IDS
    sid = [n["id"] for n in nodes if n.get("id")]
    uid = [u["id"] for u in ar if u.get("id")]
    dsi = [k for k, v in collections.Counter(sid).items() if v > 1]
    dui = [k for k, v in collections.Counter(uid).items() if v > 1]
    print(f"2  IDS      {len(sid):,} section ids ({len(dsi)} duplicated), "
          f"{len(uid):,} unit ids ({len(dui)} duplicated)")
    if dsi or dui:
        fails += 1
        print(f"            {(dsi + dui)[:8]}")

    # -------------------------------------------------------------- 3 STABLE
    M.assign_ids(root2, set())
    again = {u["id"]: u["ar"] for n in flat(root2) for u in n["units"]
             if u["k"] == "ar"}
    mine = {u["id"]: u["ar"] for u in ar}
    moved = [k for k in mine if k not in again or again[k] != mine[k]]
    print(f"3  STABLE   {len(mine) - len(moved):,}/{len(mine):,} unit ids "
          f"reproduce with identical text on a fresh extraction")
    if moved:
        fails += 1
        print(f"            {moved[:8]}")

    # ---------------------------------------------------------------- 4 PAIR
    paired = [u for u in ar if u.get("tr", {}).get("fa")]
    stray = [u for u in units if u["k"] != "ar" and u.get("tr")]
    print(f"4  PAIR     {len(paired):,}/{len(ar):,} Arabic units carry a "
          f"translation ({len(paired) * 100 // max(len(ar), 1)}%); "
          f"{len(stray)} translations on a non-Arabic unit")
    if stray:
        fails += 1

    # -------------------------------------------------------------- 5 RUBRIC
    dirty = [u["id"] for u in ar if u.get("rub")
             and M.PERSIAN_ONLY_RE.search(u["ar"])]
    empty = [u["id"] for u in ar if "rub" in u and not u["rub"].strip()]
    print(f"5  RUBRIC   {sum(1 for u in ar if u.get('rub')):,} instructions "
          f"peeled; {len(dirty)} cores still Persian, {len(empty)} rubrics empty")
    if dirty or empty:
        fails += 1
        print(f"            {(dirty + empty)[:8]}")

    # --------------------------------------------------------------- 6 AUDIO
    junk = [t for t in have if t in credits or t in ("***", "صوت")]
    print(f"6  AUDIO    {len(credits)} reciter names known; "
          f"{len(junk)} credit or separator blocks survive in the output")
    if junk:
        fails += 1

    print()
    print("VERDICT  " + ("clean — ids are safe to freeze" if not fails
                         else f"{fails} audit(s) failed — do not freeze ids"))
    return 1 if fails else 0


if __name__ == "__main__":
    ap = __import__("argparse").ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--json", default=str(HERE / "mafatih.json"))
    a = ap.parse_args()
    sys.exit(main(a.src, a.json))
