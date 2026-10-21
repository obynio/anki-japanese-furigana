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
import unicodedata
import urllib.parse
from typing import Any, Optional

from aqt import mw, gui_hooks, dialogs
from aqt.utils import tooltip
from aqt.reviewer import Reviewer

try:
    from aqt.browser.previewer import BrowserPreviewer
except ImportError:
    BrowserPreviewer = None

try:
    from .utils import removeFurigana
except ImportError:
    from utils import removeFurigana

mecab = None
config = None

REVIEWER_JS_TEMPLATE = r"""
(function() {
    function parseShortcut(sc) {
        if (!sc) return null;
        var parts = sc.split("+").map(function(s) { return s.trim().toLowerCase(); });
        var key = parts[parts.length - 1];
        return {
            ctrl: parts.indexOf("ctrl") !== -1 || parts.indexOf("control") !== -1,
            alt: parts.indexOf("alt") !== -1,
            shift: parts.indexOf("shift") !== -1,
            meta: parts.indexOf("meta") !== -1 || parts.indexOf("cmd") !== -1 || parts.indexOf("command") !== -1,
            key: key
        };
    }

    function eventMatches(e, parsed) {
        if (!parsed) return false;
        var isMac = typeof navigator !== "undefined" && /(Mac|iPhone|iPod|iPad)/i.test(navigator.platform);
        var ctrlOrCmd = isMac ? (e.metaKey || e.ctrlKey) : e.ctrlKey;
        var hasCtrl = parsed.ctrl ? ctrlOrCmd : (isMac ? (!e.metaKey && !e.ctrlKey) : !e.ctrlKey);
        var hasAlt = parsed.alt ? e.altKey : !e.altKey;
        var hasShift = parsed.shift ? e.shiftKey : !e.shiftKey;
        var hasMeta = parsed.meta ? e.metaKey : (isMac ? true : !e.metaKey);

        if (!hasCtrl || !hasAlt || !hasShift || !hasMeta) return false;

        var k = e.key ? e.key.toLowerCase() : "";
        var c = e.code ? e.code.toLowerCase() : "";
        var targetKey = parsed.key.toLowerCase();

        if (k === targetKey) return true;
        if (c === "key" + targetKey) return true;
        if (c === "digit" + targetKey) return true;
        if (c === "numpad" + targetKey) return true;
        if (targetKey.indexOf("f") === 0 && (k === targetKey || c === targetKey)) return true;

        return false;
    }

    function isEditable(el) {
        if (!el) return false;
        if (el.isContentEditable) return true;
        var ce = el.getAttribute ? el.getAttribute("contenteditable") : null;
        return ce === "true" || ce === "";
    }

    function findClosestEditable(el) {
        if (!el) return null;
        if (isEditable(el)) return el;
        if (el.closest) return el.closest('[contenteditable="true"], [contenteditable=""]');
        return null;
    }

    function getEditableElement() {
        var active = document.activeElement;
        var el = findClosestEditable(active);
        if (el) return el;

        var sel = window.getSelection();
        if (sel && sel.anchorNode) {
            var node = sel.anchorNode.nodeType === 1 ? sel.anchorNode : sel.anchorNode.parentElement;
            el = findClosestEditable(node);
            if (el) return el;
        }

        var editables = document.querySelectorAll('[contenteditable="true"], [contenteditable=""]');
        if (editables.length === 1) {
            return editables[0];
        }
        return null;
    }

    window.__japanese_furigana_trigger = function(action) {
        var now = Date.now();
        if (window.__japanese_furigana_last_trigger && (now - window.__japanese_furigana_last_trigger < 300)) {
            return;
        }
        window.__japanese_furigana_last_trigger = now;

        var editable = getEditableElement();
        if (!editable) {
            if (typeof pycmd === "function") {
                pycmd("japanese_furigana_no_field#");
            }
            return;
        }

        editable.focus();

        var sel = window.getSelection();
        var isSelection = false;
        var textToProcess = "";

        if (sel && sel.rangeCount > 0 && !sel.getRangeAt(0).collapsed && editable.contains(sel.anchorNode)) {
            var range = sel.getRangeAt(0);
            var div = document.createElement("div");
            div.appendChild(range.cloneContents());
            textToProcess = div.innerHTML;
            isSelection = true;
            window.__japanese_furigana_range = range;
        } else {
            isSelection = false;
            textToProcess = editable.innerHTML;
            window.__japanese_furigana_range = null;
        }

        window.__japanese_furigana_target = editable;

        if (!textToProcess || !textToProcess.trim()) {
            if (typeof pycmd === "function") {
                pycmd("japanese_furigana_empty#");
            }
            return;
        }

        var payload = {
            action: action,
            isSelection: isSelection,
            html: textToProcess,
            field: editable.getAttribute("data-field") || "",
            nid: editable.getAttribute("data-nid") || ""
        };

        if (typeof pycmd === "function") {
            pycmd("japanese_furigana#" + encodeURIComponent(JSON.stringify(payload)));
        }
    };

    window.__japanese_furigana_apply = function(newHtml, isSelection) {
        var editable = window.__japanese_furigana_target;
        if (!editable) return;

        editable.focus();
        var sel = window.getSelection();

        if (isSelection && window.__japanese_furigana_range) {
            try {
                sel.removeAllRanges();
                sel.addRange(window.__japanese_furigana_range);
            } catch (err) {}

            var success = false;
            try {
                success = document.execCommand("insertHTML", false, newHtml);
            } catch (e) {
                success = false;
            }

            if (!success) {
                var range = window.__japanese_furigana_range;
                range.deleteContents();
                var temp = document.createElement("div");
                temp.innerHTML = newHtml;
                var frag = document.createDocumentFragment();
                var child;
                var lastChild = null;
                while ((child = temp.firstChild)) {
                    lastChild = frag.appendChild(child);
                }
                range.insertNode(frag);
                if (lastChild) {
                    range.setStartAfter(lastChild);
                    range.collapse(true);
                    sel.removeAllRanges();
                    sel.addRange(range);
                }
            }
        } else {
            var range = document.createRange();
            range.selectNodeContents(editable);
            sel.removeAllRanges();
            sel.addRange(range);

            var success = false;
            try {
                success = document.execCommand("insertHTML", false, newHtml);
            } catch (e) {
                success = false;
            }

            if (!success) {
                editable.innerHTML = newHtml;
            }
        }

        window.__japanese_furigana_range = null;

        try {
            editable.dispatchEvent(new Event("input", { bubbles: true }));
            editable.dispatchEvent(new Event("change", { bubbles: true }));
        } catch (e) {}

        var syncData = {
            nid: editable.getAttribute("data-nid") || "",
            field: editable.getAttribute("data-field") || "",
            html: editable.innerHTML
        };

        if (typeof pycmd === "function") {
            pycmd("japanese_furigana_sync#" + encodeURIComponent(JSON.stringify(syncData)));
        }
    };

    window.__japanese_furigana_config = {
        add: parseShortcut(__ADD_SHORTCUT__),
        del: parseShortcut(__DEL_SHORTCUT__)
    };

    if (!window.__japanese_furigana_keydown_bound) {
        window.__japanese_furigana_keydown_bound = true;
        document.addEventListener("keydown", function(e) {
            var cfg = window.__japanese_furigana_config;
            if (!cfg) return;

            if (eventMatches(e, cfg.add)) {
                e.preventDefault();
                e.stopPropagation();
                window.__japanese_furigana_trigger("add");
                return;
            }

            if (eventMatches(e, cfg.del)) {
                e.preventDefault();
                e.stopPropagation();
                window.__japanese_furigana_trigger("del");
                return;
            }
        }, true);
    }
})();
"""


