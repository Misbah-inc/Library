# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Site

**https://library.misbah-inc.com** — a custom domain on GitHub Pages. The repo root is served at the domain root. Pure static HTML: no SSG framework, no build step other than the Python scripts in `_translation-kit/`.

---

## Architecture

### Two-layer content model

**Arabic source of record** lives in `bihar/<vol>/<n>/index.html`. It is never altered — not even reformatted.

**Translations** live in `<lang>/bihar/<vol>/<n>/index.html` (lang = `en`, `fa`, `ur`). They are built from the Arabic source by the pipeline below.

**In-page language switching** (without navigation) is powered by `bihar/assets/tr/<lang>.json` — plain-text strips with markup stripped. These carry both body entries (`{"i": 0, "text": "…"}`) and footnote entries (`{"n": 1, "text": "…"}`). They are separate from the built pages and cannot reconstruct them.

### Build pipeline (`_translation-kit/`)

```
extract.py → [external translation] → merge_build.py → verify.py → commit
```

| Script | Role |
|---|---|
| `extract.py` | Arabic page → JSON of `data-i` nodes + footnotes |
| `merge_build.py` | translation module + Arabic source → built pages |
| `build.py` | page template, called by `merge_build.py` |
| `verify.py` | checks built page against Arabic source — **must report 0 failures before commit** |
| `reextract.py` | built page → JSON, losslessly (for re-templating without retranslating) |
| `gen_sitemap.py` | rewrites `sitemap.xml` and `robots.txt` from what is on disk |

All of `build.py`, `merge_build.py`, and `verify.py` accept `--lang` (`en`/`fa`/`ur`) and `--volume`.

### Shared assets

One CSS file (`assets/reader.css`), one JS file (`assets/reader.js`), six web fonts (Amiri for Arabic, Oswald for UI, Vazirmatn for Persian/Urdu). No frameworks.

---

## Common commands

**Build translated pages from an existing translation module:**
```bash
python3 _translation-kit/merge_build.py tr_<lang>_<a>_<b> <outdir> --lang ur --volume 1 <ar files…>
```

**Verify before committing:**
```bash
python3 _translation-kit/verify.py <pages…> --lang ur --volume 1 --root <ar root> --out <outdir>
```

**Extract Arabic pages to JSON for translation:**
```bash
python3 _translation-kit/extract.py <ar files…> > batch.json
```

**Regenerate pages after a template change (no retranslation needed):**
```bash
python3 _translation-kit/reextract.py --lang ur <built pages…> > batch.json
python3 _translation-kit/build.py batch.json <outdir> --lang ur --volume 1
python3 _translation-kit/verify.py <pages…> --lang ur --out <outdir>
```

**Regenerate sitemap after adding pages:**
```bash
python3 _translation-kit/gen_sitemap.py --root "G:/My Drive/Misbah Library/Library"
```

**Bulk edits across ~900 files (PowerShell on Windows):**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
# then run the script — see Fix-LibrarySeo.ps1 as the worked example
```
Always read/write with `[System.IO.File]::ReadAllText/WriteAllText` and `UTF8Encoding($false)`. PowerShell's default `Set-Content` silently corrupts Arabic, Urdu, and Farsi.

**Test JS changes locally before committing:**
```powershell
cd "G:\My Drive\Misbah Library\Library"
python -m http.server 8080
```
Then open `http://localhost:8080`. This avoids CORS issues that block `catalog.json` fetches when opening `file://` directly.

---

## `reader.js` invariants — easy to get silently wrong

`assets/reader.js` is the single JS file for the entire site. Changes here affect every page.

- **`bookCard()` must generate language-aware hrefs.** For books that have a `translated` array, the link must be prefixed with the current language when `lang !== 'ar'`. The pattern: `lang + '/' + b.href` (e.g. `en/bihar/`). This links to the language-specific book index page, not directly to a reading page. Without this, English/Farsi/Urdu users clicking a book card land on the Arabic URL — the bug is invisible until you test with a non-Arabic language active.
- **Each translated book needs a language book index page** at `<lang>/<book>/index.html` (e.g. `en/bihar/index.html`). These are copies of `<book>/index.html` with `data-root="../.."`, `data-book="../../<book>"`, `data-sitelang="<lang>"`, and `href="../../"` for all Library root links. The active vol link must include `data-vol="<n>"` and a fallback `href="<n>/1/"`. The hreflang cluster (all languages + ar + x-default) must be present in `<head>` so the language switcher can navigate between them.
- **`applyLang()` must rewrite `.vols a.vol` links.** Book index pages have volume links. These are rewritten to `ROOT + '/' + lang + '/' + slug + '/' + v + '/1/'` when a non-Arabic language is active. The slug is inferred from `location.pathname`. The original volume number is cached in a `data-vol` attribute on first call.
- **Book index pages have no `#page-meta` with `data-alt-*`.** The language switcher uses hreflang links to navigate between language book index pages when `FIXED` is set. Add `<link rel="alternate" hreflang="...">` for all languages in each language book index `<head>`.
- **The Quran sura links already handle this correctly** (lines ~162–165) — use that pattern as the reference when extending for new book types.

