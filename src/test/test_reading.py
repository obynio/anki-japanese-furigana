import sys
import unittest
from unittest.mock import MagicMock, patch

sys.modules['anki'] = MagicMock()
sys.modules['anki.utils'] = MagicMock()

import reading
import re

# Just a mock to strip basic html
def stripHTML(s: str) -> str:
    cleanr = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
    cleantext = re.sub(cleanr, '', s)
    return cleantext

@patch('reading.isWin', sys.platform.startswith("win32"))
@patch('reading.isMac', sys.platform.startswith("darwin"))
@patch('reading.stripHTML', side_effect=stripHTML)
class TestReading(unittest.TestCase):

    # sentence should have readings
    def testNormalSentence(self, mock_strip):
        res = reading.mecab.reading("カリン、自分でまいた種は自分で刈り取れ")
        self.assertEqual(res, "カリン、 自分[じぶん]でまいた 種[たね]は 自分[じぶん]で 刈り取[かりと]れ")

    # kanji should have a reading
    def testNormalKanji(self, mock_strip):
        res = reading.mecab.reading("千葉")
        self.assertEqual(res, "千葉[ちば]")

    # punctuation should be ignored
    def testWithPunctuation(self, mock_strip):
        res = reading.mecab.reading("昨日、林檎を2個買った。")
        self.assertEqual(res, "昨日[きのう]、 林檎[りんご]を2 個[こ] 買[か]った。")

    # unicode characters should be ignored
    def testUnicodeChar(self, mock_strip):
        res = reading.mecab.reading("真莉、大好きだよん＾＾")
        self.assertEqual(res, "真[ま]莉、 大好[だいす]きだよん＾＾")

    # romanji numbers should not have readings
    def testRomanjiNumbers(self, mock_strip):
        res = reading.mecab.reading("彼２０００万も使った。")
        self.assertEqual(res, "彼[かれ]２０００ 万[まん]も 使[つか]った。")

    # kanji numbers should not have readings
    def testKanjiNumber(self, mock_strip):
        res = reading.mecab.reading("彼二千三百六十円も使った。")
        self.assertEqual(res, "彼[かれ]二 千[せん]三 百[ひゃく]六十 円[えん]も 使[つか]った。")