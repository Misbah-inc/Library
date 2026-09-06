#!/usr/bin/env python3
"""Ghaemiyeh مفاتیح الجنان export  ->  mafatih.json

The export is unusually good to us: it does not merely contain the Arabic and
the Persian, it *pairs* them. Every Arabic run is a <SPAN class=content_text>,
and the <A class=content_notelink> immediately after it carries that run's own
translation, both in its title attribute and in a footnote <DIV> at the foot of
the printed page:

    <SPAN class=content_text>وَ افْتَحِ اَللّٰهُمَّ لَنَا مَصَارِيعَ الصَّباحِ …</SPAN>
    <A title="خدایا! درهای روز را … بگشا" href="#content_note_161_1">(1)</A>
    …
    <DIV id=content_note_161_1 class=content_note>1- خدایا! درهای روز را … بگشا</DIV>

So the alignment is given, not inferred. The footnote numbering exists only
because print forces the translation to the bottom of the page; on screen the
number disappears and the pairing becomes the layout.

The footnote DIV is treated as authoritative and the title as the fallback: the
DIV holds the full text, while a title attribute can be truncated by whatever
produced the export.

Two structural decisions are made here and must never be revisited, because
English and Urdu will be keyed to them:

  * UNIT IDS are assigned once, in document order, as "<section-id>:<n>".
    Re-running the extractor on the same input must reproduce them exactly.
  * A phrase SPLIT BY A PAGE BREAK is rejoined into one unit, and so is its
    translation. Print pagination is not a reading unit; leaving the split in
    would hand the reader two half-sentences. The page number survives as an
    anchor on the unit it opens.
"""
import argparse, hashlib, html, json, pathlib, re, sys

sys.stdout.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------- tokenising

HEAD  = re.compile(r'<H([1-6])[^>]*>(.*?)</H\1>', re.S | re.I)
SPAN  = re.compile(r'<SPAN[^>]*class=["\']?content_text["\']?[^>]*>(.*?)</SPAN>', re.S | re.I)
LINK  = re.compile(r'<A\s+([^>]*?)class=["\']?content_notelink["\']?[^>]*?'
                   r'href=["\']?#content_note_(\d+)_(\d+)["\']?[^>]*>', re.S | re.I)
NOTE  = re.compile(r'<DIV\s+id=["\']?content_note_(\d+)_(\d+)["\']?[^>]*'
                   r'class=["\']?content_note["\']?[^>]*>(.*?)</DIV>', re.S | re.I)
TITLE = re.compile(r'title=["\'](.*?)["\']', re.S)
PAGE  = re.compile(r'^ص\s*:?\s*([0-9۰-۹]+)$')

ZWNJ = "‌"
PERSIAN_ONLY = set("پچژگ")
FA_DIGITS = "۰۱۲۳۴۵۶۷۸۹"


def clean(s):
    """Strip tags and entities but keep the text's own spacing intact."""
    s = re.sub(r"<BR[^>]*>", " ", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"[ \t\r\n]+", " ", html.unescape(s)).strip()


def fa_int(s):
    return int("".join(str(FA_DIGITS.index(c)) if c in FA_DIGITS else c for c in s))


DIA = re.compile(r"[ً-ْٰ]")
# The honorifics — (عَلَيهِ السَّلَامُ), (صَلَّى اللّه عَلَيْهِ وَ آلِهِ وَسَلَّمَ) — are fully
# vocalised Arabic embedded in Persian sentences, and they are always
# parenthesised. Left in, they make a short Persian rubric look Arabic.
HONORIFIC = re.compile(r"\([^)]*\)")


def is_arabic(t):
    """Arabic duʿā text vs Qummi's Persian rubric. A run that owns a translation
    is Arabic by construction; this is only for the runs that do not.

    The edition vocalises its Arabic fully and its Persian not at all, so mark
    density separates them by two orders of magnitude: 0.373 against 0.009 at
    the median, measured over the 4,001 runs the markup already proves Arabic
    and the 2,028 it proves Persian."""
    if any(c in PERSIAN_ONLY for c in t) or ZWNJ in t:
        return False
    core = HONORIFIC.sub(" ", t)
    if len(re.findall(r"[؀-ۿ]", core)) < 3:      # too short to measure: trust the marks
        return bool(DIA.search(t))
    return len(DIA.findall(core)) / max(len(core), 1) > 0.05


PERSIAN_ONLY_RE = re.compile("[پچژگ‌]")
DIA_RE  = re.compile("[ً-ْٰ]")
ARCH_RE = re.compile("[؀-ۿ]")


def _dens(t):
    return len(DIA_RE.findall(t)) / max(len(ARCH_RE.findall(t)), 1)


