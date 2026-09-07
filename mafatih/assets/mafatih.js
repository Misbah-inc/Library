/* مفاتیح الجنان — the book's own behaviour.
 *
 * Kept out of assets/reader.js deliberately. reader.js is loaded by every one
 * of the ~3,750 pages in the library, so anything added there has to be right
 * for all of them; this is right for one book. Same arrangement as the
 * Qur'an's qnav.js.
 *
 * Two jobs: the Arabic/Persian switch, and search.
 *
 * SEARCH is the part that matters. Nobody opens Mafatih knowing the section
 * number; they know a name they half-remember, or a line they have heard
 * recited. Those are different searches and they are answered differently:
 *
 *   NAMES  689 rows, ~20 KB gzipped, fetched the moment search opens and
 *          answered on every keystroke. Ranked by weighted token overlap, not
 *          by substring, because «دعای خمس عشر» has to find «مناجات خمس
 *          عشره» — no substring of the query appears in that title, but two
 *          of its three words do, and «خمس» and «عشره» are rare while «دعای»
 *          is not. Weighting by rarity is what makes that work.
 *
 *   TEXT   5,750 rows, ~1.3 MB gzipped, fetched ONLY when the reader asks for
 *          it. Somebody looking up دعای کمیل by name should never pay for the
 *          whole book's text, so it loads on demand and is then kept.
 *
 * A text hit links to the unit it matched — /mafatih/<slug>/#u-<unit id> —
 * and the page scrolls to it and marks it. Landing in the right place is the
 * whole point; landing on the right page and leaving the reader to scan 90
 * units is not much better than not finding it.
 */
