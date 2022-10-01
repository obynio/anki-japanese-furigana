import unittest

import reading

class TestReading(unittest.TestCase):

    # sentence should have readings
    def testNormalSentence(self):
        res = reading.mecab.reading("カリン、自分でまいた種は自分で刈り取れ")
        self.assertEqual(res, "カリン、自分[じぶん]でまいた種[たね]は自分[じぶん]で刈り取[かりと]れ")

    # kanji should have a reading
    def testNormalKanji(self):
        res = reading.mecab.reading("千葉")
        self.assertEqual(res, "千葉[ちば]")

    # punctuation should be ignored
    def testWithPunctuation(self):
        res = reading.mecab.reading("昨日、林檎を2個買った。")
        self.assertEqual(res, "昨日[きのう]、林檎[りんご]を2個[こ]買[か]った。")

    # unicode characters should be ignored
    def testUnicodeChar(self):
        res = reading.mecab.reading("真莉、大好きだよん＾＾")
        self.assertEqual(res, "真[ま]莉、大好[だいす]きだよん＾＾")

    # romanji numbers should not have readings
    def testRomanjiNumbers(self):
        res = reading.mecab.reading("彼２０００万も使った。")
        self.assertEqual(res, "彼[かれ]２０００万[まん]も使[つか]った。")

    # kanji numbers should not have readings
    def testKanjiNumber(self):
        res = reading.mecab.reading("彼二千三百六十円も使った。")
        self.assertEqual(res, "彼[かれ]二千[せん]三百[ひゃく]六十円[えん]も使[つか]った。")