QUOTED = re.compile(r"\([^)]*\)|«[^»]*»|\"[^\"]*\"")


def _tail_is_arabic(head):
    """Does this head END in Arabic — i.e. would cutting here slice a duʿā?

    Measured with parenthesised and quoted Arabic removed. An instruction
    routinely names the words it is introducing — «(اللّه أَكْبَرُ) گفته و سپس
    بگو:» — and counting that quotation makes the instruction look like body
    text, so a real boundary gets refused."""
    core = QUOTED.sub(" ", head)[-40:]
    return _dens(core) > 0.15


def _is_body(t):
    """Sustained, vocalised, Persian-free Arabic — the thing a duʿā is made of."""
    return (len(t) >= 20 and not PERSIAN_ONLY_RE.search(t[:80])
            and _dens(t[:80]) > 0.15 and _dens(t) > 0.15)


def split_rubric(t):
    """Peel Qummi's Persian instruction off the head of an Arabic run.

    The export's <SPAN> boundaries follow the printed page, not the sense, so a
    line like «پس سه مرتبه می گویی: اَللّٰهُمَّ صَلِّ …» arrives as one run: the
    instruction telling the reader what to do, fused to the words they are to
    say. Left fused it renders as duʿā body in Amiri, and the footnote's
    translation — which covers only the Arabic — reads as a translation of the
    instruction too. 849 runs are shaped this way.

    Two restraints, both learned by getting it wrong:

    * Only the HEAD is peeled, never the tail and never the middle. One Arabic
      unit carries exactly one translation, so cutting the core in two would
      leave half the duʿā translated and half not. An aside left inline is a
      blemish; an orphaned translation is a wrong reading.
    * The peel only happens when what remains is Arabic THROUGHOUT. A unit like
      «شیخ طوسی … روایت کرده: هرکه پس از «قُل هُوَ اللّٰهُ» …» is Persian prose
      quoting Arabic, not an instruction followed by a duʿā, and slicing it at
      the first colon breaks a sentence in half. Those stay whole and are
      flagged `mixed` so the builder can set them as prose.

    Returns (head_fa, arabic).
    """
    # The LAST qualifying boundary, not the first. «… آن را از «مصباح المتهجد»
    # روایت می نمایم و آن دعای شریف این است: اَللّٰهُمَّ …» offers two: the quote
    # mark around the book title, and the colon that actually introduces the
    # duʿā. Taking the first leaves a clause of Persian at the head of Kumayl.
    best = None
    for m in re.finditer(r"[:：؛»]\s*|\s«", t):
        q = m.end()
        core, head = t[q:], t[:q]
        if (_is_body(core) and not PERSIAN_ONLY_RE.search(core)
                and not is_arabic(head)
                # …and the head must not itself END in Arabic, or a colon
                # inside the duʿā would qualify and swallow its opening lines.
                and not _tail_is_arabic(head)):
            best = q
    if best:
        return t[:best].strip(), t[best:].strip()

    ms = list(PERSIAN_ONLY_RE.finditer(t))
    if ms:
        q = re.compile(r"\S*").match(t, ms[-1].end()).end()
        while q < len(t) and t[q] in " 	":
            q += 1
        core = t[q:]
        if _is_body(core) and not is_arabic(t[:q]) and not _tail_is_arabic(t[:q]):
            return t[:q].strip(), core.strip()

    return "", t.strip()


def audio_credits(root):
    """The names that appear inside a «صوت» … «***» run somewhere in the book.

    A few sections carry the credits with the «صوت» marker missing, so the
    anchor alone does not catch them. Guessing from shape would be worse — a
    short Persian block at a section head is usually a real rubric. So the
    names are learned where the markup proves them, and removed elsewhere only
    on an exact match."""
    names = set()

    def visit(n):
        us, i = n["units"], 0
        while i < len(us):
            if us[i].get("k") == "note" and us[i].get("fa") == "صوت":
                i += 1
                while i < len(us) and us[i].get("k") == "note":
                    t = us[i].get("fa", "")
                    if t == "***":
                        i += 1
                        continue
                    if len(t) >= 50:
                        break
                    names.add(t)
                    i += 1
                continue
            i += 1
        for c in n["children"]:
            visit(c)

    visit(root)
    names.discard("")
    return names


