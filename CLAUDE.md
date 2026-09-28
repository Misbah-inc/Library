# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Site

**https://library.misbah-inc.com** — a custom domain, moving from GitHub Pages to S3 + CloudFront (see `_translation-kit/DEPLOY.md`). The repo root is served at the domain root. Pure static HTML: no SSG framework, no build step other than the Python scripts in `_translation-kit/`.

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
| `verify_pagers.py` | walks every book's prev/next chain — **must report 0 broken links before commit** |
| `reextract.py` | built page → JSON, losslessly (for re-templating without retranslating) |
| `gen_sitemap.py` | rewrites `sitemap.xml` and `robots.txt` from what is on disk |
| `quran_build.py` | Tanzil text → surah pages, cover, and the Qur'an's JSON assets |
| `bihar_ar_extract.py` | Ghaemiyeh Bihar export → `bihar_v<N>.json`, one volume |
| `bihar_ar_build.py` | `bihar_v<N>.json` → Arabic reading pages, chrome templated from a published vol-1 page |
| `bihar_ar_wire.py` | volume index, toc.json rows, selector tiles, catalog — wires a built volume into the site |
| `bihar_ar_audit.py` | proves an extraction lost nothing, by word frequency against the raw export |
| `kafi_ar_build.py` | `kafi_v<N>.json` → al-Kafi's Arabic reading pages |
| `kafi_ar_wire.py` | al-Kafi's volume selector, volume indexes, `toc.json` and catalog row |
| `faqih_ar_build.py` | `faqih_v<N>.json` → «من لا يحضره الفقيه» Arabic reading pages |
| `faqih_ar_wire.py` | al-Faqih's volume selector, volume indexes, `toc.json`, catalog row |
| `abl_extract.py` | **ablibrary.net** → per-page JSON — the second extraction path, for التهذيب and الاستبصار |
| `abl_audit.py` | structural audit of an ablibrary extraction — **the round-trip check does not catch a bad split** |
| `tahdhib_ar_build.py` / `tahdhib_ar_wire.py` | تهذيب الأحكام pages, selector, indexes, `toc.json`, catalog |
| `burhan_ar_extract.py` | Ghaemiyeh البرهان export → `burhan_v<N>.json` — its OWN extractor: the page marker opens its page here, the running header splits across paragraphs, and there are no note divs |
| `burhan_ar_build.py` / `burhan_ar_wire.py` | البرهان في تفسير القرآن pages, selector, indexes, `toc.json`, catalog |
| `ghadir_ar_build.py` / `ghadir_ar_wire.py` | الغدير pages, selector, indexes, `toc.json`, catalog — extraction uses the shared `bihar_ar_extract.py` |
| `istibsar_ar_build.py` / `istibsar_ar_wire.py` | الاستبصار, likewise |
| `build_search_index.py` | per-volume in-book search indexes — **required before every deploy** |
| `build_site_index.py` | the site-wide inverted index behind `/search/` — **also required** |
| `deploy_s3.py` | publishes the site to S3 + CloudFront — see `DEPLOY.md` |
| `bayt_extract.py` | Ghaemiyeh HTML export → batch JSON (Bayt al-Ahzan) |
| `bayt_paginate.py` | splits Bayt al-Ahzan at its `[ صفحه ۷۷ ]` markers into printed pages |
| `bayt_build.py` | Bayt al-Ahzan page builder, cover, and `toc.json` |
| `bayt_ar_split.py` | segments the Arabic into sentence blocks — **run once, then treat `bayt_ar_blocks.json` as data** |
| `mafatih_extract.py` | Ghaemiyeh Mafātīḥ export → `mafatih.json` (Arabic + Ansariyan Persian, paired) |
| `mafatih_verify.py` | independent audit of `mafatih.json` — **must print `VERDICT clean`** |
| `mafatih_build.py` | `mafatih.json` → the 689 مفاتیح pages, cover and `toc.json` |
| `Fix-LibrarySeo.ps1` | one-off bulk `<head>` repair across the tree (PowerShell) |
| `Set-AssetVersion.ps1` | **retired** — stamped `?v=N` sitewide; see the frozen-`ASSETS_V` note below |

All of `build.py`, `merge_build.py`, and `verify.py` accept `--lang` (`en`/`fa`/`ur`) and `--volume`.

**GitHub Pages can no longer serve this site.** Two limits, and the second is
the one that bites first:

- **1 GB published-site cap**, hard, identical on every GitHub plan. The library
  is ~0.52 GB in Arabic and would pass 1 GB at its first translation of Bihar.
- **Deployments time out after 10 minutes**, and a deploy rebuilds the *whole*
  site, not the diff. At ~48,600 files that ceiling applies to every future
  deploy, including a one-line fix.

So the Arabic Bihar build must not be pushed to a Pages-enabled repo. The agreed
destination is **S3 static website hosting behind CloudFront**: no size or file
limit, index-document support for `/bihar/4/50/` is documented AWS behaviour, and
the custom domain is one CNAME — which matters because `misbah-inc.com` is
registered at Wix with `clientUpdateProhibited`, its nameservers are Wix's, and
the zone also carries the Wix company site and Google Workspace MX. Nothing about
GitHub changes except that it stops being the web server: it keeps the files,
the history and the push workflow, and the repo can then be private at no cost
(Pages from a private repo needs a paid GitHub plan).

**`ASSETS_V` is frozen at 9 and must never be bumped again.** All seven builders emit
the constant with that note on it; `Set-AssetVersion.ps1` is retired.

The stamp was solving a problem this host does not have. Measured against the live site
on 2026-09-13:

```
$ curl -sSI https://library.misbah-inc.com/assets/reader.js?v=9
Server: GitHub.com
Cache-Control: max-age=600
ETag: "6aa6537c-1198d"
```

and the **identical** headers come back with no query string at all. GitHub Pages caches
every asset for ten minutes and then revalidates against the ETag, so a changed
`reader.js` reaches every reader within ten minutes whether or not the URL carries a
version. There is no Cloudflare on this hostname (`Server: GitHub.com`, Fastly behind
it), so nothing overrides that.

What the stamp cost instead: rewriting every page in the repo. At 4,142 files that was
merely disproportionate; the book is going to 110 volumes, and a version baked into the
HTML is **O(pages) per asset change** — roughly 100,000 files rewritten to fix one line
of JavaScript, with the real edit buried in the same commit.

So the rule is the opposite of what it used to be:

1. **Ship the JS or CSS change on its own.** It is live for everyone within ten minutes.
   No page is touched, no bulk commit, and this stays true at 110 volumes.
2. **When a change looks like it did not land, it is the ten-minute window or your own
   browser** — hard refresh (Ctrl-Shift-R, or pull-to-refresh twice on mobile). During
   development, `fetch(url, {cache:'reload'})` then reload; a long-lived tab is not
   evidence.
3. **Do not remove the `?v=9` either.** Stripping it would cost exactly the tree-wide
   rewrite being avoided, and a frozen stamp is behaviourally identical to no stamp —
   the headers above are the proof. Leave it; new pages keep emitting 9 so the tree
   stays uniform.

If a future host ever does set a long `max-age`, the scalable fix is still not a stamp
in the HTML — it is a caching header, or one small stable loader file that the pages
point at permanently. Never per-deploy state in N pages.

### The Amiri subset is Arabic-only — do not let it claim Latin

`assets/fonts/amiri-*.woff2` is a subset. Below U+0600 it contains **exactly
`U+20`, `U+21`, `U+28`, `U+A0`** — space, `!`, `(`, nbsp. No `)`, no brackets,
no hyphen, **no ASCII digits**. Read it yourself before doubting this:

```python
from fontTools.ttLib import TTFont
sorted(TTFont("assets/fonts/amiri-400.woff2").getBestCmap())
```

That single stray `(` was drawn by Amiri while its own closing partner fell
back to the serif, so every «( 66 )» marker in the library rendered with
mismatched brackets — 29.3px against 17.8px, measured on the page. Both faces
therefore carry:

```css
unicode-range:U+20,U+A0,U+600-10FFFF;
```

which keeps Amiri for everything it has and hands `!` and `(` to the same
fallback as their neighbours. **If the font is ever re-subset, re-check that
range against the new cmap** — widen it and the mismatch returns; narrow it
carelessly and Arabic falls back across 61,000 pages.

