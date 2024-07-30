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

import os

from aqt.utils import tooltip
from aqt.operations import QueryOp
from aqt.qt import *

from aqt import mw

from anki.hooks import addHook

from . import reading
from .config import Config
from .selection import Selection
from .utils import removeFurigana
from .bulk import bulkGenerate

mecab = reading.MecabController()
config = Config()


def setupGuiMenu():
    useRubyTags = QAction(
        "Use ruby tags", mw, checkable=True, checked=config.getUseRubyTags()
    )
    useRubyTags.toggled.connect(config.setUseRubyTags)

    ignoreNumbers = QAction(
        "Ignore numbers", mw, checkable=True, checked=config.getIgnoreNumbers()
    )
    ignoreNumbers.toggled.connect(config.setIgnoreNumbers)

    mw.form.menuTools.addSeparator()
    mw.form.menuTools.addAction(useRubyTags)
    mw.form.menuTools.addAction(ignoreNumbers)


def tooltip_with_shortcut(tip, shortcut_name):
    shortcut = config.getKeyboardShortcut(shortcut_name)
    if shortcut:
        key_str = QKeySequence(shortcut).toString(
            QKeySequence.SequenceFormat.NativeText
        )
        tip += " ({})".format(key_str)
    return tip


def addButtons(buttons, editor):
    return buttons + [
        editor.addButton(
            icon=os.path.join(os.path.dirname(__file__), "icons", "add_furigana.svg"),
            cmd="generateFurigana",
            tip=tooltip_with_shortcut(
                "Automatically generate furigana", "add_furigana"
            ),
            func=lambda ed=editor: doIt(ed, generateFurigana),
            keys=config.getKeyboardShortcut("add_furigana"),
        ),
        editor.addButton(
            icon=os.path.join(os.path.dirname(__file__), "icons", "del_furigana.svg"),
            cmd="deleteFurigana",
            tip=tooltip_with_shortcut("Delete all furigana", "del_furigana"),
            func=lambda ed=editor: doIt(ed, deleteFurigana),
            keys=config.getKeyboardShortcut("del_furigana"),
        ),
    ]

def addBrowserButtons(browser):
    menu = browser.form.menuEdit
    menu.addSeparator()
    a = menu.addAction('Bulk Generate Furigana')
    a.triggered.connect(lambda _, b=browser: onBulkUpdate(b))

def onBulkUpdate(browser):
    nids = browser.selectedNotes()
    if not nids:
        tooltip("No notes selected.")
        return

    bulkUpdate(browser, nids)

def bulkUpdate(browser, nids):
    # Extract fields from the first note
    note = mw.col.get_note(nids[0])
    fields = note.keys()

    # Set up dialog
    dialog = QDialog(browser)
    dialog.setWindowTitle('Bulk Generate Furigana for ' + str(len(nids)) + ' note(s)')

    layout = QVBoxLayout(dialog)

    sourceFieldLayout = QHBoxLayout()
    layout.addLayout(sourceFieldLayout)
    sourceFieldLabel = QLabel('Source Field')
    sourceFieldLayout.addWidget(sourceFieldLabel)
    sourceField = QComboBox()
    sourceFieldLayout.addWidget(sourceField)

    destinationFieldLayout = QHBoxLayout()
    layout.addLayout(destinationFieldLayout)
    destinationFieldLabel = QLabel('Destination Field')
    destinationFieldLayout.addWidget(destinationFieldLabel)
    destinationField = QComboBox()

    destinationFieldLayout.addWidget(destinationField)

    for field in fields:
        sourceField.addItem(field)
        destinationField.addItem(field)

    buttonsLayout = QHBoxLayout()
    layout.addLayout(buttonsLayout)
    generateButton = QPushButton('Generate', parent=dialog)
    buttonsLayout.addWidget(generateButton)

    generateButton.clicked.connect(dialog.accept)
    dialog.resize(320, 150)

    if dialog.exec():
        # Get the values *before* QueryOp otherwise the QT objects will be disposed of
        sourceField = sourceField.currentText()
        destinationField = destinationField.currentText()

        def progressCallback(i, total):
            mw.taskman.run_on_main(
                lambda: mw.progress.update(
                    label=f"{i}/{total}",
                    value=i,
                    max=total,
                )
            )

        QueryOp(
            parent=mw,
            op=lambda col: bulkGenerate(col, nids, sourceField, destinationField, progressCallback),
            success=lambda col: tooltip('Furigana generated successfully')
        ).with_progress().run_in_background()

def doIt(editor, action):
    Selection(editor, lambda s: action(editor, s))


def generateFurigana(editor, s):
    html = s.selected
    html = removeFurigana(html)
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
addHook("browser.setupMenus", addBrowserButtons)