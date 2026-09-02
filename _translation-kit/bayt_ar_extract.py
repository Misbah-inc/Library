#!/usr/bin/env python3
"""Extract Bayt al-Ahzan Arabic pages from the AB Library HTML export.

  bayt_ar_extract.py <html-file> > bayt_ar.json

Outputs a JSON with one entry per printed page:
  {n, blocks:[{i:0, ar:"..."}], notes:[{n, ar}]}

Inline footnote superscripts (<sup class="fn-ref">) become [N] in the text.
"""
import json, re, sys, pathlib, html as htmllib

def unescape(s):
    return htmllib.unescape(s)

def strip_tags(s):
    return re.sub(r'<[^>]+>', '', s)

FNREF  = re.compile(r'<sup[^>]+class="fn-ref"[^>]*>.*?</sup>', re.DOTALL)
FNNUM  = re.compile(r'<a[^>]*>(\d+)</a>')
PTEXT  = re.compile(r'<p[^>]+class="page-text"[^>]*>(.*?)</p>', re.DOTALL)
ASIDE  = re.compile(r'<aside[^>]+class="footnotes"[^>]*>(.*?)</aside>', re.DOTALL)
FNITEM = re.compile(r'<div[^>]+id="fn-\d+-(\d+)"[^>]*>.*?<span>(.*?)</span>', re.DOTALL)
PAGE   = re.compile(r'<section[^>]+data-page="(\d+)"[^>]*>(.*?)</section>', re.DOTALL)


def replace_fnref(m):
    nm = FNNUM.search(m.group(0))
    return f'[{nm.group(1)}]' if nm else ''


def extract_page(n, body):
    pt = PTEXT.search(body)
    if pt:
        raw = FNREF.sub(replace_fnref, pt.group(1))
        ar_text = unescape(strip_tags(raw)).strip()
    else:
        ar_text = ''

    notes = []
    aside = ASIDE.search(body)
    if aside:
        for fn_n, fn_text in FNITEM.findall(aside.group(1)):
            notes.append({'n': int(fn_n),
                          'ar': unescape(strip_tags(fn_text)).strip()})

    return {'n': n, 'blocks': [{'i': 0, 'ar': ar_text}], 'notes': notes}


def main():
    src = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')
    pages = [extract_page(int(m.group(1)), m.group(2))
             for m in PAGE.finditer(src)]
    result = {
        'title':     'بيت الأحزان في مصائب سيدة النسوان',
        'author':    'الشيخ عباس القمي',
        'source':    'مكتبة أهل البيت الرقمية (AB Library)',
        'publisher': 'دار الحكمة، قم، إيران',
        'pages':     pages,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f'\n-- {len(pages)} pages extracted', file=sys.stderr)


if __name__ == '__main__':
    main()
