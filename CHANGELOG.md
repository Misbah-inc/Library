# Changelog

Changes to the Misbah Library website. One entry per session, most recent first.

---

## 2026-09-06 (session 8, part 27)

### Tashḷīl rounds 32–36 — شرح التصریف: 259 / 511 (50.7%)

**492 blocks · 63,961 marks · 492/492 text-preserving.** Half the treatise is done.

Covered الادغام end to end — its definition, where it is واجب (مدّ يمدّ · أعدّ · انقدّ ·
اعتدّ · اسودّ · اطمأنّ), where it is ممتنع (before the متحرّک pronoun endings, مددت …
مددتنّ), and where it is جایز (after a جازم) — then فصل فی المعتلّ: the three حروف علة,
مد vs لین, and the مثال in both its واوی and یائی forms down to یدع/یذر and their dead past
tenses.

The pair to check on this stretch is the جازم section, where the same verb takes three
different endings depending on its عین:

```
1:346:0  لَمْ یَفِرَّ   (مکسور العين)      1:347:0  لَمْ یَفْرِرْ   بفكّ الإدغام
1:346:0  لَمْ یَعَضَّ   (مفتوح العين)      1:347:0  لَمْ یَعْضَضْ   بفكّ الإدغام
1:348:0  لَمْ یَمُدَّ   (مضموم العين, three vowels admissible)
```

### One warning, correctly raised, correctly dismissed

The harness flagged `یَکُ` in `1:345:0` as marks on a Persian word. It is the apocopated
يكن in a line of Arabic verse (وَ مَنْ یَکُ ذَا فَضْلٍ), and Persian یک is "one" — a real
homograph, not a mistake. Added to `ARABIC_HOMOGRAPHS` in `jame_tashkil_check.py`, which
is where the earlier کرد/کان collisions already live. The list stays deliberately short:
each entry is a word the check must stop asking about, not a word the check was wrong to
notice.

### Seven refusals across the five rounds, five of them the same mistake

| block | printed | I wrote |
|---|---|---|
| `1:338:0` | ادرجتها | ادرجت — dropped the pronoun |
| `1:342:1` | یائه | یاؤه |
| `1:350:1` | یذکر | یذکره — added a pronoun |
| `1:357:0` | فائه | فاؤه |
| `1:363:0` | ایجل | اوجل |
| `1:366:0` | فائهما | فاءهما |

The `ایجل` one is instructive. The sentence reads و تقول یا زید ایجل تلفظ بالواو —
"say *āĩjal*, pronouncing the wāw" — and the next four lines explain at length *why* the
word is spelled with yāʾ even though a wāw is heard. I rewrote it with the wāw, which
would have deleted the paragraph's entire subject. Reading it and copying it are separate
skills; only the applier tests the second one.

Counting the hamza-seat cases from the previous rounds, `ء` → `ؤ` on a medial hamza is now
eight refusals and by a wide margin the most frequent failure. It is a house spelling of
this edition, not an error.

**Pending in this treatise: 252 blocks.**

---

## 2026-09-06 (session 8, part 26)

### Tashḷīl rounds 26–31 — شرح التصریف: 209 / 511 (40.9%)

**442 blocks · 52,964 marks · 442/442 text-preserving.**

Six rounds without stopping. Covered لام الأمر and لاء الناهیة, the two tāʾs of
تفعّل/تفاعل, افتعل assimilation in full (اصطلح · اضطرب · اطّرد · اظطلم · ادّرأ · ازدجر),
the two نون التأکید and التقاء الساکنین, the ناقص forms (لا تخشونّ · لا تخشینّ · لتبلونّ),
اسم الفاعل and المفعول of both the bare and the augmented verb, and the opening of
فصل فی المضاعف. **Eight more Qur'anic verses** spliced from the source rather than retyped
(Yūsuf 12:45, Qamar 54:9, Yūnus 10:89, Nūr 24:62, Isrāʾ 17:42, Anʿām 6:162, Isrāʾ 17:36, Wāqiʿa 56:65).

The pair worth checking on this stretch is اسم الفاعل against اسم المفعول, since the
whole section turns on one vowel:

```
1:326:1  مُکْرِم · مُدَحْرِج · مُتَدَحْرِج · مُسْتَخْرِج      اسم الفاعل (kasra)
1:326:1  مُکْرَم · مُدَحْرَج · مُتَدَحْرَج · مُسْتَخْرَج      اسم المفعول (fatha)
```

### The applier refused nine entries across the six rounds

None of them reached disk. Every one is the same instinct — writing the standard form
instead of the printed one:

| block | printed | I wrote |
|---|---|---|
| `1:300:0` | فاعل | فوعل — added the wāw the passive pattern wants |
| `1:301:0` | تائه | تاؤه — moved the hamza to its "correct" seat |
| `1:304:1` | تائه | تاؤه — same, one page later |
| `1:328:0` | الاخرین | الاخیرین — added a ی (twice in one block) |
| `1:331:0` | فائه | فاؤه — the hamza seat again |
| `1:336:1` | مست | مسست — restored the doubled sīn |

The last one is the sharpest. That block is *about* مست being the contracted form — the
source says so in the same sentence — and I still expanded it back. Reading the passage
correctly and copying it correctly turn out to be separate skills, which is the whole
argument for validating before writing rather than reviewing after.

The `تائه` → `تاؤه` correction fired three times in six rounds. It is now the most
frequent single failure and worth naming: this export seats medial hamza on **yāʾ** where
modern orthography would use **wāw**, and that is a spelling of the edition, not an error
to fix.

### Splicing by anchor, not by typing

Round 27 stalled on a regex that tried to locate a verse by typing its opening words —
which cannot match, because the source's combining-mark order differs from what NFC
produces. Replaced throughout by a `runs()` helper that scans for maximal spans already
carrying diacritics and returns them verbatim, so a verse is located by *where the
vocalisation already is* rather than by what I think it says. Rounds 28–31 use it.

**Pending in this treatise: 302 blocks.**

---

## 2026-09-06 (session 8, part 25)

### Tashkīl rounds 24–25 — شرح التصریف: 133 / 511 (26.0%)

**366 blocks · 37,935 marks · 366/366 text-preserving.**

Covered الحال/الاستقبال, السین و سوف, لام الابتداء, the مضارع prefix vowel and why it is
damma for the four-letter past, أهراق/أسطاع as the exception, المبني للمفعول of the
مضارع, الجوازم, النواصب, and لام الأمر. **Six Qur'anic verses** spliced in these two rounds
(Yūsuf 12:13, Ḍuḥā 93:5, Maryam 19:66, Sajda 32:25, Tawba 9:82, Ḥajj 22:29).

The verification that matters here is the active/passive pair. The same twenty verbs appear
in `1:279:0` as actives and `1:279:1` as passives, and each list has to hold its own shape:

```
1:279:0  یُدَحْرِجُ · یُقَاتِلُ · یُکْرِمُ · یُفَرِّحُ · یَسْتَخْرِجُ      active
1:279:1  یُدَحْرَجُ · یُقَاتَلُ · یُکْرَمُ · یُفَرَّحُ · یُسْتَخْرَجُ      passive
```

A single misplaced fatha would silently flip a verb between the two lists the text is
contrasting. Also checked: jussive after لم (لَمْ یَنْصُرْ / یَنْصُرَا / یَنْصُرُوا / تَنْصُرِی)
against subjunctive after لن (لَنْ یَنْصُرَ).

### Batch size doubled

Rounds 24–25 took 14 blocks each rather than 9, by cutting narration rather than care —
every entry still passes the applier and the harness, and round 24 was clean on first pass.
Four more catches in round 25, none reaching disk:

| printed | I wrote |
|---|---|
| تمیز | تمییز — added a ی |
| یفعلل | یفعللل — added a ل |

**Pending in this treatise: 378 blocks.**

---

## 2026-09-06 (session 8, part 24)

### Tashkīl rounds 22–23 — شرح التصریف: 105 / 511 (20.5%)

**338 blocks · 32,967 marks · 338/338 text-preserving.**

Covered المبني للفاعل and its pronoun suffixes (why the tāʾ is damma for the speaker,
fatha for the male addressee, kasra for the female), hamzat al-waṣl, المبني للمفعول in
full, and the four مضارع prefixes with the reasoning for each. Yūsuf 12:65 (رُدَّتْ إِلَیْنٰا)
spliced from the source.

The passive section reads as passive throughout — فُعِلَ · فُعْلِلَ · اُفْعِلَ · فُوعِلَ ·
تُفُعِّلَ · تُفُوعِلَ · افْتُعِلَ, with ضُرِبَ زَیْدٌ, قُتِلَ الْخَارِجِیُّ and اُسْتُخْرِجَ الْمَالُ
following suit.

### The applier caught five more, none of which reached disk

| block | printed | I wrote |
|---|---|---|
| `1:254:0` | متعد | معتد — **transposed** ت and ع |
| `1:262:0` | قلب | قلبت — added a ت |
| `1:263:0` | الاخر | الاخیر — added a ی |
| `1:264:0` | الاخر | الاخیر — same |
| `1:242:0` | تفعل | تفعلل — added a ل |

The متعد → معتد transposition is a new failure mode: معتد ("counted") actually reads
*better* in context than the printed متعد, so it is exactly the kind of silent improvement
that would never be questioned. Same instinct as راؤن and الان, arriving by a different route.

### The Persian word list keeps shrinking, and that is the right direction

`هُمُ` was flagged — Arabic "they" with its linking damma before hamzat al-waṣl, but هم is
also Persian for "also". Removed, joining یعنی and وجه. Every one of these was an Arabic
word Persian borrowed, so inside an Arabic commentary the tell fires on correct text.

The list is now doing much less work than the **tanwīn rule**, which is principled rather
than enumerated: Persian has no case endings, so ً ٍ ٌ marks a word as Arabic outright.
Re-proved after each removal that a genuine slip (vowelling Persian بَاشَد) is still caught.

**Pending in this treatise: 406 blocks.**

---

## 2026-09-06 (session 8, part 23)

### Tashkīl rounds 19–21 — شرح التصریف: 87 / 511

**320 blocks · 28,265 marks · 320/320 text-preserving.**

Covered فعّل / فاعل / تفعّل / تفاعل / انفعل / افتعل / افعلّ and their senses, the
six-letter أبواب, transitivity and حروف الجر (the Mubarrad–Sībawayh disagreement over the
transitive bāʾ), and the definition of الماضی.

### New: `jame_tashkil_apply.py` — validate before writing, not after

The same error kept recurring — writing the *standard* form of a word instead of the
printed one:

