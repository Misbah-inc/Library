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
      if (s) opt(sSura, i, num(i) + '. ' + s[0], i === keptSura);
    });
    fillAya(keptSura, keptAya);

    D.juz.forEach(function (j, i) {
      if (!j) return;
      var nm = D.suras[j[0]] ? D.suras[j[0]][0] : '';
      opt(sJuz, i, num(i) + ' — ' + nm + ' ' + num(j[1]), false);
    });
    D.pages.forEach(function (p, i) {
      if (!p) return;
      var nm = D.suras[p[0]] ? D.suras[p[0]][0] : '';
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
      }, 0);
    });
  });
})();
