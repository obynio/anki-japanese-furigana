# -*- coding: utf-8 -*-

# This file is based on the Japanese Support add-on's reading.py, which can be
# found at <https://github.com/ankitects/anki-addons>.
#
# Copyright: Ankitects Pty Ltd and contributors
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
#
# Automatic reading generation with kakasi and mecab.
#

import sys
import os
import re
import subprocess
import platform

from typing import Optional

kakasiArgs = ["-isjis", "-osjis", "-u", "-JH", "-KH"]
mecabArgs = ['--node-format=%m[%f[7]] ', '--eos-format=\n',
             '--unk-format=%m[] ']

mecabDir = os.path.join(os.path.dirname(__file__), "support")

HTML_REPLACER = '▦'
NEWLINE_REPLACER = '▧'

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
    si = None

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

    def format(self, useRubyTags: bool) -> str:
        if self.reading is None:
            return self.text

        if useRubyTags:
            return "<ruby>%s<rp>(</rp><rt>%s</rt><rp>)</rp></ruby>" % (self.text, self.reading)
        else:
            return '%s[%s]' % (self.text, self.reading)

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
        self.mecab.stdin.write(expr.encode("utf-8", "ignore") + b'\n')
        self.mecab.stdin.flush()
        expr = self.mecab.stdout.readline().rstrip(b'\r\n').decode('utf-8', "ignore")
        nodes: list[ReadingNode] = []
        for node in expr.split(" "):
            if not node:
                break

            (kanji, reading) = re.match(r"(.+)\[(.*)\]", node).groups()

            # hiragana, punctuation, not japanese, or lacking a reading
            if kanji == reading or not reading:
                nodes.append(ReadingNode(kanji, None))
                continue

            # Text in sentence is katakana
            if kanji == kakasi.reading(reading):
                nodes.append(ReadingNode(kanji, None))
                continue

            # convert to hiragana
            reading = kakasi.reading(reading)

            # Text in sentence is hiragana
            if reading == kanji:
                nodes.append(ReadingNode(kanji, None))
                continue

            # don't add readings of numbers
            if ignoreNumbers and kanji in u"一二三四五六七八九十０１２３４５６７８９":
                nodes.append(ReadingNode(kanji, None))
                continue

            # strip matching characters and beginning and end of reading and kanji
            # reading should always be at least as long as the kanji
            placeL = 0
            placeR = 0
            for i in range(1, len(kanji)):
                if kanji[-i] != reading[-i]:
                    break
                placeR = i
            for i in range(0, len(kanji)-1):
                if kanji[i] != reading[i]:
                    break
                placeL = i+1
            if placeL == 0:
                if placeR == 0:
                    # CASE: The entire word receives the entire reading (no affix)
                    # Example: 男【オトコ】
                    nodes.append(ReadingNode(kanji, reading))
                else:
                    # CASE: Okurigana at the end of the kanji (reading only applies to a prefix)
                    # Example: 口走る【クチバシル】
                    nodes.append(ReadingNode(kanji[:-placeR], reading[:-placeR]))
                    nodes.append(ReadingNode(reading[-placeR:], None))
            else:
                if placeR == 0:
                    # CASE: Kanji has a prefix that's written in kana
                    # Example: お前[オマエ]
                    nodes.append(ReadingNode(reading[:placeL], None))
                    nodes.append(ReadingNode(kanji[placeL:], reading[placeL:]))
                else:
                    # CASE: Kanji has a prefix that's written in kana AND a suffix
                    # Example: みじん切り[ミジンギリ]
                    nodes.append(ReadingNode(reading[:placeL], None))
                    nodes.append(ReadingNode(kanji[placeL:-placeR], reading[placeL:-placeR]))
                    nodes.append(ReadingNode(reading[-placeR:], None))

        # Combine our nodes together into a single sentece
        fin = ''.join(node.format(useRubyTags) for node in nodes)

        # Finalize formatting
        for match in matches:
            fin = fin.replace(HTML_REPLACER, match, 1)

        fin =  re.sub(r'& ?nbsp ?;', ' ', re.sub(r"< ?br ?>", "<br>", re.sub(r"> ", ">", fin.strip())))
        return fin

# Kakasi

class KakasiController(object):

    def __init__(self):
        self.kakasi = None

    def setup(self):
        self.kakasiCmd = mungeForPlatform([os.path.join(mecabDir, "kakasi")] + kakasiArgs)
        os.environ['ITAIJIDICT'] = os.path.join(mecabDir, "itaijidict")
        os.environ['KANWADICT'] = os.path.join(mecabDir, "kanwadict")
        if not sys.platform.startswith("win32"):
            os.chmod(self.kakasiCmd[0], 0o755)

    def ensureOpen(self):
        if not self.kakasi:
            self.setup()
            try:
                self.kakasi = subprocess.Popen(self.kakasiCmd, bufsize=-1, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=si)
            except OSError:
                raise Exception("Please install kakasi")

    def reading(self, expr):
        self.ensureOpen()
        _, expr = escapeText(expr)
        self.kakasi.stdin.write(expr.encode("sjis", "ignore") + b'\n')
        self.kakasi.stdin.flush()
        res = self.kakasi.stdout.readline().rstrip(b'\r\n').decode("sjis")
        return res

# Init

kakasi = KakasiController()
mecab = MecabController()