```
الان   → الآن      an alef given a madda
راؤن   → راؤون     a wāw supplied
قید    → قیدت      a tāʾ supplied for feminine agreement
بالاخر → بالآخر    the madda again
```

Every one is me knowing better than the page, and none is visible on screen.
`jame_tashkil_check.py` caught them, but only *after* the entry was written and 1,216 pages
rebuilt. The new applier validates each entry against the source first and writes **nothing**
if any entry fails, printing the exact divergence. Proven by deliberately feeding it the
madda error: exit 1, nothing written.

It earned itself immediately — three catches in two rounds, none of which reached disk:

| block | printed | I wrote |
|---|---|---|
| `1:242:0` | تفعل | تفعلل — added a ل (the context implies تفعلل, but the page prints تفعل) |
| `1:243:1` | فارتددت | فارتدت — dropped a د |
| `1:249:0` | لللازم | للازم — the source prints **three** ل; لِلَّازِمِ writes the doubled lām as a shadda and so has only two |

That last one is worth keeping: a shadda is a *mark*, so لِلَّازِمِ and لِلْلَازِمِ look almost
alike but differ by a letter. Doubling written as shadda vs written out is exactly the kind
of difference the strip-back invariant exists to police.

**Pending in this treatise: 424 blocks.**

---

## 2026-09-06 (session 8, part 22)

### Tashkīl rounds 16–18 — شرح التصریف: 57 / 511

**290 blocks · 23,302 marks · 290/290 text-preserving.**

Covered the Kufan objection on مصدر vs فعل, the eight-fold سالم/غیر سالم division, the
مضارع vowel rule with its throat-letter exception, أبى یأبى as شاذ, dialect variants
(بنی عامر, طیّ), and the senses of أفعل.

This stretch is dialectical prose, where the person and mood carry the argument:

```
فان قلت … قلت        2ms then 1s   قُلْتَ … قُلْتُ
لانا نقول            1p            نَقُولُ
لئلا یؤدی / یلزم     نصب            یُؤَدِّیَ · یَلْزَمَ
لیقاوم               لِ of purpose  یُقَاوِمَ
فاخذ / فاختیر /      passive        اُخِذَ · اخْتِیرَ · اشْتُقَّ · فُتِحَ
  اشتق / فتح
```

Four Qur'anic verses spliced so far in this treatise (Kahf 18:108, Ḥajj 22:15, Tawba 9:32).

### Three more single-character catches

| block | printed | I wrote |
|---|---|---|
| `1:215:0` | قید | قیدت — **added** a ت, imposing feminine agreement |
| `1:221:0` | …اللّٰه ─ | …اللّٰه  ─ — an extra space beside the spliced verse |
| `1:223:0` | …نوره ─ | …نوره  ─ — same |

The قید case is the same class as راؤن: a broken plural can take masculine agreement, so
the printed قید الحروف is correct and my "fix" was the error.

The two spacing faults were **caused by the splice itself** — the captured verse already
carries its trailing space, and I added another. Splicing must reproduce the source's own
delimiters, not re-punctuate around them.

Verified on p.223: verse renders (matched under NFC, since the stored bytes keep the
source's combining order), passives intact, toggle and page features working.

**Pending in this treatise: 454 blocks.**

---

## 2026-09-06 (session 8, part 21)

### Tashkīl round 15 — کتاب شرح التصریف begun: the خطبة and the definition

**262 blocks · 18,276 marks · 262/262 text-preserving.**

Taftāzānī's commentary opens in rhymed prose, where the case endings *are* the rhyme, so
getting them right is what makes it scan: نِقَابَهُ / غَوَامِضِهِ / حَامِضِهِ, then
شَرِیفَهً / لَطِیفَهً, then الْفَاتِرُ / الْقَاصِرُ / الْقَادِرِ. Verified on the page.

Kahf 18:108 (لاٰ یَبْغُونَ عَنْهٰا حِوَلاً) spliced from the source, byte-identical.

**Printed hamza spellings kept, not standardised** — the source writes بدء, یدرء, قراته,
براسها, and each survives stripping: بَدَءَ not بَدَاَ, یَدْرَءَ not یَدْرَاَ. This is the
same trap as راؤن and الان in earlier rounds, so it is now checked explicitly.

### The Persian check, made principled instead of a growing list

`وَجْهٍ` was flagged as Persian — the fourth homograph after بِهِ, یَا, اَیْنَ. Rather than
keep appending to an allowlist, added a rule that settles the whole class:

> **Tanwīn is Arabic inflection and nothing else.** Persian has no case endings, so a word
> carrying ً ٍ ٌ is Arabic whatever its bare form looks like.

Then removed **یعنی** and **وجه** from the Persian word list entirely. Both are Arabic words
Persian borrowed, so inside an Arabic commentary they fire on correct text — یَعْنِی here is
the verb governing أنّ, not the Persian particle. A tell that is wrong more often than right
is worse than no tell at all.

Proved the check still works after loosening it: vowelling a genuine Persian word without
altering a letter (کمتر بَاشَد) is still caught.

**شرح التصریف: 29 / 511.** 482 blocks and ~143,000 characters remain in this treatise alone.

---

## 2026-09-06 (session 8, part 20)

### Tashkīl round 14 — **کتاب التصریف complete, 80/80**

All 24 remaining blocks in one pass: الناقص's مضارع, imperative and participles, both
kinds of لفیف, المهموز, أسماء الزمان والمکان, and المرّة/الفعلة.

**246 blocks · 15,915 marks · 246/246 text-preserving. Second treatise finished.**

Checks that held:

```
Qur'anic verse (Ṭā-Hā 20:132)  spliced from source, byte-identical
اسماء الزمان/المکان follow the ع vowel:  مَجْلِس (kasra) · مَذْهَب (fatha)
                       معتل الفاء always kasra (مَوْعِد), معتل اللام always fatha (مَرْمَی)
```

`1:186:0` also settles the قین/قن forms that **round 6 deliberately skipped**. With the
surrounding context here — "و الامر منه ق … و تقول فی التاکید" — they are unambiguously the
emphatic imperative of وقى: قِیَنَّ قِیَانِّ قُنَّ قِنَّ قِیَانِّ قِینَانِّ, light قِیَنْ قُنْ قِنْ.
Leaving that gap rather than guessing was the right call; the answer arrived with context.

### Four single-character errors, all caught by the harness

None would have been visible on the page:

| block | printed | I wrote |
|---|---|---|
| `1:185:1` | رضیا | رضی — dropped an alef |
| `1:185:1` | احیی | احی — dropped a yāʾ |
| `1:189:0` | راؤن | راؤون — **added** a wāw |
| `1:189:0` | ارائه | اراءه — wrote ء where the source has ئ |

The راؤن case is the instructive one: the standard plural of رَاءٍ *is* راؤون, so I
"corrected" the page without noticing. Same failure mode as الان→الآن in round 8. The
printed text wins every time.

**Left bare on purpose:** ایا and ایو in `1:188:0` — compressed imperatives from وأى and
أوى whose vowels I cannot fix with confidence.

### Two verification artifacts worth not chasing

- Searching the rendered page for the Qur'anic verse fails on an exact match but succeeds
  under NFC — because the stored text keeps the source's combining order, which is the
  whole point. Compare normalised when checking, never store normalised.
- The toggle-off text still contains diacritics, so a "no marks when off" assertion fails.
  Correct: the printed source already carried the verse's marks. Assert that the two
  strings *differ*, not that one is bare.

**Pending: 1,986 blocks.** Next: کتاب آداب المتعلمین (70 blocks / 14,801 chars).

---

## 2026-09-06 (session 8, part 19)

### Tashkīl rounds 12–13 — التصریف: المثال, الأجوف, الناقص

**222 blocks · 12,377 marks · 222/222 text-preserving. کتاب التصریف is 56 of 80.**

Round 12 took المعتل and المثال — where the whole point is which مضارع keeps the wāw:
وَعَدَ **یَعِدُ** drops it, وَجِلَ **یَوْجَلُ** and وَجُهَ **یَوْجُهُ** keep it — and the أجوف
paradigm, whose 14 forms split by root: صُنْتُ from the wāwī, بِعْتُ from the yāʾī, with
both passives taking kasra (صِینَ, بِیعَ) exactly as the text says.

Round 13 took the أجوف jussive and imperative, its مزید, and الناقص.

`1:182:0` is the clearest case yet of the text auditing its own vocalisation. It *explains*
why its examples carry the vowels they do — "فان انفتح ما قبلها ابقی علی الفتحه و ان انضم
او انکسر ضم" — so غَزَوْا and رَمَوْا must keep a fatha while رَضُوا and سَرُوا take a damma,
and it even gives the underlying رَضِیُوا it derives رَضُوا from. All five present.

The export's proper-name markers (a leading `؟` and trailing `"` around سیبویه, ابی الحسن
الاخفش, بنو تمیم) are structure rather than text, so they are kept byte-for-byte with the
names inside them vowelled.

Two check artifacts worth not chasing again: a paradigm count came out 15 instead of 14
because صَانَ and بَاعَ each appear once in "نحو صان و باع" before their run begins; and a
substring test flagged `لِیَنْصُرُ` as an indicative when it was only matching inside
`لِیَنْصُرُوا`. Both were the check being naive, not the text being wrong — word-boundary
matching settles both.

---

## 2026-09-06 (session 8, part 18)

### Tashkīl round 11 — التصریف: participles, المضاعف, إدغام

**207 blocks · 9,827 marks · 207/207 text-preserving. کتاب التصریف is 41 of 80.**

The participle rule the text states — "تکسر ما قبل آخره فی اسم الفاعل و تفتحه فی اسم
المفعول" — checked on its own examples, which must differ in exactly that one vowel:
مُکْرِمٍ/مُکْرَمٍ · مُدَحْرِجٍ/مُدَحْرَجٍ · مُسْتَخْرِجٍ/مُسْتَخْرَجٍ.

`1:175:0` restates its verb list twice — once active, once after "اذا بنیتها للمفعول". The
second run therefore had to come out passive: مَدَّ یَمُدُّ → مُدَّ یُمَدُّ, اَعَدَّ یُعِدُّ →
اُعِدَّ یُعَدُّ, انْقَدَّ یَنْقَدُّ → انْقُدَّ یُنْقَدُّ. Both runs verified separately.

`1:176:0`: لم forces the jussive, and with a doubled verb the text allows both إدغام and
فكّ — لَمْ یَفِرَّ / لَمْ یَفْرِرْ, لَمْ یَمُدَّ / لَمْ یَمْدُدْ. Both present.

