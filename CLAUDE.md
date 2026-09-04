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
| `quran_build.py` | Tanzil XML → surah pages in all four languages |
| `bayt_extract.py` | Ghaemiyeh HTML export → batch JSON (Bayt al-Ahzan) |
| `bayt_paginate.py` | splits Bayt al-Ahzan at its `[ صفحه ۷۷ ]` markers into printed pages |
| `bayt_build.py` | Bayt al-Ahzan page builder, cover, and `toc.json` |
| `Fix-LibrarySeo.ps1` | one-off bulk `<head>` repair across the tree (PowerShell) |
| `Set-AssetVersion.ps1` | stamps `?v=N` on `reader.css`/`reader.js` sitewide |

All of `build.py`, `merge_build.py`, and `verify.py` accept `--lang` (`en`/`fa`/`ur`) and `--volume`.

**`Set-AssetVersion.ps1` is not routine.** It rewrites every page in the repo, which
makes a ~950-file diff out of a one-file change and buries any real edit in the same
commit. The site currently carries no version query and does not need one: GitHub
Pages serves `assets/` with a short max-age, so a hard refresh (Ctrl-Shift-R, or
pull-to-refresh twice on mobile) is the first thing to try when a JS change looks
like it did not land. Reach for the stamp only after a hard refresh has been tried
and failed, and get the owner's agreement first — a bulk rewrite is their call.

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

**Rebuild Bayt al-Ahzan (source of record is `_translation-kit/bayt.json`):**
```bash
python3 _translation-kit/bayt_paginate.py _translation-kit/bayt.json > bayt_pages.json
python3 _translation-kit/bayt_build.py bayt_pages.json --index --out bayt-al-ahzan
python3 _translation-kit/bayt_build.py bayt_pages.json --toc   --out bayt-al-ahzan
python3 _translation-kit/bayt_build.py bayt_pages.json --lang fa --alts fa --out bayt-al-ahzan-fa
```
`bayt.json` is the 100%-fidelity extraction of the Ghaemiyeh HTML export (that export
is not in the repo). `bayt_pages.json` is derived and need not be committed. If the
page set ever changes, **delete `bayt-al-ahzan-fa/` first** — the builder writes pages
but never removes ones that no longer exist, and a stale directory is a live wrong page.

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
- **`.suras` belongs to the Qur'an alone.** `applyLang()` rewrites `.suras a[data-n]`
  to `/<lang>/quran/<n>/` with the path hardcoded. Reusing the class on any other
  book's cover silently redirects its chapters into the Qur'an — chapters 1–2 land on
  real surahs, the rest 404. A chapter grid on any other book uses `.chaps` with
  `data-langpath="<slug>"` and `data-langs="<langs that actually have pages>"`; the
  `.chaps` handler reads both and never guesses. `.chap-cell` shares `.sura-cell`'s
  styling, so nothing new is needed in CSS.
- **`data-book` must point at a folder that has `assets/`.** `btn-toc` loads
  `BOOK + '/assets/toc.json'`. If `data-book` points at the language folder rather
  than the book's root, Contents fails with "Could not load" and nothing else says why.
- **The jump form's `data-tpl` is resolved against the site root**, not the page. It
  must carry the book's own slug (`bayt-al-ahzan-fa/{p}/`), or the box sends readers
  to the Arabic slot.
- **`.cite` is `display:none` on `en`, `fa` and `ur`** by the owner's request. A book's
  credit or attribution line must use `.book-credit`, or it disappears in three of the
  four languages.

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

## Committing from Google Drive — the failure mode to recognise

The repo lives on a streamed Google Drive folder. That works for ordinary commits and
has for months, but a large batch of new files can wedge it, and the symptom is
misleading.

**What it looks like.** GitHub Desktop fails with

```
error: unable to write file .git/objects/<xx>/<hash>: Permission denied
error: <some/path>: failed to insert into database
```

**What it actually is.** Git writes each object to a temp file and then *renames* it
into place. Drive still holds the temp file open while it uploads, so the rename fails.
Run the same `git add -A` in a terminal and git shows what Desktop hides:

```
Rename from '.git/objects/0c/tmp_obj_XXXX' to '.git/objects/0c/<hash>' failed.
Should I try again? (y/n)
```

Desktop runs git non-interactively, cannot answer, and reports the question as
"Permission denied". **Desktop is not the problem and does not need to be abandoned.**

**Do not** answer `y` repeatedly — if the same temp file and target repeat unchanged,
the failure is permanent, not transient, and the loop is infinite.

**Do not** create directories by hand inside `.git/objects` to "help" git. It does not
help, and it risks leaving a directory entry Drive reports as both existing and not
existing, which is worse than what you started with.

**The fix, in order:**

1. **Restart Google Drive** — tray icon → ⚙ → Quit, then reopen. This clears the stuck
   handle and the phantom directory entries. *This is what worked.* Try it first and
   expect it to be enough.
