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

import sys
import os
import re
import subprocess
import platform

from typing import Any, List, Mapping, Optional, Union

mecabArgs = ['--node-format=%m[%f[7]] ', '--eos-format=\n',
             '--unk-format=%m[] ']

mecabDir = os.path.join(os.path.dirname(__file__), "support")

HTML_REPLACER = '▦'
NEWLINE_REPLACER = '▧'

# Unicode character used to replace ASCII Space (0x20) in expression before
# passing in to MeCab. MeCab separates kanji/reading nodes with ASCII spaces,
# so without this we wouldn't be able to tell apart a node separator from a
# space character in the original string.
# This is unique to ASCII Space (0x20) and does not apply to any other whitespace
# character (eg CJK Space)
# Codepoint chosen to be a unicode character unlikely to ever feature in ANY
# Anki card.
ASCII_SPACE_TOKEN = u"\U0000FFFF"

def htmlReplace(text):
    pattern = r"(?:<[^<]+?>)"
    matches = re.findall(pattern, text)
    text = re.sub(r"<[^<]+?>", HTML_REPLACER, text)
    return matches, text

def escapeText(text):
    text = text.replace("\n", " ")
    text = text.replace(u'\uff5e', "~")
    text = re.sub("<br( /)?>", NEWLINE_REPLACER, text)
    #showInfo(text)
    matches, text = htmlReplace(text)
    text = text.replace(NEWLINE_REPLACER, "<br>")
    return matches, text

if sys.platform == "win32":
    si = subprocess.STARTUPINFO()
    try:
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    except:
        si.dwFlags |= subprocess._subprocess.STARTF_USESHOWWINDOW
else:
    si: Optional[Any] = None

# Syllabary utilities
UNICODE_HIRAGANA_START = 0x3041
UNICODE_HIRAGANA_END = 0x309F
UNICODE_KATAKANA_START = 0x30A1
UNICODE_KATAKANA_END = 0x30FF

UNICODE_MIDDLE_DOT = 0x30FB # '・'
UNICODE_PROLONGED_SOUND_MARK = 0x30FC # 'ー'

class Translator(Mapping[int, Union[str, int, None]]):
    def __getitem__(self, key: int) -> Union[str, int, None]:
        if not isinstance(key, int):
            # Argument error
            raise LookupError()
        
        if key >= UNICODE_KATAKANA_START and key <= UNICODE_KATAKANA_END:
            # Some general punctuation is located within the Katakana block
            # and SHOULDN'T be transformed
            if key == UNICODE_MIDDLE_DOT or key == UNICODE_PROLONGED_SOUND_MARK:
                raise LookupError()

            # Regular katakana Unicode block
            offset = key - UNICODE_KATAKANA_START
            return UNICODE_HIRAGANA_START + offset

        # Not a character we're converting
        raise LookupError()

    def __len__(self) -> int:
        # Exists only to satisfy base type
        raise NotImplementedError()

    def __iter__(self):
        # Exists only to satisfy base type
        raise NotImplementedError()

translator = Translator()

def convertToHiragana(expr: str) -> str:
    return expr.translate(translator)

def getAdditionalPossibleReadings(hiragana: str) -> Optional[List[str]]:
    # The little ヵ and ヶ can show up in readings as "か" (eg: ヶ月, ヵ国, etc)
    if hiragana == 'ゕ' or hiragana == 'ゖ':
        return ['か']

    return None

def isKana(char: str) -> bool:
    code = ord(char)

    # Hiragana
    if code >= UNICODE_HIRAGANA_START and code <= UNICODE_HIRAGANA_END:
        return True

    # Katakana
    if code >= UNICODE_KATAKANA_START and code <= UNICODE_KATAKANA_END:
        return True

    return False

# Mecab

def mungeForPlatform(popen):
    if sys.platform.startswith("win32"):
        popen = [os.path.normpath(x) for x in popen]
        popen[0] += ".exe"
    elif not sys.platform.startswith("darwin"):
        popen[0] += ".lin"
    elif platform.machine().startswith("arm"):
        popen[0] += ".arm"
    return popen

class ReadingNode:
    def __init__(self, text: str, reading: Optional[str]):
        self.text = text
        self.reading = reading

    def format(self, useRubyTags: bool, previous_character: str) -> str:
        if self.reading is None:
            return self.text

        if useRubyTags:
            return "<ruby>{}<rp>(</rp><rt>{}</rt><rp>)</rp></ruby>".format(self.text, self.reading)
        else:
            add_space = previous_character is not None and previous_character != "]"
            return '{}{}[{}]'.format(" " if add_space else "", self.text, self.reading)

class RegexDefinition:
    def __init__(self, text: str, regexGroupIndex: Optional[int]):
        self.text = text
        self.regexGroupIndex = regexGroupIndex