Two catches this round, both from the harness rather than from reading:

- **`1:175:0` lost its trailing `─` block separator.** One character, invisible in the
  rendered page, and it would have quietly changed how the block joins its neighbour.
- **`کَرَدَّ` flagged as Persian** — كَـ + رَدَّ, "like *radda*", colliding with Persian کرد
  ("did"). Added to the homograph allowlist with کَانَ (vs Persian کان, "mine"), keyed to
  the vocalised form as before.

---

## 2026-09-06 (session 8, part 17)

### Tashkīl rounds 9–10 — التصریف: passive مضارع, jussive, imperative, emphatic nūn

**198 blocks · 8,412 marks · 198/198 text-preserving.**

Round 9 covered the passive مضارع (یُنْصَرُ یُدَحْرَجُ یُکْرَمُ یُقَاتَلُ یُفَرَّحُ یُسْتَخْرَجُ — each
with the damma-on-prefix, fatha-before-last that the text itself specifies), the ناصب
(لَنْ یَنْصُرَ, nūns dropped), lām al-amr as a **jāzim** (لِیَنْصُرْ, sukūn — the same jussive
trap that defeated the mechanical pass in round 4, here with the particle explicit), and the
imperative's waṣl hamza copying the ع vowel: اُنْصُرْ but اضْرِبْ.

Round 10 covered the doubled tāʾ, افتعل assimilation (اصْطَلَحَ · اضْطَرَبَ · اطَّرَدَ; ادَّرَءَ ·
اذَّکَرَ · ازْدَجَرَ), and the emphatic nūn heavy and light.

### A new class of error found — and now permanently guarded

The Qur'anic quotations are already vocalised in the source. I said I was copying them
verbatim. I was not:

```
source : ز + shadda U+0651 + fatha U+064E      ← as printed
mine   : ز + fatha  U+064E + shadda U+0651     ← what retyping produces
NFC(source) == NFC(mine) → True
```

Canonically equivalent, pixel-identical, different bytes. The strip-back invariant could
never catch it — stripping removes both marks whatever their order. For scripture,
"renders the same" is not the standard.

`jame_tashkil_check.py` gained a check for it: **any run in the source that already carried
two or more marks must appear unchanged in the output.** It immediately found a second
instance I had missed — `1:167:0`, the Yūsuf verse from round 8 — and a deliberate
re-introduction of the bug makes it exit 1, so the guard is proven rather than assumed.

Both verses are now spliced from the source rather than retyped. The lesson is in the
check's comment: **splice pre-vocalised spans, never retype them.**

> A second-order trap while fixing it: `mine.find("إِنّ")` returns −1, because in the
> NFC-ordered copy the shadda sits after the kasra, so the marked substring does not match.
> That silently made `mine[:-1] + verse`, duplicating the verse. Anchor on an unmarked
> codepoint instead.

Verified on p.170: 3/3 Qur'anic verses render, اُنْصُرْ/اضْرِبْ correct, toggle and page intact.

**Pending: 2,164 blocks.** التصریف is 28 of 80.

---

## 2026-09-06 (session 8, part 16)

### Tashkīl round 8 — التصریف: six-letter أبواب, transitivity, the passive, the مضارع

**185 blocks · 6,881 marks · 185/185 text-preserving.**

### The harness caught me altering the text

Round 8 failed its first check — `1:166:1` changed a letter rather than only adding marks:

```
printed : تقول یفعل الان و یسمی…     ا  U+0627  plain alef
mine    : تقول یفعل الآن و یسمی…     آ  U+0622  alef with madda
```

I had silently "corrected" the source's الان to the standard الآن. That is editing the
text, not vocalising it — precisely the failure the strip-back invariant exists to catch,
and it would have been invisible on screen, in a diff, and to me. Reverted to الْانَ; the
printed orthography stands even where it departs from the standard spelling.

### Reasoning worth keeping

**1:166:0 is the passive section**, not a repeat of the active أبواب. The text says so —
"ما کان اوله مضموما", *what has a damma on its first letter* — so the list is فُعِلَ,
فُعْلِلَ, اُفْعِلَ, فُعِّلَ, فُوعِلَ, تُفُعِّلَ, تُفُوعِلَ, تُفُعْلِلَ, افْتُعِلَ, اسْتُفْعِلَ, and its own
examples follow: نُصِرَ زَیْدٌ, اسْتُخْرِجَ الْمَالُ. Reading the section heading is what settles
ten forms at once.

**لم يتجاوز الفاعل → لَمْ یَتَجَاوَزِ الْفَاعِلَ.** لم forces the jussive; the resulting sukun
then takes kasra before the article's hamzat al-waṣl.

**The Qur'anic verse in 1:167:0** (Yūsuf 12:13) is already vocalised in the source and uses
real hamza — إِنِّی لَیَحْزُنُنِی أَنْ تَذْهَبُوا بِهِ — unlike the surrounding text. Copied
verbatim rather than re-marked.

Verified on p.166: passive list renders, نُصِرَ زَیْدٌ present, الْانَ not الْآنَ, toggle and
page features intact.

**Pending: 2,170 blocks.** التصریف is 15 of 80.

---

## 2026-09-06 (session 8, part 15)

### Tashkīl round 7 — کتاب التصریف, opening

Eight blocks: the definition of تصریف, the ثلاثی/رباعی division, the three أبواب of the
sound triliteral with their throat-letter exception, and the مزید فیه forms.

**178 blocks · 5,871 marks · 178/178 text-preserving.**

**Accuracy checked against the matn's own rules**, which is the strongest test available
here — the text *states* a rule and then gives examples, so the vocalisation has to satisfy
what the text itself asserts:

```
"فَعَلَ مَفْتُوحَ الْعَیْنِ … یَفْعُلُ بِضَمِّ … اَوْ یَفْعِلُ بِکَسْرِهَا"
      → نَصَرَ یَنْصُرُ (damma)   ضَرَبَ یَضْرِبُ (kasra)          OK
throat-letter exception → سَئَلَ یَسْئَلُ · مَنَعَ یَمْنَعُ        OK
"فَعِلَ مَکْسُورَ الْعَیْنِ → یَفْعَلُ"  → عَلِمَ یَعْلَمُ, شاذ حَسِبَ یَحْسِبُ   OK
"فَعُلَ مَضْمُومَ الْعَیْنِ → یَفْعُلُ"  → حَسُنَ یَحْسُنُ                OK
8/8 مزید فیه أبواب: wazn matches exemplar                        OK
hamzat al-waṣl after و takes no vowel: وَ افْتَعَلَ, وَ افْعَلَّ      OK
```

### Console check — three 404s, all pre-existing

Read the console rather than assuming, and traced each:

| 404 | verdict |
|---|---|
| `/favicon.ico` ×3 | **site-wide and pre-existing** — no page in the library declares a favicon, so every page load asks for it and misses. Cosmetic; fixing it means touching every builder and rebuilding 3,067 pages, so not folded into this work. |
| `assets/search-index.json` | never actually requested — this book has no drawer search box, same as Bayt al-Ahzan (also 404). Only Bihar ships an in-book index. |
| `1/assets/toc.json` | expected — the TOC moved to book level in part 5. |

No regression from this session's work. TOC drawer serves 19 items; toggle, pager and
609-entry dropdown all intact.

**Pending: 2,177 blocks.** کتاب التصریف is 8 of 80 done.

---

## 2026-09-06 (session 8, part 14)

### Tashkīl round 6 — صرف میر's weak-verb and quadriliteral أبواب

Eleven blocks: لفیف مقرون (اَهْوَی یُهْوِی اِهْوَاءً), مضاعف (اَحَبَّ یُحِبُّ, with the three
imperative variants a doubled verb allows), مثال یائی (اِیتَسَرَ / اتَّسَرَ), ناقص یائی
(اِسْتَخْبَی یَسْتَخْبِی), and the four quadriliterals — فَعْلَل, تَفَعْلُل, اِفْعِنْلَال, اِفْعِلْلَال.

**170 blocks · 5,007 marks · 170/170 text-preserving.**

Persian glosses embedded in the entries stay bare — قصدکردن, دوست داشتن, خیمه زدن,
سرخ شدن — as do the Persian labels امر / نهی / ماضی, confirmed on the rendered page:
`امر دَحْرِجْ نهی لَا یُدَحْرِجْ`.

**Skipped, on purpose:** `1:127:0` — "قیان قینان─ نون تاکید خفیفه قین قن قن", the
emphatic-nun forms of وقى. I cannot pin those with confidence, and a plausible wrong vowel
is worse here than a visible gap. Also `1:76:1` and `1:78:1`, which are Persian headings.

### Scope corrected — the backlog is Arabic, but not all of it

Measured what is genuinely Arabic among the blocks tagged `ar`, rather than trusting the
tag:

```
tagged Arabic                 2,245
  genuinely Arabic            2,232   (489,663 chars)
  Persian, mis-tagged            13   ← need no vowels at all
REAL remaining                2,185
```

The detector needs two Persian tells to fire, so short headings like
"فصل [در تصور و تصدیق]" (کتاب الکبری فی المنطق) and the Persian bibliographic block
مشخصات کتاب still read as Arabic to it — they are skipped on sight instead. The tag is a
heuristic; the sentence decides.

Distribution of what is left, which is why the end is far off:

| treatise | blocks | chars |
|---|---|---|
| شرح التصریف | 509 | 150,544 |
| شرح الانموذج | 689 | 142,091 |
| الهدایه فی النحو | 261 | 63,275 |
| الصمدیه | 271 | 34,832 |
| شرح العوامل | 131 | 33,723 |
| عوامل ملا محسن | 147 | 27,637 |
| التصریف | 80 | 18,429 |
| آداب المتعلمین | 70 | 14,801 |

Two commentaries are 60% of the total. Those are running نحو prose, where mood and voice
turn on the particle before the verb — the case that defeated the mechanical pass in round 4.

---

## 2026-09-06 (session 8, part 13)

### Tashkīl round 5 — **کتاب عوامل جرجانی complete**, read sentence by sentence

First treatise finished. العوامل المائة of al-Jurjānī — all 16 of its Arabic blocks, done
by reading rather than by table lookup, because every case ending follows from the syntax:

| | reasoning |
|---|---|
| `حُرُوفٌ تَجُرُّ الْاِسْمَ فَقَطْ` | الاسم is the object of تجر → accusative |
| `وَ هِیَ تِسْعَهَ عَشَرَ حَرْفًا` | تمييز after a number → accusative |
| `فَاِنَّ الْعَوَامِلَ … مِاَهُ عَامِلٍ` | اسم إنّ accusative; عامل is the tamyīz of مائة → genitive |
| `اِذَا رُکِّبَتْ مَعَ اَحَدٍ` | passive — "when it is compounded" |