> **A rendering fault is invisible in the source.** The HTML was right, the
> data was right, the round-trip passed, and the page still looked wrong. It
> took measuring a character's drawn width — `Range.getBoundingClientRect()`
> per character — to see it. When a reader reports that something *looks*
> wrong and the markup checks out, measure what the browser draws before
> concluding the report is mistaken.

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
python3 _translation-kit/verify_pagers.py
```
`verify.py` proves the text; `verify_pagers.py` proves the navigation. Both are required —
seven broken prev/next links sat live in Farsi and Urdu Bihar for months because only the
first existed.

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

## بيت الأحزان — translation invariants

- **The Arabic is segmented once, into `bayt_ar_blocks.json`, and never re-segmented.**
  English keys to `data-i`; recomputing the split at build time would renumber every block
  and silently re-point each translated line onto the wrong Arabic. Re-run
  `bayt_ar_split.py` only on a book that has no translations yet.
- **Farsi is not a translation of this book.** رنج‌ها و فریادهای فاطمه at
  `/bayt-al-ahzan-fa/` is a different edition with unrelated pagination — Arabic chapters
  begin at 1, 18, 30, 55, 163; the Persian at 3, 6, 10, 12, 15, 31, 56… Link the two at
  **cover level only** (`hreflang="fa"` and `data-alt-fa`). Never build `/fa/bayt-al-ahzan/`.
- **One template builds both languages.** `bayt_ar_build.py --lang en --tr <json>`; do not
  fork a second builder, or the Arabic and English pages drift apart.
- **Every Arabic block gets a translation line, even an empty one.** `verify.py` aligns the
  two lists by position, so a skipped line shifts every translation after it.
- **The ARABIC build must be told which pages have a translation, with `--tr-upto N`.**
  The switcher follows `data-alt-<lang>`; without it a reader clicking EN on the Arabic
  page is told the page is untranslated while the English page sits beside it. Claiming it
  for every page is equally wrong — it points at pages nobody built. Rebuild the Arabic
  side every time the prefix grows.
- **A translated page's meta description must be in that page's language.** Taking the
  Arabic excerpt for an English page puts an Arabic snippet under an English search result.
  `excerpt()` uses the first translated block and falls back to the Arabic only when there
  is none.
- **Run `gen_sitemap.py` after every batch.** A page not in the sitemap is a page Google
  has no reason to crawl, and the translated prefix grows batch by batch.
- **A partially translated language ships its own `assets/pages.json`.** reader.js prefers
  `<lang>/<slug>/assets/pages.json` and falls back to `<slug>/assets/pages.json`; without
  the language file the jump dropdown offers every page of the original, most of them 404.
- **Publish the translation as a contiguous prefix with `--upto N`.** Never build all 189
  pages with most translations empty, and never build a scattered subset — page N's `next`
  would point at a page nobody created. `--upto` makes N the last page so the chain stays
  valid, and readers on the untranslated Arabic pages get the existing "not translated
  yet" notice.
- **A toc.json row needs `title` and `p`.** reader.js reads `x[lang] || x.title` and `x.p`;
  emitting `ar`/`pages` instead renders every Contents row as the word `undefined`.
- **After any change to that builder, rebuild the Arabic and diff it against what is live.**
  It must come out byte-identical. A stray newline in the template put a blank line on all
  189 Arabic pages and only the diff caught it.
- **`COVER_LANGS` must never contain `fa`.** The cover's `.chaps` grid takes its language
  prefix from `data-langs`; listing `fa` makes every chapter link `/fa/bayt-al-ahzan/<n>/`,
  which is a 404 for all five. This was fixed once in the built HTML and came straight back
  on the next rebuild, because only the output was patched. **A fix applied to generated
  output is not a fix** — it survives until the next build. Patch the builder.
- **Each language with pages needs a cover of its own**, built by the same
  `build_cover()` with `--lang <L> --cover`. A translated cover needs three things the
  reading pages already have: `data-sitelang="<L>"` (or it adopts whatever language the
  reader last chose, serving the wrong language under that URL's canonical),
  `data-book="../../bayt-al-ahzan"` (Contents loads `BOOK + '/assets/toc.json'`, and only
  the Arabic root has one), and depth-correct relative links — it sits one level deeper.
- **Chapter titles on the cover carry `data-ar`/`data-en` and swap in place**, through
  reader.js's `[data-ar]` handler, because the Arabic cover's links follow the chosen
  language into the translated pages. Give those spans no `lang` attribute: reader.js keeps
  `<html lang>`/`dir` in step, and a hardcoded `lang="ar"` renders swapped English in Amiri,
  right-to-left.
- **A new translation is not reachable until `catalog.json` says so.** `bookCard()` gates
  the language prefix on `translated` *and* a non-empty `volumesPublished`; without both,
  readers browsing in that language get the Arabic cover and never learn the translation
  exists.

---

## بحار الأنوار — adding an Arabic volume

- **Check the edition before anything else.** Each Ghaemiyeh export states its own
  publisher in the هوية الكتاب block. Volumes 1–3 are دار احياء التراث العربي. The
  مؤسسة الوفاء text in `Claude outputs/bihar-vol2/` is a *different* edition with its own
  pagination and must not be mixed into `bihar/`.
- **The page marker `ص: N` CLOSES its page**, and footnotes for page N follow it. Segment
  on `<SPAN class=chapter>`, which falls after the notes, so a segment is body + marker +
  notes. Match the marker as a paragraph whose entire content is «ص: N» — the bare string
  also appears mid-prose as a cross-reference.
- **A segment may hold more than one marker**, may carry text after its last marker that
  belongs to the next page, and may have no marker at all while still holding a page of
  text. All three occur in volumes 2–3, and each one silently loses text if unhandled.
- **Prove losslessness by word frequency against the raw export**, not by eyeballing page
  counts. That is the check that caught every one of the four extraction faults. It is
  now `bihar_ar_audit.py <export.htm> bihar_v<N>.json`, which must print
  **`UNCAPTURED SOURCE TOKENS: 0`** — volumes 4–6 match the source multiset exactly.
  Two things it accounts for, and any similar checker must: the page marker «ص: N» is
  structure that becomes the folio label, so its «ص» is *supposed* to be missing (skip
  this and every volume reports one phantom loss per page, which is enough noise to hide
  a real one); and the Ghaemiyeh publisher blurb is dropped deliberately, so its
  shortfall is counted separately. Mutation-test it after any change — deleting one page
  from a volume's JSON must make it fail. A checker nobody has seen fail is not evidence.
- **Two page-label faults recur across the corpus, and both destroy text in
  silence.** `resolve_pagination()` in `bihar_ar_extract.py` handles them; never
  build a volume that has not been through it.
  1. A footnote citation written «ص: 159» matches the page-marker markup, so it
     splits a page and invents a label — volume 37 had «ص: 45155155» and two
     pages numbered 0. Detect it by the one thing that is exact: deleting the
     entry makes the run contiguous (`labels[i-1] + 1 == labels[i+1]`). Merge the
     orphaned text **forward** — the marker closes its page, so text before a
     bogus marker belongs to the page the next real marker closes. Never drop it.
  2. Six volumes (29, 53, 102, 108, 109, 110) paginate publisher front matter
     1..N before al-Majlisi's text restarts at 1, so two different pages claim
     one number and one directory. Front matter takes ids **`fm-1..fm-N`**;
     al-Majlisi keeps the bare numbers, so a citation still resolves. `fm-` pages
     are in the prev/next chain but **not** in `pages-<vol>.json`, which
     reader.js reads as integers.
- **Footnote ids can be negative.** Volume 29's front matter numbers its notes
  from a negative counter (`content_note_-5_1`). A `\d+` in the NOTE pattern
  dropped six notes with no error — they are not paragraphs, so nothing else
  caught them, and only the word-frequency audit noticed the 76 missing words.
- **Volumes 2-110 ship NO edge rail; volume 1 keeps its.** The rail was 45% of
  each page for markup reader.js deletes on load. With no `.edgewrap`, reader.js
  fetches `bihar/assets/pages-<vol>.json` instead — the path translated pages
  already use — and the dropdown then offers every page. Volume 1 is the source
  of record and the template: do not restructure it without the owner's word.
- **Volume 83 is a different edition.** ghbook.ir has no HTML edition of it, so
  it comes from ablibrary and is the مؤسسة الوفاء text, whose pagination does not
  match دار احياء التراث العربي. It is published with a `.book-credit` notice on
  every page in all four languages (`.cite` would be invisible on en/fa/ur).
  `WAFA_VOLS` in `bihar_ar_build.py` is the list; add to it, never hardcode.
- **The contents drawer is scoped to the page's own volume.** 110 volumes are
  6,771 toc rows in which every volume has a «باب 1» and no row says which.
  reader.js filters on `vol`, guarded so books whose rows lack it are untouched.
  «اشارة» is the export's "note follows" marker, not a chapter title — 267 of
  them are filtered out in `bihar_ar_wire.py`.
- **The Ghaemiyeh catalogue record can name the wrong volume.** The volume-6 export's
  هوية الكتاب says «المجلد 7». The title heading inside the same file says 6, and its text
  opens at باب 19 of أبواب العدل, directly continuing volume 5's باب 18. Trust the heading
  and the seam, not the record — and always check the seam against the previous volume's
  last chapter before publishing.
- **An untranslated volume declares `ar` + `x-default` only** — no en/fa/ur hreflang, no
  `data-alt-*`, and its selector tile carries `data-langs="ar"` so `applyLang()` keeps it
  on the Arabic tree instead of rewriting it to a language folder nobody built.
- **The Arabic page template lives only in the published pages.** `build.py` emits
  en/fa/ur; `bihar_ar_build.py` therefore lifts head/header/nav/footer out of
  `bihar/1/26/index.html` at build time. Diff any new volume's structure against volume 1
  after building — 0.948 similarity is the expected figure, the gap being volume 1's
  translation hreflangs and heading spans.
- **`bihar/assets/tr/<lang>.json` is keyed by PAGE NUMBER and has no volume in it.**
  Volume 1 shipped before a second volume existed. Every other volume must address its
  own file, `<lang>-<vol>.json`, or it renders volume 1's translation of that page number
  under its own Arabic — a different text entirely, presented to the reader as this page's
  translation. Volume 1 keeps the original name; do not rename it, the three published
  translations key to it.
- **A volume with no translation says so on the page**: `data-trlangs=""` in `#page-meta`.
  reader.js reads it and skips the fetch instead of 404ing. A page that omits the
  attribute (volume 1) keeps the older fetch-and-see path, so adding a translation later
  needs the attribute updated, not just the file dropped in.
- **`load()` rejects on a non-OK response.** Anything optional — a translation store that
  may not exist — must `.catch()` back to a usable default, or a 404 leaves the page with
  neither the thing nor the notice that it is missing.
- **The edge rail is 120 evenly spaced links**, `n = 1 + round(k·(N−1)/119)`, plus the
  current page when absent. reader.js then replaces the rail with a dropdown built from
  those links, so the dropdown offers 120 pages on every volume — volume 1 included.

---

## Arabic orthography: ي / ى / ی — the check that costs one line (2026-09-28)

Ghaemiyeh exports write Persian **ی (U+06CC)** where Arabic has TWO letters:
**ي** (yāʾ) and **ى** (alif maqṣūra). They are not interchangeable — «موسى»,
«إلى», «على» take ى; «التي», «عليها», «علي» (the name) take ي.

> **NEVER convert ی → ي in bulk.** It was done to الغدير on 2026-09-27 and was
> wrong for ~12% of occurrences, turning «موسى» into «موسي». Worse, it swaps an
> obviously-foreign letter for a confidently-wrong Arabic one, which no reader
> can detect. **Leaving ی is better than guessing ي.**

**The standing check: a correctly typeset Arabic book here runs 6-23% ى**
(as a share of ي+ى). Bihar is 12.0%, الغدير 12.4% against ablibrary's 12.5%.
**A conversion producing 0% is wrong, and one number says so.** Every
verification of the الغدير conversion passed because each tested whether the
script did what was intended, never whether the intention was right. Measure the
OUTPUT against an independent reference, not against your own plan.

