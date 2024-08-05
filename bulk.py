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

import time

from . import reading
from .config import Config
from .utils import removeFurigana
from aqt import *

mecab = reading.MecabController()
config = Config()

def bulkGenerate(collection, noteIds, sourceField, destinationField, progress):
    undo_entry = collection.add_custom_undo_entry('Batch Generate Furigana')
    last_progress = 0
    i = 0

    for noteId in noteIds:
        note = collection.get_note(noteId)
        note[destinationField] = generateFurigana(note[sourceField])
        collection.update_note(note)
        collection.merge_undo_entries(undo_entry)
        i += 1

        if time.time() - last_progress >= 0.1:
            progress(i, len(noteIds))
            last_progress = time.time()

def generateFurigana(html):
    html = removeFurigana(html)
    html = mecab.reading(html, config.getIgnoreNumbers(), config.getUseRubyTags())
    return html
