/* qnav.js — Qur'an quick access and page-by-page reading.
   Runs on the surah pages and on the /quran/ cover.

   The dialog's markup is emitted by quran_build.py into the page itself, not
   built here, so reader.js's applyLang() fills its labels and refills them when
   the reader switches language. This file only wires behaviour.

   The page sets, before this script runs:
     window.QNAV = { n: <surah number, 0 on the cover>,
                     base: "<relative path to quran/assets/>",
                     index: true on the cover }                                 */
(function () {
  var cfg = window.QNAV;
  if (!cfg) return;

  var N        = cfg.n | 0;
  var IS_INDEX = !!cfg.index;
  var LAST_PAGE = 604;

  var store = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  };
  var DIG = { ar: '٠١٢٣٤٥٦٧٨٩', fa: '۰۱۲۳۴۵۶۷۸۹', ur: '۰۱۲۳۴۵۶۷۸۹', en: '0123456789' };
  function lang() { return document.documentElement.getAttribute('data-lang') || 'ar'; }
  function num(v) {
    var d = DIG[lang()] || DIG.ar;
    return String(v).replace(/\d/g, function (c) { return d[+c]; });
  }
  function all(sel) { return Array.prototype.slice.call(document.querySelectorAll(sel)); }
  /* an English reader cannot tell one Arabic surah name from another, so the
     roster carries a transliteration and every list prefers it in English */
  function nameOf(s) { return (lang() === 'en' && s[2]) ? s[2] : s[0]; }

  var jmod = document.getElementById('qjump');

  /* ------------------------- dialog open / close ------------------------- */
  function openMod() { if (jmod) jmod.hidden = false; }
  function closeMod() { if (jmod) jmod.hidden = true; }

  var openBtn = document.getElementById('btn-qjump');
  if (openBtn) openBtn.addEventListener('click', openMod);
  var closeBtn = document.getElementById('qjump-close');
  if (closeBtn) closeBtn.addEventListener('click', closeMod);
  if (jmod) jmod.addEventListener('click', function (e) { if (e.target === jmod) closeMod(); });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && jmod && !jmod.hidden) closeMod();
  });

  /* tabs switch even before the data lands, so the dialog never looks stuck */
  all('.qjump-tab').forEach(function (b) {
    b.addEventListener('click', function () {
      var name = b.getAttribute('data-tab');
      all('.qjump-tab').forEach(function (x) {
        x.setAttribute('aria-selected', String(x.getAttribute('data-tab') === name));
      });
      all('.qjump-pane').forEach(function (p) {
        p.hidden = p.getAttribute('data-pane') !== name;
      });
    });
  });

  /* ------------------- page-by-page: DOM only, no fetch ------------------- */
  var ayas  = all('.aya[data-page]');
  var marks = all('.page-mrk[data-page]');
  var basm  = all('.bismillah[data-page]');
  var pageable = ayas.concat(marks, basm);

  /* the Mushaf pages this surah actually occupies, ascending */
  var myPages = [];
  ayas.forEach(function (a) {
    var p = parseInt(a.getAttribute('data-page'), 10);
    if (p && myPages.indexOf(p) === -1) myPages.push(p);
  });
  myPages.sort(function (x, y) { return x - y; });

  var DATA = null;                 /* qnav.json, once it arrives */
  var pagingOn = false;
  var curPg = myPages.length ? myPages[0] : 1;

  var nav   = document.getElementById('pgview-nav');
  var lbl   = document.getElementById('pgview-label');
  var prevB = document.getElementById('pgview-prev');
  var nextB = document.getElementById('pgview-next');

  /* A neighbouring page is reachable if it is part of this surah, or if the
     data tells us which surah to follow it into. */
  function canStep(pg) {
    if (pg < 1 || pg > LAST_PAGE) return false;
    if (myPages.indexOf(pg) !== -1) return true;
    return !!(DATA && DATA.pages && DATA.pages[pg]);
  }
  function showPage(pg) {
    curPg = pg;
    pageable.forEach(function (el) {
      el.hidden = parseInt(el.getAttribute('data-page'), 10) !== pg;
    });
    if (lbl) lbl.textContent = num(pg);
    if (prevB) prevB.disabled = !canStep(pg - 1);
    if (nextB) nextB.disabled = !canStep(pg + 1);
  }
  function showEverything() {
    pageable.forEach(function (el) { el.hidden = false; });
  }
  function step(pg) {
    if (!canStep(pg)) return;
    if (myPages.indexOf(pg) !== -1) { showPage(pg); return; }
    var t = DATA.pages[pg];        /* page opens in another surah — follow it */
    location.href = '../' + t[0] + '/#a' + t[1];
  }
  function setPaging(mode) {
    pagingOn = (mode === 'page');
    store.set('qpaging', mode);
    all('.pagepick button').forEach(function (b) {
      b.setAttribute('aria-pressed', String(b.getAttribute('data-paging') === mode));
    });
    if (nav) nav.hidden = !pagingOn;
    if (pagingOn) showPage(curPg); else showEverything();
  }

  if (ayas.length && all('.pagepick button').length) {
    all('.pagepick button').forEach(function (b) {
      b.addEventListener('click', function () { setPaging(b.getAttribute('data-paging')); });
    });
    if (prevB) prevB.addEventListener('click', function () { step(curPg - 1); });
    if (nextB) nextB.addEventListener('click', function () { step(curPg + 1); });

    /* arriving on #a<n>, open on the page that verse sits on */
    var h = /^#a(\d+)$/.exec(location.hash || '');
    if (h) {
      var at = document.getElementById('a' + h[1]);
      var ap = at && parseInt(at.getAttribute('data-page'), 10);
      if (ap) curPg = ap;
    }
    setPaging(store.get('qpaging') === 'page' ? 'page' : 'all');
  }

  /* ------------------------- shared navigation data ------------------------- */
  var goWired = false;

  function fillModal(D) {
    var sSura = document.getElementById('qj-sura');
    var sAya  = document.getElementById('qj-aya');
    var sJuz  = document.getElementById('qj-juz');
    var sPg   = document.getElementById('qj-pg');
    if (!sSura || !sAya || !sJuz || !sPg) return;

    function opt(sel, value, text, chosen) {
      var o = document.createElement('option');
      o.value = value; o.textContent = text;
      if (chosen) o.selected = true;
      sel.appendChild(o);
    }
    function fillAya(sn, keep) {
      sAya.innerHTML = '';
      var c = (D.suras[sn] && D.suras[sn][1]) || 1;
      for (var a = 1; a <= c; a++) opt(sAya, a, num(a), a === keep);
    }

    /* rebuilt wholesale, so this is also the language-change refresh */
    var keptSura = parseInt(sSura.value, 10) || N || 1;
    var keptAya  = parseInt(sAya.value, 10) || 1;
    sSura.innerHTML = ''; sJuz.innerHTML = ''; sPg.innerHTML = '';

    D.suras.forEach(function (s, i) {
      if (s) opt(sSura, i, num(i) + '. ' + nameOf(s), i === keptSura);
    });
    fillAya(keptSura, keptAya);

    D.juz.forEach(function (j, i) {
      if (!j) return;
      var nm = D.suras[j[0]] ? nameOf(D.suras[j[0]]) : '';
      opt(sJuz, i, num(i) + ' — ' + nm + ' ' + num(j[1]), false);
    });
    D.pages.forEach(function (p, i) {
      if (!p) return;
      var nm = D.suras[p[0]] ? nameOf(D.suras[p[0]]) : '';
      opt(sPg, i, num(i) + ' — ' + nm + ' ' + num(p[1]), false);
    });

    if (goWired) return;
    goWired = true;

    sSura.addEventListener('change', function () {
      fillAya(parseInt(sSura.value, 10), 1);
    });

    function confirmGo() {
      var tab = document.querySelector('.qjump-tab[aria-selected="true"]');
      var pane = tab ? tab.getAttribute('data-tab') : 'sura';
      if (pane === 'sura') {
        navTo(parseInt(sSura.value, 10), parseInt(sAya.value, 10));
      } else if (pane === 'juz') {
        var j = D.juz[parseInt(sJuz.value, 10)];
        if (j) navTo(j[0], j[1]);
      } else {
        var p = D.pages[parseInt(sPg.value, 10)];
        if (p) navTo(p[0], p[1]);
      }
    }
    var go = document.getElementById('qjump-go');
    if (go) go.addEventListener('click', confirmGo);
    if (jmod) jmod.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') { e.preventDefault(); confirmGo(); }
    });
  }

  function navTo(s, a) {
    closeMod();
    if (IS_INDEX) {
      /* the cover carries no language of its own — follow the reader's choice */
      var lg = lang();
      location.href = (lg === 'ar' ? '' : '../' + lg + '/quran/') + s + '/#a' + a;
      return;
    }
    if (s !== N) { location.href = '../' + s + '/#a' + a; return; }
    var el = document.getElementById('a' + a);
    if (!el) return;
    if (pagingOn) {
      var p = parseInt(el.getAttribute('data-page'), 10);
      if (p) showPage(p);
    }
    location.hash = '#a' + a;
    el.scrollIntoView({ block: 'center' });
  }

  fetch(cfg.base + 'qnav.json')
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(function (D) {
      DATA = D;
      fillModal(D);
      if (pagingOn) showPage(curPg);   /* re-enable steps now the data is here */
    })
    .catch(function () {});

  /* the cover switches language in place, so its numerals need re-rendering */
  all('.langs button').forEach(function (b) {
    b.addEventListener('click', function () {
      setTimeout(function () {
        if (DATA) fillModal(DATA);
        if (pagingOn && lbl) lbl.textContent = num(curPg);
        onLangChange();
      }, 0);
    });
  });

  /* =====================================================================
     Everything below is the reading-and-research layer: which translation is
     shown, the word statistics on the cover, and the verse of the day. It
     shares this file's helpers (lang, num, all, store) and its qnav.json.
     ===================================================================== */

  var QTR   = window.QTR || null;
  var QBASE = cfg.base.replace(/assets\/$/, '');    /* the /quran/ root */
  var TRDIR = cfg.base + 'tr/';

  /* reader.js owns the phrase table; borrow the strings it has already
     rendered rather than keeping a second copy here that would drift. */
  function t(key, fallback) {
    var el = document.querySelector('[data-i18n="' + key + '"]');
    var v = el && el.textContent;
    return v || fallback || key;
  }

  /* --------------------------- translations --------------------------- */

  function roster(lg) {
    if (!QTR) return null;
    if (QTR.byLang) return QTR.byLang[lg] || null;
    return QTR.lang === lg ? QTR : null;
  }
  function chosenTr(lg) {
    var r = roster(lg);
    if (!r) return null;
    var want = store.get('qtr:' + lg);
    for (var i = 0; i < r.list.length; i++) if (r.list[i].id === want) return want;
    return r.def;
  }

  var trPick = document.getElementById('tr-pick');
  var trWho  = document.getElementById('tr-who');
  var trGrp  = document.getElementById('cover-trpick');
  var BUILTIN = null;          /* the translation written into the HTML */
  var trCache = {};            /* id -> fetched [null,[null,'aya',…],…]  */

  function fillTrPick() {
    if (!trPick) return;
    var lg = lang(), r = roster(lg);
    if (trGrp) trGrp.hidden = !r;                 /* Arabic has no translation */
    if (!r) { trPick.innerHTML = ''; return; }
    var cur = chosenTr(lg);
    trPick.innerHTML = '';
    r.list.forEach(function (x) {
      var o = document.createElement('option');
      o.value = x.id; o.textContent = x.name;
      if (x.id === cur) o.selected = true;
      trPick.appendChild(o);
    });
  }

  function trLines() { return all('.body .tr-line[data-tr]'); }

  function paintTr(id, texts) {
    /* texts is indexed by verse number, 1-based; the lines are in verse order */
    var lines = trLines(), r = roster(lang()), disp = '';
    lines.forEach(function (p, i) {
      var v = texts[i + 1];
      if (v == null) return;
      /* keep the <span class="aya-b"> marker; only the text node changes */
      var last = p.lastChild;
      if (last && last.nodeType === 3) last.nodeValue = v;
      else p.appendChild(document.createTextNode(v));
      p.setAttribute('data-tr', id);
    });
    if (r) r.list.forEach(function (x) { if (x.id === id) disp = x.display || x.name; });
    if (trWho && disp) trWho.textContent = disp;
  }

  function applyTr(id) {
    var lines = trLines();
    if (!lines.length) return;                     /* cover, or Arabic page */
    var r = roster(lang());
    if (!r) return;
    if (!BUILTIN) {
      BUILTIN = [null];
      lines.forEach(function (p) {
        var last = p.lastChild;
        BUILTIN.push(last && last.nodeType === 3 ? last.nodeValue : '');
      });
    }
    if (id === r.def) { paintTr(id, BUILTIN); return; }
    if (trCache[id]) { paintTr(id, trCache[id][N] || BUILTIN); return; }
    var bar = document.getElementById('tr-bar');
    if (bar) bar.setAttribute('data-loading', '1');
    fetch(TRDIR + lang() + '.' + id + '.json')
      .then(function (x) { if (!x.ok) throw new Error(x.status); return x.json(); })
      .then(function (d) {
        trCache[id] = d;
        if (chosenTr(lang()) === id) paintTr(id, d[N] || BUILTIN);
      })
      .catch(function () { paintTr(r.def, BUILTIN); })
      .then(function () { if (bar) bar.removeAttribute('data-loading'); });
  }

  if (trPick) {
    fillTrPick();
    trPick.addEventListener('change', function () {
      store.set('qtr:' + lang(), trPick.value);
      applyTr(trPick.value);
      if (IS_INDEX) { renderVotd(); if (lastHits) runSearch(); }
    });
    if (!IS_INDEX) applyTr(chosenTr(lang()));
  }

  /* ------------------------- cover: verse search ------------------------- */

  var FOLD = { 'أ':'ا','إ':'ا','آ':'ا','ٱ':'ا',
               'ى':'ی','ي':'ی','ك':'ک','ة':'ه',
               'ؤ':'و','ئ':'ی' };
  function fold(x) {
    return String(x)
      .replace(/[ؐ-ًؚ-ْٰۖ-ۭـ]/g, '')
      .replace(/[أإآٱىيكةؤئ]/g,
               function (c) { return FOLD[c]; })
      .toLowerCase();
  }
  /* anything that is not a letter is a word break — this covers Arabic
     punctuation, Latin punctuation and the verse separators alike */
  var NONWORD = /[^0-9A-Za-zؠ-ٟٮ-ۿࢠ-ࣿ]+/g;
  function words(x) { return fold(x).split(NONWORD).filter(Boolean); }

  function suraName(i) {
    return (DATA && DATA.suras[i]) ? nameOf(DATA.suras[i]) : '';
  }
  function verseHref(s, v) {
    var l = lang();
    return (l === 'ar' ? '' : '../' + l + '/quran/') + s + '/#a' + v;
  }

  var qi     = document.getElementById('qsearch-q');
  var qres   = document.getElementById('qsearch-res');
  var qstats = document.getElementById('qstats');
  var qadv   = document.getElementById('qadv');
  var qsura  = document.getElementById('qadv-sura');
  var verses = null;                 /* verses.json, Arabic */
  var busy   = {};
  var lastHits = null;
  var shown  = 20;

  /* The advanced-search surah picker is static HTML, so its option labels do
     not follow the language the way the cover grid does. Each option already
     carries both spellings; an English reader who cannot read the script needs
     the transliterated one, which is the whole reason data-tn is emitted. */
  function paintSuraOpts() {
    if (!qsura) return;
    var en = lang() === 'en';
    all('#qadv-sura option[data-nm]').forEach(function (o) {
      var tn = o.getAttribute('data-tn');
      o.textContent = o.value + '. ' + (en && tn ? tn : o.getAttribute('data-nm'));
    });
  }

  function advMode(sel, attr, dflt) {
    var b = document.querySelector(sel + ' button[aria-pressed="true"]');
    return b ? b.getAttribute(attr) : dflt;
  }
  function segWire(sel, attr, after) {
    all(sel + ' button').forEach(function (b) {
      b.addEventListener('click', function () {
        all(sel + ' button').forEach(function (x) {
          x.setAttribute('aria-pressed', String(x === b));
        });
        if (after) after();
      });
    });
  }

  function flatten(d) {
    var rows = [];
    for (var s = 1; s < d.length; s++)
      for (var a = 1; a < d[s].length; a++) rows.push([s, a, d[s][a]]);
    return rows;
  }

  function corpus(cb) {
    /* rows of [surah, aya, text] for whichever corpus the reader selected */
    var where = advMode('.qadv-in', 'data-in', 'ar');
    if (where === 'ar' || lang() === 'ar') {
      if (verses) return cb(verses);
      if (busy.ar) return;
      busy.ar = true;
      fetch(QBASE + 'verses.json').then(function (r) { return r.json(); })
        .then(function (d) { verses = d; busy.ar = false; cb(d); })
        .catch(function () { busy.ar = false; });
      return;
    }
    var lg = lang(), id = chosenTr(lg), key = lg + '.' + id;
    if (trCache[id]) return cb(flatten(trCache[id]));
    if (busy[key]) return;
    busy[key] = true;
    fetch(TRDIR + key + '.json').then(function (r) { return r.json(); })
      .then(function (d) { trCache[id] = d; busy[key] = false; cb(flatten(d)); })
      .catch(function () { busy[key] = false; });
  }

  function tally(rows, q) {
    var whole = advMode('.qadv-match', 'data-match', 'part') === 'whole';
    var only  = qsura ? parseInt(qsura.value, 10) || 0 : 0;
    var nq = fold(q.trim());
    if (!nq) return null;
    var hits = [], total = 0, perSura = {}, suraCount = 0;
    for (var i = 0; i < rows.length; i++) {
      var r = rows[i];
      if (only && r[0] !== only) continue;
      var c = 0;
      if (whole) {
        var w = words(r[2]);
        for (var k = 0; k < w.length; k++) if (w[k] === nq) c++;
      } else {
        var hay = fold(r[2]), at = hay.indexOf(nq);
        while (at !== -1) { c++; at = hay.indexOf(nq, at + nq.length); }
      }
      if (!c) continue;
      total += c;
      hits.push(r);
      if (!perSura[r[0]]) { perSura[r[0]] = 0; suraCount++; }
      perSura[r[0]] += c;
    }
    return { hits: hits, total: total, perSura: perSura, suras: suraCount };
  }

  function renderStats(res) {
    if (!qstats) return;
    if (!res || !res.hits.length) { qstats.hidden = true; return; }
    var top = Object.keys(res.perSura)
      .map(function (k) { return [parseInt(k, 10), res.perSura[k]]; })
      .sort(function (a, b) { return b[1] - a[1]; }).slice(0, 8);
    var max = top.length ? top[0][1] : 1;
    qstats.innerHTML =
      '<div class="qstat-nums">' +
        '<span class="qstat-n"><b>' + num(res.total) + '</b> ' +
          t('occurrences', 'matches') + '</span>' +
        '<span class="qstat-n"><b>' + num(res.hits.length) + '</b> ' +
          (res.hits.length === 1 ? t('verse', 'verse') : t('versesWord', 'verses')) + '</span>' +
        '<span class="qstat-n"><b>' + num(res.suras) + '</b> ' +
          (res.suras === 1 ? t('surah', 'surah') : t('surahs', 'surahs')) + '</span>' +
      '</div>' +
      '<div class="qstat-top"><span class="qstat-cap">' +
        t('topSurahs', 'Most frequent') + '</span><ul>' +
        top.map(function (x) {
          return '<li><a href="' + verseHref(x[0], 1) + '">' +
                 '<span class="qs-nm">' + num(x[0]) + '. ' + suraName(x[0]) + '</span>' +
                 '<span class="qs-bar"><i style="width:' +
                   Math.max(4, Math.round(x[1] / max * 100)) + '%"></i></span>' +
                 '<span class="qs-ct">' + num(x[1]) + '</span></a></li>';
        }).join('') +
      '</ul></div>';
    qstats.hidden = false;
  }

  function renderRes(res) {
    if (!qres) return;
    if (!res || !res.hits.length) {
      qres.innerHTML = '<li class="qsr-none">' + t('noResults', '—') + '</li>';
      qres.hidden = false; return;
    }
    var isAr = advMode('.qadv-in', 'data-in', 'ar') === 'ar' || lang() === 'ar';
    var rows = res.hits.slice(0, shown).map(function (m) {
      return '<li><a href="' + verseHref(m[0], m[1]) + '" data-n="' + m[0] + '">' +
        '<span class="qsr-ref">' + suraName(m[0]) + '  ' + num(m[0]) + ':' + num(m[1]) +
        '</span><span class="qsr-txt"' +
        (isAr ? ' lang="ar" dir="rtl"' : ' dir="' + (lang() === 'en' ? 'ltr' : 'rtl') + '"') +
        '>' + m[2].slice(0, 120) + '</span></a></li>';
    }).join('');
    if (res.hits.length > shown)
      rows += '<li class="qsr-more"><button type="button" id="qsr-more">' +
              t('showAllRes', 'Show all') + ' (' + num(res.hits.length) + ')</button></li>';
    qres.innerHTML = rows;
    qres.hidden = false;
    var more = document.getElementById('qsr-more');
    if (more) more.addEventListener('click', function () {
      shown = res.hits.length; renderRes(res);
    });
  }

  function runSearch() {
    if (!qi) return;
    var q = qi.value;
    var qc = document.getElementById('qsearch-clear');
    if (qc) qc.hidden = !q;
    if (!q.trim()) {
      lastHits = null;
      if (qres) qres.hidden = true;
      if (qstats) qstats.hidden = true;
      return;
    }
    corpus(function (rows) {
      shown = 20;
      lastHits = tally(rows, q);
      renderStats(lastHits);
      renderRes(lastHits);
    });
  }

  if (qi) {
    var qbtn = document.getElementById('qsearch-btn');
    var qclear = document.getElementById('qsearch-clear');
    if (qbtn) qbtn.addEventListener('click', runSearch);
    qi.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') { e.preventDefault(); runSearch(); }
    });
    qi.addEventListener('input', function () { if (qclear) qclear.hidden = !qi.value; });
    if (qclear) qclear.addEventListener('click', function () {
      qi.value = ''; qclear.hidden = true; lastHits = null;
      if (qres) qres.hidden = true;
      if (qstats) qstats.hidden = true;
      qi.focus();
    });
    var qtog = document.getElementById('qadv-toggle');
    if (qtog && qadv) qtog.addEventListener('click', function () {
      qadv.hidden = !qadv.hidden;
      qtog.setAttribute('aria-expanded', String(!qadv.hidden));
    });
    paintSuraOpts();
    segWire('.qadv-in', 'data-in', runSearch);
    segWire('.qadv-match', 'data-match', runSearch);
    if (qsura) qsura.addEventListener('change', runSearch);
  }

  /* --------------------------- verse of the day --------------------------- */

  var VOTD = null;
  var votdX = {};              /* lang.id -> 366 strings for a non-default */
  function dayIndex() {
    var d = new Date();
    var start = new Date(d.getFullYear(), 0, 0);
    return Math.floor((d - start) / 864e5);          /* 1..366 */
  }
  function renderVotd() {
    var box = document.getElementById('votd');
    if (!box || !VOTD || !VOTD.length) return;
    var v = VOTD[(dayIndex() - 1 + VOTD.length) % VOTD.length];
    var lg = lang();
    var arEl = document.getElementById('votd-ar');
    var trEl = document.getElementById('votd-tr');
    var ref  = document.getElementById('votd-ref');
    var go   = document.getElementById('votd-go');
    if (arEl) arEl.textContent = v.ar;
    if (trEl) {
      /* the card must speak in whichever translation the reader chose, not the
         built-in one; votd.json carries only the defaults, so a non-default
         needs its own 366-string file — small, and fetched only if picked */
      var id = chosenTr(lg), r = roster(lg), txt = '';
      if (lg !== 'ar') {
        if (!r || id === r.def) txt = v[lg] || '';
        else {
          var key = lg + '.' + id, i = VOTD.indexOf(v);
          if (votdX[key]) txt = votdX[key][i] || v[lg] || '';
          else {
            txt = v[lg] || '';
            if (!busy['v' + key]) {
              busy['v' + key] = true;
              fetch(cfg.base + 'votd/' + key + '.json')
                .then(function (x) { return x.json(); })
                .then(function (d) { votdX[key] = d; busy['v' + key] = false; renderVotd(); })
                .catch(function () { busy['v' + key] = false; });
            }
          }
        }
      }
      trEl.textContent = txt;
      trEl.hidden = !txt;
      trEl.setAttribute('lang', lg);
      trEl.setAttribute('dir', lg === 'en' ? 'ltr' : 'rtl');
    }
    if (ref) {
      ref.textContent = suraName(v.s) + ' ' + num(v.s) + ':' + num(v.a);
      ref.href = verseHref(v.s, v.a);
    }
    if (go) go.href = verseHref(v.s, v.a);
    box.hidden = false;
  }
  if (IS_INDEX && document.getElementById('votd')) {
    fetch(cfg.base + 'votd.json').then(function (r) { return r.json(); })
      .then(function (d) { VOTD = d; renderVotd(); }).catch(function () {});
  }

  function onLangChange() {
    fillTrPick();
    paintSuraOpts();
    renderVotd();
    if (lastHits) runSearch();
  }
})();
