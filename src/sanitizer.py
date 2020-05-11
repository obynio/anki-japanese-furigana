# -*- coding: utf-8 -*-

# Copyright (C) 2018-2020
# - Pyry Kontio <pyry.kontio@drasa.eu>
# - Jean-Christophe Sirot <simple-furigana@sirot.org>
# - Yohann Leon <yohann@leon.re>
#
# This file is part of Japanese Furigana <https://github.com/obynio/anki-japanese-furigana>.
#
# Japanese Furigana is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Japanese Furigana is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Japanese Furigana.  If not, see <http://www.gnu.org/licenses/>.

import re

from . import replacer
from .const import *


def rubySanitizer(html, after, before):

    def clozecleaner(m):
        inside = m.group(1)
        inside = inside.replace('</span>', '')
        whole = re.sub(
            r'<span class="clozewrapper"( style="[^"]*")>', '<span class="clozewrapper">', m.group(0))
        return whole.replace(m.group(1), inside)

    def cleaner(html, insideRuby=False, insideBase=False):
        if insideRuby:
            html = re.sub(r'<br ?/?>', '', html)
        if insideRuby:
            html = re.sub(r'<div[^>]*>', '', html)
        if insideRuby:
            html = html.replace('</div>', '')
        html = re.sub('<ruby[^>]*>', '', html)
        html = re.sub('<rb[^>]*>', '', html)
        html = re.sub('<rt[^>]*>', '', html)
        html = html.replace('</ruby>', '')
        html = html.replace('</rb>', '')
        html = html.replace('</rt>', '')

        html = re.sub(r'<span class="basemaru"[^>]*>', '', html)
        html = re.sub(
            r'<!-- end_basemaru_l -->[^!]*?<!-- end_basemaru_r -->', '', html)
        html = html.replace('<span class="cjk_char">', '')
        html = html.replace('<!-- end_cjkl --></span><!-- end_cjkr -->', '')
        if insideRuby:
            html = html.replace('</span>', '')

        html = re.sub(
            r'<span class="clozewrapper"[^>]*>(.*?)<!-- clozewr -->[^!]*?<!-- apper -->', clozecleaner, html)
        html = re.sub(r'<span class="clozewrapper"[^>]*>', '', html)
        html = re.sub(r'<!-- clozewr -->[^!]*?<!-- apper -->', '', html)
        html = html.replace('<div></div>', '')
        html = html.replace('<div><br /></div>', '<br>')
        html = re.sub(CLOZEDELETION_PATTERN_BRACES,
                      lambda m: wrapCloze(m, insideRuby, insideBase), html)
        return html

    def wrapCloze(match, insideRuby, insideBase):
        text = match.group(0)
        if not 'clozewrapper' in text:
            if insideRuby and insideBase:
                text = ''.join(('<span class="basemaru">'+c+'<!-- end_basemaru_l --></span><!-- end_basemaru_r -->') if re.match(
                    r'[\u3041-\u3096\u30A0-\u30FF\u3400-\u4DB5\u4E00-\u9FCB\uF900-\uFA6A]', c) else c for c in text)  # if hiragana katakana or kanji
            return '<span class="clozewrapper">'+text+'<!-- clozewr --></span><!-- apper -->'

        else:
            return match.group(0)

    def brokenRubycleaner(match):
        original = match.group(0)
        match = re.match(FURIGANA_HTML, original)
        if match:
            ruby_cleaned = cleaner(match.group('ruby'), insideRuby=True)
            base_cleaned = cleaner(match.group(
                'base'), insideRuby=True, insideBase=True)
            if ruby_cleaned.strip() != '':
                # < ja > ettei replaceis title="BASE" -argumenttii samalla
                original = original.replace(
                    '>'+match.group('base')+'<', '>'+base_cleaned+'<')
                original = original.replace(
                    '>'+match.group('ruby')+'<', '>'+ruby_cleaned+'<')
            else:
                original = base_cleaned
        else:
            match = re.match(
                r'<ruby[^>]*><rb[^>]*>(.*?)</rb></ruby>', original)
            if match:
                original = cleaner(match.group(1), insideRuby=True)
            else:
                match = re.match(
                    r'<ruby[^>]*><rt[^>]*>(.*?)</rt></ruby>', original)
                if match:
                    original = cleaner(match.group(1), insideRuby=True)
                else:
                    original = ''
        return original

    original_html = html
    r = replacer.Replacer()
    html = r.sub(html, r'<ruby[^>]*>(.*?)</ruby>',
                 'RUBY_SANITIZE', brokenRubycleaner)
    html = cleaner(html)
    html = r.restore(html)

    html = html.replace("</ruby><", u"</ruby>\u00a0<")
    html = html.replace("><ruby", u">\u00a0<ruby")
#	html = html.replace("<!-- apper --><", u"<!-- apper -->\u00a0<")
#	html = html.replace("""><span class="clozewrapper">""", u""">\u00a0<span class="clozewrapper">""")
    spaceAtLeft = 0
    spaceAtRight = 0
    # if html.endswith('</ruby>') and (after == '' or after[0] == '<'):
    #     html = html + u'\u00a0'
    #     spaceAtLeft = 1
    # if html.startswith('<ruby') and (before == '' or before[-1] == '>'):
    #     html = u'\u00a0' + html
    #     spaceAtRight = -1
    return html, [spaceAtLeft, spaceAtRight]
