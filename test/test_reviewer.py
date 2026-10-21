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
import urllib.parse


def _install_fake_anki_modules():
    aqt = types.ModuleType("aqt")
    aqt_qt = types.ModuleType("aqt.qt")
    aqt_reviewer = types.ModuleType("aqt.reviewer")
    aqt_reviewer.Reviewer = type("Reviewer", (), {})

    aqt_previewer = types.ModuleType("aqt.browser.previewer")
    aqt_previewer.BrowserPreviewer = type("BrowserPreviewer", (), {})

    class FakeTooltip:
        def __init__(self):
            self.last_msg = None

        def __call__(self, msg):
            self.last_msg = msg

    fake_tooltip = FakeTooltip()
    aqt_utils = types.ModuleType("aqt.utils")
    aqt_utils.tooltip = fake_tooltip

    aqt_gui_hooks = types.ModuleType("aqt.gui_hooks")
    class FakeHook:
        def __init__(self):
            self.hooks = []
        def append(self, fn):
            self.hooks.append(fn)

    aqt_gui_hooks.webview_will_set_content = FakeHook()
    aqt_gui_hooks.webview_did_receive_js_message = FakeHook()
    aqt_gui_hooks.state_shortcuts_will_change = FakeHook()

    aqt_dialogs = types.ModuleType("aqt.dialogs")
    aqt_dialogs._dialogs = {}

    fake_mw = types.SimpleNamespace()
    fake_mw.reviewer = types.SimpleNamespace()
    fake_mw.reviewer.web = types.SimpleNamespace(eval=lambda js: None)
    fake_mw.checkpoint = lambda desc: None
    fake_mw.col = types.SimpleNamespace()

    aqt.mw = fake_mw
    aqt.gui_hooks = aqt_gui_hooks
    aqt.dialogs = aqt_dialogs
    aqt.reviewer = aqt_reviewer
    aqt.browser = types.ModuleType("aqt.browser")
    aqt.browser.previewer = aqt_previewer
    aqt.utils = aqt_utils

    sys.modules["aqt"] = aqt
    sys.modules["aqt.qt"] = aqt_qt
    sys.modules["aqt.reviewer"] = aqt_reviewer
    sys.modules["aqt.browser"] = aqt.browser
    sys.modules["aqt.browser.previewer"] = aqt_previewer
    aqt.Reviewer = aqt_reviewer.Reviewer
    sys.modules["aqt.utils"] = aqt_utils
    sys.modules["aqt.gui_hooks"] = aqt_gui_hooks
    sys.modules["aqt.dialogs"] = aqt_dialogs

    return fake_mw, fake_tooltip


fake_mw, fake_tooltip = _install_fake_anki_modules()

import reviewer


class FakeConfig:
    def __init__(self, add_sc="Ctrl+R", del_sc="Ctrl+Alt+R", use_ruby=False, ignore_nums=True):
        self.shortcuts = {"add_furigana": add_sc, "del_furigana": del_sc}
        self.use_ruby = use_ruby
        self.ignore_nums = ignore_nums

    def getKeyboardShortcut(self, name):
        return self.shortcuts[name]

    def getUseRubyTags(self):
        return self.use_ruby

    def getIgnoreNumbers(self):
        return self.ignore_nums


class FakeMecab:
    def reading(self, text, ignore_numbers, use_ruby_tags):
        if use_ruby_tags:
            return f"<ruby>{text}<rt>よみ</rt></ruby>"
        return f"{text}[よみ]"


class FakeWeb:
    def __init__(self):
        self.evalCalls = []

    def eval(self, js):
        self.evalCalls.append(js)


class FakeNote:
    def __init__(self, data):
        self.data = dict(data)
        self.flushed = False
        self.id = 12345

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __contains__(self, key):
        return key in self.data

    def items(self):
        return self.data.items()

    def keys(self):
        return self.data.keys()

    def flush(self):
        self.flushed = True


class FakeCard:
    def __init__(self, note):
        self._note = note
        self.nid = note.id

    def note(self):
        return self._note


class FakeReviewerContext(reviewer.Reviewer):
    def __init__(self, note):
        self.web = FakeWeb()
        self.card = FakeCard(note)


