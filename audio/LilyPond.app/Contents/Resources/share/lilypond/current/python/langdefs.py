#!/home/lilydev/vc/gub/target/tools/root/usr/bin/python
#-*- coding: utf-8 -*-

"""
Documentation i18n module
"""

import re
import sys
import os

def lang_file_name (p, langext, ext):
    if langext != '':
        return p + '.' + langext + ext
    return p + ext

class LanguageDef:
    def __init__ (self, code, name, webext=None, double_punct_char_sep='', html_filter=lambda s: s):
        self.code = code
        self.name = name
        self.enabled = True
        if webext == None:
            self.webext = self.code
        else:
            self.webext = webext
        self.double_punct_char_sep = double_punct_char_sep
        self.html_filter = html_filter
    
    def file_name (self, prefix, ext):
        return lang_file_name (prefix, self.webext, ext)


# All language information needed for documentation i18n is defined
# here. For each 'Documentation/ab' directory containing docs
# translated in 'ab', there should be one entry in LANGUAGES.

site = LanguageDef ('en', 'English', webext='')

html_body_re = re.compile ('<body.*?>', re.I)
html_end_body_re = re.compile ('</body>', re.I)
french_html_typo_rules = ((' :', '&nbsp;:'),
                          (' ;', '&nbsp;;'),
                          (' ?', '<font size="-4">&nbsp;</font>?'),
                          (' !', '<font size="-4">&nbsp;</font>!'))

def french_html_filter (page):
    m = html_body_re.search (page)
    if m:
        body_begin = m.end ()
    else:
        body_begin = 0
    m = html_end_body_re.search (page)
    if m:
        body_end = m.start ()
    else:
        body_end = len (page)
    body = page[body_begin:body_end]
    for r in french_html_typo_rules:
        body = body.replace (r[0], r[1])
    return page[:body_begin] + body + page[body_end:]

fr = LanguageDef ('fr', 'français', double_punct_char_sep='&nbsp;', html_filter = french_html_filter)
es = LanguageDef ('es', 'español')
de = LanguageDef ('de', 'deutsch')
# FIXME: should use localized name for ja
ja = LanguageDef ('ja', 'japanese')
# Outdated or broken translations may be disabled
# (please run 'make web-clean' before doing that):
#fr.enabled = False

LANGUAGES = (site, fr, es, de, )#ja)

if __name__ == '__main__':
    print ' '.join ([l.code for l in LANGUAGES if l.enabled and l.code != 'en'])
else:
    LANGDICT = {}
    for l in LANGUAGES:
        LANGDICT[l.code] = l

    try:
        import gettext

        translation = {}
        for l in LANGUAGES:
            if l.enabled and l.code != 'en':
                t = gettext.translation('lilypond-doc',
                                        os.environ['LYDOC_LOCALEDIR'],
                                        [l.code])
                translation[l.code] = t.gettext
    except:
        if os.environ.has_key ('LYDOC_LOCALEDIR'):
            sys.stderr.write ('langdefs.py: warning: lilypond-doc gettext domain not found.\n')
        translation = dict ([(l.code, lambda x: x) for l in LANGUAGES])
