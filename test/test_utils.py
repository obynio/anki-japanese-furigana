import unittest

import utils

class TestRemoveFurigana(unittest.TestCase):

    # empty string should return empty string
    def testEmptyString(self):
        self.assertEqual(utils.removeFurigana(""), "")

    # ensure that bracket notation is correctly removed
    def testRemovesBrackets(self):
        self.assertEqual(utils.removeFurigana("日本語[にほんご]を勉強[べんきょう]する"), "日本語を勉強する")
        self.assertEqual(utils.removeFurigana("走[はし]り込[こ]む"), "走り込む")

    # ensure that ruby tags are correctly removed
    def testRemovesRuby(self):
        self.assertEqual(utils.removeFurigana("<ruby>日本語<rp>(</rp><rt>にほんご</rt><rp>)</rp></ruby>を<ruby>勉強<rp>(</rp><rt>べんきょう</rt><rp>)</rp></ruby>する"), "日本語を勉強する")
        self.assertEqual(utils.removeFurigana("<ruby>走<rp>(</rp><rt>はし</rt><rp>)</rp></ruby>り<ruby>込<rp>(</rp><rt>こ</rt><rp>)</rp></ruby>む"), "走り込む")