class TestReviewer(unittest.TestCase):
    def setUp(self):
        self.config = FakeConfig()
        self.mecab = FakeMecab()
        reviewer.setupReviewer(self.mecab, self.config)
        fake_tooltip.last_msg = None

    def test_get_reviewer_js(self):
        js = reviewer.get_reviewer_js("Ctrl+R", "Ctrl+Alt+R")
        self.assertIn('"Ctrl+R"', js)
        self.assertIn('"Ctrl+Alt+R"', js)
        self.assertIn("__japanese_furigana_trigger", js)
        self.assertIn("__japanese_furigana_apply", js)
        self.assertIn("document.addEventListener(\"keydown\"", js)

    def test_on_webview_will_set_content(self):
        class FakeWebContent:
            def __init__(self):
                self.head = ""

        web_content = FakeWebContent()
        reviewer_ctx = reviewer.Reviewer()

        reviewer.on_webview_will_set_content(web_content, reviewer_ctx)
        self.assertIn("<script>", web_content.head)
        self.assertIn("__japanese_furigana_trigger", web_content.head)

        # Non-reviewer context should not be modified
        other_content = FakeWebContent()
        reviewer.on_webview_will_set_content(other_content, object())
        self.assertEqual(other_content.head, "")

    def test_on_js_message_no_field(self):
        ctx = reviewer.Reviewer()
        handled = (False, None)
        res = reviewer.on_js_message(handled, "japanese_furigana_no_field#", ctx)
        self.assertEqual(res, (True, None))
        self.assertEqual(fake_tooltip.last_msg, "No editable field focused")

    def test_on_js_message_empty(self):
        ctx = reviewer.Reviewer()
        handled = (False, None)
        res = reviewer.on_js_message(handled, "japanese_furigana_empty#", ctx)
        self.assertEqual(res, (True, None))
        self.assertEqual(fake_tooltip.last_msg, "Nothing to generate!")

    def test_on_js_message_add_furigana(self):
        note = FakeNote({"Expression": "猫"})
        ctx = FakeReviewerContext(note)
        
        payload = {
            "action": "add",
            "isSelection": False,
            "html": "猫",
            "field": "Expression",
            "nid": str(note.id),
        }
        msg = "japanese_furigana#" + urllib.parse.quote(json.dumps(payload))
        res = reviewer.on_js_message((False, None), msg, ctx)
        self.assertEqual(res, (True, None))

        self.assertEqual(len(ctx.web.evalCalls), 1)
        call = ctx.web.evalCalls[0]
        self.assertIn("__japanese_furigana_apply", call)
        self.assertIn("猫[よみ]", call)

    def test_on_js_message_del_furigana(self):
        note = FakeNote({"Expression": "猫[ねこ]"})
        ctx = FakeReviewerContext(note)
        
        payload = {
            "action": "del",
            "isSelection": True,
            "html": "猫[ねこ]",
            "field": "Expression",
            "nid": str(note.id),
        }
        msg = "japanese_furigana#" + urllib.parse.quote(json.dumps(payload))
        res = reviewer.on_js_message((False, None), msg, ctx)
        self.assertEqual(res, (True, None))

        self.assertEqual(len(ctx.web.evalCalls), 1)
        call = ctx.web.evalCalls[0]
        self.assertIn("__japanese_furigana_apply", call)
        self.assertIn("猫", call)
        self.assertNotIn("ねこ", call)

    def test_on_js_message_sync(self):
        note = FakeNote({"Expression": "猫"})
        ctx = FakeReviewerContext(note)
        fake_mw.col.get_note = lambda nid: note
        sync_payload = {
            "nid": str(note.id),
            "field": "Expression",
            "html": "猫[ねこ]",
        }
        msg = "japanese_furigana_sync#" + urllib.parse.quote(json.dumps(sync_payload))
        res = reviewer.on_js_message((False, None), msg, ctx)
        self.assertEqual(res, (True, None))
        self.assertEqual(note["Expression"], "猫[ねこ]")
        self.assertTrue(note.flushed)

    def test_state_shortcuts(self):
        shortcuts = []
        reviewer.on_state_shortcuts_will_change("review", shortcuts)
        keys = [s[0] for s in shortcuts]
        self.assertIn("Ctrl+R", keys)
        self.assertIn("Ctrl+Alt+R", keys)

        # For non-review state, shortcuts should not be added
        other_shortcuts = []
        reviewer.on_state_shortcuts_will_change("deckBrowser", other_shortcuts)
        self.assertEqual(len(other_shortcuts), 0)

    def test_real_mecab_integration(self):
        import reading
        reviewer.setupReviewer(reading.mecab, self.config)
        note = FakeNote({"Expression": "千葉"})
        ctx = FakeReviewerContext(note)
        payload = {
            "action": "add",
            "isSelection": False,
            "html": "千葉",
            "field": "Expression",
            "nid": str(note.id),
        }
        msg = "japanese_furigana#" + urllib.parse.quote(json.dumps(payload))
        res = reviewer.on_js_message((False, None), msg, ctx)
        self.assertEqual(res, (True, None))
        self.assertEqual(len(ctx.web.evalCalls), 1)
        self.assertIn("千葉[ちば]", ctx.web.evalCalls[0])


if __name__ == "__main__":
    unittest.main()
