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

    # ensure that <ruby /> tags without the inessential <rp /> tags are stripped
    def testRemovesRubyWithoutRp(self):
        self.assertEqual(utils.removeFurigana("<ruby>日本語<rt>にほんご</rt></ruby>を<ruby>勉強<rt>べんきょう</rt></ruby>する"), "日本語を勉強する")
        self.assertEqual(utils.removeFurigana("<ruby>走<rt>はし</rt></ruby>り<ruby>込<rt>こ</rt></ruby>む"), "走り込む")

    # ensure that non-<ruby> related HTML tags are preserved
    def testPreservesOtherHtml(self):
        self.assertEqual(utils.removeFurigana("<b>日本語</b>"), "<b>日本語</b>")
        self.assertEqual(utils.removeFurigana("ビルの<ruby>形<rp>(</rp><rt>かたち</rt><rp>)</rp></ruby>はほぼ<b><u><ruby>正方形<rp>(</rp><rt>せいほうけい</rt><rp>)</rp></ruby></u></b>だった。"), "ビルの形はほぼ<b><u>正方形</u></b>だった。")

    # ensure that the utility function will remove both styles from the same string
    # (which also ensures that we're decoupled from the user's current config selection)
    def testRemovesBothNotations(self):
        self.assertEqual(utils.removeFurigana("<ruby>日本語<rp>(</rp><rt>にほんご</rt><rp>)</rp></ruby>を勉強[べんきょう]する"), "日本語を勉強する")
