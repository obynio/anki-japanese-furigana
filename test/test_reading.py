import unittest

import reading

class TestReading(unittest.TestCase):

    # sentence should have readings
    def testNormalSentence(self):
        res = reading.mecab.reading("カリン、自分でまいた種は自分で刈り取れ")
        self.assertEqual(res, "カリン、自分[じぶん]でまいた種[たね]は自分[じぶん]で刈[か]り取[と]れ")

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

    # ensure that verbs with okurigana don't produce furigana for the kana portions
    def testOkurigana(self):
        actual = reading.mecab.reading("口走る")
        self.assertEqual(actual, "口走[くちばし]る")
    
    # ensure that a single word that has plain kana appearing before the kanji in
    # the word do not have attached furigana
    def testKanaPrefixes(self):
        actual = reading.mecab.reading("お前")
        self.assertEqual(actual, "お前[まえ]")

    # ensure that a single word that both begins AND ends with kana but contains
    # kanji in the middle only generates furigana for the kanji portion, and not
    # for the kana
    def testKanaPrefixSuffix(self):
        actual = reading.mecab.reading("みじん切り")
        self.assertEqual(actual, "みじん切[ぎ]り")

    # ensure that for words that have kana in between two kanji, that only the
    # kanji receive furigana readings and the kana does not
    def testKanaBetweenKanji(self):
        self.assertEqual(reading.mecab.reading("書き込む"), "書[か]き込[こ]む")
        self.assertEqual(reading.mecab.reading("走り抜く"), "走[はし]り抜[ぬ]く")
        self.assertEqual(reading.mecab.reading("走り回る"), "走[はし]り回[まわ]る")