def strip_audio(units, credits=frozenset()):
    """This edition is produced alongside an app, so each piece opens with its
    recitation credits — «صوت», then reciter names separated by «***». 213 of
    them. They are not part of the book, and left in they would take unit ids
    («محَمد باقر الحکیم» has one stray mark and reads as Arabic), shifting every
    id after them."""
    out, i = [], 0
    while i < len(units):
        u = units[i]
        if u.get("k") == "note" and u.get("fa") == "صوت":
            i += 1
            while i < len(units):
                v = units[i]
                if v.get("k") == "page":
                    break
                txt = v.get("fa") or v.get("ar") or ""
                if txt == "***" or (len(txt) < 50 and not v.get("tr", {}).get("fa")):
                    i += 1
                    continue
                break
            continue
        if u.get("k") == "note" and (u.get("fa") == "***" or u.get("fa") in credits):
            i += 1
            continue
        out.append(u)
        i += 1
    return out


def slugify(title, taken):
    """A stable Latin slug. Persian titles transliterate badly, so the well
    known pieces get a hand alias and everything else falls back to a readable
    positional id — an ugly URL is better than a wrong one that later changes."""
    for needle, slug in ALIASES:
        if needle in title:
            base = slug
            break
    else:
        return None
    s, n = base, 2
    while s in taken:
        s, n = f"{base}-{n}", n + 1
    taken.add(s)
    return s


# The pieces people actually link to. Everything else is addressed positionally
# until it earns a name; adding one here later must not change an existing slug.
ALIASES = [
    ("دعای کمیل", "dua-kumayl"), ("دعای ندبه", "dua-nudba"),
    ("دعای سمات", "dua-simat"), ("دعای توسل", "dua-tawassul"),
    ("دعای عدیله", "dua-adila"), ("دعای مشلول", "dua-mashlul"),
    ("جوشن کبیر", "jawshan-kabir"), ("جوشن صغیر", "jawshan-saghir"),
    ("دعای صباح", "dua-sabah"), ("دعای عرفه", "dua-arafa"),
    ("دعای عهد", "dua-ahd"), ("دعای فرج", "dua-faraj"),
    ("مناجات خمس عشره", "munajat-khamsa-ashara"),
    ("زیارت عاشورا", "ziyarat-ashura"), ("زیارت وارث", "ziyarat-warith"),
    ("زیارت اربعین", "ziyarat-arbaeen"), ("زیارت جامعه", "ziyarat-jamia"),
    ("زیارت امین الله", "ziyarat-aminullah"),
    ("زیارت آل یس", "ziyarat-ale-yasin"),
    ("دعای ابوحمزه", "dua-abu-hamza"),
]


# ---------------------------------------------------------------- extraction

def extract(path):
    raw = pathlib.Path(path).read_text(encoding="utf-8", errors="replace")

    notes = {}
    for pg, n, body in NOTE.findall(raw):
        t = clean(body)
        t = re.sub(r"^\d+\s*[-–]\s*", "", t)      # drop the "1- " numbering
        notes[(int(pg), int(n))] = t

    # one linear pass, in document order
    events = []
    for m in HEAD.finditer(raw):
        events.append((m.start(), "head", (int(m.group(1)), clean(m.group(2)))))
    for m in SPAN.finditer(raw):
        events.append((m.start(), "text", clean(m.group(1))))
    for m in LINK.finditer(raw):
        tm = TITLE.search(m.group(1))
        events.append((m.start(), "link",
                       (int(m.group(2)), int(m.group(3)),
                        clean(tm.group(1)) if tm else "")))
    events.sort(key=lambda e: e[0])

    root = {"title": None, "level": 0, "children": [], "units": []}
    stack = [root]
    page = None
    pending = None            # an Arabic run waiting to see if a link follows
    stats = {"units": 0, "paired": 0, "notes": 0, "rejoined": 0, "rubrics": 0}

    def cur():
        return stack[-1]

    def flush_pending():
        """A text run with no link after it: a rubric, or untranslated Arabic."""
        nonlocal pending
        if pending is None:
            return
        t, pg = pending
        pending = None
        if not t:
            return
        if is_arabic(t):
            cur()["units"].append({"k": "ar", "ar": t, "tr": {}, "p": pg})
            stats["units"] += 1
        else:
            cur()["units"].append({"k": "note", "fa": t, "p": pg})
            stats["rubrics"] += 1

    for _, kind, val in events:
        if kind == "head":
            flush_pending()
            lvl, title = val
            while len(stack) > 1 and stack[-1]["level"] >= lvl:
                stack.pop()
            node = {"title": title, "level": lvl, "children": [], "units": [],
                    "page": page}
            cur()["children"].append(node)
            stack.append(node)

        elif kind == "text":
            pm = PAGE.match(val)
            if pm:
                flush_pending()
                page = fa_int(pm.group(1))
                cur()["units"].append({"k": "page", "n": page})
                continue
            # A run arriving while another is pending, with no link between
            # them, is the far side of a page break: rejoin rather than emit
            # two half sentences.
            if pending is not None and pending[0] and val:
                prev = cur()["units"]
                if prev and prev[-1].get("k") == "page":
                    pending = (pending[0] + " " + val, pending[1])
                    stats["rejoined"] += 1
                    continue
                flush_pending()
            else:
                flush_pending()
            pending = (val, page)

        elif kind == "link":
            pg, n, title = val
            tr = notes.get((pg, n)) or title      # the DIV wins; title backs it
            if notes.get((pg, n)):
                stats["notes"] += 1
            if pending is None:
                continue
            t, upg = pending
            pending = None
            if not t:
                continue
            cur()["units"].append({"k": "ar", "ar": t, "tr": {"fa": tr}, "p": upg})
            stats["units"] += 1
            if tr:
                stats["paired"] += 1

    flush_pending()
    return root, stats