---

## SEO invariants — easy to get silently wrong

- **Canonical and hreflang URLs are absolute.** `build.py` emits them from the `SITE` constant. If the domain ever changes, update `SITE` in `build.py` and in `gen_sitemap.py`, then rebuild all pages.
- **The hreflang set is reciprocal and self-referential.** Every published version of a page must list every other published version including itself. A one-directional cluster is ignored wholesale.
- **`x-default` points at the Arabic** (source of record).
- **`--alts` must match what is live.** Listing a language whose pages don't exist points hreflang at a 404 and invalidates the whole cluster. Widen `--alts` and rebuild as each translation lands.
- **Never advertise a `-draft` page.** `gen_sitemap.py` and `Fix-LibrarySeo.ps1` both skip them.
- Draft pages are placed at `<lang>/bihar/<vol>/<n>-draft/`. Renaming them into place is the owner's decision.

---

## Working via Google Drive (no local path)

The library lives at `G:\My Drive\Misbah Library`. Scheduled or remote runs can reach the same files through the Google Drive MCP connector (`mcp__Google_Drive__*`, deferred — load with ToolSearch).

Key folder IDs:

| What | Drive folder ID |
|---|---|
| Arabic `bihar/1/` | `1Azs5MZukGcHo9BjoQDdMZYZhcWA_KCoY` |
| English `en/bihar/1/` | `1ob05LhboBZ0d1PM30A1jONHAu0dXthwo` |
| `_translation-kit/` | `1VitPwwF9fJ0hnAXphK0XvxHgeJLbMJR6` |

Drive rules: `create_file` always creates (no replace). To overwrite: `search_files` → `trash_file` → `create_file`. Always pass `disableConversionToGoogleType: true` — without it HTML becomes a Google Doc and is destroyed. Page through large folders with `pageSize: 100` and `pageToken`.

---

## Translation conventions

- Literal and fidelity-first; narrator names transliterated, not anglicized.
- `b.` for ibn; `al-` prefixes kept; `&#x27;` for hamza/ayn; `&quot;` for quotes.
- *ḥaddathanā* → "There related to us"; *akhbaranā* → "There informed us"; *ḥaddathanī* → "There related to me".
- `بيان` → "Elucidation:"; `إيضاح` → "Clarification:"; `أقول` → "I say:".
- Book sigla keep both letter and expansion: `sn, al-Mahasin`; `l, al-Khisal`; `nhj, the Nahj al-Balagha`; `b, Qurb al-Isnad`.
- Editorial footnotes signed `ط` end with " T." in English.
- Qur'anic quotations translated fresh, in double quotes.
- For Urdu and Farsi, `verify.py` cannot detect untranslated Arabic (both use Arabic script) — those batches need a human eye on a sample.

---

## Page addition checklist

Every time a new HTML page is added to the site (new language book index, new reading page, new section):

1. Run `gen_sitemap.py` to regenerate `sitemap.xml`
2. Update `CHANGELOG.md` with what was added
3. Owner commits and pushes both files along with the new pages

Google picks up the updated sitemap automatically — no need to resubmit to Search Console.

---

## Standing constraints

- **Never touch GitHub.** No clone, commit, push, or Actions. Writing into the library folder is the limit; committing and pushing is the owner's job alone.
- **Never commit a page that fails `verify.py`.**
- **Never alter Arabic text or any existing translation.** This is absolute. Structural `<head>` changes (canonical, hreflang) require the owner's explicit approval each time.
- **The machine-translation badge stays on every generated page.** Readers are told to cite the Arabic.

---

## Current state

| Tree | Pages | State |
|---|---|---|
| `bihar/1/` (Arabic, source) | 231 | Complete |
| `en/bihar/1/` | 231 | Complete, machine translation |
| `fa/bihar/1/` | 231 | Complete, machine translation |
| `ur/bihar/1/` | 231 | Complete, machine translation |

Volumes 2–110 not started. All other books in `catalog.json` are placeholders.
