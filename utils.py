# -*- coding: utf-8 -*-

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
    stripped, _ = re.subn('\[[^\]]*\]', '', stripped)

    # Return the final string
    return stripped