2. `rmdir /s /q "<repo>\.git\objects\<xx>"` from **Command Prompt** for the specific
   directory named in the error. Git recreates it cleanly.
3. If the object store is genuinely damaged, clone the repo to a local disk to obtain a
   healthy `.git`, copy that folder over the broken one on Drive, and carry on from
   Drive as before. The working files never need to move.

Prevention: let Drive finish syncing before committing a large batch, and prefer adding
files in a few hundred at a time over several thousand at once.

The `LF will be replaced by CRLF` warnings are unrelated noise. Git stores LF; Windows
checkouts get CRLF; the published files are unaffected.

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

## SEO checklist

### Current status
| Item | Status |
|---|---|
| `robots.txt` — allows all, points to sitemap | ✅ |
| `sitemap.xml` — 1,173 URLs, submitted to Search Console | ✅ |
| HTTPS (GitHub Pages) | ✅ |
| Clean URL structure (`/en/bihar/1/26/`) | ✅ |
| Canonical URL on every page (absolute) | ✅ |
| hreflang cluster on every translated page (reciprocal, all 4 languages + x-default) | ✅ |
| `lang` + `dir` attributes on `<html>` | ✅ |
| Meta description on every reading page (from page content) | ✅ |
| Mobile-friendly / responsive | ✅ |
| Page titles include meaningful content | 🟡 Generic — deferred |
| Schema.org structured data | 🟠 Not done — deferred |
| Core Web Vitals (PageSpeed) | ✅ 95 Performance / 87 Accessibility / 100 Best Practices / 100 SEO (mobile, Aug 2026) |
| Backlinks from other sites | 🔴 Future project |

### SEO rules — apply on every change
- Every new page must have `<link rel="canonical">` with absolute URL
- Every translated page must have the full hreflang cluster (all 4 languages + x-default, reciprocal)
- Never list a `-draft` page in sitemap or hreflang
- Meta descriptions must come from page content, never generic
- Run `gen_sitemap.py` after adding any page and commit the result
- Update `CHANGELOG.md`

### Google Search Console — check monthly
- **Pages**: how many indexed vs. discovered
- **Coverage**: any crawl errors or excluded pages
- **Core Web Vitals**: any failing pages
- **Performance**: which queries bring traffic, which pages rank

---

## Page addition checklist

Every time a new HTML page is added to the site (new language book index, new reading page, new section):

1. Run `gen_sitemap.py` to regenerate `sitemap.xml`
2. Update `CHANGELOG.md` with what was added
3. Owner commits and pushes both files along with the new pages

Google picks up the updated sitemap automatically — no need to resubmit to Search Console.

### Adding a whole new book

On top of the above, before the owner is asked to commit:

1. **Resolve every generated link against the tree that will exist**, in all four
   languages, including what `applyLang()` rewrites them to. Every bug this project
   has shipped was a link that pointed at a folder nobody created.
2. **Check every `data-i18n` key against all four language tables** in `reader.js`.
   `t()` returns the key itself when it is missing, so a forgotten key shows up as the
   literal word `pickChapter` on the page rather than as an error.
3. **Diff the emitted text against the source JSON block for block.** Escaping and
   heading-tag bugs are invisible in a rendered page.
4. Confirm no page carries `?v=`, and that nothing outside the new book was touched.

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
| `bihar/`, `en|fa|ur/bihar/` | 4 | Volume selector pages |
| `quran/` + `quran/1–114/` | 115 | Cover and all 114 surahs, Arabic |
| `en|fa|ur/quran/1–114/` | 342 | Shakir · فولادوند · علامہ جوادی |
| `quran/assets/` | — | `toc.json`, `qnav.json`, `qnav.js` (Contents, quick access, paging) |
| `bayt-al-ahzan/` | 1 | Arabic cover (5 chapters, دار الحكمة edition, Bihar-style) |
| `bayt-al-ahzan/1–189/` | 189 | Arabic original (Qummi), pages 1–189 |
| `bayt-al-ahzan-fa/` | 1 | Farsi cover |
| `bayt-al-ahzan-fa/1–262/` | 262 | Complete Persian text (Ishtihardi), printed pages |
| `jame-al-muqaddimat/` | 1 | Volume selector |
| `jame-al-muqaddimat/1/` + `1/1–609/` | 610 | Vol 1 contents + pages, 9 treatises |
| `jame-al-muqaddimat/2/` + `2/1–607/` | 608 | Vol 2 contents + pages, 6 treatises |

**جامع المقدمات (2026-09-03).** Multi-volume, Bihar-shaped: `/jame-al-muqaddimat/<vol>/<page>/`.
Persian commentary around Arabic matn, so every block carries its own `lang` (`ar`/`fa`)
and the two set in different faces; `data-standalone="1"` as on Bayt al-Ahzan, since it
lives at its own top-level slug rather than under `/fa/`. Built by `jame_extract.py`
(Ghaemiyeh export → `jame_pages.json`) then `jame_build.py`.