**159 blocks · 4,553 marks · 159/159 text-preserving.**

The printed orthography is kept exactly: bare alef (اَمَّا, never أمّا), the Persian ی and ک
the export uses, and ه wherever the source writes ه for ة.

**Left bare, deliberately:** the two treatise titles, and all of کتاب عوامل منظومه — it is
Persian verse. Three of its lines are tagged `ar` by the extractor and are nothing of the
sort ("بعد توحید خداوند و درود مصطفی"), which is a useful reminder that the `lang` tag is a
heuristic and the text itself decides. Two blocks in عوامل جرجانی are the mirror image —
tagged `fa`, plainly Arabic — and those were vowelled.

Two more Arabic/Persian homographs joined the harness allowlist, same mechanism as بِهِ:
**یَا** (vocative; Persian یا = "or") and **اَیْنَ** ("where"; Persian این = "this"). The
vocalisation is what distinguishes them, so the exception keys on the marked form and a
real slip on Persian یا or این is still caught.

Verified on p. 483: 6 vocalised blocks, default on, toggles both ways, TOC/cite/pager intact.

**Pending: 2,086 blocks.**

---

## 2026-09-06 (session 8, part 12)

### Tashkīl round 4 — mechanised, after the manual rate proved hopeless

At two blocks a round, 2,226 blocks is over a thousand rounds. The way this finishes is
that the book **repeats itself** — it is a drill, so نَصَرُوا / یَنْصُرُونَ recur across صرف
میر, شرح الامثله and شرح التصریف. Rounds 1–3 hand-verified ~60 canonical forms; this
applies them wherever the identical bare word appears.

**`jame_tashkil_auto.py`** — new. Forms are *generated* from the six sound أبواب (one vowel
pattern per باب) rather than typed, so a slip surfaces in every form of that باب at once
instead of hiding in one cell.

**19 → 142 blocks · 3,033 marks · 142/142 text-preserving · 68 pages.**

Three findings, each of which changed the tool:

**1. Unicode combining-mark order.** The generator emitted ضَرَبْتُنَّ as shadda-then-fatha;
the hand-typed form was fatha-then-shadda. Identical on screen, different bytes, and the
same word would have failed to match itself. Now normalised to NFC — which is what the
existing hand-typed data already was.

**2. A preview caught two real errors before anything was written.** Both were single verbs
in running prose, where syntax decides the vowel:

| block | proposed | actually |
|---|---|---|
| `2:68:1` | `ان تَضْرِبُ اضرب` | conditional ان takes the **jussive** تَضْرِبْ |
| `2:324:4` | `و یَعْلَمُ من ذلک` | **passive** یُعْلَمُ — "is known" |

The common factor: یضرب / تضرب / نضرب are spelled identically in indicative, jussive **and**
passive. A word-table cannot see syntax. Those three moved behind the drill-context rule —
inside a paradigm list they are cited *as forms*, and the indicative reading is right;
outside one they are now left bare. Reach fell 270 → 123 blocks, which is the correct
trade. Both blocks now skip cleanly.

**3. The safety rule that survived.** A form is only substituted when its segment contains
two or more unambiguous forms of the same root — i.e. it is provably a drill, not a
sentence. Ambiguous spellings (ضرب as 3ms or masdar; ضربت with four readings) are never
applied outside that context.

Verified on the page: default on, toggles both ways, Persian bare, and TOC / cite / pager /
609-entry dropdown intact.

**Pending: 2,103 blocks (93.7%).** What remains is mostly running نحو prose — شرح الانموذج
(145k chars), شرح التصریف (152k), الهدایه (63k) — which the two errors above show cannot be
mechanised safely. Extending the generator to the weak-verb and derived-form paradigms is
the next automatable seam.

---

## 2026-09-04 (session 8, part 11)

### Tashkīl round 3 — the derived أبواب, and the نصر drill

- **1:84:0** — the مزید فیه أبواب: name · past · present · masdar, each with its exemplar
  (اِفْتِعَال اِفْتَعَلَ یَفْتَعِلُ اِفْتِعَالًا · چون اِکْتَسَبَ یَکْتَسِبُ اِکْتِسَابًا, and six more
  through اِفْعِیلَال)
- **1:87:1** — باب نصر in full, 14 ماضی + 14 مستقبل, then the other five أبواب abbreviated

**19 blocks · 1,375 marks · 19/19 text-preserving.**

Accuracy pass, again independent of the harness:

```
باب نصر         14/14 ماضی · 14/14 مستقبل present
five أبواب      ع-vowel agrees past↔present in all 5
derived أبواب   7/7 rows: wazn, exemplar and masdar all consistent
Persian frame   8/8 checked phrases carry no marks
```

Rendered, which is the check that matters:

```
… آن سه که مذکر را بود چون نَصَرْتَ نَصَرْتُمَا نَصَرْتُمْ─ و آن سه که مؤنث را بود …
  ^^^^^^^^^^^^^^^^^^^^^^^^ Persian, bare   ^^^^^^^^^^^^^^^^ Arabic, vowelled
```

**Left deliberately bare:** the opening fragment "ضرابا و ضیرابا" on 1:84:0. It carries over
mid-sentence from the previous page; ضِرابًا would be the فِعال masdar, but ضیرابا fits no
standard pattern here and guessing at a matn word is the one thing that must not happen.

**Website checked:** default on, toggle both ways, Persian bare, and TOC / cite / 4 pager
links / 609-entry dropdown all intact on both pages.

> Process note: `python jame_build.py … | Select-Object -First 1` returns exit 255. That is
> PowerShell closing the pipe and killing the process, **not** a build failure — the full
> run completes. Don't chase it.

**Pending: 2,226 blocks.**

---

## 2026-09-04 (session 8, part 10)

### Tashkīl round 2 — صرف میر paradigm tables

Two blocks from کتاب صرف میر, chosen because their vowels are *derivable* rather than
judged — which is what makes them safe to do at volume.

- **1:74:0** — the noun example (رَجُل رَجُلَان رِجَال · رُجَیْل) and the full 14-form
  ماضی and مستقبل drill of باب ضرب
- **1:82:0** — the six أبواب of ثلاثی مجرد, each wazn beside its exemplar

**17 blocks · 890 marks · 17/17 text-preserving.**

**Accuracy checked independently of the harness.** The harness proves no letter changed;
it cannot tell a right vowel from a wrong one. So the paradigms were also checked against
the canonical forms:

```
ماضی   14/14 forms match   ضَرَبَ ضَرَبَا ضَرَبُوا ضَرَبَتْ … ضَرَبْتُ ضَرَبْنَا
مستقبل 14/14 forms match   یَضْرِبُ یَضْرِبَانِ یَضْرِبُونَ … اَضْرِبُ نَضْرِبُ
ابواب   6/6 wazn↔exemplar  فَعَلَ یَفْعُلُ چون نَصَرَ یَنْصُرُ …
```

The اصول/فروع split the matn asserts also holds: نصر/ضرب/علم change the ع vowel between
past and present, منع/حسب/شرف keep it.

One phrase was deliberately **not** vocalised — "و مستقبل فعل یکی است". That فعل sits in
a Persian clause and which wazn is meant is not certain, so it was left bare rather than
guessed at.

**Website checked after the rebuild:** toggle defaults to **on** (`aria-pressed="true"`,
marks visible), turning it off persists to `localStorage.tashkil`, and the page's other
features are intact — TOC, cite, 4 pager links, 609-entry page dropdown.

> A caution for future rounds: while testing I left `tashkil=0` in localStorage and then
> misread the default as "off". The default is on. Clear the key before judging initial
> state.

**Pending: 2,228 blocks.** 241 of them carry six or more paradigm markers, so the
derivable-vowel seam continues for a good while yet.

---

## 2026-09-04 (session 8, part 9)

### Tashkīl round 1 — verification harness, and the rule that Persian stays bare

**`jame_tashkil_check.py`** — new. Vocalising a صرف/نحو text is where a quiet error does
real damage, so the vocalised text is no longer trusted on inspection. The check that can
be made absolute: strip every diacritic from the vocalised form and from the printed form
and the two must be byte-identical. That catches the dangerous failure — a letter changed,
a word dropped, a phrase "corrected" — which is far worse than a debatable vowel because
it alters the text itself. It also flags marks landing on Persian (via پ چ ژ گ and a
function-word list), and exits non-zero so it can gate a build.

Confirmed the rule the owner set — the Persian commentary stays bare, only the Arabic matn
and the paradigms inside it are vocalised:

```
و از ماضی چهارده وجه باز می گردد─ … ضَرَبَ ضَرَبَا ضَرَبُوا─ … ضَرَبَتْ
^^^^^^^ Persian, bare                  ^^^^^^ Arabic paradigm, vowelled
```

Round 1 added the شرح الامثله opening: the basmala with و بِهِ نَسْتَعِینُ, and the
hadith اَوَّلُ الْعِلْمِ مَعْرِفَهُ الْجَبَّارِ. Bare alef and the Persian ی of the printed
text are preserved — only marks were added, which is what the harness proves.

**15 of 2,245 blocks, 645 marks, 15/15 text-preserving.**

The harness immediately earned itself twice:

1. It flagged `بِهِ` as Persian. False positive — `به` is both the Persian preposition and
   Arabic bi-hi. Fixed by keying the exception to the *vocalised* form rather than the bare
   word: Persian بِه is "be" and could not carry the pronoun's kasra, so a genuine slip on
   Persian به is still caught.
2. Rebuilding wiped the vocalisation off all 1,216 pages. `jame_build.py` only loaded the
   overlay when `--tashkil` was passed, and nothing failed when it was forgotten. It now
   **defaults** to `jame_tashkil.json` beside the script, warns on stderr if the file is
   missing, and takes `--no-tashkil` to opt out.

Verified on the page: toggle present on 1/14, 3 vocalised blocks, swaps cleanly both ways.

**Pending: 2,230 blocks.** Next round is the صرف paradigm tables — pattern-determined, so
derivable rather than judged.

---

## 2026-09-04 (session 8, part 8)

### Change — آیه‌به‌آیه rebuilt as verse cards, so it differs from صفحهٔ مصحف

The two layouts were doing nearly the same thing. صفحهٔ مصحف is unchanged; آیه‌به‌آیه now
gives every verse its own card, and clicking one scrolls it to the top and marks it as
the focused verse — so it reads as "work through one verse at a time" rather than a
slightly different page.

