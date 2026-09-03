/* qnav.js — Qur'an surah-page navigation: jump modal + page-by-page view.
   Loaded on every Arabic and translated Qur'an surah page.
   Each page sets window.QNAV = { n: <surah_num>, base: "<path_to_quran/assets/>" }
   before this script runs. */
(function () {
  var cfg = window.QNAV;
  if (!cfg || !cfg.n || !cfg.base) return;
  var N = cfg.n;

  /* ---------- inject modal HTML (static, filled by reader.js i18n) ---------- */
  var wrap = document.createElement('div');
  wrap.innerHTML =
    '<div id="qjump" class="qjump" hidden role="dialog" aria-modal="true">' +
    '<div class="qjump-box">' +
    '<div class="qjump-head">' +
    '<div class="qjump-tabs">' +
    '<button class="qjump-tab" data-tab="sura" aria-selected="true" data-i18n="surah"></button>' +
    '<button class="qjump-tab" data-tab="juz" aria-selected="false" data-i18n="juz"></button>' +
    '<button class="qjump-tab" data-tab="page" aria-selected="false" data-i18n="mushafPage"></button>' +
    '</div>' +
    '<button id="qjump-close" class="qjump-close" data-i18n-label="close">✕</button>' +
    '</div>' +
    '<div class="qjump-pane" data-pane="sura">' +
    '<select id="qj-sura"></select>' +
    '<select id="qj-aya"></select>' +
    '</div>' +
    '<div class="qjump-pane" data-pane="juz" hidden>' +
    '<select id="qj-juz"></select>' +
    '</div>' +
    '<div class="qjump-pane" data-pane="page" hidden>' +
    '<select id="qj-pg"></select>' +
    '</div>' +
    '<button id="qjump-go" class="qjump-go" data-i18n="goVerse"></button>' +
    '</div></div>';
  document.body.appendChild(wrap.firstChild);

  var jmod = document.getElementById('qjump');

  /* ---------- open / close ---------- */
  function openMod() { if (jmod) jmod.hidden = false; }
  function closeMod() { if (jmod) jmod.hidden = true; }

  var openBtn = document.getElementById('btn-qjump');
  if (openBtn) openBtn.addEventListener('click', openMod);

  var closeBtn = document.getElementById('qjump-close');
  if (closeBtn) closeBtn.addEventListener('click', closeMod);

  if (jmod) {
    jmod.addEventListener('click', function (e) { if (e.target === jmod) closeMod(); });
    jmod.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeMod(); });
  }

  /* ---------- fetch shared data then initialise ---------- */
  fetch(cfg.base + 'qnav.json')
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(function (D) { D.n = N; initData(D); })
    .catch(function () {});

  function initData(D) {
    var sSura = document.getElementById('qj-sura');
    var sAya  = document.getElementById('qj-aya');
    var sJuz  = document.getElementById('qj-juz');
    var sPg   = document.getElementById('qj-pg');

    /* surah select */
    if (sSura) {
      D.suras.forEach(function (s, i) {
        if (!s) return;
        var o = document.createElement('option');
        o.value = i;
        o.textContent = i + '. ' + s[0];
        if (i === D.n) o.selected = true;
        sSura.appendChild(o);
      });
    }

    /* verse select */
    function fillAya(sn) {
      if (!sAya) return;
      sAya.innerHTML = '';
      var c = D.suras[sn] ? D.suras[sn][1] : 1;
      for (var a = 1; a <= c; a++) {
        var o = document.createElement('option');
        o.value = a; o.textContent = a;
        sAya.appendChild(o);
      }
    }
    fillAya(D.n);
    if (sSura) sSura.addEventListener('change', function () {
      fillAya(parseInt(sSura.value, 10));
    });

    /* juz select */
    if (sJuz) {
      D.juz.forEach(function (j, i) {
        if (!j) return;
        var o = document.createElement('option');
        o.value = i;
        var nm = D.suras[j[0]] ? D.suras[j[0]][0] : '';
        o.textContent = i + ' — ' + nm + ' · ' + j[1];
        sJuz.appendChild(o);
      });
    }

    /* page select */
    if (sPg) {
      D.pages.forEach(function (p, i) {
        if (!p) return;
        var o = document.createElement('option');
        o.value = i;
        var nm = D.suras[p[0]] ? D.suras[p[0]][0] : '';
        o.textContent = i + ' — ' + nm + ' · ' + p[1];
        sPg.appendChild(o);
      });
    }

    /* tabs */
    function tabSwitch(name) {
      document.querySelectorAll('.qjump-tab').forEach(function (b) {
        b.setAttribute('aria-selected', String(b.getAttribute('data-tab') === name));
      });
      document.querySelectorAll('.qjump-pane').forEach(function (p) {
        p.hidden = p.getAttribute('data-pane') !== name;
      });
    }
    document.querySelectorAll('.qjump-tab').forEach(function (b) {
      b.addEventListener('click', function () { tabSwitch(b.getAttribute('data-tab')); });
    });

    /* navigate */
    function navTo(s, a) {
      closeMod();
      if (s === D.n) { location.hash = '#a' + a; }
      else { location.href = '../' + s + '/#a' + a; }
    }

    var goBtn = document.getElementById('qjump-go');
    if (goBtn) goBtn.addEventListener('click', function () {
      var tab = document.querySelector('.qjump-tab[aria-selected="true"]');
      var pane = tab ? tab.getAttribute('data-tab') : 'sura';
      if (pane === 'sura') {
        navTo(parseInt(sSura ? sSura.value : D.n, 10),
              parseInt(sAya  ? sAya.value  : 1,   10));
      } else if (pane === 'juz') {
        var ji = parseInt(sJuz ? sJuz.value : 1, 10);
        if (D.juz[ji]) navTo(D.juz[ji][0], D.juz[ji][1]);
      } else {
        var pi = parseInt(sPg ? sPg.value : 1, 10);
        if (D.pages[pi]) navTo(D.pages[pi][0], D.pages[pi][1]);
      }
    });

    /* re-apply i18n so modal buttons get their translated labels */
    document.querySelectorAll('#qjump [data-i18n]').forEach(function (el) {
      var k = el.getAttribute('data-i18n');
      /* reader.js exposes T and lang via closure — replicate key lookup inline */
      var langEl = document.documentElement;
      var lg = langEl.getAttribute('data-lang') || 'ar';
      var tables = window._T; /* reader.js sets window._T if present, else fall through */
      if (tables && tables[lg] && tables[lg][k]) el.textContent = tables[lg][k];
      else if (tables && tables.ar && tables.ar[k]) el.textContent = tables.ar[k];
    });

    /* ---------- page-by-page view ---------- */
    var ayas = Array.prototype.slice.call(document.querySelectorAll('.aya[data-page]'));
    if (!ayas.length) return;

    var firstPg = parseInt(ayas[0].getAttribute('data-page'), 10);
    var curPg = firstPg;

    function showPage(pg) {
      ayas.forEach(function (a) {
        a.hidden = parseInt(a.getAttribute('data-page'), 10) !== pg;
      });
      document.querySelectorAll('.page-mrk').forEach(function (m) {
        m.hidden = parseInt(m.getAttribute('data-page'), 10) !== pg;
      });
      var lbl = document.getElementById('pgview-label');
      if (lbl) lbl.textContent = pg;
      curPg = pg;
      var pv = document.getElementById('pgview-prev');
      if (pv) pv.disabled = (pg <= 1);
      var nx = document.getElementById('pgview-next');
      if (nx) nx.disabled = (pg >= 604);
    }

    function allOn() {
      ayas.forEach(function (a) { a.hidden = false; });
      document.querySelectorAll('.page-mrk').forEach(function (m) { m.hidden = false; });
    }

    var pgBtn = document.getElementById('btn-pgview');
    if (pgBtn) {
      pgBtn.addEventListener('click', function () {
        var on = pgBtn.getAttribute('aria-pressed') === 'true';
        pgBtn.setAttribute('aria-pressed', String(!on));
        var nav = document.getElementById('pgview-nav');
        if (nav) nav.hidden = on;
        if (!on) showPage(curPg); else allOn();
      });
    }

    var prevBtn = document.getElementById('pgview-prev');
    if (prevBtn) prevBtn.addEventListener('click', function () {
      var np = curPg - 1; if (np < 1) return;
      var pd = D.pages[np];
      if (pd && pd[0] !== D.n) location.href = '../' + pd[0] + '/#a' + pd[1];
      else showPage(np);
    });

    var nextBtn = document.getElementById('pgview-next');
    if (nextBtn) nextBtn.addEventListener('click', function () {
      var np = curPg + 1; if (np > 604) return;
      var pd = D.pages[np];
      if (pd && pd[0] !== D.n) location.href = '../' + pd[0] + '/#a' + pd[1];
      else showPage(np);
    });
  }
})();
