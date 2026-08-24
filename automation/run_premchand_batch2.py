#!/usr/bin/env python3
"""Run the Premchand batch builder with extended-script and reader-text cleanup."""

from __future__ import annotations

import re

import build_premchand_batch2 as builder

_base_romanize = builder.romanize

# Some older Hindi transcriptions use extended Devanagari characters for English,
# Persian, and Marathi loan sounds. Preserve their sounds explicitly.
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

# High-frequency repairs convert transliteration spellings into familiar, readable
# Roman Hindustani. They do not remove sentences or change narrative content.
WORD_REPAIRS = {
    "paonch": "paanch", "darajaa": "darja", "daraje": "darje",
    "bhee": "bhi", "hee": "hi", "kee": "ki", "thee": "thi",
    "nahee": "nahin", "koee": "koi", "kahee": "kahin",
    "vahee": "wahi", "yahee": "yahi", "isee": "isi", "usee": "usi",
    "kabhee": "kabhi", "abhee": "abhi", "sabhee": "sabhi",
    "mainne": "maine", "hamane": "hamne", "tumane": "tumne",
    "unhonne": "unhone", "jinadagee": "zindagi", "jindagee": "zindagi",
    "angrejee": "angrezi", "angarejee": "angrezi",
    "padhanaa": "padhna", "padhane": "padhne", "padhataa": "padhta",
    "padhatee": "padhti", "padhate": "padhte", "padhaa": "padha",
    "likhanaa": "likhna", "likhane": "likhne", "likhataa": "likhta",
    "samajhanaa": "samajhna", "samajhane": "samajhne",
    "karanaa": "karna", "karane": "karne", "karataa": "karta",
    "karatee": "karti", "karate": "karte",
    "kahanaa": "kehna", "kahane": "kehne", "kahataa": "kehta",
    "kahatee": "kehti", "kahate": "kehte",
    "rahanaa": "rehna", "rahane": "rehne", "rahataa": "rehta",
    "rahatee": "rehti", "rahate": "rehte",
    "chaahanaa": "chahna", "chaahane": "chahne", "chaahataa": "chahta",
    "chaahatee": "chahti", "chaahate": "chahte",
    "dekhanaa": "dekhna", "dekhane": "dekhne", "dekhataa": "dekhta",
    "dekhatee": "dekhti", "dekhate": "dekhte",
    "bolanaa": "bolna", "bolane": "bolne", "bolataa": "bolta",
    "bolatee": "bolti", "bolate": "bolte",
    "chalanaa": "chalna", "chalane": "chalne", "chalataa": "chalta",
    "chalatee": "chalti", "chalate": "chalte",
    "rakhanaa": "rakhna", "rakhane": "rakhne", "rakhataa": "rakhta",
    "rakhatee": "rakhti", "rakhate": "rakhte",
    "sochanaa": "sochna", "sochane": "sochne", "sochataa": "sochta",
    "poochhanaa": "poochhna", "poochhane": "poochhne",
    "khelanaa": "khelna", "khelane": "khelne",
    "milanaa": "milna", "milane": "milne",
    "laganaa": "lagna", "lagane": "lagne", "lagataa": "lagta",
    "lagatee": "lagti", "lagate": "lagte",
    "nikalanaa": "nikalna", "nikalane": "nikalne",
    "aanaa": "aana", "jaanaa": "jana", "lenaa": "lena", "denaa": "dena",
    "honaa": "hona", "hotaa": "hota", "hotee": "hoti",
    "gayaa": "gaya", "gayee": "gayi", "gaee": "gayi",
    "kiyaa": "kiya", "diyaa": "diya", "liyaa": "liya",
    "huaa": "hua", "huee": "hui", "rahaa": "raha", "rahee": "rahi",
    "meraa": "mera", "meree": "meri", "teraa": "tera", "teree": "teri",
    "apanaa": "apna", "apanee": "apni", "usakaa": "uska", "usakee": "uski",
    "unakee": "unki", "tumhaaraa": "tumhara", "tumhaaree": "tumhari",
    "badaa": "bada", "badee": "badi", "chhotaa": "chhota", "chhotee": "chhoti",
    "achchhaa": "achchha", "achchhee": "achchhi",
    "saaraa": "sara", "saaree": "sari", "jaraa": "zara",
    "jaroor": "zaroor", "jyaadaa": "zyada", "roopaye": "rupaye",
    "paanee": "paani", "ghantaa": "ghanta", "maheenaa": "mahina",
    "maheene": "mahine", "kyaa": "kya", "kahaan": "kahan",
    "yahaan": "yahan", "vahaan": "wahan", "aankhon": "aankhon",
    "shuroo": "shuru", "buniyaad": "buniyad", "majaboot": "mazboot",
    "aaleeshaan": "aalishan", "kaanoon": "kanoon", "adhikaar": "adhikar",
    "savaal": "sawal", "javaab": "jawab", "khushee": "khushi",
    "mayoosee": "mayusi", "mehanat": "mehnat", "s{}vabhaav": "swabhav",
}


def repair_reader_text(output: str) -> str:
    output = output.replace("{}", "")
    output = output.replace("||", ".").replace("|", ".")
    for source, replacement in WORD_REPAIRS.items():
        output = re.sub(rf"\b{re.escape(source)}\b", replacement, output, flags=re.IGNORECASE)

    # Repair common Hindi consonant clusters left by mechanical schwa insertion.
    output = re.sub(r"\b([A-Za-z]+)hataa\b", r"\1hta", output)
    output = re.sub(r"\b([A-Za-z]+)hatee\b", r"\1hti", output)
    output = re.sub(r"\b([A-Za-z]+)hate\b", r"\1hte", output)
    output = re.sub(r"\s+([,.;:!?])", r"\1", output)
    output = re.sub(r"([.!?])(?=[A-Za-z])", r"\1 ", output)
    output = re.sub(r"[ \t]+", " ", output)
    output = re.sub(r" *\n *", "\n", output)
    output = re.sub(r"\n{3,}", "\n\n", output)
    return output.strip()


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
    return repair_reader_text(output)


builder.romanize = romanize_with_extended_cleanup

if __name__ == "__main__":
    raise SystemExit(builder.main())
