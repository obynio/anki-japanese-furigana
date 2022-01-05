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

from anki.utils import isWin, isMac

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
    if isWin:
        popen = [os.path.normpath(x) for x in popen]
        popen[0] += ".exe"
    elif not isMac:
        popen[0] += ".lin"
    return popen


class MecabController(object):

    def __init__(self):
        self.mecab = None

    def setup(self):
        self.mecabCmd = mungeForPlatform([os.path.join(mecabDir, "mecab")] + mecabArgs + ['-d', mecabDir, '-r', os.path.join(mecabDir, "mecabrc")])
        os.environ['DYLD_LIBRARY_PATH'] = mecabDir
        os.environ['LD_LIBRARY_PATH'] = mecabDir
        if not isWin:
            os.chmod(self.mecabCmd[0], 0o755)

    def ensureOpen(self):
        if not self.mecab:
            self.setup()
            try:
                self.mecab = subprocess.Popen(self.mecabCmd, bufsize=-1, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, startupinfo=si)
            except OSError:
                raise Exception(
                    "Please ensure your Linux system has 64 bit binary support.")

    def reading(self, expr, ignoreNumbers = False, useRubyTags = True):
        self.ensureOpen()
        matches, expr = escapeText(expr)
        self.mecab.stdin.write(expr.encode("utf-8", "ignore") + b'\n')
        self.mecab.stdin.flush()
        expr = self.mecab.stdout.readline().rstrip(b'\r\n').decode('utf-8', "ignore")
        out = []
        for node in expr.split(" "):
            if not node:
                break
            (kanji, reading) = re.match(r"(.+)\[(.*)\]", node).groups()
            # hiragana, punctuation, not japanese, or lacking a reading
            if kanji == reading or not reading:
                out.append(kanji)
                continue
            # katakana
            if kanji == kakasi.reading(reading):
                out.append(kanji)
                continue
            # convert to hiragana
            reading = kakasi.reading(reading)
            # ended up the same
            if reading == kanji:
                out.append(kanji)
                continue
            # don't add readings of numbers
            if ignoreNumbers and kanji in u"一二三四五六七八九十０１２３４５６７８９":
                out.append(kanji)
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
                    out.append(" %s[%s]" % (kanji, reading))
                else:
                    out.append(" %s[%s]%s" % (
                        kanji[:-placeR], reading[:-placeR], reading[-placeR:]))
            else:
                if placeR == 0:
                    out.append("%s %s[%s]" % (
                        reading[:placeL], kanji[placeL:], reading[placeL:]))
                else:
                    out.append("%s %s[%s]%s" % (
                        reading[:placeL], kanji[placeL:-placeR],
                        reading[placeL:-placeR], reading[-placeR:]))
        fin = ''.join(out)
        for match in matches:
            fin = fin.replace(HTML_REPLACER, match, 1)
        
        returnCandidate =  re.sub(r'& ?nbsp ?;', ' ', re.sub(r"< ?br ?>", "<br>", re.sub(r"> ", ">", fin.strip())))

        if not useRubyTags:
            return returnCandidate
        else:
            words = returnCandidate.split(" ")
            for i, word in enumerate(words):
                if "[" in word or "]" in word:
                    # get everthing between the brackets
                    between = re.search(r"\[(.*?)\]", word).group(1)
                    # get everything before the brackets
                    before = re.search(r"(.*?)\[", word).group(1)
                    # get everything before the closed bracket
                    toReplace = re.search(r"(.*?)\]", word).group(1) + "]"
                    words[i] = word.replace(toReplace, "<ruby>" + before + "<rp>(</rp><rt>" + between + "</rt><rp>)</rp></ruby>")
            return ''.join(words)

# Kakasi

class KakasiController(object):

    def __init__(self):
        self.kakasi = None

    def setup(self):
        self.kakasiCmd = mungeForPlatform([os.path.join(mecabDir, "kakasi")] + kakasiArgs)
        os.environ['ITAIJIDICT'] = os.path.join(mecabDir, "itaijidict")
        os.environ['KANWADICT'] = os.path.join(mecabDir, "kanwadict")
        if not isWin:
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