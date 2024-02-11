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

import re

def removeFurigana(text: str):
    stripped = text

    # First, remove Ruby tags
    rubyTags: list[str] = re.findall(r"<ruby>(.*?)<\/ruby>", stripped)
    for ruby in rubyTags:
        # Figure out what the actual body of the <ruby /> tag is.
        # Current approach: strip away any HTML tags that handle the annotation, to
        # arrive at just the body. Considering only the current HTML specification,
        # the tags to strip away are: <rp>, <rt>
        body = re.sub(r"<rp>(.*?)<\/rp>|<rt>(.*?)<\/rt>", "", ruby)

        # Replace the entire <ruby> block with just the body.
        # NOTE: We'll need to include the <ruby> tags around the search string, since
        # they aren't included in the original regex response
        stripped = stripped.replace("<ruby>" + ruby + "</ruby>", body)

    # Next, remove the bracket notation
    # remove spaces only if bracket notation was used
    if "[" in stripped:
        stripped = stripped.replace(" ", "")

    stripped, _ = re.subn('\[[^\]]*\]', '', stripped)

    # Return the final string
    return stripped