- `.body[data-unit="aya"]:not(.m-mushaf) .aya` — bordered, rounded card with hover and a
  `.v-focus` state; scoped with `:not(.m-mushaf)` so the Mushaf run-on page is untouched
- clicking a card calls `focusAya()`; the verse dropdown sets the same `.v-focus`, so
  picking a verse and tapping one look identical
- arriving on `#a<n>` focuses that verse too

**Two implementation notes worth keeping.** The verse dropdown already had a handler that
owned `location.hash`; adding a second scroller made them fight, so the existing one was
extended rather than duplicated. And the first attempt used `window.scrollTo` with an
offset measured from the sticky bar — wrong, because it assumes the window is the scroll
container. Replaced with `scrollIntoView({block:'start'})` plus `scroll-margin-top` in
CSS: it scrolls whatever the real container is, and the header clearance stops being a
number the JS has to compute.

Verified at 1100×800: card styling applied, `scroll-margin-top` 72px, click focuses
exactly one verse, the copy button does **not** hijack the click, and in صفحهٔ مصحف the
cards disappear and clicks are ignored.

> Not verified: the scroll movement itself. Nothing scrolls inside the preview pane —
> `scrollIntoView`, `body.scrollTop` and `documentElement.scrollTop` all leave the element
> rect unmoved — so the API call and its CSS clearance are confirmed but the visible glide
> is not. Worth one tap on a real device.

### Tashkīl — not advanced this session; scope measured

Coverage is **13 of 2,245 Arabic blocks (0.6%)**, on 4 pages of vol 1. کتاب الامثله is
effectively done (13 of its 16 blocks; the gaps are its title and one Persian line). The
remaining 14 treatises are ~495,000 Arabic characters — a multi-session job at any quality
worth having; see part 5 for why bulk-generating it on a صرف/نحو text is the wrong trade.

`assets/reader.css`, `assets/reader.js` changed → `ASSETS_V` 7 and all 3,067 pages
restamped.

---

## 2026-09-04 (session 8, part 7)

### Fix — asset versioning made consistent sitewide (v=6), and a broken Bihar control

Two corrections, no structure or content touched. Both verified rather than asserted.

**1. Every page now versions the shared assets.** 1,391 pages — Bihar and its three
translations, both Bayt al-Ahzan books, and the six root pages — linked
`assets/reader.css` / `reader.js` with no `?v=` at all, so they relied on whenever the
browser felt like re-fetching. Edit the shared stylesheet and a returning reader keeps
the stale one indefinitely. That is the same bug that hid the part-4 Qur'an fixes.

New `_translation-kit/stamp_assets.py` does the stamping and proves it is safe:

- **operates on bytes.** Every page here is CRLF; Python's text mode would have rewritten
  all 1,391 to LF — 1,391 files showing as wholly changed for a four-character edit.
  Bytes also cannot introduce a BOM or round-trip the Arabic.
- **proves only the version moved.** With the version stripped from both, patched and
  original must be byte-identical, and the CRLF count must match. A file failing either
  is skipped and reported, never written.

`ASSETS_V` added to `bayt_build.py`, `bayt_ar_build.py` and `build.py` (they had none), and
all five builders set to **6** so a future rebuild cannot silently revert this.

*Independently checked:* rebuilt bayt-al-ahzan from `bayt_ar.json` into a scratch directory
and diffed against the live pages — **190 identical, 0 differing**. So the surgical stamp
produced exactly what the updated builder produces; builder and site are back in sync, and
"structure and content unchanged" is demonstrated, not claimed.

**2. Bihar's page navigation was dead, and worse than merely absent.** Its pages ship 120
tick-mark links; reader.js reads the page number from `aria-label`, which those links do
not carry — it sits on the parent `<nav>`, and the links have `title="صفحة ٤٠"` in
Arabic-Indic digits that `parseInt` cannot read. So the list came out empty *and*
`install()` still replaced the working links with a dropdown containing nothing: the
control didn't degrade, it destroyed what was there. Pre-existing, not from this session
(the earlier edit sits below that `return`). Now falls back to the page number in the
href, which is language-neutral and works for every book.

Before: 120 links → **0** parsed. After: 120 links → **120** parsed, page ۴۰ selected,
targets resolve 200.

**What changed:**
- `_translation-kit/stamp_assets.py` — new: byte-exact, self-verifying asset stamper
- `_translation-kit/{bayt_build,bayt_ar_build,build}.py` — `ASSETS_V` introduced
- `_translation-kit/{jame_build,quran_build}.py` — `ASSETS_V` → 6
- `assets/reader.js` — page-number fallback for the edge-link dropdown
- 3,067 HTML files — asset refs restamped to `?v=6` (asset URL only)

Verified across 25 URLs spanning every book and all four languages: all 200, all on
`?v=6`, every reading page still has its `.body` and `.pager`. Spot-checked live: Bihar
dropdown 120 options resolving 200 · جامع المقدمات اعراب toggle swaps both ways with 609
dropdown options, TOC, cite and language switcher all present · Qur'an ا+ grows the
Arabic as well as the translation.

---

## 2026-09-04 (session 8, part 6)

### Feature — tashkīl on کتاب الامثله, as a verified toggleable layer

Vocalised the ضرب paradigm — 13 blocks, **583 marks**, vol 1 pp. 11–14. New
`_translation-kit/jame_tashkil.py` holds the table and enforces two rules:

**1. Add marks only, never substitute a letter.** The source writes `اضرب` with a bare
alef and `ضاربه` with ه. "Correcting" those to `أضرب`/`ضاربة` would be editing the text,
not vocalising it. Enforced by a machine check on every block:

```
strip_diacritics(vocalised) == original     # exact, or the build fails
```

All 13 pass. Any letter change, dropped word or typo breaks the build loudly.

**2. Vocalise positionally, never by word lookup.** In the ماضی block `ضربت` occurs four
times and is a different word each time — ضَرَبَتْ (she) · ضَرَبْتَ (you m.) · ضَرَبْتِ
(you f.) · ضَرَبْتُ (I). A word→word map gets three of four wrong, silently, for the
reader who came to learn exactly that. Each entry is a whole phrase replaced in order.

Reviewed against the standard paradigm: باب ضَرَبَ يَضْرِبُ takes kasra on the ʿayn
(یَضْرِبُ, not یَضْرُبُ); امر uses hamzat waṣl with kasra (اِضْرِبْ); and the pair the two
chapters exist to teach is correctly distinguished — **نهی is jussive** (لَا یَضْرِبْ)
against **نفی indicative** (لَا یَضْرِبُ). That one sukun/ḍamma *is* the lesson.

Shipped as an **overlay, not a rewrite**: the page emits the printed text and carries the
vocalised variant in `data-tashkil`; reader.js keeps the plain form in `data-plain` and
the اعراب button swaps them (default on, remembered). With JavaScript off a reader still
sees the printed text, and a citation is never silently something an editor added.

Coverage is 13 of ~2,975 blocks. The other 14 treatises are untouched — the remaining
~500,000 Arabic letters are mostly running نحو prose, where vocalisation is
interpretation rather than paradigm and the same per-phrase care is needed.

### Fix — three Bihar features were missing from the new book

Audited جامع المقدمات against a Bihar page element by element. Three gaps, now closed:

| feature | was | now |
|---|---|---|
| language switcher (`.langs`) | missing | present, all four buttons |
| citation (`#btn-cite` + `#cite-text`) | missing | per-language `data-cite-*`, copies with the URL |
| page dropdown (edge bar successor) | missing | 609/607 options, verified to resolve 200 |

### Fix — page dropdown was broken for every standalone book (reader.js)

Finding the third gap exposed a real bug. reader.js built the dropdown's hrefs as
`ROOT + '/' + FIXED + '/' + slug`, with no standalone guard — so on a book living at its
own top-level slug every option pointed at `/fa/<slug>/…`, which does not exist. Now
follows the same `FIXED && !STANDALONE` rule the TOC links already used. Bihar's
translated pages are unaffected (they are not standalone and keep the prefix); Bayt
al-Ahzan ships no `pages-*.json` so it had no dropdown to break.

**What changed:**
- `_translation-kit/jame_tashkil.py` — new: vocalisation table, positional application, strip-invariant verifier
- `_translation-kit/jame_tashkil.json` — new: 13-block overlay
- `_translation-kit/jame_build.py` — `--tashkil`; `data-tashkil` emission; اعراب toggle; `.langs`; cite block; `assets/pages-<vol>.json`; `ASSETS_V` → 5
- `assets/reader.js` — vocalisation overlay; standalone guard on the page dropdown; `tashkil` i18n key ×4 languages
- `assets/reader.css` — `.tashkil-bar`/`.tashkil-btn`, `.btn-cite`
- `jame-al-muqaddimat/` — 1,216 pages rebuilt; `assets/pages-1.json`, `pages-2.json`

### Fix — the part-4 Qur'an fixes would never have reached returning readers

Checking the asset versions turned this up, and it matters more than the caching note
that first prompted the check.

`?v=N` on `reader.css` / `reader.js` exists only to defeat browser caching: same URL means
the browser reuses its stored copy, so a changed stylesheet reaches nobody until the
number moves. Timestamps showed the problem plainly —

```
assets/reader.css      written  9/4 00:00     <- the ا+/ا− and mobile fixes
quran/1/index.html     built    9/3 14:40     <- and still asking for ?v=4
```

`reader.css` was edited in part 4 (Arabic scales with `--body-size`, the word-spacing fix
for the pause-mark gaps, صفحهٔ مصحف with translation) **after** the Qur'an pages were
built. Because those pages still requested `?v=4`, any returning reader would have kept a
cached v4 stylesheet and seen **none of those three fixes** — while a new visitor saw them
all. Exactly the kind of bug that looks like "works on my machine".

`quran_build.py` `ASSETS_V` → 5 and all 456 surah pages + the cover rebuilt. Verified: **0
pages anywhere on the site still ask for v=4.**

Bihar and Bayt al-Ahzan reference `reader.css` / `reader.js` with no version at all, so
they depend on ordinary HTTP cache expiry. Pre-existing, unchanged here, and worth
versioning when either builder is next touched.

Also checked for CSS leakage, since `assets/reader.css` is shared sitewide: the new
`.body h2` rule matches **0** pages across Bihar (231), Bayt al-Ahzan (189) and
bayt-al-ahzan-fa (262) — none put an `<h2>` inside `.body` — so it reaches only this book.

Verified in-browser: toggle swaps both ways and the label localises (اِعراب); dropdown
609 options resolving 200; no missing elements against the Bihar checklist; and
`/quran/`, `/bihar/`, `/bayt-al-ahzan/`, `/bayt-al-ahzan-fa/`, `/books/` all still 200.