**The repair is parallel text.** ablibrary carries the same books correctly
typeset. Four tiers, most certain first: the same 5-word window in the
reference → a form unambiguous across the whole reference corpus → an ambiguous
form settled by the preceding word → **leave ی and count it**. Only tier 1 can
separate «على» from «علي», because that is a difference of meaning. Tools:
`bihar_yeh_fix.py` (`--maqsura` inverts it: input ي, ask whether it should be
ى — that is volume 1's defect, a blanket ی→ي at build time), plus
`ghadir_yeh_fix.py`.

- **ى is word-final.** Verified: 54,717 of 54,718 reference occurrences. So a
  word's non-final ی is always ي, and fixing only the last one leaves «یحیى».
- **«علي بن» is the name and «يعلى بن» is the narrator Yaʿlā.** A rule matching
  «على بن» without a lookbehind corrupts 35 correct names to repair 25
  misprints. `(?<![ء-يى])` guards it.
- **«شی ء» is شيء** and **«علی بن» is علي** — decidable from orthography alone,
  no context needed. Still outstanding in volumes 2-110 (~14,000, 0.3/page).
- **`پ`, `چ`, `گ` are never touched** — real Persian letters with no Arabic
  equivalent, in nisbas like «الچلبي», «الگلپايگاني».

### Scope: the chrome holds real Persian and Urdu

**Edit only inside `<div class="body">`, and assert the rest byte-identical.**
The chrome carries `data-fa="علامه محمدباقر مجلسی"` and `data-ur=…` — genuine
Persian and Urdu whose ی is CORRECT. A file-wide replacement corrupts the
language switcher on 44,306 pages while the Arabic looks perfect.

> **Volume 1 puts those attributes INSIDE the body**, in its heading span, so
> the body scope does not protect them. The exact check: these passes only ever
> write ي or ى, so a `data-fa`/`data-ur` holding either is proof of damage.
> 52 found, 0 damaged.

### What must catch up outside the body — and it is all DERIVED

Repairing the body alone leaves four things in the old spelling. None is
re-inferred; each is copied from text already fixed, with the reproduction rate
measured BEFORE writing anything.

1. **`toc.json`** — the contents drawer on every page, 20,026 ی in 5,480 Arabic
   titles. Take each title from the heading on its own row's page (300/300
   reproduce). Its `fa`/`ur`/`en` fields must not change — assert the counts.
2. **The 110 volume index pages** carry chapter rows inline as
   `<span data-ar="TITLE">TITLE</span>`. Key them off the corrected toc.
3. **`<meta name="description">`** is the first 150 chars of the page's own
   block text, so it re-derives exactly (200/200). Still outstanding.
4. **en/fa/ur volume 1** — a translated page CARRIES the Arabic beside each
   translated line, so repairing the source desynchronises three trees and
   `verify.py` fails. **Copy the corrected Arabic (`bihar_v1_resync.py`); never
   re-infer it** — a second pass may disagree with the first, and on an fa/ur
   page it would be loose among genuine Persian.

### Search indexes do NOT need rebuilding for an orthography change

`fold()` maps **ي, ى AND ی all to ی**, so the stored `t` is already byte-identical
to what a rebuild would produce, and the *searchable* text never changed. Only
`part.ar`, the chapter label, is stored unfolded — and it comes from `toc.json`.
`bihar_search_relabel.py` refreshes the labels with **zero page reads**, against
seven hours for a full rebuild, and refuses to run unless it first re-derives
`t` from live pages and finds every sample identical.

## الكافي — the second Arabic book (2026-09-22)

Eight volumes, 4,484 pages, at `/kafi/<vol>/<page>/`. Built by
`kafi_ar_build.py` (one builder per book, as everywhere here) from the same
Ghaemiyeh HTML exports as Bihar, extracted by `bihar_ar_extract.py` —
the export format is identical, so the extractor and the audit are shared.

- **The edition is دار التعارف للمطبوعات، بيروت (1411 هـ / 1990 م)**, edited by
  محمد جعفر شمس الدين. All eight volumes say so in their own هوية الكتاب.
  **Do not write al-Ghaffari** anywhere — that is the دار الكتب الإسلامية
  printing, a different text with different pagination, and it is the edition
  most citations of al-Kafi in circulation actually refer to. `EDITION` in
  `kafi_ar_wire.py` is the single place the name is written.
- **The part label comes from the volume's own heading**: 1-2 «أصول الكافي»,
  3-7 «فُروعُ الكافي», 8 «روضة الكافي». It is the page `<title>` and the first
  element of every citation, so it is not cosmetic. `PART` in both kafi scripts
  must agree; they are checked against the openings — vol 3 كتاب الطهارة,
  4 أبواب الصدقة, 5 كتاب الجهاد, 6 كتاب العقيقة, 7 كتاب الوصايا, 8 كتاب الروضة.
- **Volume 4's export has no `<H4>` at all.** Its 362 باب titles ship as
  ordinary `content_paragraph`s, so the volume came out with 7 contents rows
  across 599 pages while its siblings had 300-400. They are promoted to `h4`
  before the build, by the one pattern that is exact here — a paragraph whose
  text starts `^\d+\s*-\s*باب` and is under 250 characters. It fires 362 times
  and the numbers run 1..362 with two breaks, one of them a typo in the source;
  it never fires inside a hadith. **The promotion asserts the text is
  byte-identical afterwards** and the volume re-audits at 0 uncaptured tokens,
  because the only thing allowed to change is a tag.
- **Do not apply that promotion to any other volume.** Volume 6 has *both* — an
  unnumbered `<H4>` running head and a numbered paragraph repeating it — so
  promoting there would double all 422 of its chapter rows. Volumes 1, 2, 3, 5
  and 7 match only a handful of times and almost every one is a duplicate of an
  `<H4>` on the same page carrying footnote markers the heading omits.
- **Filter «اشارة» and «هوية الكتاب» folded, not literally.** Some volumes spell
  them with Persian ی/ک and some with Arabic ي/ك; comparing the raw string
  leaks the publisher's catalogue record into the contents of volumes 3, 4
  and 8. `fold()` in `kafi_ar_wire.py` does it.
- **Volume 1 paginates its front matter 1..10 before the text restarts at 1**,
  the same fault as Bihar's six volumes, and takes the same `fm-1..fm-10` ids:
  in the prev/next chain, out of `pages-1.json`.
- Every volume is Arabic-only: `data-trlangs=""` on the pages, `data-langs="ar"`
  on the selector tiles, no `translated` array in `catalog.json`, so
  `bookCard()` keeps a reader browsing in English on the Arabic tree rather
  than linking `/en/kafi/`, which nobody has built.
- `kafi_ar_wire.py` **builds its chrome instead of lifting it** from a published
  page, which is how `bihar_ar_wire.py` works — there was no published al-Kafi
  page to lift from. Keep the markup the same shape as Bihar's (same classes,
  same `data-i18n` keys, `<main class="cover">`) so reader.js needs nothing new.

> **The home-page counter reads `pages` from `catalog.json`, and it is written
> by hand.** Bihar's said 231 — volume 1 alone — from before the 110-volume
> build until 2026-09-22, so the site advertised 2,556 pages while serving
> about 49,000. Nothing derives it, nothing checks it: set it when a book grows.

## In-book search — how it works and what it costs (2026-09-22)

There is no search engine behind this site. When a reader opens a book, clicks
**Search** and types a word, `reader.js` downloads that book's index and scans
it in the browser with `indexOf`. So the index **is** the book's text, a second
time. That is the whole reason these files are large.

- **One file per volume, never one per book.** Bihar as a single file is about
  150 MB, and — the fact that settles it — **CloudFront only auto-compresses
  below 10,000,000 bytes**. A whole-book al-Kafi index measured 10,628,733
  bytes, missing the ceiling by 6%, so every reader who searched would have
  pulled it raw. Per volume each file is 1-2 MB and arrives around 250-450 KB
  gzipped. Verified against the live site: `bihar/assets/search-index.json`
  comes back with `Content-Encoding: gzip`.
- **`reader.js` resolves four candidates in order** and takes the first that
  loads: this language's volume, this language's book, the Arabic volume, the
  Arabic book. The last is what every book used before, so nothing regressed.
  A translated page must search its OWN language, and `BOOK` cannot supply it —
  `BOOK` is pinned to the Arabic root so `toc.json` resolves.
- **`fold()` in `build_search_index.py` must match `fold()` in `reader.js`
  exactly.** The reader's query is folded by one and matched against text
  folded by the other. A disagreement is a word that can never be found, with
  no error anywhere to say so. `FOLD` and `DROP` are transcribed; change them
  together. Keep `DROP` written as `\uXXXX` escapes — an earlier edit left the
  literal combining marks in the source, where they are invisible.
- **The index includes footnotes**, matching the hand-made Bihar index: on
  `bihar/1/26/` it carries 1,400 folded characters against 1,269 for the body
  alone. A rare word is usually explained in the editor's note.
- **The files are NOT committed** — `.gitignore` covers `**/assets/search-*.json`.
  They are derived in one command and would add over 20% to a repository that
  already struggles to push over Drive. `aws s3 sync` does not read
  `.gitignore`, so `deploy_s3.py` uploads them anyway. The trap that creates is
  real and guarded: deploying from a clone that never ran the builder would
  make `--delete` **remove** them from S3 and leave every Search button saying
  "Could not load." with nothing in the output to explain it. `deploy_s3.py`
  now refuses, per volume — checking "the book has some index" would pass on
  Bihar forever, because `bihar/assets/search-index.json` is the old
  volume-1-only file and still exists.

> **Only Arabic Bihar and al-Kafi pages carry a `btn-search` at all.** Bayt
> al-Ahzan, جامع المقدمات and the translated trees have no search button, so an
> index for them is only reachable through the site-wide `/search/`, which
> reads `<slug>/assets/search-index.json` per book. Giving those books the
> button is a change to each one's builder and has not been made.

> **Site-wide full-text search does not scale to this library and has not been
> attempted.** `/search/` fetches one file per book, so it sees Bihar volume 1
> and nothing else of Bihar or al-Kafi. Covering 53,000 pages client-side means
> shipping ~165 MB. The shape that would work is asking the reader for a book
> and volume first, then loading that one index — not done.

**Run it before every deploy:**
```
python _translation-kit/build_search_index.py --all
```

