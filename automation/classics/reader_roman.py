#!/usr/bin/env python3
"""Reader-oriented Devanagari to Roman-Hindustani conversion.

This is a deterministic accessibility pass, not a substitute for literary
translation review. It uses ITRANS only as a phonetic intermediate, then applies
stable everyday spellings and common Hindi/Urdu schwa repairs.
"""

from __future__ import annotations

import re
import unicodedata

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

ROMAN_WORDS = {
    "haiM": "hain", "hai.n": "hain", "hai~M": "hain", "hUM": "hoon", "huuM": "hoon",
    "nahIM": "nahin", "nahiiM": "nahin", "meM": "mein", "maiM": "main",
    "kyA": "kya", "kyoM": "kyon", "kyo.n": "kyon", "yah": "yeh", "vah": "woh",
    "unheM": "unhein", "useM": "use", "tumheM": "tumhein", "aura": "aur",
    "phira": "phir", "lekina": "lekin", "agara": "agar", "isa": "is", "usa": "us",
    "eka": "ek", "kucha": "kuchh", "saba": "sab", "ghara": "ghar", "dila": "dil",
    "mana": "mann", "dina": "din", "raata": "raat", "loga": "log", "baata": "baat",
    "haatha": "haath", "paira": "pair", "aankha": "aankh", "mu.nha": "munh",
    "muu.nha": "munh", "kara": "kar", "para": "par", "taraha": "tarah",
    "samaya": "samay", "pAsa": "paas", "bahuta": "bahut", "jaba": "jab",
    "taba": "tab", "aba": "ab", "kaba": "kab", "kahA.n": "kahan",
    "yahA.n": "yahan", "vahA.n": "wahan", "jAegA": "jayega", "jAegI": "jayegi",
    "AegA": "aayega", "AegI": "aayegi", "rahA": "raha", "rahI": "rahi",
    "kiyA": "kiya", "liyA": "liya", "diyA": "diya", "gayA": "gaya",
    "gayI": "gayi", "huA": "hua", "huI": "hui", "koI": "koi", "aisA": "aisa",
    "aisI": "aisi", "vaisA": "waisa", "vaisI": "waisi", "kauna": "kaun",
    "kaisa": "kaisa", "kaisee": "kaisi", "jaisA": "jaisa", "jaisI": "jaisi",
}

# Frequent forms that remain awkward after generic ITRANS normalization.
EXACT_REPAIRS = {
    "batavaare": "batware", "batavaaraa": "batwara", "sarakaara": "sarkar",
    "sarakaaron": "sarkaron", "sarakaarein": "sarkarein", "paagalakhaanaa": "pagalkhana",
    "paagalakhaanon": "pagalkhanon", "hindustaan": "Hindustan", "hindostaan": "Hindustan",
    "paakistaan": "Pakistan", "musalamaan": "Musalman", "musalamaanon": "Musalmanon",
    "hindoo": "Hindu", "sikha": "Sikh", "kaidiyon": "qaidiyon", "kaidee": "qaidi",
    "khayaala": "khayal", "khyaala": "khayal", "aayaa": "aaya", "aayee": "aayi",
    "jaaye": "jaye", "jaayen": "jayen", "jaayegaa": "jayega", "jaayegee": "jayegi",
    "chahiye": "chahiye", "yaanee": "yaani", "lekin": "lekin", "magara": "magar",
    "phira": "phir", "kyonki": "kyunki", "zarooree": "zaroori", "zaroorata": "zaroorat",
    "ijjata": "izzat", "jindagee": "zindagi", "zindagee": "zindagi", "jameena": "zameen",
    "aadamee": "aadmi", "insaan": "insaan", "duniyaa": "duniya", "pyaara": "pyaar",
    "mohabbata": "mohabbat", "khushee": "khushi", "nafarata": "nafrat",
    "intejaara": "intezar", "intajaara": "intezar", "aphasara": "afsar",
    "aphasaron": "afsaron", "paisa": "paisa", "rupaye": "rupaye", "rupayaa": "rupaya",
    "gaanva": "gaon", "shahara": "shehar", "makaan": "makaan", "ghara": "ghar",
    "aurata": "aurat", "bachchaa": "bachcha", "bachchee": "bachchi", "bachche": "bachche",
    "ladakaa": "ladka", "ladakee": "ladki", "ladake": "ladke", "badaa": "bada",
    "chhotaa": "chhota", "thodaa": "thoda", "jyaadaa": "zyada", "zyaadaa": "zyada",
    "achchhaa": "achchha", "achchhee": "achchhi", "achchhe": "achchhe",
    "dekhaa": "dekha", "dekhee": "dekhi", "dekhe": "dekhe", "kahaa": "kaha",
    "bolaa": "bola", "bolee": "boli", "karanaa": "karna", "rahanaa": "rahna",
    "chalanaa": "chalna", "honA": "hona", "hotaa": "hota", "hotee": "hoti",
    "hote": "hote", "thaa": "tha", "thee": "thi", "the": "the", "rahaa": "raha",
    "rahee": "rahi", "rahe": "rahe", "gayaa": "gaya", "gayee": "gayi",
    "diyaa": "diya", "liyaa": "liya", "kiyaa": "kiya", "huaa": "hua",
    "huee": "hui", "aanaa": "aana", "jaanaa": "jana", "denaa": "dena",
    "lenaa": "lena", "milanaa": "milna", "rakhanaa": "rakhna", "samajhanaa": "samajhna",
    "poochhanaa": "poochhna", "nikalanaa": "nikalna", "pahunchanaa": "pahunchna",
}


