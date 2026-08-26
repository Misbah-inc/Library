import json, sys, html, pathlib, importlib
import extract as E, build as B

def escape_en(s):
    """Convert plain quotes to the entities the existing en/ pages use."""
    return s.replace("&", "&amp;").replace("'", "&#x27;").replace('"', "&quot;")

def run(trmod, ar_paths, outdir):
    tr = importlib.import_module(trmod)
    built = []
    for p in ar_paths:
        page = E.extract(p)
        n = page["page"]
        lines = tr.PAGES[n]
        if len(lines) != len(page["nodes"]):
            sys.exit(f"page {n}: {len(lines)} translations vs {len(page['nodes'])} nodes")
        for nd, en in zip(page["nodes"], lines):
            nd["en"] = escape_en(en)
        for nt in page["notes"]:
            if nt["id"] not in tr.NOTES:
                sys.exit(f"page {n}: missing translation for note {nt['id']}")
            nt["en"] = escape_en(tr.NOTES[nt["id"]])
        d = pathlib.Path(outdir) / f"{n}-draft"
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(B.build(page), encoding="utf-8")
        built.append((n, len(page["nodes"]), len(page["notes"])))
    return built

if __name__ == "__main__":
    mod, out = sys.argv[1], sys.argv[2]
    for n, nn, nt in run(mod, sys.argv[3:], out):
        print(f"  p.{n:>3}  {nn} nodes, {nt} notes")