## Site-wide search — the inverted index (2026-09-22)

`/search/` is the library's most-used feature and until now it could not work.
It downloaded **one index per book and scanned it**, which is fine for a
231-page book and impossible for 53,000 pages: the library's text is ~165 MB.

It is now inverted. Instead of scanning text, look up the WORD: for each word,
the list of pages it appears on. Three files answer a query:

| File | Size | When |
|---|---|---|
| `assets/search/meta.json` | **5.3 KB** — shard counts + segment table | once per visit |
| `assets/search/t-000…511.json` | 28 MB total, **median 23 KB gzipped** | one per query word |
| `assets/search/p-000…055.json` | 6.1 MB total, largest 190 KB raw | only the blocks holding results on screen |
| the result pages themselves | ~3 KB gzipped each | ~20 per result page |

Measured end to end: a three-word query with an exclusion, over the whole
library, transferred **234 KB** on the local server — less on CloudFront, which
compresses the HTML. **71,779 pages and 366,867 words** are indexed across 166
segments (rebuilt 2026-09-28): all 110 Bihar volumes, all four canonical books, both Bayt al-Ahzan
editions, جامع المقدمات, مفاتیح, the Qur'an, and every translation (en/fa/ur).

- **The page table is SHARDED, and the fields that repeat are not in it.**
  It began as one `pages.json` holding href/book/category/language/volume/
  label/chapter for every page, fetched whole by every searching reader. At
  55,393 pages that hit **8,471,418 bytes — 85% of CloudFront's 10,000,000-byte
  compression ceiling**, past which the file is served RAW: 8.5 MB instead of
  0.57 MB, with nothing anywhere to announce it. Two changes removed the cliff
  rather than postponing it:
    1. book, category, language and volume moved into a **segment table** in
       `meta.json` — each source file occupies a CONTIGUOUS run of ids, so
       those are properties of the run, not of 55,000 separate pages. 136 rows
       covering everything, and it is all the book/category filter needs.
    2. what remains (name, printed label, chapter) is split into blocks of
       1,000 ids; a reader fetches only the blocks their own results fall in.
  The once-per-visit fetch went from 8.5 MB to **5.3 KB**. Keep it that way:
  anything added to `meta.json` is paid by every reader on every visit.
- **The href is rebuilt from segment + name, not stored.** `build_site_index.py`
  asserts the rebuild reproduces the original exactly for every page and exits
  if it cannot — because if that silently drifts, every search result links to
  a 404. Any new book whose page URLs are not
  `<lang>/<book>/<vol>/<name>/` will trip this at build time, which is where it
  belongs.
- **Snippets come from fetching the RESULT PAGES, not the per-volume text.**
  Twenty results spread over twenty volumes would be 6 MB of volume files
  against 60 KB of pages, and the pages are already in the CDN.
- **That fetch is also what makes "exact phrase" exact.** The index can only
  say the words are all somewhere on the page, never that they are adjacent.
  «باب فضل الصدقة» returns 33 candidates and 17 survive the check. Anything that
  removes the page fetch silently turns phrase search into "all these words".
- **Page ids are POSITIONS in `pages.json`.** Shards and page table are one
  artefact in two files; rebuild them together, always. A stale shard does not
  error — it returns confidently wrong pages, which is worse.
- **The shard hash is FNV-1a 32 and must stay so.** The browser hashes the word
  itself, so no word→shard table ships; `crypto.subtle` offers SHA only, and
  there is no MD5 in a browser. `shard_of()` in the builder and `fnv1a()` in
  `reader.js` are the same four lines. In JS the multiply is written as shifts
  because `h * 16777619` leaves the exact-integer range.
- **`deploy_s3.py` refuses to publish without these**, because they are
  gitignored and `--delete` would otherwise strip them off S3.

### Three silent failures this feature produced, all found by measuring

None raised an error. Each returned plausible, wrong results.

1. **`\u0600-\u06FF` in the tokeniser.** The Arabic block contains the COMMA
   (U+060C), SEMICOLON, QUESTION MARK and FULL STOP (U+06D4), so «الصدقه،» was
   one token and a search for «الصدقه» could never match it. Python's `\w` is
   already Unicode-aware — the extra range was wrong *and* unnecessary.
2. **`<div class="body"` with the closing quote.** مفاتیح writes
   `class="body mafatih"`, so the match failed and the book produced **694
   empty rows** — an entire book unsearchable, no error. Match `<div class="body`
   without the quote. `build_search_index.py` now prints a count of pages that
   extracted no text; it reports only مفاتیح's 5 category landing pages, which
   genuinely have none.
3. **`'[^\p{L}\p{N}_]+'` written as a JS string.** `\p` in a string literal is
   just `p`, so the regex became `[^p{L}p{N}_]+` — a class that splits on
   Arabic LETTERS. Every query tokenised to nothing and the page said "type at
   least two characters". It needs `'[^\p{L}\p{N}_]+'`. It is built with
   `new RegExp(...)` inside try/catch rather than a `/…/u` literal so an engine
   without property escapes falls back instead of failing to parse the file.

> **The tokeniser parity test is the check that holds this together.** The
> query is tokenised by `reader.js` and the text by `build_site_index.py`; any
> disagreement is a word that can never be found, with nothing to say so. Take
> 40 real pages, tokenise in both, compare the sets — currently 5,034 tokens,
> 0 mismatches. **Extract the regex from the SHIPPED file when testing.** The
> first run of this test passed while the shipped regex was broken, because it
> tested the pattern as intended rather than as deployed.

**Run both, in this order, before every deploy:**
```
python _translation-kit/build_search_index.py --all
python _translation-kit/build_site_index.py
```

## من لا يحضره الفقيه — the third Arabic book (2026-09-23)

Four volumes, 2,484 pages, 9,519 footnotes, at `/faqih/<vol>/<page>/`. Built by
`faqih_ar_build.py` from the Ghaemiyeh export (ghbook.ir book 19340), extracted
and audited by the shared `bihar_ar_extract.py` / `bihar_ar_audit.py`.

- **Edition: تحقيق علي أكبر الغفاري، مؤسسة النشر الإسلامي / جماعة المدرسين، قم.**
  Named in every volume's own هوية الكتاب. **Do not write دار التعارف here** —
  that is al-Kafi's edition in this library, and the two builders sit next to
  each other in the same folder.
- **This export is NOT meaningfully vocalised, and the choice of source was
  argued badly the first time.** Marks per Arabic letter: Bihar vol 10 54.88%,
  al-Kafi vol 1 10.83%, **al-Faqih vol 1 0.69%, vol 3 0.51%**. The ~17,000
  marks are the editor disambiguating the odd word. The tashkīl argument that
  decided al-Kafi does not apply. Ghaemiyeh was still right, for duller
  reasons: it carries the back-matter فهارس that ablibrary drops, and it is the
  format the existing extractor and audit already read. **Measure the density
  before claiming a source is vocalised** — a raw mark count says nothing.
- **ablibrary (books 2594-2597) is the SAME edition with the SAME pagination.**
  Page N is page N, verified at 100/200/300/400 in every volume, and 98.75-99.75%
  of sampled character runs match. Either source can check a citation.
- **Compare Arabic across sources with whitespace REMOVED, not normalised.**
  Three successive comparisons here gave badly wrong answers because Ghaemiyeh
  is inconsistent about spacing: «عزوجل» for «عز وجل», «محمدبن» for «محمد بن»,
  «و قالت» for «وقالت». Only stripping whitespace entirely gave a true figure.
  The residual misses after that are chapter-heading boundaries, where one side
  puts the title in its own element — not missing text.
- **أبواب are numbered CONTINUOUSLY across the four volumes**, 1-87, 89-314,
  315-491, 492-665, and hadith likewise, vol 1 ending at 1573 and vol 4 at 5829.
  So unlike Bihar and al-Kafi there is no «باب 1» collision; the contents drawer
  is still volume-scoped, but only to keep it at 108-301 rows instead of 789.
- **Volume 1 paginates 32 front-matter pages** before the text starts, taking
  `fm-1..fm-32`; volume 3 has 2. ablibrary independently lists exactly 32 named
  front pages for volume 1, which is good evidence both captured it intact.
- The book has **no named parts**, so the part-label slot carries the book's own
  title rather than a part name — unlike al-Kafi's أصول/فروع/الروضة.

> **A heading check that counts `<H3`/`<H4>` tags is looking at the wrong thing.**
> Volume 1 marks its أبواب as `<H2 class=content_h2>`, volumes 2-3 use H3/H4,
> volume 4 mixes all three. `bihar_ar_extract.py` matches on `class=content_h(\d)`
> rather than the tag name and handles all of them — 86 / 226 / 177 / 172 باب
> headings captured. An early pass here counted raw tags and reported volume 1
> as having zero chapters, which was alarming and wrong.

## تهذيب الأحكام and الاستبصار — the ablibrary path (2026-09-23)

Ten volumes / 4,081 pages and four / 1,583, at `/tahdhib/<vol>/<page>/` and
`/istibsar/<vol>/<page>/`. Both by شيخ الطائفة الطوسي, both **تحقيق حسن الموسوي
الخرسان، دار الكتب الإسلامية، طهران**. With al-Kafi (شمس الدين، دار التعارف) and
al-Faqih (الغفاري) that is **four canonical books and three editors — never copy
an edition line between these builders.**

### Why these two do not come from Ghaemiyeh

Every other book here does. These cannot, and it was measured before choosing:

- **Neither Ghaemiyeh export has a single footnote** — zero note divs, zero
  anchors, zero `<HR>` across all fourteen volumes. ablibrary has 6,036 note
  blocks.
- **Ghaemiyeh's الاستبصار has no printed page markers at all**, only hadith ids
  (`-روایت-1-728`). This library addresses and cites every page by its printed
  number; there is nothing to build a URL from. A constraint, not a preference.

The cost is vocalisation: Ghaemiyeh is **82%** (Tahdhib) and **63%** (Istibsar)
against ablibrary's 0%. The two agree page for page, so it can be added later as
an overlay — the exports are kept in `Claude outputs/<book>-ghbook-html/` for
that. **Do not "upgrade" either book by swapping the source**; that would trade
the apparatus and, for Istibsar, the pagination itself.

### What ablibrary gives, and the checks that hold it together