def get_shortcut(name: str) -> str:
    default_shortcuts = {
        "add_furigana": "Ctrl+R",
        "del_furigana": "Ctrl+Alt+R",
    }
    if config:
        try:
            return config.getKeyboardShortcut(name)
        except Exception:
            pass
    return default_shortcuts.get(name, "")


def get_reviewer_js(add_shortcut: str, del_shortcut: str) -> str:
    return (
        REVIEWER_JS_TEMPLATE
        .replace("__ADD_SHORTCUT__", json.dumps(add_shortcut))
        .replace("__DEL_SHORTCUT__", json.dumps(del_shortcut))
    )


def mungeHTML(txt: str) -> str:
    return "" if txt in ("<br>", "<div><br></div>") else txt


def trigger_reviewer_action(action: str) -> None:
    if not mw or not hasattr(mw, "reviewer") or not mw.reviewer:
        return
    web = getattr(mw.reviewer, "web", None)
    if web:
        web.eval(f"if (window.__japanese_furigana_trigger) window.__japanese_furigana_trigger('{action}');")


def on_state_shortcuts_will_change(state: str, shortcuts: list) -> None:
    if state == "review":
        add_sc = get_shortcut("add_furigana")
        if add_sc:
            shortcuts.append((add_sc, lambda: trigger_reviewer_action("add")))
        del_sc = get_shortcut("del_furigana")
        if del_sc:
            shortcuts.append((del_sc, lambda: trigger_reviewer_action("del")))


def on_review_state_shortcuts(shortcuts: list) -> None:
    add_sc = get_shortcut("add_furigana")
    if add_sc:
        shortcuts.append((add_sc, lambda: trigger_reviewer_action("add")))
    del_sc = get_shortcut("del_furigana")
    if del_sc:
        shortcuts.append((del_sc, lambda: trigger_reviewer_action("del")))


def on_webview_will_set_content(web_content: Any, context: Any) -> None:
    is_rev = isinstance(context, Reviewer) or (hasattr(mw, "reviewer") and context is mw.reviewer)
    is_prev = BrowserPreviewer is not None and isinstance(context, BrowserPreviewer)
    if not (is_rev or is_prev):
        return

    add_sc = get_shortcut("add_furigana")
    del_sc = get_shortcut("del_furigana")

    js = get_reviewer_js(add_sc, del_sc)
    web_content.head += f"<script>{js}</script>"


