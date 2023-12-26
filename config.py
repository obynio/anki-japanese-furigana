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

from aqt.addons import AbortAddonImport
from aqt import mw


def saveMe(func):
    def wrapper(self, *args):
        func(self, args)
        mw.addonManager.writeConfig(__name__, self.data)

    return wrapper


class Config:
    def __init__(self):
        if mw is None:
            raise AbortAddonImport("No Anki main window?")

        self.data = mw.addonManager.getConfig(__name__)

    def getUseRubyTags(self):
        return self.data["useRubyTags"]

    @saveMe
    def setUseRubyTags(self, isEnabled):
        self.data["useRubyTags"] = isEnabled[0]

    @saveMe
    def setIgnoreNumbers(self, isEnabled):
        self.data["ignoreNumbers"] = isEnabled[0]

    @saveMe
    def setUseRubyTags(self, isEnabled):
        self.data["useRubyTags"] = isEnabled[0]

    @saveMe
    def setKeyboardShortcut(self, name, key):
        self.data["keyboardShortcut"][name] = key

    def getIgnoreNumbers(self):
        return self.data["ignoreNumbers"]

    def getIgnoreNumbers(self):
        return self.data["ignoreNumbers"]

    def getKeyboardShortcut(self, name):
        return self.data["keyboardShortcut"][name]