`Contents` returns **one text blob per page** plus one notes blob — no
paragraphs, no headings, no structure of any kind. All of it has to be rebuilt,
and the first attempt got the central fact backwards.

> **A newline before a block start IS a boundary; a newline inside a block is a
> wrap.** The text is hard-wrapped at ~80 characters, so it is tempting to
> strip every newline and re-split on a hadith pattern. That is what shipped
> first, and it ran whole pages together into one paragraph. Every hadith and
> every باب **begins at a line start**; only continuation lines wrap. Split on
> line starts, join the rest.

- **Four hadith numbering forms across two books.** Missing one does not fail —
  it merges every hadith on the page into the preceding paragraph, and the
  round-trip check still passes because no text was lost:

  | | |
  |---|---|
  | التهذيب v1 | `( 316 ) 7 وأخبرني…` |
  | التهذيب v3 | `* ( 125 ) * 76 - وروى…` |
  | الاستبصار v2 | `[ 28 ] 4 - فأما ما رواه…` |
  | الاستبصار v1 | `176 - 1 أخبرني…` |

  Istibsar v1 shipped with **0 splits and 251 single-block pages**; Tahdhib v2
  was 91% run together. Because the bare-number form exists, **HEAD_LINE must be
  tested before HADITH_LINE**, or «25 - باب مقدار الصاع» reads as hadith 25.
- **Headings are found on the line, not matched against the contents.** A line
  opening with an optional number and باب/كتاب/أبواب is a heading, and it **keeps
  its number** — the edition prints «25 - باب مقدار الصاع» as one heading, and
  splitting the number off strands it at the end of the previous paragraph.
  الاستبصار v3 alone brackets them, «[ 1 - باب من يستحق… ]», and found 2 of 238
  until the pattern allowed it.
- **A heading is EXACTLY ONE LINE.** Letting it absorb continuation lines the
  way a paragraph does swallowed whole passages — the ziyāra after
  «9 - باب وداع أمير المؤمنين» became part of the heading in التهذيب v6, a full
  hadith did the same in الاستبصار v4 — and both then appeared in the contents
  drawer as a chapter title hundreds of characters long. Check the longest
  heading per volume after any change; 78 characters is the real ceiling here.
- **A heading and its first hadith can share one source line**, e.g.
  «33 - باب علامة أول يوم من شهر رمضان [ 199 ] 1 - أخبرني…». Split at the
  marker, or the pair is published as one title.
- **An UNNUMBERED heading candidate must be confirmed against the contents.**
  A wrapped continuation line often begins with باب/كتاب/أبواب by accident:
  «كتاب حريز أنه قال» is the middle of hadith 1418, «كتاب الله عز وجل» is a
  quotation, «أبواب كندة في الصحن» is a place. Each became a false chapter. A
  candidate carrying its own number is trusted; one without must appear in
  ablibrary's table of contents.
- **`toc.json` is built from the headings found in the text**, so every row's
  page is true by construction. ablibrary's own page pointer is never used:
  both fields it offers are wrong in several volumes, and a contents row that
  sends a reader to an unrelated page is worse than one that is absent.
- **The notes blob holds TWO different things and they are not
  interchangeable.** `( 1 ) المظنون قويا…` is a numbered footnote with a
  matching `( 1 )` marker in the body — anchor it, so the reader can click it
  as they can in Bihar. `- 163 - التهذيب ج 1 ص 372` is the editor's تخريج, keyed
  to a HADITH number and pointing at nothing in the text — render it with `*`
  and never give it a number. Flattening both into one numbered list is what
  made the parentheses look scrambled on the page.
- **Only anchor a marker whose note exists, and never at a block's start.**
  `( 316 ) 7` opens a hadith in التهذيب; converting that to a footnote link
  would be silent nonsense.

> **A parenthesised NUMBER inside RTL text renders reversed.** «( 21 ) 4 -»
> displays as «) 21 ( 4 -» because brackets are bidi-neutral and take the
> surrounding direction. This is NOT a data fault — the source has normal
> parentheses and the round-trip proves the text is exact — so no amount of
> checking the JSON will find it. `bidi_nums()` in both builders wraps each
> number group in `<bdi>`, which isolates it. **Only number groups**:
> «( عليه السلام )» holds strong RTL text, resolves correctly on its own, and
> must be left alone. To verify, measure what the browser draws — walk the
> character rectangles with a Range and sort by x. Reading the HTML tells you
> nothing, because the HTML was right all along.

### Two checks, and why one is not enough

```
python abl_extract.py …      # round-trip: no text lost
python abl_audit.py <dir>    # structure: text split correctly
```

- **`check()` in the extractor** asserts every page's blocks re-join to the
  source character for character, undoing the `[1]` anchoring first. It caught
  the heading matcher splitting «الاستحباب» into «الاستح» + «باب».
- **`abl_audit.py` exists because the round-trip is not enough.** EVERY defect
  this book family produced — four numbering forms, bracketed headings, mixed-up
  footnotes, headings swallowing whole passages, false chapters, reversed
  parentheses — **round-tripped perfectly**. No text was ever lost; it was split,
  labelled or rendered wrongly. **Proving nothing was lost is not proving it is
  right**, and treating the first as the second is what put a broken build on
  the site. The audit checks shape per volume: blocks per page, hadith starts,
  headings, and footnote markers with no note on their own page. A healthy
  volume runs 4-5 blocks per page; a broken one runs 1.1-1.5.

> **A long single block is not a fault.** A ziyāra, one detailed legal hadith,
> or Imam Ali's endowment document each fill a page continuously. 197 such pages
> were checked by hand and 179 were genuinely one passage, so the audit
> thresholds on the RATE (>25% of a volume) rather than on any single page.

> **The hadith marker style differs per volume, and that is the source's own
> inconsistency — do not normalise it.** الاستبصار v1 is bare «176 - 1», v2 and
> v3 «[ 28 ] 4», v4 «( 21 ) 4»; التهذيب v1 and v5-v10 «( N )», v2-v4 «* ( N ) *».
> ablibrary's reader shows the same, so the pages match it character for
> character and a copied citation still matches its source. The owner chose this
> explicitly on 2026-09-25 after being shown the alternative.

> **ablibrary's book ids are not in volume order.** `6027` is Tahdhib **volume
> 10**, not volume 2, because «ج١٠» string-sorts right after «ج١». Derive the
> mapping by locating each volume's text — a wrong mapping still matches, since
> it is the same book, and only surfaces later as citations pointing at the
> wrong volume.

## البرهان في تفسير القرآن — Ghaemiyeh again, and why the source is argued per book (2026-09-25)

Five volumes, 4,348 pages, at `/burhan/<vol>/<page>/`. By السيد هاشم البحراني
(d. 1107 هـ), **تحقيق قسم الدراسات الإسلامية، مؤسسة البعثة، قم** — the Asifi
foreword is signed قم المشرفة، 10 شعبان 1412 هـ. Built by
`burhan_ar_extract.py` → `burhan_ar_build.py` → `burhan_ar_wire.py` from the
Ghaemiyeh export (ghbook.ir book 2694), kept in `Books/al-Borhan/html/`.

**This book reverses التهذيب's source decision, and the reasoning that chose
ablibrary there is simply untrue of this export.** Both were measured before
choosing:

| | ablibrary (1939-1943) | Ghaemiyeh (2694) |
|---|---|---|
| surah headings in the body | **0 in any volume** | **2,221** |
| empty pages | 193 of 4,349 (4.4%) | none |
| footnotes | 12,162 | 12,042 + 12,109 تخريج, **vocalised** |

ablibrary's «سورة المائدة مدنية» exists only in its table of contents, and 35
of its empty pages are exactly the surah-opening pages whose printed content IS
the surah title. Ghaemiyeh's `سورة فاتحة الكتاب ..... ص : 93` points at page 93
— one of those empty pages — and البقرة at 119 and آل عمران at 591 likewise, so
**the two agree page for page** and either can check a citation.

> Do not carry a source decision from one book to the next. التهذيب went to
> ablibrary because its Ghaemiyeh export had no footnotes and no printed page
> markers; this one has both. Reusing that conclusion here would have published
> a tafsīr with no chapter headings and 193 blank pages.

### Three conventions inverted from Bihar's export

Same publisher, same markup, and each of these silently destroys pages if the
Bihar rules are reused:

1. **The page marker OPENS its page here; in Bihar it CLOSES it.** A page is
   «البرهان في تفسير القرآن، ج 1، ص: 217» followed by that page's text, and
   page 216's footnotes sit BEFORE the marker. CLAUDE.md's جامع المقدمات note
   already says to check the tail of a new export before assuming either way —
   this is the export that proves why.
2. **The running header is split across paragraphs on 4% of pages**, at an
   arbitrary point, sometimes MID-WORD («الب» + «رهان في تفسير القرآن، ج 2»),
   and sometimes leaving the page NUMBER alone in its own paragraph. Matching
   it inside a single paragraph finds 96% of markers and merges the rest into
   their neighbour — which presents as 118 missing pages, not as an error.
   `reflow_markers()` matches across a window of up to four paragraphs, and the
   header must **BEGIN in the window's first paragraph**; without that anchor
   the window reaches forward over ordinary prose to the next page's header and
   republishes that prose on the wrong page, on nearly every page of the book.
3. **There are no `content_note` divs at all.** Footnotes are plain paragraphs
   after a `______` rule, in two kinds that are not interchangeable — the same
   split التهذيب has: «8- تفسير القمّي 1: 29.» is تخريج keyed to the hadith's
   own bracket number, «(1) في «س»: عن.» is a numbered footnote.

### The body marker is «N», never [N]

**«[1]» in this book is a hadith number or a Qur'anic AYA number**, not a
footnote marker — «251/ [1]- ابن بابويه» opens a narration, and
«* ( بِسْمِ اللَّه الرَّحْمنِ الرَّحِيمِ [1] ) *» carries the verse's number.
The footnote marker is «1», in guillemets. `REF` in `burhan_ar_build.py`
matches the guillemets alone; anchoring brackets the way `tahdhib_ar_build.py`
does would turn all 11,447 narration numbers and every verse number into links
to notes that do not exist.

A تخريج note **keeps its number here**, printed «٨ -» as the edition prints it,
because that 8 is the hadith's own «[8]» on the same page. التهذيب renders these
with «*» because there the key is a running id that appears nowhere on the
page; here it does. The two are still never merged into one numbered list.

### ablibrary is the authority on which pages exist

Ghaemiyeh **drops one running header roughly every 256 pages** — labels 93,
349, 605 and 861 are absent in almost every volume — and omits blank pages
entirely. Neither is recoverable from the export alone: with no header there is
nothing in the markup to say a page ended. So `--abl` supplies the missing cut,
located by matching that page's opening words.

- **Try several opening lines, not just the first.** Where a printed page
  breaks mid-sentence the two editions spell the joint differently («عز و جل»
  against «عزوجل»), so the first line can be unfindable while the second is
  exact. That is the whole difference between placing page 349 and publishing
  it blank.
- **A pre-marker match must be a whole-paragraph START, not a substring.**
  ablibrary's v1 page 2 is «بسم الله الرحمن الرحيم» alone, and that phrase also
  sits mid-sentence in the foreword's opening paragraph — a substring test
  handed the whole of مقدمة page 7 to printed page 2.
- **The run before the first marker holds SEVERAL pages**, so its cut points
  are all found first and the run sliced BETWEEN them. Taking each page as
  "everything from its own opening onwards" gives the first such page the whole
  run and leaves every later one empty.
- **Ghaemiyeh's own Persian cataloguing record is dropped** (سرشناسه / شابك /
  رده بندي / آدرس ثابت). It sits before the first marker, and left alone the
  repair pass adopts it as the printed title page — volumes 2-5 published
  «شابك 964-7866-20-8» as page 1.

