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
import sys
import types
import unittest

# selection.py imports Anki's GUI packages, which are not installable in the
# headless test environment. Register minimal stand-ins before importing it;
# the fake buildinfo version selects the modern (>= 2.1.50) code path.
def _install_fake_anki_modules():
    aqt = types.ModuleType("aqt")
    aqt_qt = types.ModuleType("aqt.qt")
    aqt_editor = types.ModuleType("aqt.editor")
    aqt_editor.Editor = type("Editor", (), {})
    anki = types.ModuleType("anki")
    anki_buildinfo = types.ModuleType("anki.buildinfo")
    anki_buildinfo.version = "25.9.4"
    aqt.qt = aqt_qt
    aqt.editor = aqt_editor
    anki.buildinfo = anki_buildinfo
    sys.modules["aqt"] = aqt
    sys.modules["aqt.qt"] = aqt_qt
    sys.modules["aqt.editor"] = aqt_editor
    sys.modules["anki"] = anki
    sys.modules["anki.buildinfo"] = anki_buildinfo

_install_fake_anki_modules()

from selection import Selection

class FakeWeb:
    def __init__(self, selectionResult):
        self.selectionResult = selectionResult
        self.evalCalls = []
        self.evalWithCallbackJs = []

    def evalWithCallback(self, js, callback):
        self.evalWithCallbackJs.append(js)
        callback(self.selectionResult)

    def eval(self, js):
        self.evalCalls.append(js)

class FakeNote:
    def __init__(self, fields):
        self.fields = fields

class FakeEditor:
    def __init__(self, fields, currentField=0, selectionResult=None):
        self.note = FakeNote(fields)
        self.currentField = currentField
        self.web = FakeWeb(selectionResult)
        self.saveCount = 0
        self.loadNoteCount = 0

    def call_after_note_saved(self, callback, keepFocus=False):
        self.saveCount += 1
        callback()

    def loadNoteKeepingFocus(self):
        self.loadNoteCount += 1

def captureSelection(editor):
    results = []
    Selection(editor, results.append)
    return results

class TestSelectionWithActiveSelection(unittest.TestCase):

    # a non-collapsed selection in the field should be used instead of the whole field
    def testUsesSelectedHtml(self):
        editor = FakeEditor(["日本語を勉強する"], selectionResult="勉強")
        results = captureSelection(editor)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].selected, "勉強")
        self.assertTrue(results[0].is_selection)

    # the selection is probed with the shadow-root JS snippet
    def testProbesWithSelectionScript(self):
        editor = FakeEditor(["日本語"], selectionResult="日本")
        captureSelection(editor)
        self.assertEqual(editor.web.evalWithCallbackJs, [Selection.js_get_selection])

    # modify() must replace only the selected range via inserthtml,
    # leaving note.fields to be synced by the editor bridge
    def testModifyReplacesSelectionOnly(self):
        editor = FakeEditor(["日本語を勉強する"], selectionResult="勉強")
        results = captureSelection(editor)
        results[0].modify("勉強[べんきょう]")
        self.assertEqual(
            editor.web.evalCalls,
            ["setFormat('inserthtml', %s);" % json.dumps("勉強[べんきょう]")],
        )
        self.assertEqual(editor.note.fields, ["日本語を勉強する"])
        self.assertEqual(editor.loadNoteCount, 0)

    # malformed non-breaking spaces are normalized in the captured selection
    # and in the html written back
    def testConvertsMalformedSpaces(self):
        editor = FakeEditor(["A&nbsp;B"], selectionResult="A&nbsp;B")
        results = captureSelection(editor)
        self.assertEqual(results[0].selected, "A B")
        results[0].modify("X& nbsp ;Y")
        self.assertIn(json.dumps("X Y"), editor.web.evalCalls[0])

class TestSelectionFallback(unittest.TestCase):

    # no selection (probe returns null) falls back to the whole field
    def testNoSelectionUsesWholeField(self):
        editor = FakeEditor(["日本語を勉強する"], selectionResult=None)
        results = captureSelection(editor)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].selected, "日本語を勉強する")
        self.assertFalse(results[0].is_selection)

    # a collapsed/empty selection behaves like no selection
    def testEmptySelectionUsesWholeField(self):
        editor = FakeEditor(["日本語"], selectionResult="")
        results = captureSelection(editor)
        self.assertEqual(results[0].selected, "日本語")
        self.assertFalse(results[0].is_selection)

    # whole-field modify() keeps the original write-back behavior
    def testModifyWritesWholeField(self):
        editor = FakeEditor(["日本語"], selectionResult=None)
        results = captureSelection(editor)
        results[0].modify("日本語[にほんご]")
        self.assertEqual(editor.note.fields, ["日本語[にほんご]"])
        self.assertEqual(editor.loadNoteCount, 1)
        self.assertEqual(editor.web.evalCalls, [])

    # pending edits are flushed before the field is read
    def testFlushesPendingEditsBeforeReading(self):
        editor = FakeEditor(["日本語"], selectionResult=None)
        captureSelection(editor)
        self.assertEqual(editor.saveCount, 1)

class TestSelectionGuards(unittest.TestCase):

    # without a focused field the callback must never fire
    def testNoCurrentField(self):
        editor = FakeEditor(["日本語"], currentField=None, selectionResult="日本")
        results = captureSelection(editor)
        self.assertEqual(results, [])

    # without a loaded note the callback must never fire
    def testNoNote(self):
        editor = FakeEditor(["日本語"], selectionResult="日本")
        editor.note = None
        results = captureSelection(editor)
        self.assertEqual(results, [])

if __name__ == "__main__":
    unittest.main()
