# Changelog

Changes to the Misbah Library website. One entry per session, most recent first.

---

## 2026-09-01 (session 5)

The session-4 commit `70d5b7f` was reverted by `1631306` — it shipped a broken book
and a ~950-file asset-version rewrite the owner had not agreed to. This entry is the
clean redo. Nothing outside the files listed here was touched.

### `reader.js` — the bug that broke Bayt al-Ahzan
- `applyLang()` rewrites `.suras a[data-n]` to `/<lang>/quran/<n>/`, path hardcoded.
  Session 4 reused `.suras` for the Bayt al-Ahzan chapter grid, so chapters 1–2 opened
  Qur'an surahs and 3–19 gave 404.
- Added a separate `.chaps[data-langpath]` handler that reads the book's slug from
  `data-langpath` and the languages that actually have pages from `data-langs`. The
  `.suras` block is byte-for-byte unchanged, so the Qur'an cannot regress.
- Added the seven missing i18n keys in all four languages: `chapter`, `chapters`,
  `pickChapter`, `translator`, `foreword`, `author`, `viewSrc`. `viewSrc` reads
  "Original" / متن اصلی, not "Arabic" — the source-view button lies on any book whose
  source of record is not Arabic.

### `reader.css`
- `.chaps` / `.chap-cell` added to the existing `.suras` / `.sura-cell` selector lists.
  Selector widening only; no existing rule changed.
- New `.book-credit`. The credit line must not ride on `.cite`, which is
  `display:none` on `en`/`fa`/`ur` by the owner's request — session 4 put the
  Ghaemiyeh and translator attribution on a class that hides it on the only pages
  where it appears.

### New book — Bayt al-Ahzan (بيت الأحزان), under عقائد
- `_translation-kit/bayt_extract.py` — Ghaemiyeh HTML export → batch JSON. Handles the
  export's uppercase `<H3>`; without normalising, all 172 headings render as `<p>`.
- `_translation-kit/bayt_paginate.py` — **printed pagination.** The export carries 228
  standalone `[ صفحه ۷۷ ]` markers. Whether a marker opens or closes its page was
  checked against the scanned Naser edition (PDF page = printed + 3): printed 76 ends
  "…از بیم آنکه شما به آن، دست نیابید." and printed 77 opens "حضرت علی (ع) بیل را به
  زمین گذارد…", which is exactly where the marker falls. The marker **opens** the page.
- Every chapter 2–17 ends *on* a marker, so a printed page routinely spans a chapter
  boundary (page 31 starts in chapter 6 and finishes in chapter 7). The book is
  therefore flattened into one block stream before splitting; paginating chapter by
  chapter would invent a page break at every chapter start.
- `_translation-kit/bayt_build.py` — page builder, cover, and `toc.json`.
- `bayt-al-ahzan/index.html` (cover: chapter grid, colophon), `bayt-al-ahzan/assets/toc.json`,
  and `fa/bayt-al-ahzan/3…262/` — **229 printed pages**, the complete Persian text.
- **Printed numbers are kept, holes and all.** 31 numbers have no page (5, 13, 14,
  28–30, 55, …). Each was checked in the scan: every one is a part-title page
  (بخش اوّل / بخش دوّم …) or a blank facing it. No text is missing. `/fa/bayt-al-ahzan/77/`
  is genuinely printed page 77, so a citation matches the paper book, and prev/next
  step through the *ordered* page list rather than n±1 — a reader never lands on a hole.
- **98 endnotes distributed to the pages that cite them.** Chapter 19 (پاورقی) was a
  lump of numbered notes; every `[n]` in the body has exactly one match. Each note now
  sits under the page carrying its citation, with `[۶۶]` a link down to it — the same
  `.fnref` / `.notes` markup Bihar uses. 98 of 98 placed, no orphans.
- Chapter 1 (مشخصات کتاب) folds into the cover as the colophon, per the owner.
- `catalog.json`: entry under `aqaid`, 17 chapters / 229 pages, `srclang: "fa"`, no
  `translated` array — `bookCard()` therefore links every language to the neutral
  cover, which routes to `/fa/` itself.