Six printed pages are published BLANK because Ghaemiyeh has no text for them:
the title page of volumes 2-5, v1's «بسم الله الرحمن الرحيم», and v4's
«سورة الفرقان» title page. Blank, not absent — CLAUDE.md's rule, so a citation
never 404s.

### Heading levels carry the navigation

`content_h3` is the surah division («سورة البقرة مدنية», «المستدرك (سورة آل
عمران)»); `h4`/`h5` are the verse groups inside it («سورة البقرة(2): آية 195»).
Bihar's `+1` mapping collapses all three to one level, which leaves the
contents drawer as 400 undifferentiated verse rows with no surah heading among
them to navigate by. **Volume 5 has 72 surah headings and volume 4 only four** —
that is the book's shape, not a fault: v5 carries من الدخان إلى الناس while v1
covers only الفاتحة والبقرة وآل عمران.

`burhan_ar_wire.py` therefore reads the contents from the headings in the pages,
not from an external index as `tahdhib_ar_wire.py` must — so every row's page is
true by construction, because the row IS the heading on that page.

### The audit

```
python burhan_ar_extract.py <export.htm> <vol> --abl <dir> --out burhan_v<N>.json
```

It exits non-zero when a page cannot be placed, and prints the repair counts
per kind. The losslessness check is the word-frequency one Bihar uses, run
against the **post-reflow** item stream rather than the raw file — the raw
stream still contains every running header, so comparing against it reports
~1,250 phantom losses per volume (the page numbers) and that is enough noise to
hide a real one. Measured that way: **67 uncaptured tokens out of 2,005,443**,
all of them the export's own `<H1>` title element and «اشارة».

## الغدير — a source typeset in Persian (2026-09-26)

Eleven volumes, 6,374 pages, 18,457 footnotes, at `/ghadir/<vol>/<page>/`. By
**العلامة عبد الحسين أحمد الأميني النجفي**, **تحقيق مركز الغدير للدراسات
الإسلامية، قم، 1416 هـ / 1995 م** (ghbook.ir 9638). The library's
second-largest book after Bihar.

**The export is the ordinary Bihar shape** — `ص: N` markers, `<SPAN
class=chapter>` segments, real `content_note` divs with `content_notelink`
anchors — so `bihar_ar_extract.py` and `bihar_ar_audit.py` read it unmodified.
Only the prep and the builder are this book's own. It arrives as ONE 25 MB
`koli` file containing all eleven volumes, split on `<H2>المجلد N</H2>`.

### The text is Persian-typeset and is normalised before extraction

The export writes every Arabic yāʾ and kāf with the PERSIAN codepoint:
**411,830 `ی` (U+06CC) and 103,778 `ک` (U+06A9) against ZERO `ي` (U+064A) and
ZERO `ك` (U+0643)**. Every other Arabic book here is the other way round —
measured on published pages of Bihar, al-Kafi, al-Faqih, التهذيب, الاستبصار and
البرهان, all Arabic-dominant with zero Persian forms. Publishing it as-is would
make الغدير the only book in the library in Persian letter forms, visible to
any reader who copies a citation.

**The owner approved the conversion on 2026-09-26.** It runs in the prep step,
verified per volume position by position: same length, only those two
codepoints differing, and the counts of `ي`/`ك` rising by exactly the number
converted.

> **`پ`, `چ` and `گ` are NEVER touched.** They are real Persian letters with no
> Arabic equivalent, and they appear in Arabic nisbas of Persian and Indian
> place names — «الچلبي», «التورپشتي», «السهارنپوري», «الگلپايگاني». Those take
> a proper Arabic `ي` for the nisba ending, so converting the yāʾ in them is
> correct; converting the `چ` would be nonsense. 92 distinct words contain one,
> 42 of which also carry a yāʾ or kāf.

> **The conversion disarmed a guard in the shared extractor.**
> `bihar_ar_extract.py` drops the Ghaemiyeh blurb by matching the literal
> «تعريف مرکز» with a PERSIAN kāf. After normalisation the text reads «تعريف
> مركز» and no longer matches, so the publisher's donation appeal — bank
> account, Isfahan office address, telephone numbers — survived into volume 11.
> The prep step now cuts it explicitly, case-insensitively, and accepting
> either kāf. **A fix in one place can disable a check in another that nothing
> connects them.**

### What the prep step must strip, and why each was missed once

- **The `<H1>` book title.** Prepending the file head to each volume
  republished «الغدير في الكتاب و السنه و الادب» as a text block on 10 of the
  11. The prefix is cut at `<BODY>` instead.
- **The `<H2>المجلد N</H2>` split marker**, which otherwise becomes a heading
  block reading "المجلد 2" on page 1.
- **Ghaemiyeh's Persian cataloguing record** — سرشناسه / عنوان و نام پديدآور /
  مشخصات نشر / وضعيت فهرست / يادداشت / موضوع / شناسه افزوده / رده بندي /
  شماره كتابشناسي / آدرس ثابت / شابك. It was published as **page 1 of volumes
  2-11**. The first pattern written for it required the key immediately
  followed by a colon and so matched only the single-word keys: «عنوان و نام
  **پديدآور**:» and «مشخصات **نشر**:» passed straight through **while the
  assertion passed**, because the assertion tested `سرشناسه` alone. Allow up to
  40 characters before the colon, and assert against every key.
- **The promo block, which sits AFTER `</BODY></HTML>`** under a LOWERCASE
  `<h1>`. The extractor reads from `<BODY` to end of file, so it sees it.

### Every note carries its own number in its text

Note 1 reads «1- أخرجه الحافظ…», so rendering the builder's «(١)» in front of
it shows the number twice — true of **2,428 of volume 1's 2,428 notes**, and of
every volume. `note_text()` in `ghadir_ar_build.py` strips it **only when the
leading number equals the note's own**, so a note that genuinely opens with a
different figure is untouched: one v1 note reads «3- 1 - نزلت… 2 - نزلت…», and
the «3- » goes while the enumeration stays.

> **al-Kafi and al-Faqih are LIVE with this same doubling** — `kafi/1/50` shows
> 3 of 3 and `faqih/1/100` 6 of 6. Bihar's export omits the numbers, so Bihar
> is unaffected. Fixing the two means rebuilding and redeploying 6,968
> published pages; it has not been done.

### `UNCAPTURED SOURCE TOKENS: 0` is necessary, not sufficient

Volumes 2-10 reported **0** while publishing Ghaemiyeh's cataloguing record as
page 1. Zero means nothing was **lost** — it says nothing about what was
wrongly **included**. It was volume 11's **142** that exposed the promo block,
and only because that block happened to fall outside a captured segment. Pair
the audit with a check on the OUTPUT for text that should never appear:
catalogue keys, promo strings, and — here — any surviving `ی` or `ک`.

## Pager invariants — the check that did not exist until 2026-09-11

- **Never derive prev/next from a batch's ordering.** A batch is a unit of translation
  work, not a run of pages. An earlier builder chained each page to the neighbouring
  *entry in its batch*, which left `fa|ur/bihar/1/48` linking "next" to page **81** and
  `fa|ur/bihar/1/84` with no next link at all — a 32-page skip and a dead end, live for
  months. Derive them from the page's own number (`n - 1`, `n + 1`, as `build.py` does)
  or from the full ordered page list, never from the batch.
- **Run `verify_pagers.py` before any commit that adds or rebuilds pages.** It walks the
  chain instead of assuming N → N+1, because that assumption is already false here:
  Farsi Bayt al-Ahzan has 31 deliberate numbering gaps and مفاتیح interleaves named slugs
  with ordinals. It asserts the chain is a single path reaching every page exactly once.
- **`<link rel=prev/next>` and the pager buttons are written separately.** They must
  agree; only the buttons are ever noticed. **This describes `build.py`'s
  en/fa/ur output; `bihar_ar_build.py` writes the head links RELATIVE**, so any
  checker must resolve them against the PAGE's directory, not the site root —
  resolving against the root reports all 360 sampled pages as broken. The head links are absolute and the buttons
  relative, so any tool comparing them has to resolve both before comparing.
- **A rebuild is not a no-op.** `build.py`'s `description()` takes the first 150 chars of
  the *first* translated line, so re-running it over a page that opens with a heading
  shortens that page's meta description to the heading alone. Diff before overwriting;
  repair links surgically when that is the only fault.
- **`verify.py` compares Arabic text, not Arabic markup.** An Arabic page wraps some
  headings in `<span data-ar= data-fa= data-ur= data-en=>` so `reader.js` can swap them
  in place; a translated page prints the translation on the next line instead and carries
  the bare heading. `unwrap_heading()` drops that wrapper before comparing — but only when
  the span's own `data-ar` equals the text it wraps, so a genuinely altered heading still
  fails. Do not "simplify" it into an unconditional strip.