(function () {
  'use strict';

  var BASE = (document.documentElement.getAttribute('data-root') || '.') + '/mafatih/assets/';
  var VKEY = 'mafatih:view';
  var MODES = { both: 1, ar: 1, tr: 1 };

  var store = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  };

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  /* ---------------------------------------------------------------- folding */

  var FOLD = { 'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ٱ': 'ا', 'ى': 'ی', 'ي': 'ی',
               'ك': 'ک', 'ة': 'ه', 'ؤ': 'و', 'ئ': 'ی' };
  var DROP = /[ؐ-ًؚ-ْٰۖ-ۭـ‌]/;
  var DIGIT = { '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4', '۵': '5',
                '۶': '6', '۷': '7', '۸': '8', '۹': '9',
                '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4', '٥': '5',
                '٦': '6', '٧': '7', '٨': '8', '٩': '9' };

  /* Returns the folded string AND the index in the ORIGINAL of each folded
     character, so a snippet can be cut from the original text at a position
     found in the folded one. Without the map, highlighting a match means
     showing the reader stripped, unvocalised Arabic. */
  function fold(text) {
    var out = '', map = [], i, c;
    for (i = 0; i < text.length; i++) {
      c = text.charAt(i);
      if (DROP.test(c)) continue;
      c = DIGIT[c] || FOLD[c] || c.toLowerCase();
      out += c; map.push(i);
    }
    return { t: out, m: map };
  }

  function foldPlain(text) { return fold(text).t; }

  function tokens(q) {
    return foldPlain(q).split(/[^؀-ۿ0-9a-z]+/).filter(function (w) {
      return w.length > 1;
    });
  }

  /* ------------------------------------------------------------------ data */

  var names = null, body = null, nameIdf = null;
  var busy = {};

  function load(file, cb) {
    if (busy[file]) return;
    busy[file] = 1;
    fetch(BASE + file)
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (d) { busy[file] = 0; cb(d); })
      .catch(function () { busy[file] = 0; cb(null); });
  }

  function idfOf(rows, get) {
    /* How rare is a word across the 689 titles? «دعای» is in scores of them
       and tells us almost nothing; «کمیل» is in one and tells us everything. */
    var df = {}, i, ws, j, seen;
    for (i = 0; i < rows.length; i++) {
      ws = get(rows[i]).split(' '); seen = {};
      for (j = 0; j < ws.length; j++) {
        if (ws[j] && !seen[ws[j]]) { seen[ws[j]] = 1; df[ws[j]] = (df[ws[j]] || 0) + 1; }
      }
    }
    return function (w) {
      return Math.log(1 + rows.length / (1 + (df[w] || 0)));
    };
  }

  /* --------------------------------------------------------------- scoring */

  function scoreName(row, qf, qt) {
    var f = row.f, b = row.bf || '', h = row.h || '', s = 0, i, w, idf;
    if (!f) return 0;
    if (f === qf) s += 1000;                       /* the exact name */
    else if (f.indexOf(qf) === 0) s += 400;        /* starts with it */
    else if (qf.length > 2 && f.indexOf(qf) !== -1) s += 260;

    for (i = 0; i < qt.length; i++) {
      w = qt[i]; idf = nameIdf(w);
      if ((' ' + f + ' ').indexOf(' ' + w + ' ') !== -1) s += 60 * idf;
      /* A word that merely STARTS with the token counts almost as much as a
         whole-word match, because Persian glues the ezafe straight onto the
         noun: the ziyarat everyone means is titled «زیارت عاشورای معروفه», and
         treating عاشورای as a weak match for عاشورا ranked three short notes
         *about* the ziyarat above the ziyarat itself. Same for Arabic plurals
         and the attached article. */
      else if ((' ' + f).indexOf(' ' + w) !== -1) s += 55 * idf;
      else if (f.indexOf(w) !== -1) s += 28 * idf;   /* عشر inside مناجات خمس عشره */
      else if (h.indexOf(w) !== -1) s += 26 * idf;   /* in the opening line */
      else if (b.indexOf(w) !== -1) s += 8 * idf;    /* only in the path */
    }
    /* the opening line naming a piece its title does not name */
    if (h && qf.length > 3 && h.indexOf(qf) !== -1) s += 150;
    /* «غیر معروفه» is the variant, «معروفه» is the one people mean. A negation
       the reader did not ask for is evidence this is the alternative reading,
       not the canonical one. */
    if (/(^|\s)غیر(\s|$)/.test(f) && qt.indexOf('غیر') === -1) s -= 170;
    /* every query word accounted for somewhere — the strongest single signal */
    var all = qt.every(function (w) {
      return f.indexOf(w) !== -1 || b.indexOf(w) !== -1 || h.indexOf(w) !== -1;
    });
    if (all && qt.length) s += 120;
    /* Three things a title cannot say for itself. «خبر صفوان در فضیلت زیارت
       عاشورا» and «متن زیارت عاشورای معروفه» score identically on words, but
       one is a short note and the other is the ziyarat. A section with no text
       must never outrank the text it is talking about. */
    if (s) {
      s += Math.min(90, 16 * Math.log(1 + (row.n || 0) * 3 + (row.x || 0)));
      if (!row.n && !row.x && row.c) s += 14;   /* a heading worth opening */
    }
    return s;
  }

  function searchNames(q, limit) {
    var qf = foldPlain(q), qt = tokens(q), out = [], i, sc;
    if (!qf) return out;
    if (!nameIdf) nameIdf = idfOf(names, function (r) { return r.f; });
    for (i = 0; i < names.length; i++) {
      if (names[i].bf === undefined) names[i].bf = foldPlain(names[i].b || '');
      sc = scoreName(names[i], qf, qt);
      if (sc > 0) out.push({ row: names[i], s: sc });
    }
    out.sort(function (a, b) { return b.s - a.s; });
    return out.slice(0, limit || 25);
  }

  function searchBody(q, limit) {
    var qf = foldPlain(q), qt = tokens(q), out = [], i, r, hit;
    if (qf.length < 2) return out;
    for (i = 0; i < body.length; i++) {
      r = body[i];
      if (!r._a) { r._a = fold(r[2] || ''); r._f = fold(r[3] || ''); }
      hit = probe(r._a, r[2], qf, qt) || probe(r._f, r[3], qf, qt);
      if (hit) { hit.row = r; out.push(hit); }
    }
    out.sort(function (a, b) { return b.s - a.s; });
    return out.slice(0, limit || 40);
  }

  function probe(folded, original, qf, qt) {
    var at = folded.t.indexOf(qf), s, i, n = 0;
    if (at !== -1) {
      return { s: 500 + Math.max(0, 40 - at) * 0.1, at: at, len: qf.length,
               folded: folded, original: original };
    }
    /* no exact phrase: every word present, somewhere */
    for (i = 0; i < qt.length; i++) if (folded.t.indexOf(qt[i]) !== -1) n++;
    if (!qt.length || n < qt.length) return null;
    at = folded.t.indexOf(qt[0]);
    s = 120 + n * 10;
    return { s: s, at: at, len: qt[0].length, folded: folded, original: original };
  }

  function snippet(hit) {
    var m = hit.folded.m, a = Math.max(0, hit.at - 45),
        b = Math.min(hit.folded.t.length, hit.at + hit.len + 55);
    var o0 = m[a] == null ? 0 : m[a];
    var o1 = m[b] == null ? hit.original.length : m[b];
    var s0 = m[hit.at] == null ? o0 : m[hit.at];
    var s1 = m[hit.at + hit.len] == null ? o1 : m[hit.at + hit.len];
    return (a > 0 ? '…' : '') + esc(hit.original.slice(o0, s0)) +
      '<mark>' + esc(hit.original.slice(s0, s1)) + '</mark>' +
      esc(hit.original.slice(s1, o1)) + (b < hit.folded.t.length ? '…' : '');
  }

  /* -------------------------------------------------------------------- UI */

  var panel, input, results, note, lastQ = '', bodyAsked = false;

  function build() {
    panel = document.createElement('div');
    panel.className = 'msearch-panel';
    panel.hidden = true;
    panel.innerHTML =
      '<div class="msearch-box" role="dialog" aria-modal="true">' +
      '<div class="msearch-head">' +
      '<input id="msearch-q" type="search" autocomplete="off" spellcheck="false" ' +
      'placeholder="نام دعا، زیارت یا بخشی از متن…" aria-label="جستجو">' +
      '<button class="msearch-x" id="msearch-x" aria-label="بستن">✕</button></div>' +
      '<p class="msearch-note" id="msearch-note"></p>' +
      '<div class="msearch-res" id="msearch-res"></div></div>';
    document.body.appendChild(panel);
    input = panel.querySelector('#msearch-q');
    results = panel.querySelector('#msearch-res');
    note = panel.querySelector('#msearch-note');

    panel.addEventListener('click', function (e) {
      if (e.target === panel) close();
    });
    panel.querySelector('#msearch-x').addEventListener('click', close);
    input.addEventListener('input', debounce(run, 120));
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') close();
      if (e.key === 'Enter') { bodyAsked = true; run(); }
    });
  }

  function debounce(fn, ms) {
    var t;
    return function () { clearTimeout(t); t = setTimeout(fn, ms); };
  }

  function open(seed) {
    if (!panel) build();
    panel.hidden = false;
    document.documentElement.style.overflow = 'hidden';
    if (seed) input.value = seed;
    input.focus();
    input.select();
    if (!names) {
      note.textContent = 'در حال آماده‌سازی…';
      load('search-titles.json', function (d) {
        names = d || [];
        run();
      });
    } else { run(); }
  }

  function close() {
    if (panel) panel.hidden = true;
    document.documentElement.style.overflow = '';
  }

  function href(slug, unit) {
    var root = document.documentElement.getAttribute('data-root') || '.';
    return root + '/mafatih/' + slug + '/' + (unit ? '#u-' + unit : '');
  }

  function run() {
    if (!names) return;
    var q = input.value.trim();
    if (q !== lastQ) { bodyAsked = bodyAsked && q.indexOf(lastQ) === 0; }
    lastQ = q;
    if (q.length < 2) {
      results.innerHTML = '';
      note.textContent = 'نام دعا یا بخشی از متن را بنویسید.';
      return;
    }

    var nm = searchNames(q, 25), html = '';
    if (nm.length) {
      html += '<h3 class="msearch-h">بخش‌ها <span>' + nm.length + '</span></h3><div class="msearch-names">';
      html += nm.map(function (h) {
        var r = h.row;
        return '<a class="mhit" href="' + esc(href(r.s)) + '">' +
          '<span class="mhit-t">' + esc(r.t) + '</span>' +
          (r.hd && r.t.length < 14 ? '<span class="mhit-b">' + esc(r.hd) + '…</span>'
             : (r.b ? '<span class="mhit-b">' + esc(r.b) + '</span>' : '')) +
          (r.p ? '<span class="mhit-p">ص ' + r.p + '</span>' : '') + '</a>';
      }).join('') + '</div>';
    }

    if (body) {
      var bd = searchBody(q, 40);
      if (bd.length) {
        html += '<h3 class="msearch-h">در متن <span>' + bd.length + '</span></h3><div class="msearch-text">';
        html += bd.map(function (h) {
          var r = h.row, nmRow = byslug(r[0]);
          return '<a class="mhit mhit-x" href="' + esc(href(r[0], r[1])) + '">' +
            '<span class="mhit-b">' + esc(nmRow ? nmRow.t : r[0]) +
            (r[4] ? ' · ص ' + r[4] : '') + '</span>' +
            '<span class="mhit-s">' + snippet(h) + '</span></a>';
        }).join('') + '</div>';
      } else if (!nm.length) {
        html += '<p class="msearch-note">چیزی یافت نشد.</p>';
      }
      note.textContent = '';
    } else {
      note.innerHTML = '<button class="msearch-more" id="msearch-more">جستجو در متن کامل کتاب</button>' +
        '<span class="msearch-hint">۱٫۳ مگابایت، یک‌بار بارگیری می‌شود</span>';
    }
    results.innerHTML = html;

    var more = document.getElementById('msearch-more');
    if (more) more.addEventListener('click', loadBody);
    if (bodyAsked && !body) loadBody();
  }

  function loadBody() {
    if (body) return;
    note.textContent = 'در حال بارگیری متن کتاب…';
    load('search-body.json', function (d) {
      body = d || [];
      run();
    });
  }

  var slugMap = null;
  function byslug(s) {
    if (!slugMap) {
      slugMap = {};
      for (var i = 0; i < names.length; i++) slugMap[names[i].s] = names[i];
    }
    return slugMap[s];
  }

  /* ------------------------------------------------ اعمال ایام هفته -------
   *
   * The weekday is the one part of the calendar that is not in dispute. A
   * Hijri DATE has to be announced and can move by a day, which is why اعمال
   * امروز is not built; but Friday is Friday in every reckoning, so the weekly
   * observances can be surfaced safely.
   *
   * One thing must not be got wrong: the Islamic day begins at MAGHRIB. So
   * «اعمال شب جُمعه» is Thursday evening — it belongs to Friday but is kept on
   * Thursday, a day earlier than its name. Those rows are flagged at build
   * time and shown as امشب rather than folded into Friday's list, where a
   * reader would find them a day too late.
   */

  var DAY_FA = ['یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه',
                'پنجشنبه', 'جمعه', 'شنبه'];

  function today() { return new Date().getDay(); }

  function paintWeekBadges() {
    var d = today(), tm = (d + 1) % 7, i, li, wd, eve;
    var rows = document.querySelectorAll('.sec-list li[data-weekday]');
    for (i = 0; i < rows.length; i++) {
      li = rows[i];
      wd = parseInt(li.getAttribute('data-weekday'), 10);
      eve = li.hasAttribute('data-eve');
      if (eve && wd === tm) tag(li, 'امشب');
      else if (!eve && wd === d) tag(li, 'امروز');
    }
  }

  function tag(li, label) {
    if (li.querySelector('.today-b')) return;
    var a = li.querySelector('a');
    if (!a) return;
    var b = document.createElement('span');
    b.className = 'today-b';
    b.textContent = label;
    a.insertBefore(b, a.firstChild);
    li.classList.add('is-today');
  }

  function renderWeek() {
    var host = document.getElementById('mweek');
    if (!host) return;
    load('weekday.json', function (rows) {
      if (!rows || !rows.length) return;
      var d = today(), tm = (d + 1) % 7;
      var now = rows.filter(function (r) { return !r.e && r.d === d; });
      var eve = rows.filter(function (r) { return r.e && r.d === tm; });
      if (!now.length && !eve.length) return;

      function list(items, label) {
        if (!items.length) return '';
        return '<div class="mweek-grp"><h3>' + label + '</h3>' +
          items.map(function (r) {
            return '<a class="mweek-i" href="' + esc(r.s) + '/">' +
              '<span>' + esc(r.t) + '</span>' +
              '<span class="mweek-n">' + r.n + ' بند</span></a>';
          }).join('') + '</div>';
      }

      host.innerHTML =
        '<h2 class="sec-h">اعمال ایام هفته</h2>' +
        '<p class="mweek-day">امروز <b>' + DAY_FA[d] + '</b> است.</p>' +
        list(now, 'امروز') +
        list(eve, 'امشب — شب ' + DAY_FA[tm]) +
        (eve.length ? '<p class="mweek-note">شب در تقویم اسلامی از مغرب آغاز '
          + 'می‌شود، پس «شب ' + DAY_FA[tm] + '» از غروب امروز است.</p>' : '');
      host.hidden = false;
    });
  }

  /* ------------------------------------------------- landing on a text hit */

  function aim(el) {
    /* behavior:'instant' is not a nicety — reader.css sets
       html{scroll-behavior:smooth} for the whole site, and scrollIntoView
       inherits it. The animation is then still running when the Arabic and
       Persian faces finish loading and reflow the page by thousands of
       pixels, at which point the browser abandons it and the reader is left
       at the top of a duʿā they searched into the middle of. */
    try { el.scrollIntoView({ block: 'center', behavior: 'instant' }); }
    catch (e) { el.scrollIntoView(); }
  }

  function markTarget() {
    if (location.hash.indexOf('#u-') !== 0) return;
    var id = decodeURIComponent(location.hash.slice(1));
    var el = document.getElementById(id);
    if (!el) return;
    var prev = document.querySelector('.u-target');
    if (prev && prev !== el) prev.classList.remove('u-target');
    el.classList.add('u-target');

    /* Aim more than once, and never smoothly.
     *
     * Amiri and Vazirmatn load AFTER this runs, and when they land the page
     * reflows by thousands of pixels — a duʿā is long. A single scroll fired
     * at DOMContentLoaded is therefore aimed at a layout that no longer
     * exists by the time the reader sees it, which is why a search result
     * appeared to open the right page at the wrong place. A smooth scroll
     * makes it worse: it is still animating when the reflow happens, and the
     * browser abandons it. */
    aim(el);
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(function () { aim(el); });
    }
    window.addEventListener('load', function () { aim(el); });
    setTimeout(function () { aim(el); }, 700);
  }

  /* Clicking a result for a unit on the page you are already reading is a
     same-document navigation: nothing reloads, so nothing would re-aim. */
  window.addEventListener('hashchange', markTarget);

  /* -------------------------------------------------------- view switching */

  function chosen() {
    var v = store.get(VKEY);
    return MODES[v] ? v : 'both';
  }

  function applyView(mode) {
    var b = document.querySelector('.body.mafatih');
    if (b) {
      b.classList.remove('view-ar', 'view-tr', 'view-both');
      b.classList.add('view-' + mode);
    }
    var btns = document.querySelectorAll('.view-bar .vbtn');
    for (var i = 0; i < btns.length; i++) {
      btns[i].setAttribute('aria-pressed',
        String(btns[i].getAttribute('data-view') === mode));
    }
  }

  function wire() {
    applyView(chosen());
    var bar = document.querySelector('.view-bar');
    if (bar) bar.addEventListener('click', function (e) {
      var b = e.target.closest ? e.target.closest('.vbtn') : null;
      if (!b) return;
      var mode = b.getAttribute('data-view');
      if (!MODES[mode]) return;
      store.set(VKEY, mode);
      applyView(mode);
    });

    var btn = document.getElementById('btn-msearch');
    if (btn) btn.addEventListener('click', function () { open(''); });

    var cover = document.getElementById('mcover-q');
    if (cover) {
      cover.addEventListener('focus', function () { open(cover.value); });
      cover.addEventListener('click', function () { open(cover.value); });
    }
    var coverBtn = document.getElementById('mcover-go');
    if (coverBtn) coverBtn.addEventListener('click', function () { open(cover ? cover.value : ''); });

    document.addEventListener('keydown', function (e) {
      if (e.key === '/' && !/^(INPUT|TEXTAREA)$/.test(document.activeElement.tagName)) {
        e.preventDefault(); open('');
      }
    });

    paintWeekBadges();
    renderWeek();
    markTarget();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', wire);
  } else {
    wire();
  }
})();
