/* Misbah Library.
   Pages render fully server-side; this file adds interface language, night mode,
   continue-reading, category filtering, search and keyboard paging. */
(function () {
  "use strict";
  var H = document.documentElement;
  var ROOT = H.getAttribute('data-root') || '.';
  var BOOK = H.getAttribute('data-book') || ROOT;

  /* ---------------- storage ---------------- */
  var store = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  };

  /* ---------------- interface languages ---------------- */
  var STRINGS = {
    ar: { home:'الرئيسية', library:'المكتبة', search:'بحث', contents:'الفهرس',
          cite:'نسخ الإحالة', copied:'تم النسخ ✓', night:'ليلي', day:'نهاري',
          bigger:'تكبير الخط', smaller:'تصغير الخط',
          ph:'ابحث في المكتبة…', scopeText:'نصوص الكتب', scopeTitle:'عناوين الكتب',
          scopeAuthor:'المؤلفون', advanced:'بحث متقدم',
          allWords:'كل هذه الكلمات', phrase:'هذه العبارة بالضبط', anyWord:'أي من هذه الكلمات',
          without:'بدون هذه الكلمات', inBook:'في كتاب', inCat:'في قسم', anyBook:'كل الكتب',
          anyCat:'كل الأقسام', run:'ابحث', clear:'مسح',
          continue:'متابعة القراءة', continueNone:'ستظهر هنا الكتب التي بدأت قراءتها.',
          categories:'الأقسام', books:'كتاب', page:'صفحة', volume:'المجلد',
          results:'النتائج', noResults:'لا نتائج.', minChars:'اكتب حرفين على الأقل.',
          searching:'جارٍ البحث…', occurrences:'موضع', loadFail:'تعذّر التحميل.',
          first:'الأولى', prev:'السابقة', next:'التالية', last:'الأخيرة',
          start:'ابدأ القراءة', pages:'الصفحات', notes:'الحواشي', edition:'النسخة',
          parts:'الأقسام', noBooks:'لا كتب في هذا القسم بعد.' },
    fa: { home:'خانه', library:'کتابخانه', search:'جستجو', contents:'فهرست',
          cite:'کپی ارجاع', copied:'کپی شد ✓', night:'شب', day:'روز',
          bigger:'بزرگ‌تر', smaller:'کوچک‌تر',
          ph:'در کتابخانه جستجو کنید…', scopeText:'متن کتاب‌ها', scopeTitle:'عنوان کتاب‌ها',
          scopeAuthor:'مؤلفان', advanced:'جستجوی پیشرفته',
          allWords:'همه این کلمات', phrase:'دقیقاً این عبارت', anyWord:'هر یک از این کلمات',
          without:'بدون این کلمات', inBook:'در کتاب', inCat:'در بخش', anyBook:'همه کتاب‌ها',
          anyCat:'همه بخش‌ها', run:'جستجو', clear:'پاک کردن',
          continue:'ادامه مطالعه', continueNone:'کتاب‌هایی که شروع کرده‌اید اینجا می‌آید.',
          categories:'بخش‌ها', books:'کتاب', page:'صفحه', volume:'جلد',
          results:'نتایج', noResults:'نتیجه‌ای نیست.', minChars:'حداقل دو حرف بنویسید.',
          searching:'در حال جستجو…', occurrences:'مورد', loadFail:'بارگذاری ناموفق بود.',
          first:'اول', prev:'قبلی', next:'بعدی', last:'آخر',
          start:'شروع مطالعه', pages:'صفحات', notes:'پانوشت‌ها', edition:'نسخه',
          parts:'بخش‌ها', noBooks:'هنوز کتابی در این بخش نیست.' },
    ur: { home:'صفحہ اول', library:'کتب خانہ', search:'تلاش', contents:'فہرست',
          cite:'حوالہ نقل کریں', copied:'نقل ہو گیا ✓', night:'رات', day:'دن',
          bigger:'بڑا', smaller:'چھوٹا',
          ph:'کتب خانے میں تلاش کریں…', scopeText:'کتابوں کا متن', scopeTitle:'کتابوں کے نام',
          scopeAuthor:'مصنفین', advanced:'اعلیٰ تلاش',
          allWords:'یہ تمام الفاظ', phrase:'بالکل یہی جملہ', anyWord:'ان میں سے کوئی لفظ',
          without:'ان الفاظ کے بغیر', inBook:'کتاب میں', inCat:'زمرے میں',
          anyBook:'تمام کتابیں', anyCat:'تمام زمرے', run:'تلاش کریں', clear:'صاف کریں',
          continue:'مطالعہ جاری رکھیں', continueNone:'جو کتابیں آپ نے شروع کیں وہ یہاں آئیں گی۔',
          categories:'زمرے', books:'کتاب', page:'صفحہ', volume:'جلد',
          results:'نتائج', noResults:'کوئی نتیجہ نہیں۔', minChars:'کم از کم دو حروف لکھیں۔',
          searching:'تلاش جاری ہے…', occurrences:'مقام', loadFail:'لوڈ نہیں ہو سکا۔',
          first:'پہلا', prev:'پچھلا', next:'اگلا', last:'آخری',
          start:'مطالعہ شروع کریں', pages:'صفحات', notes:'حواشی', edition:'نسخہ',
          parts:'حصے', noBooks:'اس زمرے میں ابھی کوئی کتاب نہیں۔' },
    en: { home:'Home', library:'Library', search:'Search', contents:'Contents',
          cite:'Copy citation', copied:'Copied ✓', night:'Night', day:'Day',
          bigger:'Larger text', smaller:'Smaller text',
          ph:'Search the library…', scopeText:'Book texts', scopeTitle:'Book titles',
          scopeAuthor:'Authors', advanced:'Advanced search',
          allWords:'All of these words', phrase:'This exact phrase',
          anyWord:'Any of these words', without:'None of these words',
          inBook:'In book', inCat:'In category', anyBook:'All books',
          anyCat:'All categories', run:'Search', clear:'Clear',
          continue:'Continue reading', continueNone:'Books you have opened will appear here.',
          categories:'Categories', books:'books', page:'page', volume:'Volume',
          results:'Results', noResults:'No results.', minChars:'Type at least two characters.',
          searching:'Searching…', occurrences:'matches', loadFail:'Could not load.',
          first:'First', prev:'Previous', next:'Next', last:'Last',
          start:'Start reading', pages:'Pages', notes:'Footnotes', edition:'Edition',
          parts:'Parts', noBooks:'No books in this category yet.' }
  };
  var RTL = { ar: 1, fa: 1, ur: 1 };
  var lang = store.get('lang') || 'ar';
  if (!STRINGS[lang]) lang = 'ar';
  function t(k) { return (STRINGS[lang] && STRINGS[lang][k]) || STRINGS.ar[k] || k; }

  function applyLang() {
    H.setAttribute('data-lang', lang);
    H.setAttribute('dir', RTL[lang] ? 'rtl' : 'ltr');
    each('[data-i18n]', function (el) { el.textContent = t(el.getAttribute('data-i18n')); });
    each('[data-i18n-ph]', function (el) {
      el.setAttribute('placeholder', t(el.getAttribute('data-i18n-ph')));
    });
    each('[data-i18n-label]', function (el) {
      el.setAttribute('aria-label', t(el.getAttribute('data-i18n-label')));
    });
    /* names carried in several languages: <b data-ar="…" data-en="…"> */
    each('[data-ar]', function (el) {
      var v = el.getAttribute('data-' + lang) || el.getAttribute('data-ar');
      if (v) el.textContent = v;
    });
    each('.langs button', function (b) {
      b.setAttribute('aria-pressed', String(b.getAttribute('data-lang') === lang));
    });
    var th = document.getElementById('btn-theme');
    if (th) th.textContent = H.getAttribute('data-theme') === 'night' ? t('day') : t('night');
  }
  function each(sel, fn) { Array.prototype.forEach.call(document.querySelectorAll(sel), fn); }
  each('.langs button', function (b) {
    b.addEventListener('click', function () {
      lang = b.getAttribute('data-lang'); store.set('lang', lang); applyLang();
      if (document.getElementById('cats')) renderCats();
      if (document.getElementById('continue')) renderContinue();
    });
  });

  /* ---------------- theme + type size ---------------- */
  function applyTheme(night) {
    H.setAttribute('data-theme', night ? 'night' : '');
    var b = document.getElementById('btn-theme');
    if (b) { b.setAttribute('aria-pressed', String(night)); b.textContent = night ? t('day') : t('night'); }
  }
  applyTheme(store.get('theme') === 'night');
  var size = parseFloat(store.get('size') || '1.24');
  H.style.setProperty('--body-size', size + 'rem');
  on('btn-theme', 'click', function () {
    var night = H.getAttribute('data-theme') !== 'night';
    store.set('theme', night ? 'night' : 'day'); applyTheme(night);
  });
  function bump(d) {
    size = Math.max(0.95, Math.min(1.75, size + d));
    store.set('size', size); H.style.setProperty('--body-size', size + 'rem');
  }
  on('btn-bigger', 'click', function () { bump(0.06); });
  on('btn-smaller', 'click', function () { bump(-0.06); });
  function on(id, ev, fn) { var el = document.getElementById(id); if (el) el.addEventListener(ev, fn); }

  /* ---------------- Arabic / Persian folding ---------------- */
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
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;' }[c];
    });
  }
  function marked(text, q) {
    var f = fold(text), out = '', cursor = 0, pos = 0;
    while ((pos = f.text.indexOf(q, pos)) !== -1) {
      var s = f.map[pos], e2 = f.map[pos + q.length - 1] + 1;
      if (s < cursor) { pos += q.length; continue; }
      out += esc(text.slice(cursor, s)) + '<mark>' + esc(text.slice(s, e2)) + '</mark>';
      cursor = e2; pos += q.length;
    }
    return out ? out + esc(text.slice(cursor)) : null;
  }
  var AR_D = '٠١٢٣٤٥٦٧٨٩';
  function toAr(n) {
    return lang === 'en' ? String(n)
      : String(n).replace(/\d/g, function (d) { return AR_D[+d]; });
  }
  function toEn(s) {
    return String(s).replace(/[٠-٩۰-۹]/g, function (c) {
      var a = '٠١٢٣٤٥٦٧٨٩'.indexOf(c);
      return String(a >= 0 ? a : '۰۱۲۳۴۵۶۷۸۹'.indexOf(c));
    });
  }

  /* ---------------- data ---------------- */
  var cache = {};
  function load(url) {
    if (!cache[url]) {
      cache[url] = fetch(url).then(function (r) {
        if (!r.ok) throw new Error(r.status);
        return r.json();
      });
    }
    return cache[url];
  }
  var catalogURL = ROOT + '/catalog.json';

  /* ---------------- continue reading ---------------- */
  var KEY = 'reading';
  function readList() {
    try { return JSON.parse(store.get(KEY) || '[]'); } catch (e) { return []; }
  }
  function recordRead(entry) {
    var list = readList().filter(function (x) { return x.slug !== entry.slug; });
    list.unshift(entry);
    store.set(KEY, JSON.stringify(list.slice(0, 8)));
  }
  function renderContinue() {
    var box = document.getElementById('continue');
    if (!box) return;
    var list = readList();
    if (!list.length) {
      box.innerHTML = '<p class="empty-note">' + esc(t('continueNone')) + '</p>';
      return;
    }
    box.innerHTML = '<div class="rail">' + list.map(function (x) {
      var pct = x.total ? Math.round(100 * (x.pos + 1) / x.total) : 0;
      return '<a class="rcard" href="' + ROOT + '/' + esc(x.href) + '">' +
        '<b>' + esc(x.title) + '</b><span>' + esc(t('page')) + ' ' + esc(x.label) +
        ' · ' + esc(t('volume')) + ' ' + toAr(x.volume || 1) + '</span>' +
        '<span class="prog"><i style="width:' + pct + '%"></i></span></a>';
    }).join('') + '</div>';
  }
  renderContinue();

  var meta = document.getElementById('page-meta');
  if (meta) {
    recordRead({
      slug: meta.getAttribute('data-slug'),
      title: meta.getAttribute('data-title'),
      href: meta.getAttribute('data-href'),
      label: meta.getAttribute('data-label'),
      volume: meta.getAttribute('data-volume'),
      pos: parseInt(meta.getAttribute('data-pos'), 10) || 0,
      total: parseInt(meta.getAttribute('data-total'), 10) || 0,
      at: Date.now()
    });
  }

  /* ---------------- categories + book list (home) ---------------- */
  var CAT = null, active = null;
  function renderCats() {
    if (!CAT) return;
    var tabs = document.getElementById('tabs');
    var body = document.getElementById('cat-body');
    if (!tabs || !body) return;
    var cats = CAT.categories.filter(function (c) {
      return CAT.books.some(function (b) { return b.category === c.id; }) || c.always;
    });
    if (!active || !cats.some(function (c) { return c.id === active; })) {
      active = cats.length ? cats[0].id : null;
    }
    tabs.innerHTML = cats.map(function (c) {
      var n = CAT.books.filter(function (b) { return b.category === c.id; }).length;
      return '<button class="tab" role="tab" data-cat="' + esc(c.id) + '" aria-selected="' +
             (c.id === active) + '">' + esc(c.name[lang] || c.name.ar) +
             ' <small>· ' + toAr(n) + '</small></button>';
    }).join('');
    var cat = cats.filter(function (c) { return c.id === active; })[0];
    var books = CAT.books.filter(function (b) { return b.category === active; });
    body.innerHTML =
      (cat && cat.desc ? '<p class="cat-desc">' + esc(cat.desc[lang] || cat.desc.ar || '') + '</p>' : '') +
      (books.length ? '<div class="books">' + books.map(bookCard).join('') + '</div>'
                    : '<p class="empty-note">' + esc(t('noBooks')) + '</p>');
    Array.prototype.forEach.call(tabs.children, function (b) {
      b.addEventListener('click', function () { active = b.getAttribute('data-cat'); renderCats(); });
    });
  }
  function bookCard(b) {
    var title = (b.title && (b.title[lang] || b.title.ar)) || '';
    var sub = b.subtitle && (b.subtitle[lang] || b.subtitle.en);
    var who = (b.author && (b.author[lang] || b.author.ar)) || '';
    return '<a class="bcard" href="' + ROOT + '/' + esc(b.href) + '">' +
      '<span class="spine"><span>' + esc((b.title.ar || '').slice(0, 14)) + '</span></span>' +
      '<span class="bmeta"><b>' + esc(title) + '</b>' +
      (sub ? '<i>' + esc(sub) + '</i>' : '') +
      (b.volumes > 1 ? '<em>(' + toAr(b.volumes) + ' ' + esc(t('volume')) + ')</em>' : '') +
      '<span class="who">' + esc(who) + '</span></span>' +
      '<span class="chev">›</span></a>';
  }
  if (document.getElementById('tabs')) {
    load(catalogURL).then(function (c) { CAT = c; renderCats(); })
      .catch(function () {
        document.getElementById('cat-body').innerHTML =
          '<p class="empty-note">' + esc(t('loadFail')) + '</p>';
      });
  }

  /* ---------------- search ---------------- */
  function params() {
    var out = {}, s = location.search.replace(/^\?/, '');
    s.split('&').forEach(function (kv) {
      if (!kv) return;
      var i = kv.indexOf('=');
      var k = decodeURIComponent(kv.slice(0, i < 0 ? kv.length : i).replace(/\+/g, ' '));
      var v = i < 0 ? '' : decodeURIComponent(kv.slice(i + 1).replace(/\+/g, ' '));
      out[k] = v;
    });
    return out;
  }
  function goSearch(p) {
    var q = Object.keys(p).filter(function (k) { return p[k]; })
      .map(function (k) { return k + '=' + encodeURIComponent(p[k]); }).join('&');
    location.href = ROOT + '/search/?' + q;
  }
  var homeForm = document.getElementById('home-search');
  if (homeForm) {
    homeForm.addEventListener('submit', function (e) {
      e.preventDefault();
      goSearch({ q: document.getElementById('home-q').value.trim(),
                 in: document.getElementById('home-scope').value });
    });
    on('adv-toggle', 'click', function () {
      var a = document.getElementById('adv');
      a.setAttribute('data-open', a.getAttribute('data-open') === '1' ? '0' : '1');
    });
    on('adv-run', 'click', function () {
      goSearch({ all: val('adv-all'), phrase: val('adv-phrase'), any: val('adv-any'),
                 without: val('adv-not'), book: val('adv-book'), cat: val('adv-cat'),
                 in: 'text' });
    });
    on('adv-clear', 'click', function () {
      ['adv-all','adv-phrase','adv-any','adv-not'].forEach(function (id) {
        var el = document.getElementById(id); if (el) el.value = '';
      });
    });
    load(catalogURL).then(function (c) {
      var sb = document.getElementById('adv-book'), sc = document.getElementById('adv-cat');
      if (sb) sb.innerHTML = '<option value="">' + esc(t('anyBook')) + '</option>' +
        c.books.map(function (b) {
          return '<option value="' + esc(b.slug) + '">' + esc(b.title.ar) + '</option>';
        }).join('');
      if (sc) sc.innerHTML = '<option value="">' + esc(t('anyCat')) + '</option>' +
        c.categories.map(function (x) {
          return '<option value="' + esc(x.id) + '">' + esc(x.name.ar) + '</option>';
        }).join('');
    }).catch(function () {});
  }
  function val(id) { var el = document.getElementById(id); return el ? el.value.trim() : ''; }

  var resBox = document.getElementById('results');
  if (resBox) {
    var p = params();
    var titleEl = document.getElementById('res-q');
    if (titleEl) titleEl.textContent = p.q || p.phrase || p.all || p.any || '';
    var qInput = document.getElementById('res-input');
    if (qInput) qInput.value = p.q || '';
    var form = document.getElementById('res-form');
    if (form) form.addEventListener('submit', function (e) {
      e.preventDefault();
      goSearch({ q: qInput.value.trim(), in: document.getElementById('res-scope').value });
    });
    runSearch(p);
  }

  function tokens(s) {
    return fold(s || '').text.split(/\s+/).filter(function (x) { return x.length > 1; });
  }
  function runSearch(p) {
    resBox.innerHTML = '<p class="empty-note">' + esc(t('searching')) + '</p>';
    var scope = p['in'] || 'text';
    load(catalogURL).then(function (cat) {
      var books = cat.books.filter(function (b) {
        return (!p.book || b.slug === p.book) && (!p.cat || b.category === p.cat);
      });
      if (scope === 'title' || scope === 'author') {
        var q = fold(p.q || '').text.trim();
        var hits = books.filter(function (b) {
          var hay = scope === 'title'
            ? Object.keys(b.title).map(function (k) { return b.title[k]; }).join(' ')
            : Object.keys(b.author).map(function (k) { return b.author[k]; }).join(' ');
          return fold(hay).text.indexOf(q) !== -1;
        });
        resBox.innerHTML = hits.length
          ? '<div class="books">' + hits.map(bookCard).join('') + '</div>'
          : '<p class="empty-note">' + esc(t('noResults')) + '</p>';
        return;
      }
      var phrase = fold(p.phrase || p.q || '').text.trim();
      var all = tokens(p.all), any = tokens(p.any), not = tokens(p['without']);
      if (!phrase && !all.length && !any.length) {
        resBox.innerHTML = '<p class="empty-note">' + esc(t('minChars')) + '</p>';
        return;
      }
      Promise.all(books.map(function (b) {
        return load(ROOT + '/' + b.slug + '/assets/search-index.json')
          .then(function (idx) { return { book: b, idx: idx }; })
          .catch(function () { return null; });
      })).then(function (sets) {
        var out = [];
        sets.filter(Boolean).forEach(function (set) {
          set.idx.forEach(function (row) {
            var txt = row.t;
            if (not.some(function (w) { return txt.indexOf(w) !== -1; })) return;
            if (all.length && !all.every(function (w) { return txt.indexOf(w) !== -1; })) return;
            if (any.length && !any.some(function (w) { return txt.indexOf(w) !== -1; })) return;
            var mark = phrase || all[0] || any.filter(function (w) {
              return txt.indexOf(w) !== -1; })[0] || '';
            if (phrase && txt.indexOf(phrase) === -1) return;
            var at = mark ? txt.indexOf(mark) : 0, n = 0, i = 0;
            if (mark) { while ((i = txt.indexOf(mark, i)) !== -1) { n++; i += mark.length; } }
            out.push({ b: set.book, row: row, at: Math.max(0, at), n: n, mark: mark });
            });
        });
        if (!out.length) {
          resBox.innerHTML = '<p class="empty-note">' + esc(t('noResults')) + '</p>';
          return;
        }
        out.sort(function (x, y) { return y.n - x.n; });
        var head = '<p class="empty-note">' + toAr(out.length) + ' · ' + esc(t('results')) + '</p>';
        resBox.innerHTML = head + out.slice(0, 300).map(function (h) {
          var s = Math.max(0, h.at - 50);
          var snip = h.row.t.slice(s, Math.min(h.row.t.length, h.at + 60));
          var link = ROOT + '/' + h.row.href + (h.mark ? '?q=' + encodeURIComponent(h.mark) : '');
          return '<a class="res" href="' + link + '"><span class="res-h">' +
            esc(h.b.title.ar) + ' · ' + esc(h.row.part) + ' · ' + esc(t('page')) + ' ' +
            esc(h.row.label) + (h.n ? ' · ' + toAr(h.n) + ' ' + esc(t('occurrences')) : '') +
            '</span><span class="res-t">…' + (marked(snip, h.mark) || esc(snip)) +
            '…</span></a>';
        }).join('');
      });
    }).catch(function () {
      resBox.innerHTML = '<p class="empty-note">' + esc(t('loadFail')) + '</p>';
    });
  }

  /* ---------------- reading page ---------------- */
  var Q = (function () {
    var m = location.search.match(/[?&]q=([^&]*)/);
    if (!m) return '';
    try { return fold(decodeURIComponent(m[1].replace(/\+/g, ' '))).text.trim(); }
    catch (e) { return ''; }
  })();
  if (Q.length > 1 && document.querySelector('.body')) {
    each('.body p, .body h3, .note span:last-child', function (el) {
      if (el.querySelector('mark')) return;
      var html = marked(el.textContent, Q);
      if (html) el.innerHTML = html;
    });
    var first = document.querySelector('mark');
    if (first) first.scrollIntoView({ block: 'center' });
  }

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

  on('btn-toc', 'click', function () {
    var body = openDrawer(t('contents'));
    body.innerHTML = '<p class="note-msg">…</p>';
    load(BOOK + '/assets/toc.json').then(function (toc) {
      body.innerHTML = toc.length ? toc.map(function (x) {
        return '<a class="toc-i" href="' + ROOT + '/' + x.href + '"><span>' +
               (x.label || '—') + '</span>' + esc(x.title) + '</a>';
      }).join('') : '<p class="note-msg">—</p>';
    }).catch(function () {
      body.innerHTML = '<p class="note-msg">' + esc(t('loadFail')) + '</p>';
    });
  });

  on('btn-search', 'click', function () {
    var body = openDrawer(t('search'));
    body.innerHTML = '<div class="search-row"><input id="dq" data-i18n-ph="ph">' +
      '<button class="btn" id="dq-go" data-i18n="run"></button></div><div id="dhits"></div>';
    applyLang();
    var q = document.getElementById('dq');
    q.focus();
    function run() {
      var raw = q.value.trim(), needle = fold(raw).text;
      var box = document.getElementById('dhits');
      if (needle.length < 2) { box.innerHTML = '<p class="note-msg">' + esc(t('minChars')) + '</p>'; return; }
      box.innerHTML = '<p class="note-msg">' + esc(t('searching')) + '</p>';
      load(BOOK + '/assets/search-index.json').then(function (idx) {
        var hits = [];
        idx.forEach(function (row) {
          var n = 0, at = -1, i = 0;
          while ((i = row.t.indexOf(needle, i)) !== -1) { if (at < 0) at = i; n++; i += needle.length; }
          if (n) hits.push({ row: row, n: n, at: at });
        });
        if (!hits.length) { box.innerHTML = '<p class="note-msg">' + esc(t('noResults')) + '</p>'; return; }
        box.innerHTML = hits.map(function (h) {
          var s = Math.max(0, h.at - 45);
          var snip = h.row.t.slice(s, Math.min(h.row.t.length, h.at + needle.length + 45));
          return '<a class="hit" href="' + ROOT + '/' + h.row.href + '?q=' +
            encodeURIComponent(raw) + '"><span class="hit-p">' + esc(h.row.part) + ' · ' +
            esc(t('page')) + ' ' + esc(h.row.label) + ' · ' + toAr(h.n) + ' ' +
            esc(t('occurrences')) + '</span><span class="hit-t">…' +
            (marked(snip, needle) || esc(snip)) + '…</span></a>';
        }).join('');
      }).catch(function () {
        box.innerHTML = '<p class="note-msg">' + esc(t('loadFail')) + '</p>';
      });
    }
    q.addEventListener('keydown', function (e) { if (e.key === 'Enter') run(); });
    document.getElementById('dq-go').addEventListener('click', run);
  });

  on('btn-cite', 'click', function (e) {
    var el = document.getElementById('cite-text');
    if (!el) return;
    var text = el.getAttribute('data-cite') + ' ' + location.href.split('?')[0];
    var btn = e.currentTarget;
    function done(ok) {
      btn.textContent = ok ? t('copied') : '—';
      setTimeout(function () { btn.textContent = t('cite'); }, 1600);
    }
    if (navigator.clipboard) navigator.clipboard.writeText(text).then(
      function () { done(true); }, function () { done(false); });
    else done(false);
  });

  var jump = document.getElementById('jump');
  if (jump) jump.addEventListener('submit', function (e) {
    var n = toEn(document.getElementById('jump-num').value).replace(/\D/g, '');
    var tpl = jump.getAttribute('data-tpl');
    if (n && tpl) { e.preventDefault(); location.href = ROOT + '/' + tpl.replace('{p}', n); }
  });
  function rel(r) {
    var l = document.querySelector('link[rel="' + r + '"]');
    return l && l.getAttribute('href');
  }
  document.addEventListener('keydown', function (e) {
    var tag = e.target.tagName;
    if (tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA') {
      if (e.key === 'Escape') e.target.blur();
      return;
    }
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    var fwd = RTL[lang] ? 'ArrowLeft' : 'ArrowRight';
    var back = RTL[lang] ? 'ArrowRight' : 'ArrowLeft';
    if (e.key === fwd && rel('next')) location.href = rel('next');
    else if (e.key === back && rel('prev')) location.href = rel('prev');
    else if (e.key === '/') {
      e.preventDefault();
      var b = document.getElementById('btn-search') || document.getElementById('home-q');
      if (b) b.focus ? b.focus() : b.click();
      if (b && b.id === 'btn-search') b.click();
    } else if (e.key === 'Escape') closeDrawer();
  });

  applyLang();
})();