def on_js_message(handled: tuple[bool, Any], message: str, context: Any) -> tuple[bool, Any]:
    if handled[0]:
        return handled

    is_rev = isinstance(context, Reviewer) or (hasattr(mw, "reviewer") and context is mw.reviewer)
    is_prev = BrowserPreviewer is not None and isinstance(context, BrowserPreviewer)
    if not (is_rev or is_prev):
        return handled

    if message == "japanese_furigana_no_field#":
        tooltip("No editable field focused")
        return True, None

    if message == "japanese_furigana_empty#":
        tooltip("Nothing to generate!")
        return True, None

    if message.startswith("japanese_furigana#"):
        raw_payload = message.split("#", 1)[1]
        try:
            data = json.loads(urllib.parse.unquote(raw_payload))
        except Exception:
            return True, None

        action = data.get("action")
        is_selection = data.get("isSelection", False)
        html = data.get("html", "")

        html = re.sub(r'& ?nbsp ?;', ' ', html)

        if action == "add":
            if not mecab:
                return True, None
            use_ruby = config.getUseRubyTags() if config else False
            ignore_num = config.getIgnoreNumbers() if config else True
            new_html = removeFurigana(html)
            new_html = mecab.reading(new_html, ignore_num, use_ruby)
            if new_html == html:
                tooltip("Nothing to generate!")
                return True, None
        elif action == "del":
            new_html = removeFurigana(html)
            if new_html == html:
                tooltip("No furigana found to delete")
                return True, None
        else:
            return True, None

        new_html = re.sub(r'& ?nbsp ?;', ' ', new_html)

        web = getattr(context, "web", None)
        if web is None and is_prev and hasattr(context, "_web"):
            web = context._web
        if web is None and hasattr(mw, "reviewer"):
            web = getattr(mw.reviewer, "web", None)

        if web:
            web.eval(f"if (window.__japanese_furigana_apply) window.__japanese_furigana_apply({json.dumps(new_html, ensure_ascii=False)}, {json.dumps(is_selection)});")

        return True, None

    if message.startswith("japanese_furigana_sync#"):
        raw_payload = message.split("#", 1)[1]
        try:
            data = json.loads(urllib.parse.unquote(raw_payload))
        except Exception:
            return True, None

        nid_str = data.get("nid", "")
        field = data.get("field", "")
        val = data.get("html", "")

        note = None
        if nid_str:
            try:
                nid = int(nid_str)
                if hasattr(context, "card"):
                    card = context.card() if callable(context.card) else context.card
                    if card and card.nid == nid:
                        note = card.note()
                if note is None and hasattr(mw, "col"):
                    note = mw.col.get_note(nid) if hasattr(mw.col, "get_note") else mw.col.getNote(nid)
            except Exception:
                pass

        if note is None and hasattr(mw, "reviewer") and getattr(mw.reviewer, "card", None):
            note = mw.reviewer.card.note()

        if note:
            if not field or field not in note:
                for f, v in note.items():
                    if f in ("Front", "Expression", "Text", "Japanese") or len(note.keys()) == 1:
                        field = f
                        break

            if field and field in note:
                txt = urllib.parse.unquote(val)
                txt = unicodedata.normalize("NFC", txt)
                txt = mungeHTML(txt)
                txt = txt.replace("\x00", "")
                if hasattr(mw, "col") and hasattr(mw.col, "media") and hasattr(mw.col.media, "escapeImages"):
                    txt = mw.col.media.escapeImages(txt, unescape=True)

                if note[field] != txt:
                    if hasattr(mw, "checkpoint"):
                        mw.checkpoint("Generate Furigana")
                    note[field] = txt
                    note.flush()

                    if is_prev and hasattr(context, "_parent") and hasattr(context._parent, "begin_reset"):
                        context._parent.begin_reset()
                        context._parent.end_reset()
                    else:
                        card = getattr(context, "card", None)
                        if card is None and hasattr(mw, "reviewer"):
                            card = getattr(mw.reviewer, "card", None)
                        card_obj = card() if callable(card) else card
                        if card_obj and hasattr(card_obj, "q"):
                            try:
                                card_obj.q(reload=True)
                            except Exception:
                                pass

                    if hasattr(dialogs, "_dialogs"):
                        edit_current = dialogs._dialogs.get("EditCurrent", [None, None])[1]
                        if (
                            edit_current
                            and hasattr(edit_current, "editor")
                            and edit_current.editor.note
                            and edit_current.editor.note.id == note.id
                        ):
                            edit_current.editor.set_note(note)

        return True, None

    return handled


def setupReviewer(mecab_ctrl: Any, cfg: Any) -> None:
    global mecab, config
    mecab = mecab_ctrl
    config = cfg

    try:
        gui_hooks.webview_will_set_content.append(on_webview_will_set_content)
        gui_hooks.webview_did_receive_js_message.append(on_js_message)
        if hasattr(gui_hooks, "state_shortcuts_will_change"):
            gui_hooks.state_shortcuts_will_change.append(on_state_shortcuts_will_change)
    except Exception:
        pass

    try:
        from anki.hooks import addHook
        addHook("reviewStateShortcuts", on_review_state_shortcuts)
    except Exception:
        pass