- **`reextract.py` does not reconfigure stdout.** On Windows it dies with
  `UnicodeEncodeError: 'charmap'` on the first Arabic character — run it as
  `PYTHONIOENCODING=utf-8 python reextract.py …`.

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
- **No automated check tests whether a translation is CORRECT.** The Bayt al-Ahzan
  checks prove the Arabic is byte-exact, that every block has a line, that the line
  matches the translation file, and — for Urdu — that it is written in Urdu and not
  left as Arabic. None of that is accuracy. 814 blocks and 336 notes in each of two
  languages are machine output that no human has read; the machine-translation badge
  on every page is the only thing standing between a reader and that fact. A sampled
  human review is outstanding for both English and Urdu.

---

## SEO checklist

### Current status
| Item | Status |
|---|---|
| `robots.txt` — allows all, points to sitemap | ✅ |
| `sitemap.xml` — **index** over 2 shards, 48,556 URLs | ✅ |
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

1. Run `verify_pagers.py` — it must report 0 broken links
2. Run `gen_sitemap.py` to regenerate `sitemap.xml`
3. Update `CHANGELOG.md` with what was added
4. Owner commits and pushes both files along with the new pages

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
4. Confirm the new pages carry the tree's current `?v=` (9), and that nothing
   outside the new book was touched.

---

## Site icon

`/favicon.ico`, `/apple-touch-icon.png` and `/icon-512.png` sit at the **repo root** and
are found by convention — no page declares them, and none should. A browser requests
`/favicon.ico` from the origin root whatever the page's depth, so one file covers all
~4,100 pages; adding `<link rel="icon">` would rewrite every page for nothing.

They are generated from `Misbah Website/assets/logo.png` (the dark-green disc) with the
**MISBAH wordmark cropped away** — at 16px the full logo is an illegible smudge. The mark
is scaled to 72% of the disc. Two things to keep if they are ever regenerated: the disc
stays dark (a cream-on-white mark disappears on a light tab bar), and the Apple icon is
**flattened onto the brand green**, because iOS ignores alpha and composites on black.

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
| `bihar/2/`…`bihar/110/` (Arabic, source) | 44,306 | Complete 2026-09-13, no translation (`data-trlangs=""`) |
| `en/bihar/1/` | 231 | Complete, machine translation |
| `fa/bihar/1/` | 231 | Complete, machine translation |
| `ur/bihar/1/` | 231 | Complete, machine translation |
| `bihar/`, `en|fa|ur/bihar/` | 4 | Volume selectors — all 110 tiles active |
| `quran/` + `quran/1–114/` | 115 | Cover and all 114 surahs, Arabic |
| `en|fa|ur/quran/1–114/` | 342 | 12 translations, reader-selectable; defaults Shakir · فولادوند · علامہ جوادی |
| `quran/assets/` | — | `toc.json`, `qnav.json`, `qnav.js`, `tr/*.json` (12 translations), `votd.json` + `votd/*.json` |
| `bayt-al-ahzan/` | 1 | Arabic cover (5 chapters, دار الحكمة edition, Bihar-style) |
| `bayt-al-ahzan/1–189/` | 189 | Arabic original (Qummi), pages 1–189 |
| `en/bayt-al-ahzan/` | 1 | English cover (5 chapters, English titles) |
| `ur/bayt-al-ahzan/` | 1 | Urdu cover (5 chapters, Urdu titles) |
| `en/bayt-al-ahzan/1–189/` | 189 | English of the Arabic — **machine translation, not reviewed by a human**, complete 2026-09-11 |
| `ur/bayt-al-ahzan/1–189/` | 189 | Urdu of the Arabic — **machine translation, not reviewed by a human**, complete 2026-09-11 |
| `bayt-al-ahzan-fa/` | 1 | Farsi cover |
| `bayt-al-ahzan-fa/1–262/` | 262 | Complete Persian text (Ishtihardi), printed pages |
| `jame-al-muqaddimat/` | 1 | Volume selector |
| `jame-al-muqaddimat/1/` + `1/1–609/` | 610 | Vol 1 contents + pages, 9 treatises |
| `jame-al-muqaddimat/2/` + `2/1–607/` | 608 | Vol 2 contents + pages, 6 treatises |
| `mafatih/` + 689 pieces | 690 | Cover (11 tiles) + every piece, Arabic + انصاریان Persian |
| `kafi/` | 1 | Volume selector — all 8 tiles active |
| `kafi/1/`…`kafi/8/` | 8 | Volume indexes, 2,703 chapter rows total |
| `kafi/1/…8/<page>/` (Arabic, source) | 4,484 | Complete 2026-09-22, no translation (`data-trlangs=""`) |
| `faqih/` | 1 | Volume selector — all 4 tiles active |
| `faqih/1/`…`faqih/4/` | 4 | Volume indexes, 789 chapter rows total |
| `faqih/1/…4/<page>/` (Arabic, source) | 2,484 | Complete 2026-09-23, no translation (`data-trlangs=""`) |
| `tahdhib/` + `tahdhib/1/`…`10/` | 11 | Volume selector + volume indexes, 360 chapter rows |
| `tahdhib/1/…10/<page>/` (Arabic, **ablibrary**) | 4,081 | Complete 2026-09-23, no translation |
| `istibsar/` + `istibsar/1/`…`4/` | 5 | Volume selector + volume indexes, 837 chapter rows |
| `istibsar/1/…4/<page>/` (Arabic, **ablibrary**) | 1,583 | Complete 2026-09-23, no translation |
| `burhan/` + `burhan/1/`…`5/` | 6 | Volume selector + volume indexes, 2,168 chapter rows |
| `burhan/1/…5/<page>/` (Arabic, **Ghaemiyeh**) | 4,348 | Complete 2026-09-25, no translation |
| `ghadir/` + `ghadir/1/`…`11/` | 12 | Volume selector + volume indexes, 853 chapter rows |
| `ghadir/1/…11/<page>/` (Arabic, **Ghaemiyeh**) | 6,374 | Complete 2026-09-26, no translation |

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

**Tashkīl.** The source is unvocalised (~0.5%). **764 blocks, 110,532 marks** are now
vocalised as an overlay in `_translation-kit/jame_tashkil.json`. Four treatises are
complete: کتاب الامثله, شرح الامثله, کتاب التصریف (80/80) and **کتاب شرح التصریف
(511/511)**. عوامل ملا محسن is in progress. Three rules any future treatise must follow:

1. **Add marks only, never substitute a letter.** The source writes `اضرب` and `ضاربه`,
   not `أضرب`/`ضاربة`; changing those is editing, not vocalising. Verified per block by
   `strip_diacritics(vocalised) == original`, exact — the build fails otherwise.
2. **Vocalise positionally, never by word lookup.** `ضربت` appears four times in the ماضی
   block as four different words (ضَرَبَتْ / ضَرَبْتَ / ضَرَبْتِ / ضَرَبْتُ). A word map gets
   three wrong, silently, for exactly the reader trying to learn it.
3. **Never write a batch straight to the overlay — go through `jame_tashkil_apply.py`.**
   It refuses the whole batch if any entry alters the text, printing the first differing
   character with context. Over 764 blocks it caught ~40 attempts, every one of them a
   case of writing the *standard* form instead of the *printed* one: `فائه`→`فاؤه`
   fourteen times, `الان`→`الآن`, `متعد`→`معتد` (transposed), `مست`→`مسست` in a sentence
   that is *about* مست being contracted, and `قه`→`ته` where the edition's own example
   repeats itself. None is visible on a rendered page.

> **Pre-vocalised runs in the source must be spliced, never retyped.** Qur'anic verses in
> this export already carry their marks, and the source writes shadda-then-vowel where NFC
> writes vowel-then-shadda — canonically equal, visually identical, not byte-identical.
> `runs()` (see any `batch*.py`) finds maximal spans that already carry diacritics and
> returns them verbatim. `jame_tashkil_check.py` verifies all 65 survive.

> **A "Persian" block is not always the one tagged `fa`.** `1:496:1` is Arabic prose that
> quotes a mnemonic the author introduces with نَظَمْتُهَا بِالْفَارِسِیَّةِ — "I versified them in
> Persian." Nothing about the line looks Persian; the only evidence is the sentence before
> it. The harness's Persian-word check caught it. That line ships unmarked.

It ships as an overlay: the page emits the printed text plus `data-tashkil`, and reader.js
swaps them behind the اعراب button. Never replace the printed text — a citation must not
resolve to something an editor added.

```
python jame_tashkil_check.py       # in-loop check: must print "All clear"
python jame_tashkil_review.py      # independent audit: must print "no mechanical fault"
python jame_build.py jame_pages.json --out <L>/jame-al-muqaddimat
```

> **Progress counts must not ask "is the key in the overlay?"** An early automated pass
> vocalised the ضرب/نصر paradigm book-wide, which leaves a key on blocks whose prose is
> untouched. Counting keys overstated شرح التصریف as 511/511 and التصریف as 80/80 when
> eleven of those blocks carried three or four marks in 400+ letters. `jame_tashkil_review.py`
> audit 5 lists them; the count must require ≥0.05 marks per letter *added by the overlay*.

> **When comparing vocalised against printed, strip BOTH sides.** The printed text carries
> its own diacritics wherever the source quotes a vocalised verse. Stripping only one side
> can never match and looks like catastrophic corruption. This mistake has been made three
> times in this project — in a browser check and twice in review code.

> The overlay is NFC (vowel-then-shadda) **except** inside spliced source runs, which keep
> the edition's shadda-then-vowel order byte-for-byte. Both render identically. Do not
> normalise the file: it would break the splice guarantee.

> `jame_build.py` loads the overlay **by default**. Passing `--no-tashkil` silently strips
> vocalisation from all 1,216 pages with no error, which is how it was lost once.

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

**Qur'an translations (2026-09-06).** Twelve Tanzil translations, four English,
five Persian, three Urdu. `TRANSLATIONS` in `quran_build.py` is the registry and
**the first entry of each language is the default**: its text is written into the
HTML, so it is what a reader without JavaScript sees and what Google indexes. The
other eleven ship as `quran/assets/tr/<lang>.<id>.json` and are swapped in by
`qnav.js` when the reader picks them. The reader's pick is stored as `qtr:<lang>`
in `localStorage`, so the cover and every surah page share one setting.

