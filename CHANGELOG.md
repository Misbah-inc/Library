# Changelog

Changes to the Misbah Library website. One entry per session, most recent first.

---

## 2026-09-01 (session 4)

### New book — Bayt al-Ahzan (بيت الأحزان), under عقائد
- Added `_translation-kit/bayt_extract.py` — parses the Ghaemiyeh HTML export into the kit's batch JSON. Verified 100% text fidelity (292,830 chars in and out) with contiguous block indices.
- Added `_translation-kit/bayt_build.py` — chapter page + cover generator.
- Created `bayt-al-ahzan/index.html` (cover, 19 chapters) and `fa/bayt-al-ahzan/1…19/` — the complete Persian text.
- `catalog.json`: new entry under `aqaid`, `unit: "chapters"`, `translated: ["fa"]`.
- **The Persian sits in `/fa/`, not the root.** This book's source of record is Persian (Ishtihardi's rendering); Qummi's Arabic original is not yet sourced. Leaving `/bayt-al-ahzan/<n>/` empty means the Arabic can drop in later as source of record with no migration and no broken URLs.
- **Do not machine-translate this into Arabic.** The original *is* Arabic; back-translating the Persian would read as Qummi's own words while being two translation layers from them. Source the real Arabic instead.
- Credit line names author, translator (اشتهاردی), foreword (مکارم شیرازی) and قائمیه as source. Ghaemiyeh distributes freely; there is no explicit third-party redistribution licence, so attribution is what makes relying on that defensible.

### `reader.js`
- Added i18n keys in all four languages: `chapter`, `chapters`, `pickChapter`, `translator`, `foreword`, `author`, `viewSrc`.
- `viewSrc` reads "Original" / متن اصلی rather than "Arabic" — the source-view button would otherwise lie on any non-Arabic-source book.

### Sitemap
- Regenerated: **963 URLs** (was 943), adding the cover and 19 Persian chapters.

### Known gap
- `bookCard()` gates language-prefixed hrefs on `volumesPublished`, using it as a proxy for "this book has per-language index pages". Those are different facts. A book with per-language indexes but no volume data (the Qur'an, once it gets them) would fail the test. An explicit field such as `langIndex: true` would be sturdier.

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