- **The Persian sits in `/fa/`, not the root.** This book's source of record is Persian
  (Ishtihardi's rendering); Qummi's Arabic original is not yet sourced. Leaving
  `/bayt-al-ahzan/<n>/` empty means the Arabic can drop in later as source of record
  with no migration and no broken URLs.
- Credit line names author, translator (اشتهاردی), foreword (مکارم شیرازی) and قائمیه
  as source. Ghaemiyeh distributes freely; there is no explicit third-party
  redistribution licence, so attribution is what makes relying on that defensible.

### Verification
- 230 pages, 2,475 blocks, 98 footnotes. Every `href`/`src` resolved against the tree;
  `applyLang()` simulated for all four languages honouring `data-root`; prev/next
  confirmed to form one unbroken chain over the ordered page list, so every gap is
  hopped; jump-form and `toc.json` targets resolved; every emitted block diffed against
  its source; every `[n]` link confirmed to anchor a note present on the same page; all
  98 notes present exactly once across the book; 23 `data-i18n` keys checked against all
  four language tables; canonical, self-referential hreflang, `x-default` and meta
  description on all 229 pages. 0 failures.

### Sitemap
- Regenerated: **1,173 URLs** (was 943), adding the cover and 229 Persian pages.

### `CLAUDE.md`
- Script table was missing five of the eleven scripts; added.
- "Current state" omitted the Qur'an and the volume-selector pages; added.
- Replaced the note recommending the Qur'an `.suras` block "as the reference when
  extending for new book types" — following it is what caused the bug — with the four
  invariants that actually bite (`.suras`, `data-book`, `data-tpl`, `.cite`).
- Recorded that `Set-AssetVersion.ps1` is not routine: try a hard refresh first, and a
  sitewide stamp needs the owner's agreement.
- Added an "Adding a whole new book" checklist.

### Still open
- `bookCard()` gates language-prefixed hrefs on `volumesPublished`, using it as a proxy
  for "this book has per-language index pages". Those are different facts. An explicit
  field such as `langIndex: true` would be sturdier. Not changed here — it touches the
  Bihar and Qur'an cards, which are working.

---

## 2026-08-31 (session 3)

### Bug fix — Quran broken for non-Arabic languages
- `assets/reader.js` `bookCard()`: previous fix applied lang prefix to all translated books including Quran, sending users to `en/quran/` which has no index.html. Restored `volumesPublished` check as the gate — only books with volume-based index pages get the lang prefix. Quran continues linking to `quran/` for all languages (applyLang handles surah link rewriting there).

---

## 2026-08-31 (session 2)

### SEO / infrastructure
- Set up Google Search Console for `library.misbah-inc.com`
- Regenerated `sitemap.xml` — now 943 URLs (was 931, added en/fa/ur book index pages)
- Added "Page addition checklist" to `CLAUDE.md` as a standing rule
- Added `CHANGELOG.md` as a permanent session log

---

## 2026-08-31 (session 1)

### Bug fix — language routing on book cards
- `assets/reader.js` `bookCard()`: non-Arabic language selection was always generating Arabic URLs. Fixed by adding language-aware href: `lang + '/' + b.href` when `b.translated` includes the active language.

### Bug fix — volume selector bypassed for non-Arabic languages
- `assets/reader.js` `bookCard()`: previous fix hardcoded `volumesPublished[0] + '/1/'`, skipping the volume selector entirely. Simplified to `lang + '/' + b.href` so it links to the language book index page instead.
- `assets/reader.js` `applyLang()`: added `.vols a.vol` rewriting so volume links on book index pages resolve to the correct language URL (`ROOT/lang/slug/vol/1/`). Volume number cached in `data-vol` on first call.
- Created `en/bihar/index.html` — English volume selector page for Bihar al-Anwar.
- Created `fa/bihar/index.html` — Farsi volume selector page for Bihar al-Anwar.
- Created `ur/bihar/index.html` — Urdu volume selector page for Bihar al-Anwar.
- All three pages include full hreflang cluster + canonical, `data-sitelang`, and correct relative paths (`data-root="../.."`, `data-book="../../bihar"`).
