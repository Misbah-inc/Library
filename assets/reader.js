/* Every page of this site is readable with JavaScript disabled: the text, the
   footnotes and the prev/next links are all in the HTML. This file adds the
   conveniences on top. */
(function () {
  "use strict";
  var ROOT = document.documentElement.getAttribute('data-root') || '.';
  var BOOK = document.documentElement.getAttribute('data-book') || ROOT;
  var AR_D = '٠١٢٣٤٥٦٧٨٩';
  function toAr(n) { return String(n).replace(/\d/g, function (d) { return AR_D[+d]; }); }
  function toEn(s) {
    return String(s).replace(/[٠-٩۰-۹]/g, function (c) {
      var a = '٠١٢٣٤٥٦٧٨٩'.indexOf(c);
      return String(a >= 0 ? a : '۰۱۲۳۴۵۶۷۸۹'.indexOf(c));
    });
  }
  function esc(s) {
    return s.replace(/[&<>]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c];
    });
  }

  /* ---- preferences ---------------------------------------------------- */
  var store = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  };
  var size = parseFloat(store.get('size') || '1.24');
  function applySize() {
    document.documentElement.style.setProperty('--body-size', size + 'rem');
  }
  function bumpSize(d) {
    size = Math.max(0.95, Math.min(1.75, size + d));
    store.set('size', size); applySize();
  }
  function applyTheme(night) {
    document.documentElement.setAttribute('data-theme', night ? 'night' : '');
    var b = document.getElementById('btn-theme');
    if (b) { b.setAttribute('aria-pressed', String(night)); b.textContent = night ? 'نهاري' : 'ليلي'; }
  }
  applySize();
  applyTheme(store.get('theme') === 'night');
  on('btn-theme', 'click', function () {
    var night = document.documentElement.getAttribute('data-theme') !== 'night';
    store.set('theme', night ? 'night' : 'day'); applyTheme(night);
  });
  on('btn-bigger', 'click', function () { bumpSize(0.06); });
  on('btn-smaller', 'click', function () { bumpSize(-0.06); });

  function on(id, ev, fn) {
    var el = document.getElementById(id);
    if (el) el.addEventListener(ev, fn);
  }

  /* ---- Arabic / Persian folding, with a map back to original offsets --- */
  var FOLD = { 'أ':'ا','إ':'ا','آ':'ا','ٱ':'ا','ى':'ی','ي':'ی','ك':'ک','ة':'ه','ؤ':'و','ئ':'ی' };
  var DROP = /[\u0610-\u061A\u064B-\u0652\u0670\u06D6-\u06ED\u0640]/;
  function fold(text) {
    var out = '', map = [];
    for (var i = 0; i < text.length; i++) {
      var c = text.charAt(i);
      if (DROP.test(c)) continue;
      out += (FOLD[c] || c.toLowerCase()); map.push(i);
    }
    return { text: out, map: map };
  }
  function marked(text, q) {
    var f = fold(text), out = '', cursor = 0, pos = 0;
    while ((pos = f.text.indexOf(q, pos)) !== -1) {
      var s = f.map[pos], e = f.map[pos + q.length - 1] + 1;
      if (s < cursor) { pos += q.length; continue; }
      out += esc(text.slice(cursor, s)) + '<mark>' + esc(text.slice(s, e)) + '</mark>';
      cursor = e; pos += q.length;
    }
    return out ? out + esc(text.slice(cursor)) : null;
  }

  /* ---- highlight ?q= on arrival, so search results land pre-marked ---- */
  var Q = (function () {
    var m = location.search.match(/[?&]q=([^&]*)/);
    if (!m) return '';
    try { return fold(decodeURIComponent(m[1].replace(/\+/g, ' '))).text.trim(); }
    catch (e) { return ''; }
  })();
  if (Q.length > 1) {
    var scope = document.querySelectorAll('.body p, .body h3, .note span:last-child');
    Array.prototype.forEach.call(scope, function (el) {
      if (el.querySelector('mark')) return;
      var html = marked(el.textContent, Q);
      if (html) el.innerHTML = html;
    });
    var first = document.querySelector('mark');
    if (first) first.scrollIntoView({ block: 'center' });
  }

  /* ---- drawer -------------------------------------------------------- */
  var drawer = document.getElementById('drawer');
  var scrim = document.getElementById('scrim');
  function closeDrawer() {
    if (!drawer) return;
    drawer.setAttribute('data-open', '0');
    drawer.setAttribute('aria-hidden', 'true');
    if (scrim) scrim.setAttribute('data-open', '0');
  }
  function openDrawer(title) {
    drawer.setAttribute('data-open', '1');
    drawer.setAttribute('aria-hidden', 'false');
    if (scrim) scrim.setAttribute('data-open', '1');
    document.getElementById('drawer-title').textContent = title;
    return document.getElementById('drawer-body');
  }
  on('drawer-close', 'click', closeDrawer);
  if (scrim) scrim.addEventListener('click', closeDrawer);

  var cache = {};
  function load(name) {
    if (cache[name]) return cache[name];
    cache[name] = fetch(BOOK + '/assets/' + name).then(function (r) {
      if (!r.ok) throw new Error(r.status);
      return r.json();
    });
    return cache[name];
  }

  on('btn-toc', 'click', function () {
    var body = openDrawer('الفهرس');
    body.innerHTML = '<p class="note-msg">…</p>';
    load('toc.json').then(function (toc) {
      body.innerHTML = toc.length ? toc.map(function (t) {
        return '<a class="toc-i" href="' + ROOT + '/' + t.href + '">' +
               '<span>' + (t.label || '—') + '</span>' + esc(t.title) + '</a>';
      }).join('') : '<p class="note-msg">لا يوجد فهرس.</p>';
    }).catch(function () {
      body.innerHTML = '<p class="note-msg">تعذّر تحميل الفهرس.</p>';
    });
  });

  function runSearch(body) {
    var raw = document.getElementById('q').value;
    var q = fold(raw).text.trim();
    var box = document.getElementById('hits');
    if (q.length < 2) { box.innerHTML = '<p class="note-msg">اكتب حرفين على الأقل.</p>'; return; }
    box.innerHTML = '<p class="note-msg">…</p>';
    load('search-index.json').then(function (idx) {
      var hits = [];
      for (var i = 0; i < idx.length; i++) {
        var t = idx[i].t, n = 0, at = -1, p = 0;
        while ((p = t.indexOf(q, p)) !== -1) { if (at < 0) at = p; n++; p += q.length; }
        if (n) hits.push({ r: idx[i], n: n, at: at });
        if (hits.length >= 300) break;
      }
      if (!hits.length) { box.innerHTML = '<p class="note-msg">لا نتائج.</p>'; return; }
      box.innerHTML = '<p class="note-msg">' + toAr(hits.length) + ' صفحة تحتوي على «' +
        esc(raw.trim()) + '».</p>' + hits.map(function (h) {
          var s = Math.max(0, h.at - 45);
          var snip = h.r.t.slice(s, Math.min(h.r.t.length, h.at + q.length + 45));
          return '<a class="hit" href="' + ROOT + '/' + h.r.href +
                 '?q=' + encodeURIComponent(raw.trim()) + '">' +
                 '<span class="hit-p">' + esc(h.r.part) + ' · ص ' + h.r.label +
                 ' · ' + toAr(h.n) + ' موضع</span><span class="hit-t">…' +
                 (marked(snip, q) || esc(snip)) + '…</span></a>';
        }).join('');
    }).catch(function () {
      box.innerHTML = '<p class="note-msg">تعذّر تحميل فهرس البحث.</p>';
    });
  }
  on('btn-search', 'click', function () {
    var body = openDrawer('البحث في الكتاب');
    body.innerHTML = '<div class="search-row"><input id="q" placeholder="كلمة أو عبارة…">' +
      '<button class="btn" id="q-go">بحث</button></div><div id="hits">' +
      '<p class="note-msg">يبحث في كل الصفحات المنشورة.</p></div>';
    var q = document.getElementById('q');
    q.value = new URLSearchParams(location.search).get('q') || '';
    q.focus();
    q.addEventListener('keydown', function (e) { if (e.key === 'Enter') runSearch(body); });
    document.getElementById('q-go').addEventListener('click', function () { runSearch(body); });
  });

  /* ---- citation ------------------------------------------------------- */
  on('btn-cite', 'click', function (e) {
    var t = document.getElementById('cite-text');
    if (!t) return;
    var text = t.getAttribute('data-cite') + ' ' + location.href.split('?')[0];
    var btn = e.currentTarget;
    var done = function (ok) {
      btn.textContent = ok ? 'تم النسخ ✓' : 'تعذّر النسخ';
      setTimeout(function () { btn.textContent = 'نسخ الإحالة'; }, 1600);
    };
    if (navigator.clipboard) navigator.clipboard.writeText(text).then(
      function () { done(true); }, function () { done(false); });
    else done(false);
  });

  /* ---- paging -------------------------------------------------------- */
  function href(rel) {
    var l = document.querySelector('link[rel="' + rel + '"]');
    return l && l.getAttribute('href');
  }
  var form = document.getElementById('jump');
  if (form) form.addEventListener('submit', function (e) {
    var n = toEn(document.getElementById('jump-num').value).replace(/\D/g, '');
    var tpl = form.getAttribute('data-tpl');
    if (n && tpl) { e.preventDefault(); location.href = ROOT + '/' + tpl.replace('{p}', n); }
  });
  document.addEventListener('keydown', function (e) {
    var tag = e.target.tagName;
    if (tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA') {
      if (e.key === 'Escape') e.target.blur();
      return;
    }
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.key === 'ArrowLeft' && href('next')) location.href = href('next');
    else if (e.key === 'ArrowRight' && href('prev')) location.href = href('prev');
    else if (e.key === '/') { e.preventDefault(); var b = document.getElementById('btn-search'); if (b) b.click(); }
    else if (e.key === 'Escape') closeDrawer();
  });

  /* ---- keep old hash links alive: #/1/7 -> /1/1/7 --------------------- */
  var legacy = (location.hash || '').match(/^#\/(\d+)\/(\d+)/);
  if (legacy && document.body.getAttribute('data-cover') === '1') {
    location.replace(BOOK + '/' + document.body.getAttribute('data-vol') +
                     '/' + legacy[1] + '/' + legacy[2] + '/');
  }
})();
