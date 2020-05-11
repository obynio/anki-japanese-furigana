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
# from aqt.utils import showInfo


class Replacer:
    def __init__(self):
        self.substitutes = []
        self.substitutes_dict = {}
        self.index = 0

    def sub(self, html, pattern, type='SUBSTITUTE', processing=lambda x: x.group(0)):
        html = re.sub(pattern, lambda match: self.subOne(
            match, type, processing), html, flags=re.UNICODE)
        return html

    def subOne(self, match, type, processing):
        sub = u"2304985732409587{0}".format(self.index)+type
        self.index += 1
        original = processing(match)
        self.substitutes.append((sub, original))
        self.substitutes_dict[sub] = original
        return sub

    def restore(self, html):
        for sub, original in reversed(self.substitutes):
            html = html.replace(sub, original)
            sub = sub.strip()
            html = html.replace(sub, original)
        return html

    def subEach(self, match, different_r):
        return self.subOne(match, type='SUBSTITUTE', processing=lambda x: x.group(0))
