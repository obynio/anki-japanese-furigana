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

import re
import os

from aqt.utils import tooltip
from aqt.qt import *
from aqt.editor import Editor

from aqt import mw

from anki.hooks import addHook

from . import reading
from . import config
from .selection import Selection
from .utils import removeFurigana

mecab  = reading.MecabController()
config = config.Config()

def setupGuiMenu():
    useRubyTags = QAction("Use ruby tags", mw, checkable=True, checked=config.getUseRubyTags())
    useRubyTags.toggled.connect(config.setUseRubyTags)

    ignoreNumbers = QAction("Ignore numbers", mw, checkable=True, checked=config.getIgnoreNumbers())
    ignoreNumbers.toggled.connect(config.setIgnoreNumbers)

    mw.form.menuTools.addSeparator()
    mw.form.menuTools.addAction(useRubyTags)
    mw.form.menuTools.addAction(ignoreNumbers)

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
    html = mecab.reading(html, config.getIgnoreNumbers(), config.getUseRubyTags())
    if html == s.selected:
        tooltip("Nothing to generate!")
    else:
        s.modify(html)

def deleteFurigana(editor, s):
    stripped = removeFurigana(s.selected)
    if stripped == s.selected:
        tooltip("No furigana found to delete")
    else:
        s.modify(stripped)

setupGuiMenu()
addHook("setupEditorButtons", addButtons)
