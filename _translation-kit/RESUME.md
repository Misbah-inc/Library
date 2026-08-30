# Misbah Library — translation kit and handoff notes

This folder is the working kit for the Library. It builds translated pages from
the Arabic source of record, verifies them, and regenerates the site's SEO
files.

**Site:** https://library.misbah-inc.com (a custom domain on GitHub Pages; the
repo root is served at the domain root, so `misbah-inc.github.io/Library/X` is
now `library.misbah-inc.com/X`. Old github.io URLs redirect automatically.)

---

## Status

| tree | pages | state |
|---|---|---|
| `bihar/1/` (Arabic, source of record) | 231 | complete |
| `en/bihar/1/` | 231 | complete, machine translation |
| `fa/bihar/1/` | 231 | complete, machine translation |
| `ur/bihar/1/` | 231 | complete, machine translation |

Volume 1 is done in all three translation languages, footnotes included.
Volumes 2–110 are not started. `catalog.json` lists the four canonical hadith
collections and the other books as placeholders.

---

## The scripts

| script | what it does |
|---|---|
| `extract.py` | Arabic page → JSON of `data-i` nodes and footnotes |
| `merge_build.py` | translation module + Arabic → built pages |
| `build.py` | the page template; called by `merge_build.py` |
| `verify.py` | checks a built page against its Arabic source |
| `reextract.py` | built page → JSON, losslessly (see *Regenerating*) |
| `gen_sitemap.py` | rewrites `sitemap.xml` and `robots.txt` from what is on disk |
| `Fix-LibrarySeo.ps1` | one-time SEO repair pass over published pages |

All of `build.py`, `merge_build.py` and `verify.py` take `--lang` (`en`/`fa`/`ur`)
and `--volume`. Nothing is hardcoded to English or to volume 1 any more.

---

## The pipeline

1. Stage the Arabic sources for the batch.
2. `python3 extract.py <ar files…> > batch.json`
3. Translate. Write `tr_<lang>_<a>_<b>.py` with
   `PAGES = {page: [line, …]}` (one line per `data-i` node, in order) and
   `NOTES = {"fn-0-12-1": "…"}`. Use plain apostrophes; `merge_build.py`
   escapes them.
4. `python3 merge_build.py tr_<lang>_<a>_<b> <outdir> --lang ur --volume 1 <ar files…>`
5. `python3 verify.py <pages…> --lang ur --volume 1 --root <ar root> --out <outdir>`
   — **must report 0 failures before anything is committed.**
6. Write to `Library/<lang>/bihar/<vol>/<n>-draft/index.html`.
7. After any batch that adds pages, regenerate the sitemap:
   `python3 gen_sitemap.py --root "G:/My Drive/Misbah Library/Library"`

`verify.py` checks: Arabic byte-identical to source, `data-i` contiguous, one
translation line per node, no empty lines, footnote refs matched to note blocks,
every note translated, correct page/volume/total, the full absolute hreflang set,
no stale domain, and no Arabic-only chrome leaked in.

---

## Adding a volume

The generators are volume-aware, so this is mostly mechanical:

```
--volume 2 --total <pages in volume 2>
```

Then:

1. The Arabic tree must exist first at `bihar/2/<n>/`. It is the source of record.
2. Build each language as above.
3. **`--alts` matters.** It declares which language versions actually exist for
   that volume. If only Arabic and English are published, pass `--alts ar,en`.
   Listing a language whose pages are not live points hreflang at a 404, and one
   bad URL invalidates the whole cluster. Widen `--alts` and rebuild as each
   translation lands.
4. Update `catalog.json`: `volumesPublished`, and `pages` for the new volume.
5. Regenerate the sitemap.

---

## SEO invariants — the part that is easy to get silently wrong

These were all wrong at some point and none of them announced themselves.

- **Canonical and hreflang URLs are absolute.** Google discards relative
  hreflang. `build.py` emits absolute URLs from the `SITE` constant.
- **The hreflang set is reciprocal and self-referential.** Every page lists
  every published version *including itself*, and each of those pages must point
  back. A one-directional cluster is ignored wholesale — which is what happened
  when the Arabic pages carried no alternates at all.
- **`x-default` points at the Arabic**, the source of record.
- **`SITE` lives in `build.py`.** It was previously hardcoded to the github.io
  URL in the template, so every regenerated page silently reverted. If the
  domain ever changes, change it there and in `gen_sitemap.py`, then rebuild.
- **Never advertise a `-draft` page.** `gen_sitemap.py` skips them; the path
  filter in `Fix-LibrarySeo.ps1` skips them too.

---

## Regenerating pages after a template change

The `tr_<lang>_*.py` modules are working files from whichever session produced a
batch and are **not** kept. The published pages are the durable record — they
carry the Arabic and the translation together with markup intact.