def kanjiToRegex(kanji: str):
    regexPieces: list[str] = []
    definitions: list[RegexDefinition] = []
    numCaptureGroups = 0
    index = 0
    while index < len(kanji):
        # Hiragana and Katakana characters are inlined into the Regex
        if isKana(kanji[index]):
            # The reading variable is ALWAYS in hiragana only
            hiragana = convertToHiragana(kanji[index])

            additional = getAdditionalPossibleReadings(hiragana)
            if additional:
                # If it's possible that this kana could be read as a totally different kana
                # (eg "ヶ" being read as "か"), we want to give it furigana.
                # We'll register it as a capture group -- both because we don't know
                # for SURE which reading we're expecting (so we'll register multiple
                # possibilities), but ALSO so that we can go down the furigana generation
                # pathway that's normally/usually reserved for kanji
                regexPieces.append("(" + "|".join([hiragana] + additional) + ")")

                # Use kanji[index] here to retain original katakana/hiragana
                # (We convert to hiragana just to match against reading)
                definitions.append(RegexDefinition(kanji[index], numCaptureGroups))
                numCaptureGroups += 1
            else:
                regexPieces.append(hiragana)

                # Use kanji[index] here to retain original katakana/hiragana
                # (We convert to hiragana just to match against reading)
                definitions.append(RegexDefinition(kanji[index], None))

            # Advance to the next character
            index += 1
            continue

        # We have a kanji character, which will become a lazy capture group
        # in our Regex. First, absorb all sequential kanji characters into a
        # single capture group
        captureGroup = ""
        while index < len(kanji) and not isKana(kanji[index]):
            captureGroup += kanji[index]
            index += 1

        regexPieces.append("(.+?)")
        definitions.append(RegexDefinition(captureGroup, numCaptureGroups))
        numCaptureGroups += 1

    return ("^{}$".format(str().join(regexPieces)), definitions)

class MecabController(object):

    def __init__(self):
        self.mecab = None

    def setup(self):
        self.mecabCmd = mungeForPlatform([os.path.join(mecabDir, "mecab")] + mecabArgs + ['-d', mecabDir, '-r', os.path.join(mecabDir, "mecabrc")])
        os.environ['DYLD_LIBRARY_PATH'] = mecabDir
        os.environ['LD_LIBRARY_PATH'] = mecabDir
        if not sys.platform.startswith("win32"):
            os.chmod(self.mecabCmd[0], 0o755)

    def ensureOpen(self):
        if not self.mecab:
            self.setup()
            try:
                self.mecab = subprocess.Popen(self.mecabCmd, bufsize=-1, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=si)
            except OSError:
                raise Exception(
                    "Please ensure your Linux system has 64 bit binary support.")

    def reading(self, expr, ignoreNumbers = True, useRubyTags = False):
        self.ensureOpen()
        matches, expr = escapeText(expr)
        expr = expr.replace(" ", ASCII_SPACE_TOKEN)
        self.mecab.stdin.write(expr.encode("utf-8", "ignore") + b'\n')
        self.mecab.stdin.flush()
        expr = self.mecab.stdout.readline().rstrip(b'\r\n').decode('utf-8', "ignore")
        nodes: list[ReadingNode] = []
        for node in expr.split(" "):
            if not node:
                break

            (kanji, reading) = re.match(r"(.+)\[(.*)\]", node).groups()

            # katakana, punctuation, not japanese, or lacking a reading
            # NOTE: Katakana goes down this path because Mecab returns all
            # readings in katakana, so a katakana word looks like 'カリン[カリン]'
            if kanji == reading or not reading:
                nodes.append(ReadingNode(kanji, None))
                continue

            # convert reading from katakana to hiragana
            reading = convertToHiragana(reading)

            # Text in sentence is hiragana
            if kanji == reading:
                nodes.append(ReadingNode(kanji, None))
                continue

            # don't add readings of numbers
            if ignoreNumbers and kanji in u"一二三四五六七八九十０１２３４５６７８９":
                nodes.append(ReadingNode(kanji, None))
                continue

            # Convert the kanji variable into a Regex pattern where non-kana are
            # turned into Regex capture groups, and then apply it to the reading
            # to figure out (using lazy matching) what the smallest furigana readings
            # are for the kanji
            (regexPattern, regexDefinitions) = kanjiToRegex(kanji)
            match = re.search(regexPattern, reading)
            for definition in regexDefinitions:
                if definition.regexGroupIndex is None:
                    nodes.append(ReadingNode(definition.text, None))
                else:
                    groupReading = match.group(definition.regexGroupIndex + 1)
                    nodes.append(ReadingNode(definition.text, groupReading))

        # Combine our nodes together into a single sentece
        fin = str()
        for node in nodes:
            fin += node.format(useRubyTags, fin[-1] if len(fin) > 0 else None)

        # Finalize formatting
        fin = fin.replace(ASCII_SPACE_TOKEN, ' ')
        for match in matches:
            fin = fin.replace(HTML_REPLACER, match, 1)

        fin =  re.sub(r'& ?nbsp ?;', ' ', re.sub(r"< ?br ?>", "<br>", re.sub(r"> ", ">", fin.strip())))
        return fin

# Init

mecab = MecabController()
