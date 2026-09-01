/* Misbah Library — interface behaviour.
   Everything the server renders that is language-dependent carries
   data-ar / data-fa / data-ur / data-en attributes, so switching language
   translates the whole page, not just the buttons. */
(function () {
  "use strict";
  var H = document.documentElement;
  var ROOT = H.getAttribute('data-root') || '.';
  var BOOK = H.getAttribute('data-book') || ROOT;

  var store = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  };

  var T = {
    ar: { first:'الأولى', prev:'السابقة', next:'التالية', last:'الأخيرة', volumes:'المجلدات', published:'المنشور', pickVolume:'اختر المجلد', otherVolumes:'مجلدات أخرى', volsNote:'المجلدات غير المفعّلة لم تُنشر بعد.', soon:'قريباً', citeAr:'للإحالة استعمل الصفحة العربية:', machineTr:'ترجمة آلية بالذكاء الاصطناعي، غير مراجَعة وقد تحتوي أخطاء. للإحالة يُعتمد الأصل العربي.', viewAr:'العربية', viewTr:'الترجمة', viewBoth:'كلاهما', viewSide:'مقابل', verse:'الآية', surah:'السورة', surahs:'السور', pickSurah:'اختر السورة', script:'الخط', scriptUthmani:'أميري', scriptSimple:'بسيط', copyVerse:'نسخ الآية', copyRef:'الإحالة', copyLink:'الرابط', copyDo:'نسخ', ayat:'آية', meccan:'مكية', medinan:'مدنية', textFrom:'النص من', transFrom:'الترجمات عبر', noTr:'لم تُترجم هذه الصفحة بعد؛ النص معروض بالعربية.', draft:'ترجمة أولية غير مراجَعة.', trBy:'الترجمة', home:'الرئيسية', mylib:'مكتبتي', search:'بحث', allBooks:'كل الكتب',
          contact:'اتصل بنا', about:'من نحن', menu:'القائمة', close:'إغلاق',
          contents:'الفهرس', cite:'نسخ الإحالة', copied:'تم النسخ ✓',
          night:'ليلي', day:'نهاري', bigger:'تكبير الخط', smaller:'تصغير الخط',
          libName:'مكتبة مصباح', tagline:'نصوص كاملة قابلة للإحالة، صفحةً بصفحة',
          quote:'تمضي أيامي في ولاء عليٍّ عليه السلام',
          ph:'ابحث في المكتبة…', scopeText:'نصوص الكتب', scopeTitle:'عناوين الكتب',
          scopeAuthor:'المؤلفون', advanced:'بحث متقدم',
          allWords:'كل هذه الكلمات', phrase:'هذه العبارة بالضبط', anyWord:'أي من هذه الكلمات',
          without:'بدون هذه الكلمات', inBook:'في كتاب', inCat:'في قسم',
          anyBook:'كل الكتب', anyCat:'كل الأقسام', run:'ابحث', clear:'مسح',
          continue:'متابعة القراءة', continueNone:'ستظهر هنا الكتب التي بدأت قراءتها.',
          categories:'الأقسام', statBooks:'كتب', statVolumes:'مجلدات', statPages:'صفحات',
          books:'كتاب', page:'صفحة', volume:'مجلد',
          results:'النتائج', noResults:'لا نتائج.', minChars:'اكتب حرفين على الأقل.',
          searching:'جارٍ البحث…', occurrences:'موضع', loadFail:'تعذّر التحميل.',
          start:'ابدأ القراءة', pages:'الصفحات', notes:'الحواشي', edition:'النسخة',
          parts:'الأقسام', noBooks:'لا كتب في هذا القسم بعد.', citation:'الإحالة',
          urlNote:'لكل صفحة عنوان ثابت، ورقم الصفحة هو رقم الطبعة المطبوعة، فتبقى الإحالة صالحة.',
          rights:'مكتبة مصباح — نصوص تراثية بصيغة مفتوحة.',
          browse:'تصفح', aboutBody:'مكتبة مصباح مشروع لنشر النصوص التراثية على الإنترنت بصيغة '
                 + 'قابلة للإحالة الدقيقة: كل صفحة تحمل رقمها في الطبعة المطبوعة وعنواناً ثابتاً '
                 + 'لا يتغير، ليستطيع الباحث أن يحيل إليها ويثق ببقاء الرابط.',
          contactBody:'للاقتراحات وتصحيح الأخطاء والمساهمة في المكتبة، يرجى التواصل معنا.' },
    fa: { first:'نخست', prev:'صفحه قبل', next:'صفحه بعد', last:'پایان', volumes:'مجلدات', published:'منتشرشده', pickVolume:'انتخاب جلد', otherVolumes:'جلدهای دیگر', volsNote:'جلدهای غیرفعال هنوز منتشر نشده‌اند.', soon:'به‌زودی', citeAr:'برای ارجاع از صفحهٔ عربی استفاده کنید:', machineTr:'ترجمهٔ ماشینی با هوش مصنوعی، بازبینی‌نشده و ممکن است خطا داشته باشد. برای ارجاع به متن عربی استناد کنید.', viewAr:'عربی', viewTr:'ترجمه', viewBoth:'هر دو', viewSide:'دوستونه', verse:'آیه', surah:'سوره', surahs:'سوره‌ها', pickSurah:'انتخاب سوره', script:'خط', scriptUthmani:'امیری', scriptSimple:'ساده', copyVerse:'کپی آیه', copyRef:'ارجاع', copyLink:'پیوند', copyDo:'کپی', ayat:'آیه', meccan:'مکی', medinan:'مدنی', textFrom:'متن از', transFrom:'ترجمه‌ها از', noTr:'این صفحه هنوز ترجمه نشده است؛ متن عربی نمایش داده می‌شود.', draft:'ترجمهٔ اولیه و بازبینی‌نشده.', trBy:'ترجمه', home:'خانه', mylib:'کتابخانهٔ من', search:'جستجو', allBooks:'همهٔ کتاب‌ها',
          contact:'تماس با ما', about:'دربارهٔ ما', menu:'فهرست', close:'بستن',
          contents:'فهرست', cite:'کپی ارجاع', copied:'کپی شد ✓',
          night:'شب', day:'روز', bigger:'بزرگ‌تر', smaller:'کوچک‌تر',
          libName:'کتابخانهٔ مصباح', tagline:'متن‌های کامل و قابل ارجاع، صفحه به صفحه',
          quote:'روزگارم با غلامی علی سر می‌شود',
          ph:'در کتابخانه جستجو کنید…', scopeText:'متن کتاب‌ها', scopeTitle:'عنوان کتاب‌ها',
          scopeAuthor:'مؤلفان', advanced:'جستجوی پیشرفته',
          allWords:'همهٔ این کلمات', phrase:'دقیقاً این عبارت', anyWord:'هر یک از این کلمات',
          without:'بدون این کلمات', inBook:'در کتاب', inCat:'در بخش',
          anyBook:'همهٔ کتاب‌ها', anyCat:'همهٔ بخش‌ها', run:'جستجو', clear:'پاک کردن',
          continue:'ادامهٔ مطالعه', continueNone:'کتاب‌هایی که آغاز کرده‌اید اینجا می‌آید.',
          categories:'بخش‌ها', statBooks:'کتاب', statVolumes:'جلد', statPages:'صفحه',
          books:'کتاب', page:'صفحه', volume:'جلد',
          results:'نتایج', noResults:'نتیجه‌ای یافت نشد.', minChars:'دست‌کم دو حرف بنویسید.',
          searching:'در حال جستجو…', occurrences:'مورد', loadFail:'بارگذاری ناموفق بود.',
          start:'شروع مطالعه', pages:'صفحات', notes:'پانوشت‌ها', edition:'نسخه',
          parts:'بخش‌ها', noBooks:'هنوز کتابی در این بخش نیست.', citation:'ارجاع',
          urlNote:'هر صفحه نشانی ثابت دارد و شمارهٔ صفحه همان شمارهٔ چاپی است؛ ارجاع معتبر می‌ماند.',
          rights:'کتابخانهٔ مصباح — متون تراثی به شکل باز.',
          browse:'مرور', aboutBody:'کتابخانهٔ مصباح پروژه‌ای است برای انتشار متون تراثی بر '
                 + 'بستر وب به شکلی که ارجاع دقیق ممکن باشد: هر صفحه شمارهٔ چاپی خود و نشانی '
                 + 'ثابتی دارد که تغییر نمی‌کند.',
          contactBody:'برای پیشنهاد، گزارش اشتباه یا همکاری با کتابخانه با ما در تماس باشید.' },
    ur: { first:'پہلا', prev:'پچھلا', next:'اگلا', last:'آخری', volumes:'جلدیں', published:'شائع شدہ', pickVolume:'جلد منتخب کریں', otherVolumes:'دیگر جلدیں', volsNote:'غیر فعال جلدیں ابھی شائع نہیں ہوئیں۔', soon:'جلد آ رہا ہے', citeAr:'حوالے کے لیے عربی صفحہ استعمال کریں:', machineTr:'مصنوعی ذہانت سے تیار کردہ مشینی ترجمہ، غیر نظرثانی شدہ اور اس میں غلطیاں ممکن ہیں۔ حوالے کے لیے عربی اصل پر اعتماد کریں۔', viewAr:'عربی', viewTr:'ترجمہ', viewBoth:'دونوں', viewSide:'آمنے سامنے', verse:'آیت', surah:'سورہ', surahs:'سورتیں', pickSurah:'سورہ منتخب کریں', script:'خط', scriptUthmani:'امیری', scriptSimple:'سادہ', copyVerse:'آیت نقل کریں', copyRef:'حوالہ', copyLink:'لنک', copyDo:'نقل', ayat:'آیات', meccan:'مکی', medinan:'مدنی', textFrom:'متن بشکریہ', transFrom:'تراجم بشکریہ', noTr:'اس صفحے کا ترجمہ ابھی نہیں ہوا؛ عربی متن دکھایا جا رہا ہے۔', draft:'ابتدائی، غیر نظرثانی شدہ ترجمہ۔', trBy:'ترجمہ', home:'صفحۂ اول', mylib:'میری لائبریری', search:'تلاش', allBooks:'تمام کتب',
          contact:'رابطہ کریں', about:'ہمارے بارے میں', menu:'مینو', close:'بند کریں',
          contents:'فہرست', cite:'حوالہ نقل کریں', copied:'نقل ہو گیا ✓',
          night:'رات', day:'دن', bigger:'بڑا', smaller:'چھوٹا',
          libName:'مصباح لائبریری', tagline:'مکمل متون، صفحہ بہ صفحہ قابلِ حوالہ',
          quote:'میرا زمانہ علیؑ کی غلامی میں بسر ہوتا ہے',
          ph:'لائبریری میں تلاش کریں…', scopeText:'کتابوں کا متن', scopeTitle:'کتابوں کے نام',
          scopeAuthor:'مصنفین', advanced:'اعلیٰ تلاش',
          allWords:'یہ تمام الفاظ', phrase:'بالکل یہی جملہ', anyWord:'ان میں سے کوئی لفظ',
          without:'ان الفاظ کے بغیر', inBook:'کتاب میں', inCat:'زمرے میں',
          anyBook:'تمام کتابیں', anyCat:'تمام زمرے', run:'تلاش کریں', clear:'صاف کریں',
          continue:'مطالعہ جاری رکھیں', continueNone:'جو کتابیں آپ نے کھولیں وہ یہاں آئیں گی۔',
          categories:'زمرے', statBooks:'کتب', statVolumes:'جلدیں', statPages:'صفحات',
          books:'کتاب', page:'صفحہ', volume:'جلد',
          results:'نتائج', noResults:'کوئی نتیجہ نہیں۔', minChars:'کم از کم دو حروف لکھیں۔',
          searching:'تلاش جاری ہے…', occurrences:'مقام', loadFail:'لوڈ نہیں ہو سکا۔',
          start:'مطالعہ شروع کریں', pages:'صفحات', notes:'حواشی', edition:'نسخہ',
          parts:'حصے', noBooks:'اس زمرے میں ابھی کوئی کتاب نہیں۔', citation:'حوالہ',
          urlNote:'ہر صفحے کا مستقل پتہ ہے اور صفحہ نمبر مطبوعہ نسخے کا ہے، اس لیے حوالہ قائم رہتا ہے۔',
          rights:'مصباح لائبریری — تراثی متون، کھلے انداز میں۔',
          browse:'دیکھیں', aboutBody:'مصباح لائبریری کا مقصد تراثی متون کو ایسے انداز میں '
                 + 'شائع کرنا ہے کہ درست حوالہ ممکن ہو: ہر صفحہ اپنا مطبوعہ نمبر اور ایک '
                 + 'مستقل پتہ رکھتا ہے۔',
          contactBody:'تجاویز، اغلاط کی نشاندہی یا تعاون کے لیے ہم سے رابطہ کریں۔' },
    en: { first:'First', prev:'Previous', next:'Next', last:'Last', volumes:'Volumes', published:'Published', pickVolume:'Choose a volume', otherVolumes:'Other volumes', volsNote:'Greyed volumes have not been published yet.', soon:'Coming soon', citeAr:'For citation use the Arabic page:', machineTr:'Machine translation by AI. Not reviewed and may contain errors — cite the Arabic original, not this translation.', viewAr:'Arabic', viewTr:'Translation', viewBoth:'Both', viewSide:'Side by side', verse:'Verse', surah:'Surah', surahs:'Surahs', pickSurah:'Choose a surah', script:'Script', scriptUthmani:'Amiri', scriptSimple:'Simple', copyVerse:'Copy verse', copyRef:'Reference', copyLink:'Link', copyDo:'Copy', ayat:'ayat', meccan:'Meccan', medinan:'Medinan', textFrom:'Text from', transFrom:'translations via', noTr:'This page has not been translated yet; the Arabic text is shown.', draft:'Draft translation, not yet reviewed.', trBy:'Translation', home:'Home', mylib:'My library', search:'Search', allBooks:'All books',
          contact:'Contact us', about:'About us', menu:'Menu', close:'Close',
          contents:'Contents', cite:'Copy citation', copied:'Copied ✓',
          night:'Night', day:'Day', bigger:'Larger text', smaller:'Smaller text',
          libName:'Misbah Library', tagline:'Complete texts, citable page by page',
          quote:'My days are spent in the service of Ali',
          ph:'Search the library…', scopeText:'Book texts', scopeTitle:'Book titles',
          scopeAuthor:'Authors', advanced:'Advanced search',
          allWords:'All of these words', phrase:'This exact phrase',
          anyWord:'Any of these words', without:'None of these words',
          inBook:'In book', inCat:'In category', anyBook:'All books',
          anyCat:'All categories', run:'Search', clear:'Clear',
          continue:'Continue reading', continueNone:'Books you have opened will appear here.',
          categories:'Categories', statBooks:'Books', statVolumes:'Volumes', statPages:'Pages',
          books:'books', page:'Page', volume:'Volume',
          results:'Results', noResults:'No results.', minChars:'Type at least two characters.',
          searching:'Searching…', occurrences:'matches', loadFail:'Could not load.',
          start:'Start reading', pages:'Pages', notes:'Footnotes', edition:'Edition',
          parts:'Parts', noBooks:'No books in this category yet.', citation:'Citation',
          urlNote:'Every page has a permanent address and carries its printed page number, '
                + 'so a citation stays valid.',
          rights:'Misbah Library — classical texts in an open format.',
          browse:'Browse', aboutBody:'Misbah Library publishes classical texts on the web in a '
                 + 'form that can be cited precisely: every page carries its printed page number '
                 + 'and a permanent address that does not change, so a reference made today still '
                 + 'resolves years from now.',
          contactBody:'For suggestions, corrections, or to contribute to the library, '
                    + 'please get in touch.' }
  };
  var RTL = { ar: 1, fa: 1, ur: 1 };
  var DIGITS = { ar: '٠١٢٣٤٥٦٧٨٩', fa: '۰۱۲۳۴۵۶۷۸۹', ur: '۰۱۲۳۴۵۶۷۸۹', en: '0123456789' };
  var FIXED = H.getAttribute('data-sitelang') || '';
  var lang = FIXED || store.get('lang') || 'ar';
  if (!T[lang]) lang = 'ar';
  function t(k) { return (T[lang] && T[lang][k]) || T.ar[k] || k; }
  function num(n) {
    var d = DIGITS[lang] || DIGITS.ar;
    return String(n).replace(/\d/g, function (c) { return d[+c]; });
  }
  function toEn(s) {
    return String(s).replace(/[٠-٩۰-۹]/g, function (c) {
      var a = '٠١٢٣٤٥٦٧٨٩'.indexOf(c);
      return String(a >= 0 ? a : '۰۱۲۳۴۵۶۷۸۹'.indexOf(c));
    });
  }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;' }[c];
    });
  }
  function each(sel, fn) { Array.prototype.forEach.call(document.querySelectorAll(sel), fn); }
  function on(id, ev, fn) { var el = document.getElementById(id); if (el) el.addEventListener(ev, fn); }

  /* ---------- apply language everywhere ---------- */
  function applyLang() {
    H.setAttribute('lang', lang);
    H.setAttribute('data-lang', lang);
    H.setAttribute('dir', RTL[lang] ? 'rtl' : 'ltr');
    each('[data-i18n]', function (el) { el.textContent = t(el.getAttribute('data-i18n')); });
    each('[data-i18n-ph]', function (el) {
      el.setAttribute('placeholder', t(el.getAttribute('data-i18n-ph')));
    });
    each('[data-i18n-label]', function (el) {
      el.setAttribute('aria-label', t(el.getAttribute('data-i18n-label')));
    });
    each('[data-ar]', function (el) {
      var v = el.getAttribute('data-' + lang);
      if (v === null || v === '') v = el.getAttribute('data-ar');
      if (v !== null) el.textContent = v;
    });
    each('[data-num]', function (el) { el.textContent = num(el.getAttribute('data-num')); });
    each('[data-num-val]', function (el) { el.value = num(el.getAttribute('data-num-val')); });
    each('#vsel option', function (o) { o.textContent = num(o.value); });
    each('.suras a[data-n]', function (a) {
      a.setAttribute('href', ROOT + '/' + (lang === 'ar' ? '' : lang + '/') +
                             'quran/' + a.getAttribute('data-n') + '/');
    });
    each('.vols a.vol[href]', function (a) {
      var v = a.getAttribute('data-vol');
      if (!v) { v = a.getAttribute('href').replace(/\//g, ''); a.setAttribute('data-vol', v); }
      var parts = location.pathname.replace(/\/$/, '').split('/');
      var slug = parts[parts.length - 1];
      a.setAttribute('href', lang !== 'ar'
        ? ROOT + '/' + lang + '/' + slug + '/' + v + '/1/'
        : v + '/');
    });
    each('.langs button', function (b) {
      b.setAttribute('aria-pressed', String(b.getAttribute('data-lang') === lang));
    });
    var th = document.getElementById('btn-theme');
    if (th) th.textContent = H.getAttribute('data-theme') === 'night' ? t('day') : t('night');
    document.title = document.title;
    if (document.getElementById('tabs')) renderCats();
    if (document.getElementById('continue')) renderContinue();
    if (document.getElementById('all-books')) renderAll();
    fillAdv();
  }
  each('.langs button', function (b) {
    b.addEventListener('click', function () {
      var to = b.getAttribute('data-lang');
      store.set('lang', to);
      /* a translated page lives at its own URL, so follow it rather than
         re-rendering — that URL is what search engines have indexed */
      var m = document.getElementById('page-meta');
      var alt = m && m.getAttribute('data-alt-' + to);
      if (alt) { location.href = alt; return; }
      if (FIXED) {
        var back = document.querySelector('link[rel="alternate"][hreflang="ar"]');
        if (to === 'ar' && back) { location.href = back.getAttribute('href'); return; }
        var other = document.querySelector('link[rel="alternate"][hreflang="' + to + '"]');
        if (other) { location.href = other.getAttribute('href'); return; }
      }
      lang = to; applyLang();
    });
  });

  /* ---------- theme + size ---------- */
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

  /* ---------- nav drawer ---------- */
  var nav = document.getElementById('nav'), scrim = document.getElementById('scrim');
  function closeAll() {
    if (nav) { nav.setAttribute('data-open', '0'); nav.setAttribute('aria-hidden', 'true'); }
    var d = document.getElementById('drawer');
    if (d) { d.setAttribute('data-open', '0'); d.setAttribute('aria-hidden', 'true'); }
    if (scrim) scrim.setAttribute('data-open', '0');
  }
  on('btn-menu', 'click', function () {
    nav.setAttribute('data-open', '1'); nav.setAttribute('aria-hidden', 'false');
    if (scrim) scrim.setAttribute('data-open', '1');
  });
  on('nav-close', 'click', closeAll);
  if (scrim) scrim.addEventListener('click', closeAll);

  /* ---------- folding / highlight ---------- */
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
    if (!q) return null;
    var f = fold(text), out = '', cur = 0, pos = 0;
    while ((pos = f.text.indexOf(q, pos)) !== -1) {
      var s = f.map[pos], e2 = f.map[pos + q.length - 1] + 1;
      if (s < cur) { pos += q.length; continue; }
      out += esc(text.slice(cur, s)) + '<mark>' + esc(text.slice(s, e2)) + '</mark>';
      cur = e2; pos += q.length;
    }
    return out ? out + esc(text.slice(cur)) : null;
  }

  var cache = {};
  function load(url) {
    if (!cache[url]) {
      cache[url] = fetch(url).then(function (r) {
        if (!r.ok) throw new Error(r.status); return r.json();
      });
    }
    return cache[url];
  }
  var CATURL = ROOT + '/catalog.json';

  /* ---------- continue reading ---------- */
  function readList() { try { return JSON.parse(store.get('reading') || '[]'); } catch (e) { return []; } }
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
      var title = (x.titles && (x.titles[lang] || x.titles.ar)) || x.title || '';
      return '<a class="rcard" href="' + ROOT + '/' + esc(x.href) + '">' +
        '<b>' + esc(title) + '</b><span>' + esc(t('page')) + ' ' + num(x.pageNum) +
        ' · ' + esc(t('volume')) + ' ' + num(x.volume || 1) + '</span>' +
        '<span class="prog"><i style="width:' + pct + '%"></i></span></a>';
    }).join('') + '</div>';
  }

  var meta = document.getElementById('page-meta');
  if (meta) {
    var titles = {};
    ['ar','fa','ur','en'].forEach(function (L) {
      titles[L] = meta.getAttribute('data-title-' + L) || meta.getAttribute('data-title-ar');
    });
    var entry = { slug: meta.getAttribute('data-slug'), titles: titles,
      href: meta.getAttribute('data-href'), pageNum: meta.getAttribute('data-pagenum'),
      volume: meta.getAttribute('data-volume'),
      pos: parseInt(meta.getAttribute('data-pos'), 10) || 0,
      total: parseInt(meta.getAttribute('data-total'), 10) || 0, at: Date.now() };
    var list = readList().filter(function (x) { return x.slug !== entry.slug; });
    list.unshift(entry);
    store.set('reading', JSON.stringify(list.slice(0, 8)));
  }

  /* ---------- catalog rendering ---------- */
  var CAT = null, active = null;
  function pick(o) { return o ? (o[lang] || o.ar || o.en || '') : ''; }
  /* subtitles are optional and must not leak another language onto the page */
  function pickStrict(o) { return (o && o[lang]) || ''; }
  function bookCard(b) {
    var sub = pickStrict(b.subtitle);
    var spine = (b.title && (b.title.ar || b.title.en) || '').slice(0, 16);
    if (b.placeholder) {
      return '<div class="bcard soon">' +
        '<span class="spine"><span>' + esc(spine) + '</span></span>' +
        '<span class="bmeta"><b>' + esc(pick(b.title)) + '</b>' +
        (sub ? '<i>' + esc(sub) + '</i>' : '') +
        '<span class="badge">' + num(b.volumes) + ' ' + esc(t(b.unit || 'volumes')) + '</span>' +
        '<span class="who">' + esc(pick(b.author)) +
        '<em class="soon-tag">' + esc(t('soon')) + '</em></span></span></div>';
    }
    var href = (lang !== 'ar' && b.translated && b.translated.indexOf(lang) !== -1 &&
                b.volumesPublished && b.volumesPublished.length)
      ? lang + '/' + b.href
      : b.href;
    return '<a class="bcard" href="' + ROOT + '/' + esc(href) + '">' +
      '<span class="spine"><span>' + esc(spine) + '</span></span>' +
      '<span class="bmeta"><b>' + esc(pick(b.title)) + '</b>' +
      (sub ? '<i>' + esc(sub) + '</i>' : '') +
      (b.volumes > 1 ? '<span class="badge">' + num(b.volumes) + ' ' + esc(t(b.unit || 'volumes')) +
        '</span>' : '') +
      '<span class="who"><svg class="ic" viewBox="0 0 24 24"><circle cx="12" cy="8" r="3.2"/>' +
      '<path d="M5 20c1.2-3.6 4-5.4 7-5.4s5.8 1.8 7 5.4"/></svg>' +
      esc(pick(b.author)) + '</span></span></a>';
  }
  function renderCats() {
    if (!CAT) return;
    var tabs = document.getElementById('tabs'), body = document.getElementById('cat-body');
    if (!tabs || !body) return;
    var cats = CAT.categories;
    if (!active || !cats.some(function (c) { return c.id === active; })) {
      var first = cats.filter(function (c) {
        return CAT.books.some(function (b) { return b.category === c.id; }); })[0];
      active = (first || cats[0]).id;
    }
    tabs.innerHTML = cats.map(function (c) {
      var n = CAT.books.filter(function (b) { return b.category === c.id; }).length;
      return '<button class="tab" role="tab" data-cat="' + esc(c.id) + '" aria-selected="' +
        (c.id === active) + '">' + esc(pick(c.name)) + ' <small>· ' + num(n) + '</small></button>';
    }).join('');
    var cat = cats.filter(function (c) { return c.id === active; })[0];
    var books = CAT.books.filter(function (b) { return b.category === active; });
    body.innerHTML = (cat && pick(cat.desc) ? '<p class="cat-desc">' + esc(pick(cat.desc)) + '</p>' : '') +
      (books.length ? '<div class="books">' + books.map(bookCard).join('') + '</div>'
                    : '<p class="empty-note">' + esc(t('noBooks')) + '</p>');
    Array.prototype.forEach.call(tabs.children, function (b) {
      b.addEventListener('click', function () { active = b.getAttribute('data-cat'); renderCats(); });
    });
    var st = document.getElementById('stats');
    if (st) {
      /* count what is actually readable, not what is announced */
      var live = CAT.books.filter(function (b) { return !b.placeholder; });
      var vols = live.reduce(function (a, b) {
        return a + ((b.volumesPublished && b.volumesPublished.length) || 1); }, 0);
      var pgs = live.reduce(function (a, b) { return a + (b.pages || 0); }, 0);
      st.innerHTML = [[live.length, 'statBooks'], [vols, 'statVolumes'], [pgs, 'statPages']]
        .map(function (p) {
          return '<div class="stat"><b>' + num(p[0]) + '</b><span>' + esc(t(p[1])) + '</span></div>';
        }).join('');
    }
  }
  function renderAll() {
    var box = document.getElementById('all-books');
    if (!box || !CAT) return;
    box.innerHTML = CAT.categories.map(function (c) {
      var books = CAT.books.filter(function (b) { return b.category === c.id; });
      if (!books.length) return '';
      return '<section class="sec"><div class="sec-h"><h2>' + esc(pick(c.name)) +
        '</h2><span>' + num(books.length) + ' ' + esc(t('books')) + '</span></div>' +
        '<div class="books">' + books.map(bookCard).join('') + '</div></section>';
    }).join('') || '<p class="empty-note">' + esc(t('noBooks')) + '</p>';
  }
  if (document.getElementById('tabs') || document.getElementById('all-books')) {
    load(CATURL).then(function (c) { CAT = c; renderCats(); renderAll(); })
      .catch(function () {
        var b = document.getElementById('cat-body') || document.getElementById('all-books');
        if (b) b.innerHTML = '<p class="empty-note">' + esc(t('loadFail')) + '</p>';
      });
  }

  /* ---------- search ---------- */
  function params() {
    var out = {};
    location.search.replace(/^\?/, '').split('&').forEach(function (kv) {
      if (!kv) return;
      var i = kv.indexOf('=');
      var k = decodeURIComponent(kv.slice(0, i < 0 ? kv.length : i).replace(/\+/g, ' '));
      out[k] = i < 0 ? '' : decodeURIComponent(kv.slice(i + 1).replace(/\+/g, ' '));
    });
    return out;
  }
  function goSearch(p) {
    var q = Object.keys(p).filter(function (k) { return p[k]; })
      .map(function (k) { return k + '=' + encodeURIComponent(p[k]); }).join('&');
    location.href = ROOT + '/search/?' + q;
  }
  function val(id) { var el = document.getElementById(id); return el ? el.value.trim() : ''; }
  function fillAdv() {
    var sb = document.getElementById('adv-book'), sc = document.getElementById('adv-cat');
    if (!CAT || (!sb && !sc)) return;
    if (sb) {
      var keepB = sb.value;
      sb.innerHTML = '<option value="">' + esc(t('anyBook')) + '</option>' +
        CAT.books.map(function (b) {
          return '<option value="' + esc(b.slug) + '">' + esc(pick(b.title)) + '</option>';
        }).join('');
      sb.value = keepB;
    }
    if (sc) {
      var keepC = sc.value;
      sc.innerHTML = '<option value="">' + esc(t('anyCat')) + '</option>' +
        CAT.categories.map(function (x) {
          return '<option value="' + esc(x.id) + '">' + esc(pick(x.name)) + '</option>';
        }).join('');
      sc.value = keepC;
    }
  }
  var homeForm = document.getElementById('home-search');
  if (homeForm) {
    homeForm.addEventListener('submit', function (e) {
      e.preventDefault();
      goSearch({ q: val('home-q'), 'in': document.getElementById('home-scope').value });
    });
    on('adv-toggle', 'click', function () {
      var a = document.getElementById('adv');
      a.setAttribute('data-open', a.getAttribute('data-open') === '1' ? '0' : '1');
    });
    on('adv-run', 'click', function () {
      goSearch({ all: val('adv-all'), phrase: val('adv-phrase'), any: val('adv-any'),
                 without: val('adv-not'), book: val('adv-book'), cat: val('adv-cat'), 'in': 'text' });
    });
    on('adv-clear', 'click', function () {
      ['adv-all','adv-phrase','adv-any','adv-not'].forEach(function (id) {
        var el = document.getElementById(id); if (el) el.value = '';
      });
    });
    load(CATURL).then(function (c) { CAT = c; fillAdv(); }).catch(function () {});
  }

  var resBox = document.getElementById('results');
  if (resBox) {
    var P = params();
    var qi = document.getElementById('res-input');
    if (qi) qi.value = P.q || P.phrase || P.all || P.any || '';
    var rf = document.getElementById('res-form');
    if (rf) rf.addEventListener('submit', function (e) {
      e.preventDefault();
      goSearch({ q: qi.value.trim(), 'in': document.getElementById('res-scope').value });
    });
    runSearch(P);
  }
  function tok(s) {
    return fold(s || '').text.split(/\s+/).filter(function (x) { return x.length > 1; });
  }
  function runSearch(P) {
    resBox.innerHTML = '<p class="empty-note">' + esc(t('searching')) + '</p>';
    var scope = P['in'] || 'text';
    load(CATURL).then(function (cat) {
      CAT = cat;
      var books = cat.books.filter(function (b) {
        return (!P.book || b.slug === P.book) && (!P.cat || b.category === P.cat);
      });
      if (scope === 'title' || scope === 'author') {
        var q = fold(P.q || '').text.trim();
        var hits = books.filter(function (b) {
          var o = scope === 'title' ? b.title : b.author;
          var hay = Object.keys(o).map(function (k) { return o[k]; }).join(' ');
          return fold(hay).text.indexOf(q) !== -1;
        });
        resBox.innerHTML = hits.length
          ? '<div class="books">' + hits.map(bookCard).join('') + '</div>'
          : '<p class="empty-note">' + esc(t('noResults')) + '</p>';
        return;
      }
      var phrase = fold(P.phrase || P.q || '').text.trim();
      var all = tok(P.all), any = tok(P.any), not = tok(P['without']);
      if (!phrase && !all.length && !any.length) {
        resBox.innerHTML = '<p class="empty-note">' + esc(t('minChars')) + '</p>'; return;
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
            if (phrase && txt.indexOf(phrase) === -1) return;
            if (all.length && !all.every(function (w) { return txt.indexOf(w) !== -1; })) return;
            if (any.length && !any.some(function (w) { return txt.indexOf(w) !== -1; })) return;
            var mark = phrase || all[0] ||
              any.filter(function (w) { return txt.indexOf(w) !== -1; })[0] || '';
            var at = mark ? txt.indexOf(mark) : 0, n = 0, i = 0;
            if (mark) { while ((i = txt.indexOf(mark, i)) !== -1) { n++; i += mark.length; } }
            out.push({ b: set.book, row: row, at: Math.max(0, at), n: n, mark: mark });
          });
        });
        if (!out.length) {
          resBox.innerHTML = '<p class="empty-note">' + esc(t('noResults')) + '</p>'; return;
        }
        out.sort(function (x, y) { return y.n - x.n; });
        resBox.innerHTML = '<p class="empty-note">' + num(out.length) + ' · ' +
          esc(t('results')) + '</p>' + out.slice(0, 300).map(function (h) {
          var s = Math.max(0, h.at - 50);
          var snip = h.row.t.slice(s, Math.min(h.row.t.length, h.at + 60));
          var part = h.row.part && (h.row.part[lang] || h.row.part.ar) || '';
          return '<a class="res" href="' + ROOT + '/' + h.row.href +
            (h.mark ? '?q=' + encodeURIComponent(h.mark) : '') + '"><span class="res-h">' +
            esc(pick(h.b.title)) + ' · ' + esc(part) + ' · ' + esc(t('page')) + ' ' +
            num(h.row.p) + (h.n ? ' · ' + num(h.n) + ' ' + esc(t('occurrences')) : '') +
            '</span><span class="res-t">…' + (marked(snip, h.mark) || esc(snip)) +
            '…</span></a>';
        }).join('');
      });
    }).catch(function () {
      resBox.innerHTML = '<p class="empty-note">' + esc(t('loadFail')) + '</p>';
    });
  }

  /* ---------- reading page ---------- */
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
    var fm = document.querySelector('mark');
    if (fm) fm.scrollIntoView({ block: 'center' });
  }

  function openDrawer(title) {
    var d = document.getElementById('drawer');
    d.setAttribute('data-open', '1'); d.setAttribute('aria-hidden', 'false');
    if (scrim) scrim.setAttribute('data-open', '1');
    document.getElementById('drawer-title').textContent = title;
    return document.getElementById('drawer-body');
  }
  on('drawer-close', 'click', closeAll);
  on('btn-toc', 'click', function () {
    var body = openDrawer(t('contents'));
    body.innerHTML = '<p class="note-msg">' + esc(t('searching')) + '</p>';
    load(BOOK + '/assets/toc.json').then(function (toc) {
      body.innerHTML = toc.map(function (x) {
        var label = (lang !== 'ar' && x[lang]) ? x[lang] : x.title;
        return '<a class="toc-i" href="' + ROOT + '/' + x.href + '"><span>' +
          (x.p == null ? '—' : num(x.p)) + '</span><span style="flex:1">' +
          esc(label) + '</span></a>';
      }).join('') || '<p class="note-msg">—</p>';
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
          var part = h.row.part && (h.row.part[lang] || h.row.part.ar) || '';
          return '<a class="hit" href="' + ROOT + '/' + h.row.href + '?q=' +
            encodeURIComponent(raw) + '"><span class="hit-p">' + esc(part) + ' · ' +
            esc(t('page')) + ' ' + num(h.row.p) + ' · ' + num(h.n) + ' ' +
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
    var text = (el.getAttribute('data-cite-' + lang) || el.getAttribute('data-cite-ar')) +
      ' ' + location.href.split('?')[0];
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
    else if (e.key === 'Escape') closeAll();
    else if (e.key === '/') {
      var b = document.getElementById('btn-search') || document.getElementById('home-q');
      if (!b) return;
      e.preventDefault();
      if (b.id === 'btn-search') b.click(); else b.focus();
    }
  });

  /* ---------- body translation layer ----------
     Pages ship as Arabic. When a reader picks another language we look for a
     translation file for this book and swap in whatever exists, block by block.
     Nothing translated yet simply stays Arabic, and the page says so. */
  var TRVIEW = store.get('trview') || 'tr';   /* tr | both | ar */
  function blocks() { return document.querySelectorAll('.body [data-i]'); }
  function clearTr() {
    each('.tr-line', function (el) { el.parentNode.removeChild(el); });
    each('.tr-note-line', function (el) { el.parentNode.removeChild(el); });
    each('.body [data-i]', function (el) { el.hidden = false; });
    var b = document.getElementById('tr-bar');
    if (b) b.parentNode.removeChild(b);
  }
  function setMode(m) {
    TRVIEW = m; store.set('trview', m);
    each('#tr-bar [data-mode]', function (b) {
      b.setAttribute('aria-pressed', String(b.getAttribute('data-mode') === m));
    });
    /* 'side' shows both texts, laid out in two columns */
    each('.body [data-i]', function (el) { el.hidden = (m === 'tr'); });
    each('.tr-line', function (el) { el.hidden = (m === 'ar'); });
    each('.tr-note-line', function (el) { el.hidden = (m === 'ar'); });
    each('.aya', function (el) { el.classList.toggle('side', m === 'side'); });
  }
  function wireModes() {
    var bar = document.getElementById('tr-bar');
    if (!bar) return;
    each('#tr-bar [data-mode]', function (b) {
      b.addEventListener('click', function () { setMode(b.getAttribute('data-mode')); });
    });
    setMode(TRVIEW);
  }
  /* pages served under /en/ /fa/ /ur/ already carry both texts */
  if (document.querySelector('[data-tr-static]')) { wireModes(); }

  function applyTranslation() {
    if (document.querySelector('[data-tr-static]')) return;
    if (!document.querySelector('.body') || !meta) return;
    clearTr();
    if (lang === 'ar') return;
    var slug = meta.getAttribute('data-slug');
    var page = meta.getAttribute('data-pagenum');
    load(BOOK + '/assets/tr/' + lang + '.json').then(function (tr) {
      var rows = tr[page] || [];
      var head = document.createElement('div');
      head.id = 'tr-bar';
      head.className = 'tr-bar';
      if (!rows.length) {
        head.innerHTML = '<span class="tr-note">' + esc(t('noTr')) + '</span>';
      } else {
        head.innerHTML = '<div class="tr-modes">' +
          ['tr','both','ar'].map(function (m) {
            var lbl = m === 'tr' ? 'viewTr' : (m === 'both' ? 'viewBoth' : 'viewAr');
            return '<button data-mode="' + m + '" aria-pressed="' + (TRVIEW === m) + '">' +
                   esc(t(lbl)) + '</button>';
          }).join('') + '</div>' +
          (tr._meta && tr._meta.machine
            ? '<span class="tr-note machine"><svg class="ic" viewBox="0 0 24 24">' +
              '<path d="M12 3v2M5 8h14v11H5z"/><circle cx="9" cy="13" r="1.2"/>' +
              '<circle cx="15" cy="13" r="1.2"/></svg>' + esc(t('machineTr')) + '</span>'
            : (tr._meta && tr._meta.reviewed === false
               ? '<span class="tr-note draft">' + esc(t('draft')) + '</span>' : '')) +
          '';
      }
      var leaf = document.querySelector('.body');
      leaf.parentNode.insertBefore(head, leaf);
      Array.prototype.forEach.call(head.querySelectorAll('[data-mode]'), function (b) {
        b.addEventListener('click', function () { setMode(b.getAttribute('data-mode')); });
      });
      if (!rows.length) return;
      rows.filter(function (r) { return r.n != null; }).forEach(function (r) {
        var note = document.querySelector('.note[id$="-' + r.n + '"] span:last-child');
        if (!note || note.querySelector('.tr-note-line')) return;
        var sp = document.createElement('span');
        sp.className = 'tr-note-line';
        sp.setAttribute('lang', lang);
        sp.textContent = r.text;
        note.appendChild(sp);
      });
      rows.filter(function (r) { return r.i != null; }).forEach(function (r) {
        var el = document.querySelector('.body > [data-i="' + r.i + '"]');
        if (!el) return;
        var p = document.createElement(el.tagName === 'H3' ? 'h3' : 'p');
        p.className = 'tr-line';
        p.setAttribute('lang', lang);
        p.setAttribute('dir', RTL[lang] ? 'rtl' : 'ltr');
        if (r.h) {
          var tag = document.createElement('span');
          tag.className = 'h-num';
          tag.textContent = num(r.h);
          p.appendChild(tag);
        }
        p.appendChild(document.createTextNode(r.text));
        el.parentNode.insertBefore(p, el.nextSibling);
      });
      setMode(TRVIEW);
    }).catch(function () {
      var leaf = document.querySelector('.body');
      var head = document.createElement('div');
      head.id = 'tr-bar'; head.className = 'tr-bar';
      head.innerHTML = '<span class="tr-note">' + esc(t('noTr')) + '</span>';
      leaf.parentNode.insertBefore(head, leaf);
    });
  }
  /* Qur'an: the verse picker scrolls to an ayah and lets :target mark it, so
     browsing to a verse and arriving from a shared link look identical */
  (function () {
    var vs = document.getElementById('vsel');
    if (!vs) return;
    vs.addEventListener('change', function () {
      var id = 'a' + vs.value;
      location.hash = '#' + id;
      var el = document.getElementById(id);
      if (el) el.scrollIntoView({ block: 'center' });
    });
  })();


  /* ---------- Qur'an: script choice and per-verse copy ---------- */
  (function () {
    var qbody = document.querySelector('.body[data-unit="aya"]');
    if (!qbody) return;

    /* --- which Arabic face --- */
    function setFont(f) {
      store.set('qfont', f);
      qbody.setAttribute('data-font', f);
      each('.fontpick button', function (b) {
        b.setAttribute('aria-pressed', String(b.getAttribute('data-font') === f));
      });
    }
    each('.fontpick button', function (b) {
      b.addEventListener('click', function () { setFont(b.getAttribute('data-font')); });
    });
    setFont(store.get('qfont') || 'uthmani');

    /* --- copy a verse, with the reader choosing what goes on the clipboard --- */
    var DEF = { ar: 1, tr: 1, ref: 1, link: 0 };
    function prefs() {
      try { return JSON.parse(store.get('qcopy')) || DEF; } catch (e) { return DEF; }
    }
    function textOf(el, dropSel) {
      if (!el) return '';
      var c = el.cloneNode(true);
      Array.prototype.forEach.call(c.querySelectorAll(dropSel), function (x) {
        x.parentNode.removeChild(x);
      });
      return c.textContent.replace(/\s+/g, ' ').trim();
    }
    function closePop() {
      var old = document.querySelector('.copy-pop');
      if (old) old.parentNode.removeChild(old);
    }
    document.addEventListener('click', function (e) {
      if (!e.target.closest('.copy-pop') && !e.target.closest('.aya-copy')) closePop();
    });

    each('.aya-copy', function (btn) {
      btn.addEventListener('click', function (e) {
        e.stopPropagation();
        var aya = btn.closest('.aya');
        if (aya.querySelector('.copy-pop')) { closePop(); return; }
        closePop();
        var pr = prefs();
        var pop = document.createElement('div');
        pop.className = 'copy-pop';
        pop.innerHTML =
          [['ar', t('viewAr')], ['tr', t('viewTr')],
           ['ref', t('copyRef')], ['link', t('copyLink')]]
          .map(function (r) {
            return '<label><input type="checkbox" data-k="' + r[0] + '"' +
                   (pr[r[0]] ? ' checked' : '') + '>' + esc(r[1]) + '</label>';
          }).join('') +
          '<button class="go">' + esc(t('copyDo')) + '</button>';
        aya.appendChild(pop);

        pop.querySelector('.go').addEventListener('click', function () {
          var picked = {};
          each('.copy-pop input', function (i) { picked[i.getAttribute('data-k')] = i.checked ? 1 : 0; });
          store.set('qcopy', JSON.stringify(picked));

          var out = [];
          if (picked.ar) out.push(textOf(aya.querySelector('p[lang="ar"]'), '.aya-n'));
          if (picked.tr) {
            Array.prototype.forEach.call(aya.querySelectorAll('.tr-line'), function (l) {
              out.push(textOf(l, '.aya-b'));
            });
          }
          if (picked.ref) {
            var nm = document.querySelector('.sura-name');
            out.push((nm ? nm.textContent.trim() + ' ' : '') + aya.getAttribute('data-ref'));
          }
          if (picked.link) {
            out.push(location.origin + location.pathname + '#' + aya.id);
          }
          var text = out.join('\n');
          function done() {
            btn.classList.add('done');
            setTimeout(function () { btn.classList.remove('done'); }, 1400);
            closePop();
          }
          if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(done, done);
          } else {
            var ta = document.createElement('textarea');
            ta.value = text; document.body.appendChild(ta); ta.select();
            try { document.execCommand('copy'); } catch (err) {}
            document.body.removeChild(ta); done();
          }
        });
      });
    });
  })();

  var _applyLang = applyLang;
  applyLang = function () { _applyLang(); applyTranslation(); };

  applyLang();
})();
