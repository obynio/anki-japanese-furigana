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

import json
import re
import os
from time import sleep
from aqt import mw
from aqt.utils import showInfo, tooltip
from aqt.qt import *
import aqt as aqt

from anki.hooks import addHook, wrap

from . import reading

mecab = reading.MecabController()

myfunction1 = """
<script>
function getSelectionHtml() {
    var html = "";
    if (typeof window.getSelection != "undefined") {
        var sel = window.getSelection();
        if (sel.rangeCount) {
            var container = document.createElement("div");
            for (var i = 0, len = sel.rangeCount; i < len; ++i) {
                container.appendChild(sel.getRangeAt(i).cloneContents());
            }
            html = container.innerHTML;
        }
    } else if (typeof document.selection != "undefined") {
        if (document.selection.type == "Text") {
            html = document.selection.createRange().htmlText;
        }
    }
    pycmd("formattedHtml:" + html);
}
</script>
"""


myfunction2 = """
<script>
function getSelectionHtml() {
    var selection = window.getSelection();
    var range = selection.getRangeAt(0);
    var div = document.createElement('div');
    div.appendChild(range.cloneContents());
    pycmd("formattedHtml:" + div.innerHTML);
}
</script>
"""

# TODO replace this method by the built-in anki method
def stripHtml(text):
    text = re.sub(HTMLTAG, r'', text)
    return text


def addButtons(buttons, editor):
    editor._links["generateFurigana"] = lambda ed=editor: doIt(ed, generateFurigana)
    editor._links["deleteFurigana"] = lambda ed=editor: doIt(ed, deleteFurigana)
    return buttons + [
        editor._addButton(os.path.join(os.path.dirname(__file__), "icons", "add_furigana.svg"), "generateFurigana", tip=u"Automatically generate furigana"),
        editor._addButton(os.path.join(os.path.dirname(__file__), "icons", "del_furigana.svg"), "deleteFurigana", tip=u"Mass delete furigana")
    ]


def doIt(editor, action):
    #Selection(editor, lambda s: action(editor, s))
    editor.getFormattedText()



def finalizeRuby(html, s):
    #html, spaces = sanitizer.rubySanitizer(html, s.after, s.before)
    s.modify(html, 0, 0)


def generateFurigana(editor, s):
    html = s.selected

    html = makeRuby(html)
    
    if html == s.selected:
        tooltip(_("Nothing to generate!"))
        return
    finalizeRuby(html, s)


def deleteFurigana(editor, s):
    html = s.selected
    # https://github.com/mass-immersion-approach/MIA-Japanese-Add-on/blob/master/src/js/removeBrackets.js
    html, deletions = re.subn('\[.+\]', '', html)
    if deletions == 0:
        tooltip(_("No furigana found"))
    finalizeRuby(html, s)


def makeRuby(html):
    html = re.sub('\[.+\]', '', html)
    html = mecab.reading(html)
    return html

def myBridgeCmd(editor, cmd, _old):
    if not cmd.startswith("formattedHtml:"):
        return _old(editor, cmd)
    (handlername, text) = cmd.split(":")
    showInfo(text, textFormat="plain")
aqt.editor.Editor.onBridgeCmd = wrap(aqt.editor.Editor.onBridgeCmd, myBridgeCmd, "around")
# https://github.com/mass-immersion-approach/MIA-Japanese-Add-on/blob/master/src/main.py#L304

aqt.editor._html += myfunction2
addHook("setupEditorButtons", addButtons)

def getFormattedText(self):
    self.web.eval("getSelectionHtml();")
aqt.editor.Editor.getFormattedText = getFormattedText

