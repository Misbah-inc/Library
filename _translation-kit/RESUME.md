# Bihar vol. 1 — English translation: resume notes

This folder is the handoff kit for the Bihar vol. 1 translation.

**Status: volume 1 is complete.** All 231 pages of the English tree are covered —
pages 1-48 and 81-84 were translated before this project; pages 49-80 and 85-231 were
produced here and sit in `<n>-draft/` folders. Every batch passed `verify.py` with
0 failures. What remains is the owner's: reviewing the drafts, renaming them into
place, and the prev/next sweep noted at the bottom.

The notes below stand for volume 2 and for any re-run.

## Where the work stands

- Arabic source of record: `Library/bihar/1/<page>/index.html`, pages **1–231**.
- English output: `Library/en/bihar/1/<page>/index.html`.
- Pages **1–48** and **81–84** were already translated before this project began.
- Pages **49–80** and **85–231** were produced by this project and are complete.
- Everything produced by this task is written to `Library/en/bihar/1/<page>-draft/`
  — a sibling folder, so the live `en/` tree is never touched.

## How to find where to resume

Do **not** guess. List `Library/en/bihar/1/` on the device and compute:

    covered  = pages with a plain `<n>/` folder  (1–48, 81–84)
             + pages with an `<n>-draft/` folder (produced by this task)
    next     = lowest page in 1..231 not in `covered`

Work forward from `next`. Skip any page already covered.

## Running without the owner's computer (Google Drive path)

`G:\My Drive\Misbah Library` is Google Drive. A scheduled run has **no link to the
owner's computer**, but it can reach the very same files through the Google Drive
connector (`mcp__Google_Drive__*`, load with ToolSearch — they are deferred). Writes
land in Drive and sync down to `G:` on the owner's machine automatically.

Round-trip is byte-exact. This was verified: a file written with `create_file` and read
back with `download_file_content` was identical to the byte, Arabic and HTML entities
included; and page 173's Arabic source in Drive matched the owner's copy at 21,473 bytes.

### Folder IDs (stable)

| what | Drive folder ID |
|---|---|
| Arabic `bihar/1/` | `1Azs5MZukGcHo9BjoQDdMZYZhcWA_KCoY` |
| English `en/bihar/1/` | `1ob05LhboBZ0d1PM30A1jONHAu0dXthwo` |
| this kit `_translation-kit/` | `1VitPwwF9fJ0hnAXphK0XvxHgeJLbMJR6` |

### Reading a page

    search_files: parentId = '<bihar/1 id>' and title = '<n>'     -> page folder id
    search_files: parentId = '<page folder id>'                    -> index.html file id
    download_file_content: fileId = '<file id>'                    -> base64, decode to bytes

Write the decoded bytes to `<localroot>/bihar/1/<n>/index.html` so the kit scripts see
the layout they expect, then pass `--root <localroot>` to `verify.py`.

### Writing a page

`create_file` **always creates a new file** — there is no content-replace tool, so a
second write of the same title produces a *duplicate*, not an overwrite. Therefore:

1. `search_files: parentId = '<en/bihar/1 id>' and title = '<n>-draft'`
   — if the folder is missing, `create_file` with
   `mimeType: application/vnd.google-apps.folder` under the `en/bihar/1` id.
2. `search_files: parentId = '<that folder id>' and title = 'index.html'`
   — if a file comes back, `trash_file` it first.
3. `create_file` with `parentId` = that folder, `title` = `index.html`,
   `contentMimeType` = `text/html`, `disableConversionToGoogleType` = **true**,
   and `textContent` = the built HTML.

Omitting `disableConversionToGoogleType` converts the file into a Google Doc and
destroys it as a web page. Always set it.

### Listing what is already done

`en/bihar/1/` holds well over 231 child folders, so a single search will not return them
all. Page through with `pageSize: 100` and `pageToken` from `next_page_token` until the
response comes back empty, and only then compute `next`.

## The format