---

## 2026-09-03 (session 8, part 5)

### Feature — جامع المقدمات added: 2 volumes, 1,216 printed pages

New book from the two Ghaemiyeh HTML exports, in a new **زبان عربي** category.
URL shape follows Bihar, the library's model for a multi-volume work:

```
/jame-al-muqaddimat/            volume selector
/jame-al-muqaddimat/1/          volume 1 contents — 9 treatises
/jame-al-muqaddimat/1/<page>/   printed pages 1..609
/jame-al-muqaddimat/2/<page>/   printed pages 1..607
```

Volume 1: الامثله · شرح الامثله · صرف میر · التصریف · شرح التصریف · عوامل جرجانی ·
عوامل منظومه · عوامل ملا محسن · شرح العوامل فی النحو
Volume 2: الکبری فی المنطق · آداب المتعلمین · الهدایه فی النحو · صیغ مشکله ·
شرح الانموذج · الصمدیه

**Pagination.** The export marks pages as `ص :137`. The marker *closes* the page it
names, the opposite of Bayt al-Ahzan's `[ صفحه N ]`. Established from the tail of both
files: the last marker is 609 / 607 with no content after it, impossible if a marker
opened its page. Both volumes number 1..N with **no gaps**, so unlike Bayt al-Ahzan
there was nothing to fill in. 66 pages carry no text in the export and render as blank
but navigable, preserving the printed numbering.

**Per-block language.** This edition is Persian commentary wrapped around Arabic matn,
interleaved down to the line. Every block is tagged `ar` or `fa` so each sets in the
right face — Arabic in Amiri, Persian in Vazirmatn — via the `.body p[lang="fa"]` rule
already in the stylesheet. Classification is biased toward `fa`: mislabelling Persian as
Arabic would set it in the Arabic serif and expose it to vocalisation, the worse failure.
Measured ~90% clean; the residue is genuinely mixed lines (Arabic paradigm + Persian
gloss), which no per-block scheme can split.

**Bug found and fixed during verification.** The TOC drawer came up empty. reader.js
rewrites `BOOK` to `ROOT + '/' + data-slug` on any page carrying `data-sitelang`, so the
per-volume `assets/toc.json` was never fetched. Moved to one book-level
`assets/toc.json` spanning both volumes — which is the better listing anyway: all 15
treatises in one drawer, so a reader can cross from volume 1 to volume 2 without backing
out. Verified: 19 rows, links resolve 200.

**Tashkīl — NOT applied. Deliberate, and it needs a decision.** The request was to
vocalise Arabic where it aids reading. On measuring, the source is essentially bare:
**0–3.9% vocalised, ~500,000 Arabic letters across the two volumes**. Two reasons not to
bulk-generate it:

1. These are صرف/نحو primers. The case endings *are* the lesson — a wrong ḥaraka does not
   look untidy, it teaches the opposite rule, and it is invisible to the reader who came
   to learn it. This is the one corpus where vocalisation errors do maximum damage.
2. Arabic and Persian interleave *within* single lines, so there is no clean seam to
   vocalise along.

The book ships faithful to the printed text, with the ~4,200 existing marks preserved.
Proposed next step: vocalise **one** treatise — کتاب الامثله (18 blocks, the shortest) —
as a reviewable sample, and if the quality holds, extend treatise by treatise with the
vocalised text as a *toggleable layer* rather than a replacement, so citations stay clean.

**What changed:**
- `_translation-kit/jame_extract.py` — new: Ghaemiyeh export → printed pages + per-block language
- `_translation-kit/jame_build.py` — new: pages, volume contents, cover, book-level toc.json
- `_translation-kit/jame_pages.json` — new: extracted source (1.4 MB)
- `jame-al-muqaddimat/` — new: cover, 2 volume contents, 1,216 reading pages, `assets/toc.json`
- `catalog.json` — new `arabic` category (6th tab) + the book entry
- `assets/reader.css` — `.body h2` treatise headings, `.part-label .up-link`, `.blank-page`
- `.claude/launch.json` — new: local preview server on :8099 for browser verification
- `sitemap.xml`, `robots.txt` — regenerated: **3,066 URLs** (was 1,847; +1,219)

Verified in-browser at 8099: page renders with correct fonts per language, part label and
folio correct, pager resolves, TOC populated, new category shows on `/books/`, and
`/quran/`, `/bihar/`, `/bayt-al-ahzan/`, `/bayt-al-ahzan-fa/` all still return 200.

---

## 2026-09-03 (session 8, part 4)

### Not a bug — Bayt al-Ahzan was never deleted

Reported as a 404 on the Arabic book. Nothing was lost; both editions are live:

| URL | status |
|---|---|
| `/bayt-al-ahzan/` and `/bayt-al-ahzan/30/` | **200** |
| `/bayt-al-ahzan-fa/` and `/bayt-al-ahzan-fa/30/` | **200** |
| `/fa/bayt-al-ahzan/` and `/fa/bayt-al-ahzan/30/` | **404** — the orphan path, never published |

All 189 Arabic pages are on disk, last written **2026-09-02**, i.e. before this session
touched anything. The two attempted deletions of the orphan both failed against Google
Drive, and nothing was pushed from here. Checked live, the book cards resolve correctly
in Farsi (`../bayt-al-ahzan/` and `../bayt-al-ahzan-fa/`) and the Arabic page's
`data-alt-fa` / `hreflang="fa"` both point at `/bayt-al-ahzan-fa/`. The 404 URL is not
reachable from any current link — it is a stale history entry or bookmark.

### Fix — ا+ / ا− did not resize the Arabic, only the translation

`.aya > p[lang="ar"]` carried `font-size:clamp(1.3rem,4vw,1.6rem)` — a fixed clamp that
`--body-size` could not reach, so the text-size buttons moved the translation and left the
verse alone. Now `clamp(1.25rem, calc(var(--body-size) * 1.35), 3rem)`; the basmala and both
Mushaf variants scale the same way. On a 375px phone the Arabic starts at **26.8px**
(was 20.8px) and the buttons move it (30.7px after ا+ ×3, 22.9px after ا− ×3).

### Fix — gaps inside words on phones

Not a font-loading fault. The Uthmani source flanks every pause mark with a real space on
both sides — `نَ` + `U+20` + `ۗ` + `U+20` + `إِ`. At the old 20.8px the mark is tiny while
those two spaces keep full width, so they read as a hole mid-word; at desktop's 25.6px the
same gap goes unnoticed, which is why it looked mobile-only. **The text is not altered** —
the verse keeps every mark and space. The larger default above plus `word-spacing:-.07em`
on the Qur'anic Arabic closes the gap visually. Scoped to `[data-unit="aya"]`, so Bihar's
prose keeps `word-spacing:0` and its justification.

### Change — صفحهٔ مصحف can now show a translation

Mushaf layout was Arabic-only and hid the text control entirely. It now keeps it:

- **عربی** — verses run on continuously inside the gold frame, as a printed page reads
- **ترجمه** / **هر دو** — the frame and Mushaf typography stay, the verse break returns so
  each rendering sits with its own verse
- **دوستونه** steps aside while in Mushaf layout (two columns have no meaning on a page),
  and anyone already in it lands on **هر دو**

Driven by an `m-withtr` class that `setMode()` maintains, so it follows the reader's choice
rather than being latched at layout-switch time. The per-verse Arabic is right-aligned, not
justified — justifying one short verse across a narrow column reopens exactly the word-gaps
the run-on page avoids by having a whole page to spread across.

**Verified** (mobile 375px and desktop): text-size buttons move the Arabic; all three Mushaf
text modes; Mushaf + page-by-page + translation together, incl. stepping 249→250 and keeping
the page when switching to Arabic; the Arabic-only surah page keeps all 286 verses visible
through every layout toggle (`setLayout` never calls `setMode` where there is no translation);
Bihar unchanged — `word-spacing:0`, justified, ا+/ا− still working, no Qur'an classes present.

---

## 2026-09-03 (session 8, part 3)

### Cleanup — orphaned `fa/bayt-al-ahzan/` identified (deletion still pending); CLAUDE.md corrected

`fa/bayt-al-ahzan/` held 2 stray page folders (149, 254), no cover, no `assets/`.
Confirmed orphaned before touching it:

| check | result |
|---|---|
| `sitemap.xml` URLs under `/fa/bayt-al-ahzan/` | **0** (vs 263 for `/bayt-al-ahzan-fa/`) |
| `catalog.json` entry | none — lists `bayt-al-ahzan` and `bayt-al-ahzan-fa` only |
| Arabic pages' `data-alt-fa` / `hreflang="fa"` | both point at `/bayt-al-ahzan-fa/` |
| pages 149 + 254 in `bayt-al-ahzan-fa/` | present and intact (6,669 and 6,749 bytes) |

So nothing linked to it and no content was unique to it. The live Farsi edition is
`bayt-al-ahzan-fa/` — 262 pages, own cover and `assets/toc.json`.

**Deletion is blocked by Google Drive**, which reports both folders as *both*
"Access is denied" *and* "does not exist" on consecutive calls — the phantom-directory
state described under "Committing from Google Drive". Per that guidance the retry loop
was not continued. **Restart Google Drive (tray → ⚙ → Quit, reopen), then run:**

```
rmdir /s /q "G:\My Drive\Misbah Library\Library\fa\bayt-al-ahzan"
```

Nothing else depends on it, so this can happen whenever convenient — it does not block
committing the Qur'an work.

### Docs — `Library/CLAUDE.md` was stale and would have misdirected a rebuild

It described the Farsi Bayt al-Ahzan as living at `/fa/bayt-al-ahzan/`; on disk and in the
sitemap it is `/bayt-al-ahzan-fa/`. A rebuild following the documented command would have
written 262 pages into the wrong folder and left the live ones stale. Corrected:

- `bayt_build.py` rebuild command → `--out bayt-al-ahzan-fa`
- "delete `fa/bayt-al-ahzan/` first" → `bayt-al-ahzan-fa/`
- jump-form `data-tpl` note → the book's own slug, not a language segment
- architecture paragraph now records that the Farsi edition is a **top-level sibling book**
  (a different edition, Ishtihardi, not a translation of the Arabic), with a note not to
  recreate `fa/bayt-al-ahzan/`
- current-state table: Qur'an rows corrected to 114 surahs / 342 translated pages, plus the
  new `quran/assets/` row; Bayt al-Ahzan Farsi rows repointed
- open-work item 1 ("Qur'an surahs 3–114 not built") removed — done; list renumbered

