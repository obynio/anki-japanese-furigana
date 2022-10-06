# -*- coding: utf-8 -*-

import re

def removeFurigana(text: str):
    stripped = text

    # First, remove Ruby tags
    betweens = list(map(lambda x: "<ruby>"+x+"</ruby>", re.findall(r"<ruby>(.*?)<\/ruby>", stripped)))
    if len(betweens) > 0:
        for b in betweens:
            replacement = re.search(r"<ruby>(.*?)<rp>",b).group(1).strip()
            stripped = stripped.replace(b, replacement)

    # Next, remove the bracket notation
    stripped, _ = re.subn('\[[^\]]*\]', '', stripped)

    # Return the final string
    return stripped
