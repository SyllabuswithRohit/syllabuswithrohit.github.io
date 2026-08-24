#!/usr/bin/env python3
"""Run the Premchand batch builder with extended-script normalization diagnostics."""

from __future__ import annotations

import re

import build_premchand_batch2 as builder

_base_romanize = builder.romanize

# Some older Hindi transcriptions use extended Devanagari characters for English,
# Persian, and Marathi loan sounds. The primary transliterator does not emit every
# one consistently, so preserve their sounds explicitly rather than deleting them.
RESIDUAL_MAP = {
    "ऄ": "a", "ऍ": "e", "ऎ": "e", "ऑ": "o", "ऒ": "o",
    "ऩ": "n", "ऱ": "r", "ऴ": "l",
    "क़": "q", "ख़": "kh", "ग़": "gh", "ज़": "z", "ड़": "d",
    "ढ़": "dh", "फ़": "f", "य़": "y",
    "ॲ": "a", "ॳ": "oe", "ॴ": "o", "ॵ": "aw", "ॶ": "ue", "ॷ": "uue",
    "।": ".", "॥": ".", "॰": ".", "ऽ": "'",
    "ँ": "n", "ं": "n", "ः": "h", "़": "", "्": "",
    "ा": "aa", "ि": "i", "ी": "ee", "ु": "u", "ू": "oo",
    "ृ": "ri", "ॄ": "ree", "ॅ": "e", "े": "e", "ै": "ai",
    "ॉ": "o", "ो": "o", "ौ": "au", "ॆ": "e", "ॊ": "o",
    "ॎ": "e", "ॏ": "aw", "॑": "", "॒": "", "॓": "", "॔": "",
}


def romanize_with_extended_cleanup(text: str) -> str:
    output = _base_romanize(text)
    for source, replacement in RESIDUAL_MAP.items():
        output = output.replace(source, replacement)

    # Vedic accents and ornamental marks have no lexical role in these prose files.
    output = re.sub(r"[\u0951-\u0954\u0964-\u0965\u0970-\u0971]", "", output)
    bad = re.search(r"[\u0900-\u097f\u0600-\u06ff]", output)
    if bad:
        raise RuntimeError(
            f"unconverted character U+{ord(bad.group()):04X} {bad.group()!r} remains"
        )
    output = re.sub(r"[ \t]+", " ", output)
    output = re.sub(r" *\n *", "\n", output)
    return output.strip()


builder.romanize = romanize_with_extended_cleanup

if __name__ == "__main__":
    raise SystemExit(builder.main())
