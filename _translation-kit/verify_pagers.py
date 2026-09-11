#!/usr/bin/env python3
"""Check that every paginated book's prev/next chain is a single unbroken path.

    python verify_pagers.py                 # whole library
    python verify_pagers.py --root <path>

Why this exists. `verify.py` proves a translated page carries the right text.
Nothing proved it carried the right *navigation*, and for months
`fa/bihar/1/48` linked "next" to page 81 while `fa/bihar/1/84` had no next link
at all — a reader going straight through skipped 32 pages, or stopped dead. The
text on every one of those pages was perfect, so every check the project had
passed them.

The fault came from a superseded builder that chained prev/next from the
neighbouring entries in a TRANSLATION BATCH rather than from the page number.
Batches are not contiguous runs, so wherever a batch jumped the chain jumped
with it, and wherever a batch ended the chain ended. Today's `build.py` derives
both arithmetically and cannot reproduce it — but nothing stops a future
builder from reintroducing the same shape, and nothing would have told us.

HOW IT CHECKS — it walks the chain rather than assuming page N links to N+1.
That assumption is wrong for two books already in the library: the Farsi Bayt
al-Ahzan has 31 deliberate gaps in its numbering, and مفاتیح interleaves named
slugs (`dua-kumayl`) with ordinals, so its neighbours are not numeric
neighbours at all. Following the links instead is both stricter and general:

  * every prev/next href must resolve to a real page in the same book
  * `next` and `prev` must be inverses of each other
  * exactly one page may lack a prev, and exactly one may lack a next
  * starting from that head and following `next` must visit EVERY page in the
    book exactly once — which is what catches both a chain that skips pages and
    one that dead-ends in the middle
  * `<link rel=prev/next>` in <head> must agree with the pager buttons, since
    the two are written separately and only the buttons were ever eyeballed
  * `data-pagenum`, where present, must match the folder the page sits in

A page is anything with an index.html that contains a pager. Covers, category
pages and volume selectors have none, so they are skipped without special
cases.

Exit code is non-zero if anything fails, so it can gate a commit.
"""
import argparse, collections, os, pathlib, re, sys

sys.stdout.reconfigure(encoding="utf-8")

PAGER = re.compile(r'<nav class="pager">(.*?)</nav>', re.S)
BTN = r'class="btn %s" href="([^"]+)"'
HEADLINK = r'<link rel="%s" href="([^"]+)"'
PAGENUM = re.compile(r'data-pagenum="([^"]+)"')
DISABLED = re.compile(r'aria-disabled="true"><span data-i18n="(prev|next)"')


SITE = "https://library.misbah-inc.com"


def resolve(page_dir, href, root):
    """A pager href -> the page directory it points at, or None.

    The pager buttons are relative («../2/») but the <head> links are absolute
    («https://library.misbah-inc.com/mafatih/2/»), because canonical and
    hreflang have to be absolute and prev/next are written beside them. Both
    forms have to land on the same directory or the comparison between them is
    meaningless — resolving the absolute one as if it were relative reported
    every page in the library as broken."""
    if not href:
        return None
    href = href.split("#")[0].split("?")[0]
    for prefix in (SITE, "http://library.misbah-inc.com"):
        if href.startswith(prefix):
            href = href[len(prefix):]
            break
    if href.startswith("//") or href.startswith("http"):
        return None                      # some other host: not our page
    if href.startswith("/"):
        return pathlib.Path(os.path.normpath(root / href.lstrip("/")))
    return pathlib.Path(os.path.normpath(page_dir / href))


def scan(root):
    """Every directory holding a page with a pager, grouped by its parent."""
    books = collections.defaultdict(list)
    for f in root.rglob("index.html"):
        if any(part.startswith((".", "_")) for part in f.relative_to(root).parts):
            continue
        try:
            s = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if '<nav class="pager">' not in s:
            continue
        books[f.parent.parent].append((f.parent, s))
    return books


def check(book, entries, root):
    pages = {d.resolve(): d for d, _ in entries}
    bad = []
    nxt, prv = {}, {}

    for d, s in entries:
        here = d.resolve()
        nav = PAGER.search(s).group(1)
        dead = set(DISABLED.findall(nav))

        pn = PAGENUM.search(s)
        if pn and pn.group(1) != d.name:
            bad.append((d.name, f"data-pagenum={pn.group(1)} but sits in /{d.name}/"))

        for rel, table in (("prev", prv), ("next", nxt)):
            m = re.search(BTN % rel, nav)
            target = resolve(d, m.group(1), root) if m else None
            if target is not None:
                t = target.resolve()
                if t not in pages:
                    bad.append((d.name, f"{rel} -> {m.group(1)} , which is not a "
                                        f"page of this book"))
                else:
                    table[here] = t
            elif rel not in dead:
                bad.append((d.name, f"{rel} button is missing entirely"))

            h = re.search(HEADLINK % rel, s)
            ht = resolve(d, h.group(1), root) if h else None
            if (ht.resolve() if ht else None) != (target.resolve() if target else None):
                bad.append((d.name, f"<link rel={rel}> and the {rel} button disagree "
                                    f"({h.group(1) if h else 'absent'} vs "
                                    f"{m.group(1) if m else 'absent'})"))

    # next and prev must be inverses
    for a, b in nxt.items():
        if prv.get(b) != a:
            bad.append((pages[a].name, f"next is {pages[b].name}, but that page's "
                                       f"prev is "
                                       f"{pages[prv[b]].name if prv.get(b) in pages else 'absent'}"))

    heads = [p for p in pages if p not in prv]
    tails = [p for p in pages if p not in nxt]
    for lst, what in ((heads, "no prev"), (tails, "no next")):
        if len(lst) != 1:
            for p in sorted(lst, key=lambda x: pages[x].name)[:6]:
                bad.append((pages[p].name, f"has {what}; only one page in a book may"))

    # the walk: from the head, following next must cover every page once
    if len(heads) == 1:
        seen, cur, order = set(), heads[0], 0
        while cur is not None and cur not in seen:
            seen.add(cur)
            cur = nxt.get(cur)
            order += 1
        if len(seen) != len(pages):
            missed = sorted((pages[p].name for p in pages if p not in seen),
                            key=lambda x: (len(x), x))
            bad.append((pages[heads[0]].name,
                        f"the chain reaches {len(seen)} of {len(pages)} pages; "
                        f"unreachable: {', '.join(missed[:10])}"
                        + (" …" if len(missed) > 10 else "")))
    return pages, bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(pathlib.Path(__file__).parent.parent))
    a = ap.parse_args()
    root = pathlib.Path(a.root).resolve()

    books = scan(root)
    total = 0
    for book in sorted(books, key=lambda p: str(p)):
        entries = books[book]
        if len(entries) < 2:
            continue
        pages, bad = check(book, entries, root)
        total += len(bad)
        label = str(book.relative_to(root)).replace(os.sep, "/") or "(root)"
        print(f"  {label:28} {len(pages):>4} pages   "
              f"{'OK' if not bad else '** ' + str(len(bad)) + ' BROKEN **'}")
        for n, why in bad[:12]:
            print(f"        {n}: {why}")
        if len(bad) > 12:
            print(f"        … {len(bad) - 12} more")

    print()
    print("VERDICT  " + (f"{len(books)} paginated book(s); every prev/next chain is a "
                         f"single unbroken path over all pages"
                         if not total else
                         f"{total} broken link(s) — do not commit"))
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
