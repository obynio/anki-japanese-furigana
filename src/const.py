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

TYPEIN_PATTERN = r"\[\[type:.*?\]\]"
SOUND_PATTERN = r"\[sound:.*?\]"
CLOZEDELETION_PATTERN_HTML = r'<span class="?cloze"?>(.*?)</span>'
CLOZEDELETION_PATTERN_BRACES = r'{{c\d+::(.*?)}}'
HTMLTAG = r'<[^>]+>'
LINEBREAK = r'<br ?/?>|<div>|</div>'
FURIGANA_BRACKETS = r"[^\S\n]?(?P<base_part>(?P<base>[^\s。、？！!?：]+?)(?P<base_hide>!?))(?P<ruby_part>\[(?P<ruby_hide>!?)(?P<ruby>[^\]]*?)\])"
FURIGANA_HTML = r'<ruby( title="(?P<title>[^"]*)")?([^>]*?)><rb(?P<base_hide>[^>]*?)>(?P<base>.*?)</rb><rt(?P<ruby_hide>[^>]*?)>(?P<ruby>.*?)</rt></ruby>'