'''
class Selection:

    js_get_html = u"""
        sel = window.getSelection();
        range = sel.getRangeAt(0);
        if ( range.collapsed) {
            html = ""; htmlAfter = ""; htmlBefore = "";
        } else {
            ancestorStart = $(range.startContainer).closest("ruby").get(0);
            ancestorEnd = $(range.endContainer).closest("ruby").get(0);
            if ( ancestorStart ) {
                range.setStartBefore( ancestorStart );
            }
            if ( ancestorEnd ) {
                range.setEndAfter( ancestorEnd );
            }
            afterRange = range.cloneRange();
            afterRange.collapse(false);
            endPoint = $(range.endContainer).closest("div").get(0).lastChild;
            if (endPoint === null) {endPoint = $(range.endContainer).closest("div").get(0).parentNode.lastChild}
            afterRange.setEndAfter(endPoint);
            docFragmentAfter = afterRange.cloneContents();
            div = document.createElement('div');
            div.appendChild(docFragmentAfter);
            htmlAfter = div.innerHTML;
            div = null;

            beforeRange = range.cloneRange();
            beforeRange.collapse(true);
            startPoint = $(range.startContainer).closest("div").get(0).firstChild;
            if (startPoint === null) {startPoint = $(range.startContainer).closest("div").get(0).parentNode.firstChild}
            beforeRange.setStartBefore(startPoint);
            docFragmentBefore = beforeRange.cloneContents();
            div = document.createElement('div');
            div.appendChild(docFragmentBefore);
            htmlBefore = div.innerHTML;
            div = null;

            sel.removeAllRanges();
            sel.addRange(range);

            docFragment = range.cloneContents();
            div = document.createElement('div');
            div.appendChild(docFragment);
            html = div.innerHTML;
            div = null;

            range.detach();
            afterRange.detach();
            beforeRange.detach();
        }
        [htmlBefore, html, htmlAfter]
    """

    def __init__(self, window, callback):
        self.window = window

        # self.window.web.eval("setFormat('selectAll', '');")
        window.web.page().runJavaScript(self.js_get_html,
                                        lambda x: self._setHtml(x, callback))

    def _setHtml(self, elements, callback, allowEmpty=False):
        self.before, self.selected, self.after = elements
        if not allowEmpty and self.selected.strip() == '':
            self.window.web.eval("setFormat('selectAll', '');")
            self.window.web.page().runJavaScript(self.js_get_html,
                                                 lambda x: self._setHtml(x, callback, True))
            return
        self.selected = self.selected.replace('&nbsp;', u'\u00a0')
        self.before = self.before.replace('&nbsp;', u'\u00a0')
        self.after = self.after.replace('&nbsp;', u'\u00a0')
        callback(self)

    def length(self, callback, text=None):
        html = text if text else self.selected
        # Btw. inserthtml doesn't have inserted html selected, so we must select it by ourselves:
        textRows = []
        rows = html.split("<div>")

        def appendText(text, textRows):
            textRows.append(text)
            if len(textRows) == len(rows):
                if textRows[0] == '':
                    textRows = textRows[1:]
                selectedText = '\n'.join(textRows).replace('&nbsp;', u'\u00a0')
                selectedText = re.sub(r'( +)', ' ', selectedText)
                selectionLength = len(selectedText)
                selectionLength += len(re.findall(
                    r'<rt[^>]*>', html)) + html.count('</rt>')
                callback(selectionLength)
        for row in rows:
            js_get_text = u"""
			div = document.createElement('div');
			div.innerHTML = {0};
			text = div.textContent;
			div = null;
			text
			""".format(json.dumps(row))
            self.window.web.page().runJavaScript(
                js_get_text, lambda x: appendText(x, textRows))

    def modify(self, html, selectionLength=None, spaceAtLeft=0, spaceAtRight=0):
        def insert(selectionLength):
            self.window.web.eval(
                "setFormat('inserthtml', %s);" % json.dumps(html))
            # for _ in range(spaceAtRight):
            #     self.window.web.triggerPageAction(QWebPage.MoveToPreviousChar)
            # for _ in range(selectionLength-spaceAtLeft):
            #     self.window.web.triggerPageAction(QWebPage.SelectPreviousChar)
        html = html.replace(u'\u00a0', '&nbsp;')
        if not html.endswith("</ruby>") and not self.selected.endswith("</ruby>") and not self.after.startswith('<ruby') and not self.after.startswith('<div') and self.after != '' and self.before != '' and not self.before.endswith('</div>'):
            self.length(insert, html)

        # if the selection contains ruby element on its end border, QWebView can't handle it without creating mess.
        # So, we must implement our own replacement code - unfortunately this doesn't have undo functionality.
        else:
            js_replace_selection = u"""
			sel = window.getSelection();
			range = sel.getRangeAt(0);
			frag = document.createDocumentFragment();
			div = document.createElement('div');
			div.innerHTML = {0};
			while (child = div.firstChild) {{
				frag.appendChild(child);
			}}
			div = null;
			ancestorStart = $(range.startContainer).closest("ruby").get(0);
			ancestorEnd = $(range.endContainer).closest("ruby").get(0);
				if ( ancestorStart ) {{
					range.setStartBefore( ancestorStart );
				}}
				if ( ancestorEnd ) {{
					range.setEndAfter( ancestorEnd );
				}}
			range.deleteContents();
			range.insertNode(frag);
			sel.removeAllRanges();
			sel.addRange(range);
			range.toString(); 
			""".format(json.dumps(html))
            self.window.web.page().runJavaScript(js_replace_selection)
'''