def _replace_exact_words(text: str, mapping: dict[str, str]) -> str:
    for old, new in sorted(mapping.items(), key=lambda item: len(item[0]), reverse=True):
        text = re.sub(rf"(?<![A-Za-z]){re.escape(old)}(?![A-Za-z])", new, text, flags=re.IGNORECASE)
    return text


def romanize_devanagari(text: str) -> str:
    text = unicodedata.normalize("NFC", text).translate(DEV_DIGITS)
    out = transliterate(text, sanscript.DEVANAGARI, sanscript.ITRANS)

    # ITRANS symbols -> familiar reader spellings.
    out = out.replace("RRi", "ri").replace("RRI", "ree").replace("LLi", "li")
    out = out.replace("Ch", "chh").replace("Th", "th").replace("Dh", "dh")
    out = out.replace("T", "t").replace("D", "d").replace("N", "n")
    out = out.replace("~n", "n").replace("~N", "n")
    out = out.replace("Sh", "sh").replace("shh", "sh").replace("S", "sh")
    out = out.replace("j~n", "gy").replace("GY", "gy")
    out = out.replace("A", "aa").replace("I", "ee").replace("U", "oo")
    out = out.replace("R", "r").replace("L", "l")
    out = out.replace("M", "n").replace("H", "h")
    out = out.replace(".a", "").replace(".n", "n").replace("~", "")

    for old, new in ROMAN_WORDS.items():
        out = re.sub(rf"\b{re.escape(old)}\b", new, out)

    repairs = [
        (r"aa([,.!?;:])", r"a\1"),
        (r"([kgcjtdnpbmyrlvshf])ataa\b", r"\1ata"),
        (r"([kgcjtdnpbmyrlvshf])anaa\b", r"\1ana"),
        (r"([kgcjtdnpbmyrlvshf])iyaa\b", r"\1iya"),
        (r"\bkarataa\b", "karta"), (r"\bkaratee\b", "karti"),
        (r"\bkarate\b", "karte"), (r"\bkahataa\b", "kehta"),
        (r"\bkahatee\b", "kehti"), (r"\bkahate\b", "kehte"),
        (r"\bjaataa\b", "jata"), (r"\bjaatee\b", "jati"),
        (r"\baataa\b", "aata"), (r"\baatee\b", "aati"),
        (r"\bbolatee\b", "bolti"), (r"\bbolate\b", "bolte"),
        (r"\bpa\.Daa\b", "pada"), (r"\bba\.Daa\b", "bada"),
        (r"\bla\.Dak", "ladak"),
    ]
    for pattern, replacement in repairs:
        out = re.sub(pattern, replacement, out, flags=re.IGNORECASE)

    out = _replace_exact_words(out, EXACT_REPAIRS)
    out = re.sub(r"\.{2,}", "...", out)
    out = re.sub(r"[ \t]+", " ", out)
    out = re.sub(r" *\n *", "\n", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()
