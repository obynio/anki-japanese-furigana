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

ANKI_SEMVER_AS_INT = int(''.join(c for c in version if c.isdigit()))

class Selection:

    selected: Optional[str]
    js_get_html = u"""
        var selection = window.getSelection();
        var range = selection.getRangeAt(0);
        var div = document.createElement('div');
        div.appendChild(range.cloneContents());
        div.innerHTML;
    """
    # The modern editor keeps each field's contenteditable (<anki-editable>)
    # inside a shadow root, so the selection must be read via
    # ShadowRoot.getSelection() (Chromium-only API, same one Anki uses).
    # Returns null when there is no usable selection, including when the
    # field is in plain-text (CodeMirror) mode.
    js_get_selection = u"""
        (function () {
            let root = document;
            let el = document.activeElement;
            while (el && el.shadowRoot && el.shadowRoot.activeElement) {
                root = el.shadowRoot;
                el = root.activeElement;
            }
            if (!el || el.tagName !== "ANKI-EDITABLE") return null;
            const sel = root.getSelection ? root.getSelection() : document.getSelection();
            if (!sel || sel.rangeCount === 0) return null;
            const range = sel.getRangeAt(sel.rangeCount - 1);
            if (range.collapsed) return null;
            const div = document.createElement("div");
            div.appendChild(range.cloneContents());
            return div.innerHTML;
        })();
    """

    def __init__(self, window: Editor, callback):
        self.window = window
        self.is_selection = False
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

            # flush pending edits first so the whole-field fallback never
            # reads a stale note; saveNow(1) keeps focus and the DOM
            # selection alive
            self.window.call_after_note_saved(
                lambda: self.window.web.evalWithCallback(
                    self.js_get_selection,
                    lambda sel_html: self._onSelection(sel_html, callback),
                ),
                keepFocus=True,
            )
            return

    def _onSelection(self, sel_html: Optional[str], callback) -> None:
        if sel_html:
            self.is_selection = True
            self.setHtml(sel_html, callback, True)
            return

        if self.window.currentField is None:
            return

        if self.window.note is None:
            return

        self.is_selection = False
        self.setHtml(self.window.note.fields[self.window.currentField], callback, True)

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

            if self.is_selection:
                # replaces only the selected range; the resulting input
                # event syncs note.fields through the editor bridge, so no
                # loadNoteKeepingFocus() (it would clobber the caret and
                # race the debounced save)
                self.window.web.eval("setFormat('inserthtml', %s);" % json.dumps(html))
            else:
                self.window.note.fields[self.window.currentField] = html
                self.window.loadNoteKeepingFocus()