> Adding a translation is a data drop: put Tanzil's `sura|aya|text` file in
> `_translation-kit/quran-source/tr/`, add an entry to `TRANSLATIONS`, then
> `quran_build.py --lang ar --out <L>/quran --assets` and rebuild that language's
> pages. Never insert one at position 0 — that silently changes the default
> translation on 114 published pages.

> **A `.tr-line` must carry its own `dir`.** The Mushaf layout puts `.body` in
> `direction:rtl`; an English paragraph that inherits it reads correctly word by
> word but lays its lines out right-to-left. `quran_build.py` writes the attribute
> and `reader.css` pins it from `:lang()`.

> `votd.json` carries only each language's **default** translation. A reader on a
> non-default gets `votd/<lang>.<id>.json` (366 strings) instead — pulling a whole
> 900 KB corpus to render one verse would be absurd.

> **`ASSETS_V` in `quran_build.py` is the same frozen 9 as everywhere else.** It once
> looked cheap to bump here alone (457 pages), which is how the tree ended up on two
> different values. It is frozen now; see the `ASSETS_V` note above.

**مفاتیح الجنان (2026-09-06).** Live at `/mafatih/` — cover + 689 pages.
`mafatih.json` holds 689 sections and 4,073 Arabic units, 98% of them paired with
حسین انصاریان's Persian. The export *pairs* the two explicitly (a `content_notelink`
after each Arabic span carries that span's own translation), so the print edition's
footnote numbering never has to reach the screen. The Arabic arrives fully vocalised.

> **The landing page and the reading order are two different things.** `/mafatih/` is a
> chooser — five editorial categories (اعمال/زیارت/نماز/ادعیه/قرآن), each its own page.
> The edition's own order lives behind «شروع خواندن» and the contents drawer and is never
> reordered. Categories are matched on the FOLDED section title (honorific diacritics
> cannot be retyped reliably) and the build fails loudly if one stops matching.

> **`html{scroll-behavior:smooth}` is set site-wide in reader.css.** Any programmatic
> `scrollIntoView` must pass `behavior:'instant'` or it inherits the animation, which the
> webfont reflow then abandons — the reader lands at the top of the page they searched
> into the middle of. Re-aim on `fonts.ready` and `load` as well, and bind to
> `hashchange` for same-page links.

> **One pairing may span two units.** Where the print edition breaks a phrase across a
> page, the export splits it and hangs the footnote on the SECOND half; 41 units look
> untranslated because of it. They are joined in `body_html` at render time and never in
> the data — merging would renumber the frozen unit ids.

> **Search is two indexes, not one.** Names (689 rows, 20 KB gzipped) load with the
> search panel and answer per keystroke, ranked by IDF-weighted token overlap so
> «دعای خمس عشر» finds «مناجات خمس عشره». Text (5,750 rows, 1.3 MB gzipped) is fetched
> only on request. Both sides are folded (diacritics, ی/ي, ک/ك, ه/ة, ZWNJ, digits); the
> fold keeps an index map back to the original so snippets show vocalised text. Hits link
> to a UNIT — `/mafatih/<slug>/#u-<unit id>` — not just a page.

> **92 sections are titled «إشارَة:».** One of them is زیارت اربعین. Each section's first
> line is indexed as an alias for its name and shown as the result subtitle; without it
> those sections are unfindable by name.

> **اعمال هفته: the Islamic day begins at maghrib.** «اعمال شب جُمعه» is *Thursday*
> evening. Those rows carry `data-eve` and surface a day before their name says, labelled
> امشب. Weekday detection matches longest-first (یکشنبه/سه شنبه/پنجشنبه all end in شنبه)
> and is gated on ancestry, or «سوره جُمعه» becomes a Friday devotion.

> **One page is one piece, not one printed page.** دعای کمیل is a single page top to
> bottom; the printed edition's 1,871 page breaks ride inline as «ص ۱۶۵» markers instead.
> The book is recited, not consulted — printed-page pagination would interrupt a
> supplication five times. Citation survives because the folio numbers are on the page.

> **Slugs are navigation, ids are data.** 26 famous pieces carry a Latin alias
> (`/mafatih/dua-kumayl/`), the rest an ordinal (`/mafatih/137/`). Renumbering a page is
> survivable; renumbering a UNIT id is not, because translations key to those.

> **The book's own script is `mafatih/assets/mafatih.js`,** not `reader.js` — same rule as
> the Qur'an's `qnav.js`. `reader.js` is loaded by every page in the library.

> **A cover must be `<main class="cover">`, never `<main class="wrap">`.** `.wrap` is
> `display:flex`, so a cover nested inside it shrinks to its content and any tile grid
> collapses to one narrow column. The Qur'an cover has always done this correctly.

> `reader.js` skips the `pages.json` fetch for `quran` **and** `mafatih`; both paginate
> through their own pager and ship none, so asking for one is a guaranteed 404.

> **Unit ids are frozen and are the one thing that must never be revised.** English and
> Urdu will be keyed to `<section-id>:<n>` later, so an id that moves silently re-points
> a translation. They are derived from the section's **title path, hashed** — never from
> its position, because a positional id looks stable and is not: merge two sections and
> every id after them shifts. `mafatih_verify.py` audit 3 re-extracts and compares.

> **The Persian instruction is peeled off the head of an Arabic run, never the tail and
> never the middle.** One Arabic unit carries exactly one translation, so cutting the core
> in two would leave half a duʿā translated and half not. 832 runs are peeled into
> `rub` + `ar`; 36 are Persian prose quoting Arabic inline and stay whole, flagged `mixed`.

> **The edition ships with an app, so each piece opens with reciter credits** — `صوت`,
> names, `***`. They must be stripped *before* ids are assigned: one reciter name reads as
> Arabic and otherwise holds `dua-kumayl:1`. Some sections carry the credits without the
> `صوت` marker, so the 38 names are learned where the markup proves them and removed
> elsewhere only on an exact match.

**Bihar is complete in Arabic: all 110 volumes**, and **al-Kafi is complete in
Arabic: all 8.** Bihar volume 1 is also in en/fa/ur; 2–110 and all of al-Kafi are
not translated. The Qur'an is complete in all four languages.
**All four canonical books are published in Arabic** — الكافي, من لا يحضره الفقيه,
تهذيب الأحكام and الاستبصار. The last two come from **ablibrary**, not Ghaemiyeh;
see that section for why, and do not swap their source. **البرهان في تفسير القرآن**
is published too, from Ghaemiyeh — the opposite choice, argued from that export
rather than carried over. الغدير remains a `catalog.json` placeholder.

---

## Open work

In rough priority order. Nothing here is started.

1. ~~**`bookCard()` gates on `volumesPublished`**~~ — **done 2026-09-12.** `catalog.json`
   now carries an explicit `langIndex: true` on the books that have an index page at
   `<lang>/<slug>/`, and `bookCard()` reads that. `volumesPublished` went back to meaning
   only what it says and is read only by the stats counter. Bayt al-Ahzan's fictitious
   `volumesPublished: [1]` is gone.
2. **Bayt al-Ahzan is finished in Arabic, English and Urdu** (2026-09-11). Nothing
   remains on this book. Any fourth language follows the same route: translate into
   `bayt_tr_<lang>.json` keyed `<page>:<block>` and `<page>:n<note>`, then the builds
   **together** — the new language, the Arabic rebuild, every *other* translated language,
   and `gen_sitemap.py`.

   > **`--tr-upto` is per language and every build needs the full set.**
   > `--tr-upto en=189,ur=189` on *every* invocation, including the new language's own.
   > Omitting it there is what left the whole Urdu tree with no `hreflang="en"` and no
   > `data-alt-en`: English claimed Urdu, Urdu did not claim English, and a
   > one-directional cluster is ignored wholesale. Automated checks passed it because they
   > compared each translation to the **Arabic** and never to each other.

3. ~~**Bihar volumes 7–110**~~ — **done 2026-09-13.** All 110 volumes in Arabic.
   Translations are the remaining work, and they are what forces the hosting move.
4. **A `.gitattributes`** to silence the CRLF warnings, if the noise ever matters.
5. **Finish the Bihar orthography pass in volumes 2-110** — «شی ء» → «شي ء»
   (~14,000, 0.3/page) and the meta descriptions, both exactly derivable and
   both already implemented in `bihar_chrome_fix.py`; volume 1 has them.
   Dropped on 2026-09-28 only because the pass measured at ~24 hours of Drive
   I/O. **Fold it into the next Bihar rebuild rather than paying a separate
   44,537-page rewrite**, and thread it — see the Drive note below.
6. **Run `verify_pagers.py` in full** at the next genuine page rebuild. It was
   substituted by a 360-page sample on 2026-09-28 (0 problems) because it walks
   71,779 pages single-file (~8 hours) to check navigation that byte-equality
   guards already proved untouched. That reasoning holds for an in-place text
   edit; it does NOT hold once pages are rebuilt.

> **When Drive goes slow, measure before blaming the code.** On 2026-09-28 reads
> went from 0.4s to **8-20s per file** and the Drive client showed "Syncing… 1
> file, more than 12 hours left" — a stuck transfer, with an ETA computed from
> ~zero throughput. Compute was **8-12 ms against 8,000 ms of waiting**.
> **Quit and reopen Google Drive** (tray → ⚙ → Quit); it came back 20× faster.
> And thread anything touching thousands of files: 32 concurrent reads give
> ~29 files/sec where serial gives 2.4.

### Known-good state

As of 2026-09-01 (pre-Arabic build): 1,173 URLs in sitemap, Farsi Bayt al-Ahzan's 229
pages verified 0 failures, Qur'an and Bihar untouched. `.suras` is the Qur'an's alone;
`.chaps` is every other book's chapter grid.

**Pending commit (2026-09-01):** Arabic Bayt al-Ahzan build — 189 new reading pages +
Arabic cover + Farsi cover at `/fa/bayt-al-ahzan/` + all Farsi reading pages rebuilt
(data-book update) + `bayt_ar_build.py` + `bayt_ar.json`. Sitemap not yet regenerated
for these 190 new URLs — run `gen_sitemap.py` before committing.
