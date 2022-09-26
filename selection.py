# -*- coding: utf-8 -*-

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

import json
import re

from typing import Optional

from aqt.qt import *
from aqt.editor import Editor

from anki.buildinfo import version

ANKI_SEMVER_AS_INT = int(version.replace('.', ''))

class Selection:

    selected: Optional[str]
    js_get_html = u"""
        var selection = window.getSelection();
        var range = selection.getRangeAt(0);
        var div = document.createElement('div');
        div.appendChild(range.cloneContents());
        div.innerHTML;
    """

    def __init__(self, window: Editor, callback):
        self.window = window
        self.setHtml(None, callback)

    def setHtml(self, elements, callback, allowEmpty=False) -> None:
        self.selected = elements
        if self.selected is not None:
            self.selected = self.convertMalformedSpaces(self.selected)
            callback(self)
            return

        if ANKI_SEMVER_AS_INT < 2141:
            self.window.web.eval("setFormat('selectAll');")
            self.window.web.page().runJavaScript(self.js_get_html, lambda x: self.setHtml(x, callback, True))
        elif ANKI_SEMVER_AS_INT < 2150:
            self.window.web.page().runJavaScript("getCurrentField().fieldHTML", lambda x: self.setHtml(x, callback, True))
        else:
            if self.window.currentField is None:
                return

            if self.window.note is None:
                return

            self.setHtml(self.window.note.fields[self.window.currentField], callback, True)
            return

    def convertMalformedSpaces(self, text: str) -> str:
        return re.sub(r'& ?nbsp ?;', ' ', text)

    def modify(self, html: str) -> None:
        html = self.convertMalformedSpaces(html)

        if ANKI_SEMVER_AS_INT < 2141:
            self.window.web.eval("setFormat('insertHTML', %s);" % json.dumps(html))
        elif ANKI_SEMVER_AS_INT < 2150:
            self.window.web.page().runJavaScript("getCurrentField().fieldHTML = %s;" % json.dumps(html))
        else:
            if self.window.currentField is None:
                return

            if self.window.note is None:
                return
            
            self.window.note.fields[self.window.currentField] = html
            self.window.loadNoteKeepingFocus()
