import unittest

import reading

class TestMecab(unittest.TestCase):

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

    # ensure that any regular ASCII space characters (0x20) that are in the original
    # string are found in the resultant string as well
    def testSpacesRetained(self):
        self.assertEqual(reading.mecab.reading("この文に 空白が あります"), "この文[ぶん]に 空白[くうはく]が あります")
        self.assertEqual(reading.mecab.reading("hello world"), "hello world")

class TestKakasi(unittest.TestCase):
    # ensure that if the function is called with an empty string, it will return
    # an empty string
    def testEmptyReturnsEmpty(self):
        self.assertEqual(reading.kakasi.reading(""), "")

    # ensure that any non-Japanese characters provided to Kakasi are returned
    # exactly as they are
    def testEnglishReturnsSelf(self):
        self.assertEqual(reading.kakasi.reading("hello world"), "hello world")

    # ensure that if hiragana is provided to Kakasi, that it will return back the
    # same hiragana
    def testHiraReturnsSelf(self):
        self.assertEqual(reading.kakasi.reading("にほんご"), "にほんご")
        self.assertEqual(reading.kakasi.reading("あ"), "あ")
        self.assertEqual(reading.kakasi.reading("あじ"), "あじ")

    # ensure that katakana provided to Kakasi returns the hiragana equivalent
    def testKataReturnsHira(self):
        self.assertEqual(reading.kakasi.reading("ニホンゴ"), "にほんご")
        self.assertEqual(reading.kakasi.reading("ア"), "あ")
        self.assertEqual(reading.kakasi.reading("アジ"), "あじ")
        self.assertEqual(reading.kakasi.reading("ローマ"), "ろーま")

    # ensure that Kakasi supports strings that contain a mixture of hiragana and
    # katakana, and will always return the entire string in hiragana
    def testMixtureReturnsFullHira(self):
        self.assertEqual(reading.kakasi.reading("おカネ"), "おかね")
        self.assertEqual(reading.kakasi.reading("ポケもり"), "ぽけもり")

    # Standalone diacritic characters should be preserved. These will be common
    # especially in manga to make "impossible" sounds.
    def testStandaloneDiacritics(self):
        self.assertEqual(reading.kakasi.reading("あ゜"), "あ゜")
        self.assertEqual(reading.kakasi.reading("イ゜"), "い゜")
        self.assertEqual(reading.kakasi.reading("あ゛"), "あ゛")
        self.assertEqual(reading.kakasi.reading("イ゛"), "い゛")

    # Ensure that Kakasi preserves any punctuation characters
    def testPreservesPunctuation(self):
        self.assertEqual(reading.kakasi.reading("にほんへ。"), "にほんへ。")
        self.assertEqual(reading.kakasi.reading("ポケットモンスター ダイヤモンド・パール"), "ぽけっともんすたー だいやもんど・ぱーる")

    # Ensure that any ASCII whitespace (0x20) that goes in returns as an ASCII
    # whitespace character, rather than being converted to CJK space (0x3000)
    def testPreserveAsciiWhitespace(self):
        self.assertEqual(reading.kakasi.reading("しょしんしゃ です"), "しょしんしゃ です")

    # Kakasi doesn't support half-width conversion, so ensure that half-width
    # kana return the same characters
    def testHalfWidthKata(self):
        self.assertEqual(reading.kakasi.reading("ﾒｶﾞﾈ"), "ﾒｶﾞﾈ")
        self.assertEqual(reading.kakasi.reading("ｱ"), "ｱ")
        self.assertEqual(reading.kakasi.reading("ﾊﾞｶ"), "ﾊﾞｶ")

    # Ensure that small katakana characters are converted to their hiragana equivalent
    def testSmallKana(self):
        self.assertEqual(reading.kakasi.reading("ウィキペディア"), "うぃきぺでぃあ")
        self.assertEqual(reading.kakasi.reading("ぁ"), "ぁ")
        self.assertEqual(reading.kakasi.reading("ァ"), "ぁ")
        self.assertEqual(reading.kakasi.reading("ツィッター"), "つぃったー")
        self.assertEqual(reading.kakasi.reading("ぁぃぅぇぉ"), "ぁぃぅぇぉ")
        self.assertEqual(reading.kakasi.reading("ァィゥェォ"), "ぁぃぅぇぉ")