---

## 2026-09-03 (session 8, part 2)

### Fix — Qur'an verse search never matched الله (or any word spelled with a variant letter)

Both Qur'an searches stripped tashkeel but did not fold letter variants. Uthmani
spells الله with an **alef wasla** (ٱ, U+0671), so a reader typing the ordinary alef
matched **nothing** — 55 of Surah Yaseen's 83 verses contain ٱ. Searching `الله` in
Yaseen returned "No match"; it now returns 2. The cover's whole-Qur'an search had the
same fault and now returns results from 1:1 onward.

Both now fold the same way `fold()` in `reader.js` already did for the site search:
tashkeel **and** the Qur'anic annotation marks (U+06D6–U+06ED) are dropped, and the
alef/yaa/kaf/taa-marbuta variants are unified.

### Change — Qur'an reading controls rebuilt around words, not icons

The unlabelled icon buttons were replaced with named controls, and an empty
`.pgview-nav` bar was showing on every page because its `display:flex` silently beat
the `hidden` attribute.

1. **"All Surahs" moved** off the search row (where it read as a search control) to a
   breadcrumb above the surah banner.
2. **The stray bar** below the nav is fixed — `[hidden]` guards added for
   `.pgview-nav`, `.aya`, `.page-mrk`, `.bismillah`, `.tr-group`, `.qjump`. Every one of
   these sets `display`, which overrides the UA's `[hidden]{display:none}`.
3. **The unlabelled grid icon** is now a spelled-out choice: `SHOW: All verses | Page by page`.
   Its bar reads `Previous page · Page 251 of 604 · Next page`, in the reader's own numerals.
4. **Quick-access dialog redesigned** to guide the reader: title, a `GO TO` label, three
   named tabs (Surah / Juz / Page), labelled fields, and a full-width Confirm button.
   **It is now on the cover page as well**, where it navigates with the reader's language
   prefix (`/en/quran/36/#a9`).
5. **Page separator made distinct** — the Mushaf page break is now a gold double rule with
   a gold-ringed numeral, no longer the same grey hairline that divides one verse from the next.
6. **Page-by-page reading** works from either layout and is remembered between pages;
   arriving on `#a<n>` opens the page that verse sits on.
7. **IndoPak removed** (Nastaliq mangles Uthmani mark placement) and replaced with
   **Uthmani**. The four faces are now Uthmani (Amiri Quran), Mushaf (Scheherazade New),
   Amiri (self-hosted), Simple (Noto Naskh Arabic) — all four verified distinct.
8. **Mushaf layout added** — `LAYOUT: Verse by verse | Mushaf page`. Mushaf runs the Arabic
   on continuously as justified text inside a gold-ruled frame, the way a printed page reads.
   It is Arabic-only by nature, so choosing it hides the text-mode control and restores the
   reader's previous choice on the way back. Combined with page-by-page it reads like the book.

**The control bar is now emitted on Arabic-only pages too** (it carries the script and
layout pickers, which apply there). That needed a guard in `wireModes()`: those pages have
no `.tr-line`, and the stored `setMode('tr')` would have hidden the Arabic and left the
page blank.

**What changed:**
- `assets/reader.js` — verse search now folds via `fold()`; `wireModes()` guard; layout
  picker wiring with text-mode save/restore; retired-font fallback; i18n reworked across all
  four tables (`scriptIndoPak`→`scriptAmiri`, `scriptUthmani` relabelled, plus `quickAccess`,
  `goTo`, `layout`, `layoutVerse`, `layoutMushaf`, `showAs`, `showAll`, `showPaged`, `pageOf`,
  `prevPage`, `nextPage`, `textView`)
- `assets/reader.css` — Quran control block rewritten: `[hidden]` guards, gold page rule,
  breadcrumb, labelled `.tr-group`/`.segbtns`, `.btn-goto`, page-nav strip, redesigned dialog,
  `.m-mushaf` layout
- `_translation-kit/quran_build.py` — control bar always emitted; `LAYOUT_PICKER`, `JUMP_MODAL`,
  `GOTO_BUTTON` added; breadcrumb; worded nav; basmala carries `data-page`; page numerals use
  `data-num`; cover gains the dialog; cover search folding fixed; Nastaliq dropped from `FONT_LINKS`
- `quran/assets/qnav.js` — rewritten: wires the page-emitted dialog, cover mode, DOM-first
  paging that works before the JSON lands, localized numerals, language-change refresh
- all 456 surah pages + the cover rebuilt

**Verified in a browser** (localhost, all four languages): dialog tabs and navigation, Juz and
Page jumps, page stepping incl. correct disabling at page 604, Mushaf layout, Arabic-only page
still renders its text, both searches, Contents (114 entries), all 4 fonts, all 4 text modes.
Bihar and Bayt al-Ahzan re-checked — unaffected, no Qur'an controls leak in.

---

## 2026-09-03 (session 8)

### Feature — Quran reader: 6 new features

1. **Contents button fixed** — Created `quran/assets/toc.json` with all 114 surahs. The
   Contents drawer (⟰ button in the header) now loads and lists every surah for in-surah
   navigation. Works for all 4 languages via reader.js's existing BOOK-path fix.

2. **Back to all surahs link** — Each surah page now has an "All Surahs" link (→ index)
   in the verse-navigation bar, pointing to `quran/index.html` from any language variant.

3. **Jump modal** — A new `↕` icon button next to the verse picker opens a 3-tab modal:
   - **Surah** tab: choose surah + verse, navigate directly
   - **Juz** tab: choose 1–30, navigates to the juz's opening verse
   - **Page** tab: choose 1–604 Mushaf page, navigates to that page's first verse
   Navigation across surahs uses relative URLs so it works for all 4 languages.
   Shared JS logic lives in `quran/assets/qnav.js`; data in `quran/assets/qnav.json`.

4. **Mushaf page numbers** — Each surah page now shows a page-break marker (circled
   Arabic numeral, flanked by hairlines) before the first verse of each new Mushaf page.
   Verse divs carry `data-page="N"` for JS access. Data derived from `quran-data.xml`.

5. **Page-by-page view** — A new grid-icon button toggles "page view" mode: only the
   verses belonging to the current Mushaf page are shown. Prev/Next buttons navigate
   between pages; crossing a surah boundary follows the URL to the adjacent surah.

6. **Font picker expanded to 4 options:**
   - Amiri (عثماني) — existing Uthmani script
   - Scheherazade New (مصحف) — traditional Mushaf print style
   - Noto Nastaliq Urdu (هندی/IndoPak) — Nastaliq calligraphic style
   - Noto Naskh Arabic (بسیط) — simple reading face

   Font choice is persisted in localStorage and applies across all surah pages.

**What changed:**
- `assets/reader.js` — added 7 i18n keys to all 4 language tables (`scriptMushaf`, `scriptIndoPak`, `juz`, `mushafPage`, `allSurahs`, `goVerse`, `pageView`)
- `assets/reader.css` — added font rules for `scheherazade`/`nastaliq`, page-break marker styles, vnav button styles, jump-modal styles, page-view nav styles; bumped asset version to `4`
- `_translation-kit/quran_build.py` — `read_meta()` now returns page boundaries; added `verse_pages_for_surah()`, `build_toc()`, `build_qnav()` helpers; `FONT_PICKER` expanded to 4 buttons; `FONT_LINKS` adds Scheherazade New + Noto Nastaliq Urdu; `build()` now injects page-break markers, vnav with back link + jump + page-view buttons, and `window.QNAV` config script; `main()` writes `toc.json` + `qnav.json`; `ASSETS_V` bumped to `4`
- `quran/assets/qnav.js` — new shared JS: jump modal + page-by-page view logic
- `quran/assets/toc.json` — new: 114-entry TOC for Contents button
- `quran/assets/qnav.json` — new: surah names/ayat counts, juz + page boundaries (604 pages)
- `quran/1–114/index.html`, `fa/quran/1–114/`, `ur/quran/1–114/`, `en/quran/1–114/` — all 456 pages rebuilt

---

## 2026-09-02 (session 7, part 2)

### Feature — All 114 Quran surahs built in all 4 languages

Built all 114 surahs (was: 1–2 only) in Arabic, English (Shakir), Farsi (فولادوند),
and Urdu (علامہ جوادی). 456 surah reading pages total. The language switcher on each
page navigates between the four language versions via hreflang links.

Removed the "نسخه پروژهٔ تنزیل / Tanzil Project" edition row from the Quran index cover.

Sitemap regenerated: **1,847 URLs** (was 1,209; +638 new pages).

**What changed:**
- `_translation-kit/quran_build.py` — removed edition `<dl>` row from index template
- `quran/index.html` — rebuilt, now shows 114/114 published
- `quran/verses.json` — regenerated
- `quran/1–114/` — all 114 Arabic surah pages (was 1–2)
- `en/quran/1–114/`, `fa/quran/1–114/`, `ur/quran/1–114/` — all 114 × 3 language pages
- `sitemap.xml`, `robots.txt` — regenerated

---

## 2026-09-02 (session 7)

### Feature — Quran reader redesign + verse search

**Header redesign.**
Surah header now has a solid green banner (`var(--green)`, matching the nav bar)
with a gold double-border frame and corner ornaments, replacing the old warm gradient.
Surah name is `var(--on-green)`; badges (`مدنی`, `۲۸۶ آیه`) are language-pure with no
mixed English labels. Credit line removed. Font sizes reduced:
Arabic verse text `clamp(1.3rem,4vw,1.6rem)` (was `clamp(1.55rem,5.5vw,1.9rem)`).

**Verse search fix.**
`stripDiac()` in `reader.js` used a regex whose character ranges accidentally included
Arabic letters (U+0621–U+064A), stripping them and making every search return zero
results. Fixed to `[ً-ٰٟ]` (tashkeel only).

Also fixed: `.aya.v-hidden{display:none!important}` — the `!important` was missing, so
hidden verses still showed in side-by-side mode due to a specificity clash with
`.body.m-side .aya{display:grid}`.

**Search fires on button press.** Both search boxes (in-page verse search on surah pages,
global verse search on the Quran index cover) now trigger on an explicit **جستجو** button
click or Enter key, not on every keystroke. A `✕` clear button appears once the field
has text.

**Global verse search on index page.**
New `verses.json` (1.4 MB, all 6,236 verses) is generated by `quran_build.py` alongside
`quran/index.html`. Loaded lazily (only on first search). Results show surah name +
verse reference + Arabic text snippet; clicking a result navigates to the surah page
at its verse anchor (`#a<n>`).