> Its `assets/toc.json` is **book-level, not per volume**. reader.js rewrites `BOOK` to
> `ROOT + '/' + data-slug` on any page with `data-sitelang`, so a per-volume toc.json is
> never fetched and the drawer silently comes up empty. Any future multi-volume book has
> the same constraint.

> Page markers in this export (`ص :137`) **close** the page they name — the opposite of
> Bayt al-Ahzan's `[ صفحه N ]`, which opens it. Check the tail of a new export before
> assuming either way.

**Tashkīl.** The source is unvocalised (~0.5%). کتاب الامثله (vol 1 pp. 11–14) has been
vocalised — 13 blocks, 583 marks — by `jame_tashkil.py`, which enforces two rules any
future treatise must also follow:

1. **Add marks only, never substitute a letter.** The source writes `اضرب` and `ضاربه`,
   not `أضرب`/`ضاربة`; changing those is editing, not vocalising. Verified per block by
   `strip_diacritics(vocalised) == original`, exact — the build fails otherwise.
2. **Vocalise positionally, never by word lookup.** `ضربت` appears four times in the ماضی
   block as four different words (ضَرَبَتْ / ضَرَبْتَ / ضَرَبْتِ / ضَرَبْتُ). A word map gets
   three wrong, silently, for exactly the reader trying to learn it.

It ships as an overlay: the page emits the printed text plus `data-tashkil`, and reader.js
swaps them behind the اعراب button. Never replace the printed text — a citation must not
resolve to something an editor added. The other 14 treatises are unvocalised.

**Architecture change (2026-09-01):** Bayt al-Ahzan now follows the Bihar model.
`/bayt-al-ahzan/` is the Arabic primary cover. **The Farsi edition is a top-level sibling
book at `/bayt-al-ahzan-fa/`, not under `/fa/`** — it is a different edition (Ishtihardi,
262 printed pages) rather than a translation of the Arabic, so it carries its own slug in
`catalog.json`, its own cover and its own `assets/toc.json`. Its reading pages have
`data-root="../.."`, `data-book=".."` and `data-sitelang="fa"`.
Arabic reading pages have `data-book="../../bayt-al-ahzan"` and `data-alt-fa="../../bayt-al-ahzan-fa/"`.
When EN/Urdu translations of the Arabic are built they go at `/en/bayt-al-ahzan/<n>/`
and `/ur/bayt-al-ahzan/<n>/` — `bayt_ar_build.py` then adds them to `hreflang` and `data-alt-*`.

> An empty `fa/bayt-al-ahzan/` existed until 2026-09-03 as a leftover of an earlier plan.
> Nothing referenced it — 0 sitemap URLs, absent from `catalog.json`, and no page linked to
> it. Do not recreate it; the Farsi edition belongs at `bayt-al-ahzan-fa/`.

**Farsi page-number holes:** the Naser edition has 31 holes (5, 13, 14, 28–30, 55, …).
Do not renumber — prev/next walk the ordered list, so holes are invisible to readers.

Bihar volumes 2–110 not started. The Qur'an is complete in all four languages.
The remaining `catalog.json` entries are placeholders.

---

## Open work

In rough priority order. Nothing here is started.

1. **`bookCard()` gates on `volumesPublished`**, using it as a proxy for "this book has
   per-language index pages". Those are different facts, and the Qur'an already had to be
   special-cased around it once. An explicit `langIndex: true` in `catalog.json` would be
   sturdier. Touches the Bihar and Qur'an cards, which currently work — change carefully.
2. **Bayt al-Ahzan in en / ur.** Arabic original is now live at `/bayt-al-ahzan/1–189/`.
   Extract Arabic blocks with `bayt_ar_build.py`, send to translation, then `bayt_ar_build.py`
   with `--lang en --tr en.json --out ../Library/en/bayt-al-ahzan` (pipeline TBD). The Farsi
   is the source of record for the Persian translation — that too can go to en/ur via `bayt_build.py`.
3. **Bihar volume 2.** The pipeline is proven on volume 1; this is throughput, not design.
4. **A `.gitattributes`** to silence the CRLF warnings, if the noise ever matters.

### Known-good state

As of 2026-09-01 (pre-Arabic build): 1,173 URLs in sitemap, Farsi Bayt al-Ahzan's 229
pages verified 0 failures, Qur'an and Bihar untouched. `.suras` is the Qur'an's alone;
`.chaps` is every other book's chapter grid.

**Pending commit (2026-09-01):** Arabic Bayt al-Ahzan build — 189 new reading pages +
Arabic cover + Farsi cover at `/fa/bayt-al-ahzan/` + all Farsi reading pages rebuilt
(data-book update) + `bayt_ar_build.py` + `bayt_ar.json`. Sitemap not yet regenerated
for these 190 new URLs — run `gen_sitemap.py` before committing.