def assign_ids(node, taken, titles=(), seen=None, credits=frozenset()):
    """Stable ids, assigned once and never renumbered.

    Derived from the section's TITLE PATH, not its position, and hashed. A
    positional id would look stable and quietly is not: fix a bug that merges
    two sections and every id after it shifts, silently re-pointing whatever
    translations were keyed to them. A title-derived hash only moves if the
    edition's own wording moves, which is the behaviour we want."""
    if seen is None:
        seen, credits = {}, audio_credits(node)
    node["units"] = strip_audio(node["units"], credits)
    for u in node["units"]:
        if u["k"] != "ar":
            continue
        head, core = split_rubric(u["ar"])
        if head:
            u["rub"], u["ar"] = head, core          # rubric renders as prose
        elif PERSIAN_ONLY_RE.search(u["ar"]):
            u["mixed"] = 1                          # Persian prose quoting Arabic
    here = titles
    if node["title"] is not None:
        here = titles + (node["title"],)
        slug = slugify(node["title"], taken)
        node["slug"] = slug
        # Three title paths genuinely repeat — «نماز حاجت» and «نماز دیگر» each
        # appear twice under one parent, «إشارَة:» twice. The nth occurrence is
        # folded into the hash so they separate; document order decides n, and
        # only among sections that already share every title above them.
        seen[here] = n_occ = seen.get(here, 0) + 1
        stem = "␟".join(here) + ("" if n_occ == 1 else f"␟#{n_occ}")
        digest = hashlib.sha1(stem.encode("utf-8")).hexdigest()[:8]
        node["id"] = slug or f"x{digest}"
        node["key"] = digest                 # survives even if a slug is added later
    n = 0
    for u in node["units"]:
        if u["k"] == "ar":
            n += 1
            u["id"] = f'{node.get("id", "root")}:{n}'
    for c in node["children"]:
        assign_ids(c, taken, here, seen, credits)


def walk(node, depth=0, out=None):
    out = [] if out is None else out
    if node["title"] is not None:
        out.append((depth, node))
    for c in node["children"]:
        walk(c, depth + 1, out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--out", default=str(pathlib.Path(__file__).parent / "mafatih.json"))
    a = ap.parse_args()

    root, stats = extract(a.src)
    assign_ids(root, set())

    nodes = walk(root)
    leaves = [n for _, n in nodes if n["units"]]
    print(f"sections            : {len(nodes):,}   ({len(leaves):,} carry text)")
    print(f"Arabic units        : {stats['units']:,}")
    print(f"  with a translation: {stats['paired']:,} "
          f"({stats['paired']*100//max(stats['units'],1)}%)")
    print(f"  translation from the footnote DIV : {stats['notes']:,}")
    print(f"Persian rubric blocks: {stats['rubrics']:,}")
    print(f"phrases rejoined across a page break: {stats['rejoined']:,}")
    allu = [u for _, n in nodes for u in n["units"]]
    print(f"Persian instructions peeled off an Arabic run: "
          f"{sum(1 for u in allu if u.get('rub')):,}")
    print(f"units left whole as Persian prose quoting Arabic: "
          f"{sum(1 for u in allu if u.get('mixed')):,}")
    named = sum(1 for _, n in nodes if n.get("slug"))
    ids = [n.get("id") for _, n in nodes]
    print(f"named slugs assigned : {named}")
    print(f"section ids          : {len(ids):,} total, {len(set(ids)):,} distinct"
          f"  ({'unique' if len(ids) == len(set(ids)) else 'COLLISIONS'})")
    uids = [u["id"] for _, n in nodes for u in n["units"] if u["k"] == "ar"]
    print(f"unit ids             : {len(uids):,} total, {len(set(uids)):,} distinct"
          f"  ({'unique' if len(uids) == len(set(uids)) else 'COLLISIONS'})")

    pathlib.Path(a.out).write_text(
        json.dumps(root, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8")
    print(f"-> {a.out}")


if __name__ == "__main__":
    main()