**What changed:**
- `assets/reader.css` — header banner styles, font sizes, v-hidden fix, search button CSS
- `assets/reader.js` — stripDiac fix, search fires on button/Enter, clear button handler
- `_translation-kit/quran_build.py` — credit removed, `build_verse_index()` added,
  HTML templates updated with search button + clear button, index JS updated to match
- Rebuilt: `quran/index.html`, `quran/1–2/`, `en|fa|ur/quran/1–2/` (9 files)
- New: `quran/verses.json`

---

## 2026-09-01 (session 6, part 4)

### Feature — Bayt al-Ahzan: 33 missing pages added (1–262 now complete)

The original Ghaemiyeh HTML export had 229 of the 262 printed text pages. The
remaining 33 were part-title pages, blank facing pages, or the bibliographic
colophon (pages 1–2) — all verified against the scanned Naser edition in
session 5. Those page numbers had no URLs, causing prev/next to jump over them.

**What changed:**

- `_translation-kit/bayt_paginate.py`: Added `fill_gaps(result)` function.
  Called after `paginate()` in `__main__`. It:
  - Inserts pages 1 and 2 as the colophon (مشخصات کتاب), splitting the 19
    bibliographic blocks roughly in half across the two pages.
  - Inserts a blank page (empty `.body`) for every hole between 3 and 262,
    labelling each blank with the title of the chapter it leads into. Uses
    `chapter_n=0` so the `starts` dict in `build_index`/`build_toc` is not
    corrupted — the chapter grid still links to the first content page of each
    chapter, not the preceding blank.
  - `bayt_pages.json` regenerated: 262 pages (was 229).

- All 262 `fa/bayt-al-ahzan/<n>/index.html` pages regenerated via
  `bayt_build.py`:
  - The 33 new pages were created from scratch.
  - All 229 existing pages were updated: first-page link now `/1/` (was `/3/`),
    prev/next corrected for pages adjacent to gaps, `data-pos`/`data-total`
    updated throughout.

- `bayt-al-ahzan/index.html` (cover) regenerated: "Start reading" button now
  links to page 1 (was page 3); pages count shows 262 (was 229).

- `bayt-al-ahzan/assets/toc.json` regenerated (chapter starts unchanged).

- `bayt-al-ahzan/assets/pages.json` updated: all 262 page numbers (was 229),
  so the edge bar tick marks cover the complete page range.

- `sitemap.xml` regenerated: **1,209 URLs** (was 1,176; +33 new pages).

---

## 2026-09-01 (session 6, part 3)

### Bug — فهرست (TOC drawer) button did nothing on translated reading pages

Root cause: two separate problems.

**Missing drawer HTML.** The translated-page builder (`build.py`) emits `<button id="btn-toc">` in the header but never emits the `<aside class="drawer" id="drawer">` panel that `openDrawer()` writes into. `openDrawer()` called `null.setAttribute(...)` and crashed silently before the drawer appeared — identical to having no handler at all.
- Fixed in `reader.js`: before registering `drawer-close` / `btn-toc` handlers, inject the full drawer panel (`aside#drawer`, `#drawer-title`, `#drawer-close`, `#drawer-body`) if it is absent. This covers all 693 existing translated reading pages without touching their HTML files.

**Wrong link paths in the TOC drawer.** `toc.json` stores hrefs as `"bihar/1/6/"` (no language prefix). The drawer rendered links as `ROOT + '/' + x.href` → Arabic page. On a Farsi page at `/fa/bihar/1/1/`, a chapter link resolved to `/bihar/1/6/` instead of `/fa/bihar/1/6/`.
- Fixed in `reader.js` `btn-toc` handler: links now use `ROOT + '/' + (FIXED ? FIXED + '/' : '') + x.href`, so the chapter list correctly navigates to the active language's reading pages.

Only `assets/reader.js` was changed. No translated pages or Arabic pages were touched.

---

## 2026-09-01 (session 6, part 2)

### Bug — فهرست (chapter index) missing for translated languages

Root cause: `en/bihar/1/index.html`, `fa/bihar/1/index.html`, and
`ur/bihar/1/index.html` did not exist. When a non-Arabic language was active,
`applyLang()` rewrote `.vols a.vol` links to point directly to page 1
(`lang/slug/vol/1/`) — bypassing the volume index entirely. Arabic worked because
its `bihar/1/index.html` has always existed.

- Created `en/bihar/1/index.html` — English volume index for Bihar vol. 1, with
  full hreflang cluster (canonical for `en/bihar/1/`, reciprocal for all 4
  languages + x-default), `data-root="../../.."`, `data-book="../../../bihar"`,
  `data-sitelang="en"`. All chapter toc-i links use the same relative hrefs as
  the Arabic page; `applyLang()` handles language display at runtime.
- Created `fa/bihar/1/index.html` — Farsi version, RTL, `lang="fa" dir="rtl"`.
- Created `ur/bihar/1/index.html` — Urdu version, RTL, `lang="ur" dir="rtl"`.
- Updated `applyLang()` in `reader.js`: changed
  `ROOT + '/' + lang + '/' + slug + '/' + v + '/1/'`
  to `ROOT + '/' + lang + '/' + slug + '/' + v + '/'`
  so vol links land on the volume index page, not page 1.
- Updated no-JS fallback href on vol 1 in `en/bihar/index.html`,
  `fa/bihar/index.html`, `ur/bihar/index.html` from `href="1/1/"` to `href="1/"`.
- Sitemap regenerated: **1,176 URLs** (was 1,173).

---

## 2026-09-01 (session 6)

Six reader bugs fixed. Only `assets/reader.css`, `assets/reader.js`,
`_translation-kit/bayt_build.py`, and the 229 Bayt al-Ahzan reading pages were
touched. Two new JSON data files were created.

### Bug 1 — نخست/پایان (First/Last) pager buttons hidden on mobile (CSS)
- Removed a four-line `@media (max-width:560px)` block in `reader.css` that set
  `display:none` on `.pager .btn:first-child` and `.pager .btn:last-child`.
  First/Last buttons are now visible at all viewport widths, matching desktop.

### Bug 2 — page-jump form broken on mobile + navigates to wrong language (JS)
- Replaced the submit-only listener with a `doJump()` helper called on both
  `submit` and `change` events on `#jump-num`. The `change` event fires when the
  mobile keyboard's Done/Return key closes without submitting the form.
- Added a lang-prefix guard: when `FIXED` is set (translated page) and the
  template (`data-tpl`) doesn't already start with `FIXED + '/'`, the prefix is
  prepended before navigating. This fixes translated pages (en/fa/ur) navigating
  to the Arabic slot instead of the correct language slot.

### Bug 3 — edge bar (chapter tick marks) missing on translated pages (JS + new data files)
- Arabic source pages have the `.edgewrap`/`.edge` bar hardcoded. Translated
  pages had no equivalent at all.
- Created `bihar/assets/pages-1.json` — ordered array of all 231 Bihar vol 1
  page numbers.
- Created `bayt-al-ahzan/assets/pages.json` — ordered array of all 229 Bayt
  al-Ahzan printed page numbers (with their natural gaps preserved).
- Added a self-contained IIFE in `reader.js` (runs after page load) that: checks
  `FIXED` is set and `.edgewrap` is absent; reads `data-slug` and `data-volume`
  from `#page-meta`; fetches the appropriate `pages-{vol}.json` or `pages.json`;
  and injects a `.edgewrap`/`.edge` bar after `.bar`, with the current page
  highlighted via `class="cur"` and `aria-current="page"`. Works on both Bihar
  translated pages (all three languages) and Bayt al-Ahzan.

### Bug 4 — فهرست/Contents (TOC) button silent on translated pages (JS)
- Root cause: `data-book` on translated Bihar pages resolved to `en/` (or `fa/`,
  `ur/`) instead of `bihar/`, so `btn-toc` fetched from `en/assets/toc.json`
  which does not exist.
- Fixed in `reader.js` by overriding `BOOK` at runtime: when `FIXED` is set and
  `#page-meta` has a `data-slug`, `BOOK` is set to `ROOT + '/' + slug`. This
  ensures `BOOK + '/assets/toc.json'` always resolves to the Arabic book root
  regardless of page depth.

### Bug 5 — "Continue reading" unreliable; position/title loss on translated pages (JS)
- **href fallback**: translated pages carry no `data-href` on `#page-meta`, so
  stored entries had `href: null` and "Continue reading" links navigated to
  `/null`. Fixed by falling back to `location.pathname.replace(/^\//, '')`.
- **lang field**: each reading-list entry now stores a `lang` field (`FIXED || 'ar'`).
- **per-language deduplication**: previously deduplicated by `slug` only, so reading
  an English Bihar page overwrote the Arabic reading position and vice versa. Now
  deduplicates by `slug + ':' + lang`, keeping one position per book per language.
- **list capacity**: increased from 8 to 12 entries.
- **title fallback**: added `SLUG_NAMES` lookup table in `reader.js` for bihar,
  bayt-al-ahzan, and quran. `renderContinue()` now uses it when `data-title-*`
  attributes are absent (as on all translated pages), so the book name always shows.

### Bug 6 — credit line on every Bayt al-Ahzan page (229 pages + builder)
- The `<p class="book-credit">` attribution line (author, translator, foreword,
  قائمیه) appeared at the bottom of all 229 reading pages — already present on the
  cover, so redundant.
- Removed from all 229 `fa/bayt-al-ahzan/*/index.html` via PowerShell
  (`[System.IO.File]::ReadAllText/WriteAllText` with `UTF8Encoding($false)` to
  preserve Arabic/Farsi text).
- Removed the `{credit_block()}` call from the per-page template in
  `_translation-kit/bayt_build.py`. The call on the cover-page template was kept —
  attribution is correct there.

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

### Source data now in the repo
- `_translation-kit/bayt.json` — the 100%-fidelity extraction of the Ghaemiyeh HTML
  export, committed so the book can be rebuilt without the original export, which is not
  in the repo. `bayt_pages.json` is derived from it in one command and is not committed.

### Operational — committing this batch from Google Drive
- The 231-file batch wedged git: `unable to write .git/objects/0c/<hash>: Permission
  denied` in GitHub Desktop. The real cause is Drive holding git's temp object file open
  so the *rename* into place fails; Desktop runs git non-interactively and reports the
  resulting y/n prompt as a permission error. **Quitting and restarting Google Drive
  cleared it**; Desktop then committed normally.
- Recorded in `CLAUDE.md` under "Committing from Google Drive" with the full symptom,
  the cause, and what not to do — notably: do not answer `y` in a loop when the same
  temp file and target repeat, and never hand-create directories inside `.git/objects`.

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
