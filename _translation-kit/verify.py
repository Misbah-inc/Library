import re, sys, pathlib, html
import extract as E

FAIL = 0
def bad(msg):
    global FAIL; FAIL += 1; print("  FAIL:", msg)

def check(ar_path, en_path):
    src = E.extract(ar_path)
    out = pathlib.Path(en_path).read_text(encoding="utf-8")
    n = src["page"]

    ar_nodes = re.findall(r'<(p|h3) lang="ar" data-i="(\d+)">(.*?)</\1>', out, re.S)
    en_nodes = re.findall(r'<(p|h3) class="tr-line" lang="en">(.*?)</\1>', out, re.S)

    if len(ar_nodes) != len(src["nodes"]): bad(f"p{n}: ar node count {len(ar_nodes)} != {len(src['nodes'])}")
    if len(en_nodes) != len(src["nodes"]): bad(f"p{n}: en line count {len(en_nodes)} != {len(src['nodes'])}")
    if [int(i) for _,i,_ in ar_nodes] != list(range(len(ar_nodes))): bad(f"p{n}: data-i not contiguous")

    for (tag,i,txt), s in zip(ar_nodes, src["nodes"]):
        if txt != s["ar"]: bad(f"p{n}: arabic altered at data-i={i}")
        if tag != s["tag"]: bad(f"p{n}: tag mismatch at data-i={i} ({tag} vs {s['tag']})")
    for tag, txt in en_nodes:
        if not txt.strip(): bad(f"p{n}: empty english line")
        if re.search(r'[؀-ۿ]', re.sub(r'<[^>]+>','',txt)): bad(f"p{n}: arabic left inside an english line")

    # footnotes
    refs = set(re.findall(r'href="#(fn-[\d-]+)"', out))
    notes = set(re.findall(r'class="note" lang="ar" id="(fn-[\d-]+)"', out))
    if refs != notes: bad(f"p{n}: fnref/note mismatch refs={sorted(refs)} notes={sorted(notes)}")
    if len(notes) != len(src["notes"]): bad(f"p{n}: note count {len(notes)} != {len(src['notes'])}")
    for nt in src["notes"]:
        if f'id="{nt["id"]}"' not in out: bad(f"p{n}: note {nt['id']} missing")
        if 'class="tr-note-line"' not in out and src["notes"]: pass
    if src["notes"] and out.count('class="tr-note-line"') != len(src["notes"]):
        bad(f"p{n}: translated-note count wrong")

    # shell sanity
    for must in [f'data-pagenum="{n}"', f'data-pos="{n-1}"', 'data-total="231"',
                 f'<span data-num="{n}">{n}</span>', 'data-tr-static="1"',
                 f'href="../../../../bihar/1/{n}/"', 'lang="en" dir="ltr"',
                 f'<title>Bihar al-Anwar — p. {n}</title>']:
        if must not in out: bad(f"p{n}: missing {must!r}")
    if 'class="edge"' in out or 'id="cite-text"' in out or 'id="drawer"' in out:
        bad(f"p{n}: arabic-only chrome leaked in")
    if re.search(r'lang="ar"[^>]*>\s*</(p|h3)>', out): bad(f"p{n}: empty arabic node")

import os
# usage: verify.py [--root AR_ROOT] [--out OUT_DIR] <page...>
argv = sys.argv[1:]
U = os.environ.get("AR_ROOT", "/mnt/user-data/uploads/Misbah Library/Library")
OUT = os.environ.get("OUT_DIR", "/home/claude/work/out")
while argv and argv[0].startswith("--"):
    flag = argv.pop(0)
    val = argv.pop(0)
    if flag == "--root": U = val
    elif flag == "--out": OUT = val
pages = [int(x) for x in argv]
for p in pages:
    check(f"{U}/bihar/1/{p}/index.html", f"{OUT}/{p}-draft/index.html")
print(f"\n{len(pages)} pages checked — {FAIL} failures")
sys.exit(1 if FAIL else 0)