Each English page interleaves at paragraph level, keyed by `data-i`:

    <p lang="ar" data-i="N">…Arabic, byte-identical to source…</p>
    <p class="tr-line" lang="en">…English…</p>

Footnotes: the Arabic keeps its `<a class="fnref" href="#fn-…">` markers untouched;
the English line renders the marker as a plain `(1)`, `(2)`. Each note block carries a
`<span class="tr-note-line" lang="en">` with the translated note.

The `en/` shell differs from the Arabic shell: `lang="en" dir="ltr"`, four-level
`data-root`, `hreflang` alternates, the `tr-bar` view toggle with the machine-translation
badge, `data-tr-static="1"`, `#page-meta` with `data-alt-*`. It does **not** carry the
Arabic-only chrome (edge nav, cite block, drawer). `build.py` handles all of this.

## Translation conventions (keep consistent — this matters most)

- Literal and fidelity-first, with narrator names transliterated, not anglicized.
- `b.` for ibn; `al-` prefixes kept; `&#x27;` for hamza/ayn; `&quot;` for quoted material.
- *ḥaddathanā* → "There related to us"; *akhbaranā* → "There informed us";
  *ḥaddathanī* → "There related to me".
- `بيان` → "Elucidation:"; `إيضاح` → "Clarification:"; `أقول` → "I say:".
- Book sigla keep both letter and expansion: `sn, al-Mahasin`; `l, al-Khisal`;
  `ma, the Amali of al-Shaykh al-Tusi`; `'a, 'Ilal al-Shara'i'`; `n, 'Uyun Akhbar al-Rida`;
  `yr, Basa'ir al-Darajat`; `nhj, the Nahj al-Balagha`; `f, Tuhaf al-'Uqul`;
  `m', Ma'ani al-Akhbar`; `ms, Misbah al-Shari'a`; `dh, Rawdat al-Wa'izin`;
  `khts, al-Ikhtisas`; `ghw, Ghawali al-La'ali`; `thw, Thawab al-A'mal`; `b, Qurb al-Isnad`.
- Editorial footnotes signed `ط` end with " T." in English.
- Qur'anic quotations are translated fresh, in double quotes.

## The pipeline

1. Stage the Arabic sources for the batch into the container.
2. `python3 extract.py <ar files…> > batch.json` — pulls the `data-i` nodes and footnotes.
3. Translate. Write a `tr_<a>_<b>.py` module with `PAGES = {page: [english, …]}` and
   `NOTES = {fn-id: english}`. Plain apostrophes; `merge_build.py` escapes them.
4. `python3 merge_build.py tr_<a>_<b> <outdir> <ar files…>` — builds the pages.
5. `python3 verify.py [--root <ar root>] [--out <outdir>] <pages…>` — **must report 0
   failures before committing.** `--root`/`--out` (or the `AR_ROOT`/`OUT_DIR` env vars)
   default to the device-bridge paths; a Drive-based run must pass them explicitly.
   It checks: Arabic byte-identical to source, `data-i` contiguous, one English line per
   node, no empty translations, no Arabic left inside an English line, footnote refs
   matched to note blocks, correct page numbers/`data-pos`, no Arabic-only chrome.
6. Write each built file to `Library/en/bihar/1/<n>-draft/index.html` — via
   `device_commit_files` when the owner's computer is linked, or via the Google Drive
   path above when it is not.

## Standing constraints

- Never modify anything under `Library/bihar/` (the Arabic) or the existing `en/` pages.
- Never commit a page that fails verification.
- Never touch GitHub. No clone, no commit, no push, no Actions. Committing and pushing
  the repository is the owner's job alone. Write only into the library folder.
- The machine-translation badge stays on every generated page. These pages are not
  scholar-reviewed; the reader is told to cite the Arabic.
- Renaming `-draft` folders into place is the owner's decision, not the task's.

## Known follow-up (not yet done)

`rel=prev/next` and the pager's first/last are stale across the whole `en/` tree:
page 48 still points to 81, and every existing page's "last" points to 84. Once the
drafts are renamed into place, a single sweep should rewire all 231 pages.
