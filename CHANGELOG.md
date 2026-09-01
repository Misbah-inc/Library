# Changelog

Changes to the Misbah Library website. One entry per session, most recent first.

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
