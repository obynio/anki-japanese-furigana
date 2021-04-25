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
import os
from time import sleep
from aqt import mw
from aqt.utils import showInfo, tooltip
from aqt.qt import *

from anki.hooks import addHook

from . import reading

mecab = reading.MecabController()

def addButtons(buttons, editor):
    editor._links["generateFurigana"] = lambda ed=editor: doIt(ed, generateFurigana)
    editor._links["deleteFurigana"] = lambda ed=editor: doIt(ed, deleteFurigana)
    return buttons + [
        editor._addButton(os.path.join(os.path.dirname(__file__), "icons", "add_furigana.svg"), "generateFurigana", tip=u"Automatically generate furigana"),
        editor._addButton(os.path.join(os.path.dirname(__file__), "icons", "del_furigana.svg"), "deleteFurigana", tip=u"Mass delete furigana")
    ]

def doIt(editor, action):
    Selection(editor, lambda s: action(editor, s))
    
def generateFurigana(editor, s):
    html = s.selected
    html = re.sub('\[[^\]]*\]', '', html)
    html = mecab.reading(html)

    if html == s.selected:
        tooltip(_("Nothing to generate!"))
    else:
        s.modify(html)

def deleteFurigana(editor, s):
    html = s.selected
    html, deletions = re.subn('\[[^\]]*\]', '', html)

    if deletions == 0:
        tooltip(_("No furigana found"))
    else:
        s.modify(html)

class Selection:

    js_get_html = u"""
        var selection = window.getSelection();
        var range = selection.getRangeAt(0);
        var div = document.createElement('div');
        div.appendChild(range.cloneContents());
        div.innerHTML;
    """

    def __init__(self, window, callback):
        self.window = window
        window.web.page().runJavaScript(self.js_get_html, lambda x: self.setHtml(x, callback))

    def setHtml(self, elements, callback, allowEmpty=False):
        self.selected = self.window.web.selectedText()
        if self.window.web.selectedText() == '':
            self.window.web.eval("setFormat('selectAll');")
            self.window.web.page().runJavaScript(self.js_get_html, lambda x: self.setHtml(x, callback, True))
            return
        self.selected = self.convertMalformedSpaces(self.selected)
        callback(self)

    def convertMalformedSpaces(self, text):
        return re.sub(r'& ?nbsp ?;', ' ', text)

    def modify(self, html):
        html = self.convertMalformedSpaces(html)
        self.window.web.eval("setFormat('insertHTML', %s);" % json.dumps(html))

addHook("setupEditorButtons", addButtons)