```
python3 reextract.py --lang ur <built pages…> > batch.json
python3 build.py batch.json <outdir> --lang ur --volume 1
python3 verify.py <pages…> --lang ur --out <outdir>
```

Round-trip is lossless; this was verified byte-for-byte. No translation is ever
retyped.

Note `bihar/assets/tr/<lang>.json` is a *different* thing: plain text for the
search index and the in-page translation layer, with markup stripped. It cannot
rebuild a page. It does carry footnote entries (`{"n": 1, "text": "…"}`)
alongside body entries (`{"i": 0, "text": "…"}`) — both are needed, because a
reader switching language on an Arabic page gets footnotes injected from there.

---

## Working without the owner's computer (Google Drive path)

`G:\My Drive\Misbah Library` is Google Drive. A scheduled run has no link to the
owner's computer but can reach the same files through the Drive connector
(`mcp__Google_Drive__*`, deferred — load with ToolSearch). Round-trip is
byte-exact, Arabic and HTML entities included.

| what | Drive folder ID |
|---|---|
| Arabic `bihar/1/` | `1Azs5MZukGcHo9BjoQDdMZYZhcWA_KCoY` |
| English `en/bihar/1/` | `1ob05LhboBZ0d1PM30A1jONHAu0dXthwo` |
| this kit `_translation-kit/` | `1VitPwwF9fJ0hnAXphK0XvxHgeJLbMJR6` |

`create_file` always creates; there is no replace. To overwrite: `search_files`
for the existing file, `trash_file` it, then `create_file`. Always pass
`disableConversionToGoogleType: true` — without it the file becomes a Google Doc
and is destroyed as a web page.

`en/bihar/1/` holds well over 231 child folders, so page through listings with
`pageSize: 100` and `pageToken` until empty before concluding anything is missing.

## Bulk edits across the published tree

Editing ~900 files through the device bridge is slow and floods the chat. A
PowerShell pass on the owner's machine takes seconds. `Fix-LibrarySeo.ps1` is
the worked example. Two rules:

- Read and write with `[System.IO.File]::ReadAllText/WriteAllText` and
  `UTF8Encoding($false)`. PowerShell's default `Set-Content` encoding corrupts
  Arabic, Urdu and Farsi silently.
- Make it idempotent and report a change count, so a second run proves the pass
  was clean.

Windows blocks unsigned scripts; run with
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force` first, which
lasts only for that window.

---

## Translation conventions (keep consistent — this matters most)

- Literal and fidelity-first, narrator names transliterated, not anglicized.
- `b.` for ibn; `al-` prefixes kept; `&#x27;` for hamza/ayn; `&quot;` for quotes.
- *ḥaddathanā* → "There related to us"; *akhbaranā* → "There informed us";
  *ḥaddathanī* → "There related to me".
- `بيان` → "Elucidation:"; `إيضاح` → "Clarification:"; `أقول` → "I say:".
- Book sigla keep both letter and expansion, e.g. `sn, al-Mahasin`;
  `l, al-Khisal`; `nhj, the Nahj al-Balagha`; `b, Qurb al-Isnad`.
- Editorial footnotes signed `ط` end with " T." in English.
- Qur'anic quotations translated fresh, in double quotes.

For Urdu and Farsi, `verify.py` cannot check for "Arabic left untranslated" —
both are written in the Arabic script, so that check runs for English only.
Those languages need a human eye on a sample of each batch.

---

## Standing constraints

- **Never touch GitHub.** No clone, commit, push, or Actions. Committing and
  pushing is the owner's job alone. Write only into the library folder.
- **Never commit a page that fails verification.**
- **The machine-translation badge stays on every generated page.** These pages
  are not scholar-reviewed; the reader is told to cite the Arabic.
- **Renaming `-draft` folders into place is the owner's decision.**
- **Never alter the Arabic text or an existing translation.** This is the
  content rule and it stands absolutely.

On that last point: the Arabic and `en/` trees were previously off-limits
*entirely*. The owner authorized structural edits to their `<head>` and
`#page-meta` during the domain migration, because the canonical and hreflang
repair could not work otherwise. Page **content** was never touched, and that
was verified byte-for-byte. Treat structural head changes as requiring the
owner's explicit approval each time, and content as never editable.

---

## Known follow-up

- `catalog.json` still describes volume 1 only (`pages: 231`,
  `volumesPublished: [1]`).
- Translations are machine-generated. Google treats bulk machine translation as
  low-value, so expect the Arabic to be found far more readily than the
  translations. Scholar review would change that; the badge should stay until
  it happens.
- After the first deploy to the new domain, add `library.misbah-inc.com` in
  Google Search Console and submit `sitemap.xml`. Nothing gets crawled until
  that happens.
