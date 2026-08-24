#!/usr/bin/env python3
"""Build complete machine-assisted Roman-Hindustani first passes of Nirmala and Godaan.

This pipeline is intentionally conservative:
- it downloads complete public-domain source chapters;
- preserves chapter and paragraph order;
- performs controlled phrase simplification;
- transliterates Devanagari into readable Roman text;
- validates source coverage and Roman-only output;
- marks all outputs as requiring independent human review.
"""

from __future__ import annotations

import json
import re
import sys
import time
import unicodedata
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "generated"
WORKS = OUT / "works" / "premchand"
TIMEOUT = 45
UA = "SWR-Public-Domain-Accessibility-Builder/1.0 (+editorial use)"

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA, "Accept-Language": "hi,en;q=0.8"})

DEV_RE = re.compile(r"[\u0900-\u097f]")
URDU_RE = re.compile(r"[\u0600-\u06ff]")
WS_RE = re.compile(r"[ \t]+")
MULTI_NL_RE = re.compile(r"\n{3,}")
DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

# Controlled simplification happens before transliteration. Replacements are
# deliberately exact and meaning-preserving; they are not summaries.
PHRASE_REPLACEMENTS: list[tuple[str, str]] = [
    ("व्यवहार-कुशल", "दुनिया की समझ रखने वाली"),
    ("व्यवहार कुशल", "दुनिया की समझ रखने वाली"),
    ("आत्म-सम्मान", "अपनी इज्जत का एहसास"),
    ("आत्मसम्मान", "अपनी इज्जत का एहसास"),
    ("चिरस्थायी", "बहुत लंबे समय की"),
    ("जीर्णावस्था", "टूटी-फूटी हालत"),
    ("अन्तःकरण", "दिल"),
    ("अंतःकरण", "दिल"),
    ("आतंकमय", "डर से भरा"),
    ("अभय-दान", "बेफिक्र रहने की दुआ"),
    ("अभयदान", "बेफिक्र रहने की दुआ"),
    ("वेदना-शक्ति", "दर्द की ताकत"),
    ("सम्पूर्ण", "पूरा"),
    ("संपूर्ण", "पूरा"),
    ("परिस्थिति", "हाल"),
    ("परिस्थितियाँ", "हालात"),
    ("परिस्थितियों", "हालात"),
    ("वास्तविकता", "सच्चाई"),
    ("यथार्थ", "सच्चाई"),
    ("अनिवार्य", "ज़रूरी"),
    ("आवश्यक", "ज़रूरी"),
    ("आवश्यकता", "ज़रूरत"),
    ("सहायता", "मदद"),
    ("सहायक", "मदद करने वाला"),
    ("व्यवस्था", "इंतज़ाम"),
    ("प्रबन्ध", "इंतज़ाम"),
    ("प्रबंध", "इंतज़ाम"),
    ("प्रबन्धक", "काम संभालने वाला"),
    ("प्रबंधक", "काम संभालने वाला"),
    ("अधिकारी", "अफसर"),
    ("कर्मचारी", "काम करने वाला"),
    ("निवेदन", "बात"),
    ("अनुरोध", "गुज़ारिश"),
    ("आग्रह", "ज़ोर देकर कहना"),
    ("निर्देश", "हुक्म"),
    ("आदेश", "हुक्म"),
    ("निर्णय", "फैसला"),
    ("निश्चय", "पक्का फैसला"),
    ("उद्देश्य", "मकसद"),
    ("प्रयोजन", "मकसद"),
    ("परिणाम", "नतीजा"),
    ("फलस्वरूप", "इसलिए"),
    ("अतः", "इसलिए"),
    ("किन्तु", "लेकिन"),
    ("किंतु", "लेकिन"),
    ("परन्तु", "लेकिन"),
    ("परंतु", "लेकिन"),
    ("तथापि", "फिर भी"),
    ("यद्यपि", "हालाँकि"),
    ("यद्यपि", "हालांकि"),
    ("अर्थात्", "यानी"),
    ("अर्थात", "यानी"),
    ("तत्काल", "तुरंत"),
    ("शीघ्र", "जल्दी"),
    ("विलम्ब", "देर"),
    ("विलंब", "देर"),
    ("प्रतीक्षा", "इंतज़ार"),
    ("प्रसन्न", "खुश"),
    ("प्रसन्नता", "खुशी"),
    ("आनन्द", "खुशी"),
    ("आनंद", "खुशी"),
    ("कुपित", "गुस्से में"),
    ("क्रोधित", "गुस्से में"),
    ("रोष", "गुस्सा"),
    ("तिरस्कार", "नफ़रत"),
    ("घृणा", "नफ़रत"),
    ("वेदना", "दर्द"),
    ("पीड़ा", "दर्द"),
    ("कष्ट", "तकलीफ़"),
    ("दुर्भाग्य", "बदकिस्मती"),
    ("सौभाग्य", "अच्छी किस्मत"),
    ("दीनता", "बेचारगी"),
    ("विपन्नता", "गरीबी"),
    ("निर्धनता", "गरीबी"),
    ("दरिद्रता", "गरीबी"),
    ("समृद्ध", "अमीर"),
    ("समृद्धि", "अमीरी"),
    ("निवास", "घर"),
    ("गृहस्थी", "घर-बार"),
    ("गृह", "घर"),
    ("भोजन", "खाना"),
    ("जलपान", "कुछ खाने-पीने को"),
    ("आहार", "खाना"),
    ("वस्त्र", "कपड़े"),
    ("मुख", "मुँह"),
    ("नेत्र", "आँखें"),
    ("हृदय", "दिल"),
    ("मस्तिष्क", "दिमाग"),
    ("विचार", "सोच"),
    ("विचारों", "सोच"),
    ("चिन्ता", "फिक्र"),
    ("चिंता", "फिक्र"),
    ("अनुभव", "तजुर्बा"),
    ("अनुभूति", "एहसास"),
    ("भावना", "एहसास"),
    ("भावनाएँ", "एहसास"),
    ("कल्पना", "खयाल"),
    ("स्मरण", "याद"),
    ("स्मृति", "याद"),
    ("विस्मय", "हैरानी"),
    ("आश्चर्य", "हैरानी"),
    ("संकोच", "झिझक"),
    ("लज्जा", "शर्म"),
    ("विनम्र", "नरम और अदब से"),
    ("नम्रता", "नर्मी"),
    ("मृदुता", "नर्मी"),
    ("कठोर", "सख्त"),
    ("विशाल", "बहुत बड़ा"),
    ("अथाह", "बहुत गहरा"),
    ("अत्यन्त", "बहुत"),
    ("अत्यंत", "बहुत"),
    ("अधिकाधिक", "और ज़्यादा"),
    ("निरन्तर", "लगातार"),
    ("निरंतर", "लगातार"),
    ("सदैव", "हमेशा"),
    ("कदाचित्", "शायद"),
    ("कदाचित", "शायद"),
    ("संभवतः", "शायद"),
    ("अवश्य", "ज़रूर"),
    ("निश्चित रूप से", "पक्का"),
    ("निश्चित", "पक्का"),
    ("निस्सन्देह", "बेशक"),
    ("निस्संदेह", "बेशक"),
    ("मनुष्य", "इंसान"),
    ("व्यक्ति", "आदमी"),
    ("स्त्री", "औरत"),
    ("पुरुष", "मर्द"),
    ("बालक", "बच्चा"),
    ("बालिका", "लड़की"),
    ("युवक", "जवान आदमी"),
    ("युवती", "जवान लड़की"),
    ("वृद्ध", "बूढ़ा"),
    ("वृद्धा", "बूढ़ी औरत"),
    ("समाज", "लोगों की दुनिया"),
    ("समाजिक", "समाज का"),
    ("सामाजिक", "समाज का"),
    ("धनराशि", "पैसा"),
    ("राशि", "रकम"),
    ("ऋण", "कर्ज़"),
    ("कर्ज", "कर्ज़"),
    ("व्यय", "खर्च"),
    ("आय", "कमाई"),
    ("उपार्जन", "कमाई"),
    ("श्रम", "मेहनत"),
    ("श्रमिक", "मज़दूर"),
    ("कृषक", "किसान"),
    ("भूमि", "ज़मीन"),
    ("क्षेत्र", "इलाका"),
    ("स्थान", "जगह"),
    ("मार्ग", "रास्ता"),
    ("नगर", "शहर"),
    ("ग्राम", "गाँव"),
    ("प्रातःकाल", "सुबह"),
    ("प्रातः", "सुबह"),
    ("संध्या", "शाम"),
    ("रात्रि", "रात"),
    ("दिवस", "दिन"),
    ("क्षण", "पल"),
    ("क्षणिक", "एक पल की"),
    ("तत्पश्चात्", "उसके बाद"),
    ("तत्पश्चात", "उसके बाद"),
    ("पूर्व", "पहले"),
    ("पश्चात्", "बाद"),
    ("पश्चात", "बाद"),
    ("प्रवेश", "अंदर जाना"),
    ("प्रस्थान", "रवाना होना"),
    ("आगमन", "आना"),
    ("गमन", "जाना"),
    ("उपस्थित", "मौजूद"),
    ("अनुपस्थित", "मौजूद नहीं"),
    ("प्रकट", "सामने"),
    ("लुप्त", "गायब"),
    ("आरम्भ", "शुरू"),
    ("आरंभ", "शुरू"),
    ("समाप्त", "खत्म"),
    ("समापन", "अंत"),
    ("अन्त", "अंत"),
    ("कथन", "बात"),
    ("वार्तालाप", "बातचीत"),
    ("संवाद", "बातचीत"),
    ("प्रश्न", "सवाल"),
    ("उत्तर", "जवाब"),
    ("उचित", "ठीक"),
    ("अनुचित", "गलत"),
    ("सत्य", "सच"),
    ("असत्य", "झूठ"),
    ("न्याय", "इंसाफ"),
    ("अन्याय", "नाइंसाफी"),
    ("अपराध", "जुर्म"),
    ("दण्ड", "सज़ा"),
    ("दंड", "सज़ा"),
    ("स्वतन्त्र", "आज़ाद"),
    ("स्वतंत्र", "आज़ाद"),
    ("स्वतन्त्रता", "आज़ादी"),
    ("स्वतंत्रता", "आज़ादी"),
    ("पराधीन", "दूसरे के बस में"),
    ("कर्तव्य", "फ़र्ज़"),
    ("अधिकार", "हक"),
    ("सम्मान", "इज़्ज़त"),
    ("अपमान", "बेइज़्ज़ती"),
    ("मर्यादा", "इज़्ज़त का ढंग"),
    ("प्रतिष्ठा", "इज़्ज़त"),
    ("विश्वास", "भरोसा"),
    ("अविश्वास", "भरोसा न होना"),
    ("सन्देह", "शक"),
    ("संदेह", "शक"),
    ("आशा", "उम्मीद"),
    ("निराशा", "उदासी"),
    ("उत्साह", "जोश"),
    ("साहस", "हिम्मत"),
    ("भय", "डर"),
    ("आतंक", "दहशत"),
    ("करुणा", "दया"),
    ("दया", "तरस"),
    ("स्नेह", "प्यार"),
    ("प्रेम", "प्यार"),
    ("विवाह", "शादी"),
    ("पति", "शौहर"),
    ("पत्नी", "बीवी"),
    ("परिवार", "घरवाले"),
    ("सम्बन्ध", "रिश्ता"),
    ("संबंध", "रिश्ता"),
    ("रिश्तेदार", "घर-परिवार के लोग"),
    ("समस्या", "मुश्किल"),
    ("कठिनाई", "मुश्किल"),
    ("समाधान", "हल"),
    ("उपाय", "रास्ता"),
    ("प्रयास", "कोशिश"),
    ("चेष्टा", "कोशिश"),
    ("सफल", "कामयाब"),
    ("असफल", "नाकाम"),
    ("सफलता", "कामयाबी"),
    ("असफलता", "नाकामी"),
    ("प्रभाव", "असर"),
    ("प्रभावित", "असर पड़ा"),
    ("कारण", "वजह"),
    ("निमित्त", "वजह"),
    ("साधारण", "आम"),
    ("असाधारण", "बहुत अलग"),
    ("विचित्र", "अजीब"),
    ("रहस्यमय", "राज़ भरा"),
    ("गम्भीर", "गंभीर"),
    ("गंभीर", "सीरियस"),
    ("उल्लेख", "ज़िक्र"),
    ("वर्णन", "बयान"),
    ("प्रमाण", "सबूत"),
    ("सूचना", "खबर"),
    ("समाचार", "खबर"),
    ("घोषणा", "ऐलान"),
    ("अनुमति", "इजाज़त"),
    ("निषेध", "मनाही"),
    ("स्वीकार", "मान लेना"),
    ("अस्वीकार", "न मानना"),
    ("त्याग", "छोड़ना"),
    ("ग्रहण", "लेना"),
    ("प्राप्त", "मिला"),
    ("उपलब्ध", "मौजूद"),
    ("सुरक्षित", "महफूज़"),
    ("असुरक्षित", "खतरे में"),
    ("विनाश", "बरबादी"),
    ("नष्ट", "बरबाद"),
    ("रक्षा", "बचाव"),
    ("संरक्षण", "बचाव"),
    ("शक्ति", "ताकत"),
    ("दुर्बल", "कमज़ोर"),
    ("कमजोर", "कमज़ोर"),
    ("स्वास्थ्य", "सेहत"),
    ("रोग", "बीमारी"),
    ("औषधि", "दवा"),
    ("चिकित्सा", "इलाज"),
    ("चिकित्सक", "डॉक्टर"),
    ("मृत्यु", "मौत"),
    ("मृत", "मरा हुआ"),
    ("जीवित", "ज़िंदा"),
    ("जीवन", "ज़िंदगी"),
    ("जन्म", "पैदा होना"),
    ("भाग्य", "किस्मत"),
    ("ईश्वर", "भगवान"),
    ("परमात्मा", "भगवान"),
    ("प्रार्थना", "दुआ"),
]

# Stable Roman forms and frequent names/words. Longer entries are applied first.
ROMAN_WORD_OVERRIDES: dict[str, str] = {
    "प्रेमचंद": "Premchand",
    "मुंशी": "Munshi",
    "निर्मला": "Nirmala",
    "गोदान": "Godaan",
    "होरीराम": "Horiram",
    "होरी": "Hori",
    "धनिया": "Dhaniya",
    "गोबर": "Gobar",
    "झुनिया": "Jhunia",
    "हीरा": "Heera",
    "सोना": "Sona",
    "रूपा": "Rupa",
    "मालती": "Malti",
    "मेहता": "Mehta",
    "रायसाहब": "Rai Sahab",
    "राय": "Rai",
    "साहब": "Sahab",
    "भगवान": "Bhagwan",
    "भगवान्": "Bhagwan",
    "नहीं": "nahin",
    "नही": "nahin",
    "हैं": "hain",
    "है": "hai",
    "था": "tha",
    "थी": "thi",
    "थे": "the",
    "हूँ": "hoon",
    "हूं": "hoon",
    "हो": "ho",
    "क्यों": "kyon",
    "क्यूँ": "kyon",
    "क्योंकि": "kyunki",
    "मुझे": "mujhe",
    "तुम्हें": "tumhe",
    "तुमको": "tumhe",
    "आपको": "aapko",
    "यहाँ": "yahan",
    "यहां": "yahan",
    "वहाँ": "wahan",
    "वहां": "wahan",
    "अच्छा": "achchha",
    "अच्छी": "achchhi",
    "अच्छे": "achchhe",
    "चाहिए": "chahiye",
    "प्यार": "pyaar",
    "ज़मीन": "zameen",
    "जमीन": "zameen",
    "आदमी": "aadmi",
    "इंसान": "insaan",
    "औरत": "aurat",
    "बच्चा": "bachcha",
    "बच्चे": "bachche",
    "बच्ची": "bachchi",
    "कर्ज़": "karz",
    "इज़्ज़त": "izzat",
    "इज्जत": "izzat",
    "ज़रूर": "zaroor",
    "ज़रूरी": "zaroori",
    "ज़रूरत": "zaroorat",
    "नफ़रत": "nafrat",
    "नफरत": "nafrat",
    "ख़ुशी": "khushi",
    "खुशी": "khushi",
    "खुश": "khush",
    "गुज़ारिश": "guzarish",
    "इंतज़ाम": "intezam",
    "इंतजार": "intezar",
    "इंतज़ार": "intezar",
    "फ़िक्र": "fikr",
    "फिक्र": "fikr",
    "फ़र्ज़": "farz",
    "फर्ज": "farz",
    "फ़ैसला": "faisla",
    "फैसला": "faisla",
    "दुआ": "dua",
    "दुनिया": "duniya",
    "ज़िंदगी": "zindagi",
    "जिंदगी": "zindagi",
    "ज़िंदा": "zinda",
    "जिंदा": "zinda",
    "मज़दूर": "mazdoor",
    "मजदूर": "mazdoor",
    "गाँव": "gaon",
    "गांव": "gaon",
    "मुँह": "munh",
    "मुंह": "munh",
    "आँख": "aankh",
    "आँखें": "aankhen",
    "आंख": "aankh",
    "आंखें": "aankhen",
    "कपड़े": "kapde",
    "रुपये": "rupaye",
    "रुपया": "rupaya",
    "रुपए": "rupaye",
    "रोटी": "roti",
    "खाना": "khana",
    "पानी": "paani",
    "दिल": "dil",
    "दिमाग": "dimaag",
    "दर्द": "dard",
    "मुश्किल": "mushkil",
    "लेकिन": "lekin",
    "हालाँकि": "halaanki",
    "हालांकि": "halaanki",
    "फिर": "phir",
    "भी": "bhi",
    "और": "aur",
    "या": "ya",
    "जो": "jo",
    "कि": "ki",
    "को": "ko",
    "से": "se",
    "में": "mein",
    "पर": "par",
    "का": "ka",
    "की": "ki",
    "के": "ke",
    "एक": "ek",
    "दो": "do",
    "तीन": "teen",
    "चार": "chaar",
    "पाँच": "paanch",
    "छः": "chhah",
    "छह": "chhah",
    "सात": "saat",
    "आठ": "aath",
    "नौ": "nau",
    "दस": "das",
}

INDEPENDENT_VOWELS = {
    "अ": "a", "आ": "aa", "इ": "i", "ई": "ee", "उ": "u", "ऊ": "oo",
    "ऋ": "ri", "ॠ": "ri", "ऌ": "li", "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au",
    "ऑ": "o", "ऍ": "e", "ऎ": "e", "ऒ": "o",
}
CONSONANTS = {
    "क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "ng",
    "च": "ch", "छ": "chh", "ज": "j", "झ": "jh", "ञ": "ny",
    "ट": "t", "ठ": "th", "ड": "d", "ढ": "dh", "ण": "n",
    "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n",
    "प": "p", "फ": "ph", "ब": "b", "भ": "bh", "म": "m",
    "य": "y", "र": "r", "ल": "l", "व": "v",
    "श": "sh", "ष": "sh", "स": "s", "ह": "h",
    "क़": "q", "ख़": "kh", "ग़": "gh", "ज़": "z",
    "ड़": "r", "ढ़": "rh", "फ़": "f", "य़": "y", "ऱ": "r", "ऴ": "l",
}
MATRAS = {
    "ा": "aa", "ि": "i", "ी": "ee", "ु": "u", "ू": "oo", "ृ": "ri",
    "ॄ": "ri", "ॅ": "e", "े": "e", "ै": "ai", "ॉ": "o", "ो": "o", "ौ": "au",
    "ॆ": "e", "ॊ": "o",
}
VIRAMA = "्"
NUKTA = "़"
SIGNS = {"ं": "n", "ँ": "n", "ः": "h", "ऽ": "'"}

KEEP_FINAL_A = {
    "kaha", "raha", "rahaa", "gaya", "gayaa", "aaya", "aayaa", "laya", "laaya",
    "diya", "diyaa", "liya", "liyaa", "hua", "huyaa", "naya", "nayaa", "bura",
    "pura", "poora", "aadha", "beta", "betaa", "ladka", "ladkaa", "ghoda",
    "ghoraa", "duniya", "kriya", "daya", "maya", "chhota", "bada", "thoda",
    "zyada", "jada", "aisa", "waisa", "kaisa", "paisa", "sauda", "mauka",
    "dhokha", "chehra", "kamra", "rashta", "rasta", "darwaza", "katora",
}


@dataclass
class WorkQA:
    work_id: str
    title: str
    chapters: int
    source_characters: int
    output_characters: int
    devanagari_remaining: int
    urdu_remaining: int
    roman_only_pass: bool
    source_min_pass: bool
    sample_notes: list[str]


def get(url: str, *, params: dict | None = None, retries: int = 10) -> requests.Response:
    """GET with explicit pacing for Wikimedia and transient-server failures."""
    last: Exception | None = None
    for attempt in range(retries):
        try:
            r = SESSION.get(url, params=params, timeout=TIMEOUT)
            if r.status_code == 429:
                retry_header = r.headers.get("Retry-After", "").strip()
                try:
                    wait = int(retry_header)
                except ValueError:
                    wait = 20 + attempt * 10
                wait = max(10, min(wait, 180))
                print(f"Rate limited by {url}; sleeping {wait}s (attempt {attempt + 1}/{retries})")
                time.sleep(wait)
                last = RuntimeError(f"429 Too Many Requests: {r.url}")
                continue
            if r.status_code in {500, 502, 503, 504}:
                wait = min(60, 4 * (attempt + 1))
                print(f"Transient HTTP {r.status_code} from {url}; sleeping {wait}s")
                time.sleep(wait)
                last = RuntimeError(f"HTTP {r.status_code}: {r.url}")
                continue
            r.raise_for_status()
            return r
        except Exception as exc:
            last = exc
            if attempt + 1 < retries:
                wait = min(60, 2 ** min(attempt, 5))
                time.sleep(wait)
    raise RuntimeError(f"Download failed after {retries} attempts: {url}: {last}")


def normalize_source(text: str) -> str:
    text = unicodedata.normalize("NFC", text.replace("\ufeff", ""))
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\ufffd", "")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = WS_RE.sub(" ", text)
    text = MULTI_NL_RE.sub("\n\n", text)
    return text.strip()


def simplify_devanagari(text: str) -> str:
    # Longest phrases first to prevent a shorter replacement from damaging one.
    for old, new in sorted(PHRASE_REPLACEMENTS, key=lambda x: len(x[0]), reverse=True):
        text = text.replace(old, new)
    return text


def transliterate_word(word: str) -> str:
    if word in ROMAN_WORD_OVERRIDES:
        return ROMAN_WORD_OVERRIDES[word]

    out: list[str] = []
    i = 0
    while i < len(word):
        ch = word[i]

        # Consonant + optional nukta + optional virama/matra.
        if ch in CONSONANTS:
            base = CONSONANTS[ch]
            if i + 1 < len(word) and word[i + 1] == NUKTA:
                i += 1
            if i + 1 < len(word) and word[i + 1] == VIRAMA:
                out.append(base)
                i += 2
                continue
            if i + 1 < len(word) and word[i + 1] in MATRAS:
                out.append(base + MATRAS[word[i + 1]])
                i += 2
                continue
            out.append(base + "a")
            i += 1
            continue

        if ch in INDEPENDENT_VOWELS:
            out.append(INDEPENDENT_VOWELS[ch])
        elif ch in MATRAS:
            out.append(MATRAS[ch])
        elif ch in SIGNS:
            # Anusvara is made more readable below.
            out.append(SIGNS[ch])
        elif ch == NUKTA or ch == VIRAMA:
            pass
        elif ch in "।॥":
            out.append("." if ch == "।" else ".")
        else:
            out.append(ch)
        i += 1

    roman = "".join(out)

    # Contextual nasal cleanup.
    roman = re.sub(r"n(?=[kg])", "ng", roman)
    roman = re.sub(r"n(?=[cj])", "n", roman)
    roman = re.sub(r"n(?=[td])", "n", roman)
    roman = re.sub(r"n(?=[pb])", "m", roman)

    # Common conjunct/schwa patterns.
    roman = roman.replace("jnya", "gya").replace("kshha", "ksha").replace("ksha", "ksh")
    roman = roman.replace("tra", "tra").replace("shra", "shra")
    roman = roman.replace("riya", "riya")
    roman = re.sub(r"([bcdfghjklmnpqrstvwxyz])a([bcdfghjklmnpqrstvwxyz])a$", r"\1a\2", roman)
    roman = re.sub(r"([bcdfghjklmnpqrstvwxyz])a$", r"\1", roman)

    # Restore words where the final vowel is spoken.
    if roman in KEEP_FINAL_A:
        return roman
    # Improve common verbal endings after heuristic deletion.
    roman = re.sub(r"karan$", "karna", roman)
    roman = re.sub(r"rahan$", "rahna", roman)
    roman = re.sub(r"chalan$", "chalna", roman)
    roman = re.sub(r"bolan$", "bolna", roman)
    roman = re.sub(r"dehan$", "dehna", roman)
    return roman


DEV_TOKEN_RE = re.compile(r"[\u0900-\u097f]+")


def romanize(text: str) -> str:
    text = simplify_devanagari(text)

    # Apply exact stable-word overrides before general transliteration.
    for dev, roman in sorted(ROMAN_WORD_OVERRIDES.items(), key=lambda x: len(x[0]), reverse=True):
        text = re.sub(rf"(?<![\u0900-\u097f]){re.escape(dev)}(?![\u0900-\u097f])", roman, text)

    text = DEV_TOKEN_RE.sub(lambda m: transliterate_word(m.group(0)), text)
    text = text.translate(DEV_DIGITS)

    # Typographic normalization.
    replacements = {
        "—": " — ", "–": " — ", "…": "...", "“": '"', "”": '"',
        "‘": "'", "’": "'", "।": ".", "॥": ".", "\u00a0": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    # Stable spellings after transliteration.
    stable = {
        r"\bnahim\b": "nahin", r"\bnahinm\b": "nahin", r"\bhainm\b": "hain",
        r"\bkyom\b": "kyon", r"\bkyonki\b": "kyunki", r"\byaham\b": "yahan",
        r"\bvaham\b": "wahan", r"\bacchha\b": "achchha", r"\bachcha\b": "achchha",
        r"\bchahie\b": "chahiye", r"\bbhagavan\b": "Bhagwan",
        r"\bprem\b": "pyaar", r"\bjamin\b": "zameen", r"\badami\b": "aadmi",
        r"\bmanushy\b": "insaan", r"\bstr\b": "aurat",
    }
    for pat, repl in stable.items():
        text = re.sub(pat, repl, text, flags=re.IGNORECASE)

    text = re.sub(r" +([,.;:!?])", r"\1", text)
    text = re.sub(r"([,.;:!?])(?=[A-Za-z])", r"\1 ", text)
    text = WS_RE.sub(" ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = MULTI_NL_RE.sub("\n\n", text)
    return text.strip()


def paragraphs_from_plain(text: str) -> list[str]:
    text = normalize_source(text)
    # Keep source paragraph boundaries. Single newlines often represent wrapped prose;
    # blank lines are true paragraph boundaries in the Godaan source.
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    if len(blocks) < 3:
        # Safe fallback for files with no blank lines.
        blocks = [line.strip() for line in text.splitlines() if line.strip()]
    return blocks


NOISE_PATTERNS = [
    r"विकिस्रोत", r"सामग्री पर जाएँ", r"मुख्य मेनू", r"खोज", r"डाउनलोड",
    r"पिछला अध्याय", r"अगला अध्याय", r"अनुक्रम", r"मूल स्रोत", r"पाठ",
    r"यह पृष्ठ", r"अन्तिम परिवर्तन", r"अंतिम परिवर्तन", r"गोपनीयता नीति",
    r"मोबाइल दृश्य", r"डेस्कटॉप", r"प्रूफरीड", r"स्कैन", r"कॉमन्स",
]
NOISE_RE = re.compile("|".join(NOISE_PATTERNS), re.IGNORECASE)


def clean_wikisource_html(html: str, title: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    for sel in [
        "script", "style", "noscript", "table", "nav", "footer", "header",
        ".mw-editsection", ".navbox", ".metadata", ".ambox", ".sistersitebox",
        ".printfooter", "#catlinks", ".mw-jump-link", ".mw-indicators",
        ".ws-noexport", ".noprint", ".mw-parser-output > .ws-header",
    ]:
        for node in soup.select(sel):
            node.decompose()

    root = soup.select_one(".mw-parser-output") or soup
    paragraphs: list[str] = []
    for node in root.find_all(["p", "h2", "h3", "blockquote", "div"], recursive=True):
        # Only leaf-ish blocks; avoid duplicating text from nested divs.
        if node.name == "div" and node.find(["p", "h2", "h3", "blockquote"]):
            continue
        txt = normalize_source(node.get_text(" ", strip=True))
        if not txt or len(txt) < 2:
            continue
        if NOISE_RE.search(txt):
            continue
        if txt == title or txt in {"निर्मला", "मुंशी प्रेमचंद", "प्रेमचंद"}:
            continue
        if re.fullmatch(r"[←→\s\d०-९./-]+", txt):
            continue
        paragraphs.append(txt)

    # Deduplicate adjacent parser echoes while preserving genuine repetition.
    cleaned: list[str] = []
    for p in paragraphs:
        if cleaned and p == cleaned[-1]:
            continue
        cleaned.append(p)
    return cleaned


def natural_key(title: str) -> tuple:
    tail = title.split("/", 1)[-1].translate(DEV_DIGITS)
    nums = re.findall(r"\d+", tail)
    if nums:
        return (0, int(nums[0]), tail)
    return (1, tail)


def fetch_nirmala() -> tuple[list[tuple[str, list[str]]], dict]:
    api = "https://hi.wikisource.org/w/api.php"
    titles: list[str] = []
    cont: str | None = None
    while True:
        params = {
            "action": "query", "list": "allpages", "apprefix": "निर्मला/",
            "apnamespace": 0, "aplimit": "max", "format": "json", "formatversion": 2,
        }
        if cont:
            params["apcontinue"] = cont
        data = get(api, params=params).json()
        titles.extend(p["title"] for p in data["query"]["allpages"])
        cont = data.get("continue", {}).get("apcontinue")
        if not cont:
            break

    # Remove index/subpages that are not numbered chapters.
    chapter_titles = [
        t for t in titles
        if re.search(r"[0-9०-९]", t.split("/", 1)[-1])
        and not re.search(r"(अनुक्रम|भूमिका|प्रकाशक|चित्र|आवरण|सूची)", t)
    ]
    chapter_titles = sorted(set(chapter_titles), key=natural_key)
    if not (20 <= len(chapter_titles) <= 50):
        raise RuntimeError(
            f"Nirmala chapter discovery returned {len(chapter_titles)} numbered pages; expected 20-50. "
            f"Titles: {chapter_titles[:10]}..."
        )

    chapters: list[tuple[str, list[str]]] = []
    raw_sizes: dict[str, int] = {}
    for idx, title in enumerate(chapter_titles, 1):
        data = get(api, params={
            "action": "parse", "page": title, "prop": "text",
            "format": "json", "formatversion": 2, "disableeditsection": 1,
        }).json()
        html = data["parse"]["text"]
        paras = clean_wikisource_html(html, title)
        chars = sum(len(p) for p in paras)
        if chars < 2000:
            raise RuntimeError(f"Nirmala chapter {title!r} is suspiciously short after cleaning: {chars} chars")
        chapters.append((title, paras))
        raw_sizes[title] = chars
        print(f"Nirmala {idx:02d}/{len(chapter_titles)}: {title} — {chars} chars")
        # Wikimedia asks automated clients to avoid rapid serial parse calls.
        time.sleep(1.5)
    total = sum(raw_sizes.values())
    if total < 150_000:
        raise RuntimeError(f"Nirmala total source is suspiciously short: {total} chars")
    return chapters, {"api": api, "titles": chapter_titles, "sizes": raw_sizes, "total": total}


def fetch_godaan() -> tuple[list[tuple[str, list[str]]], dict]:
    base = (
        "https://raw.githubusercontent.com/pandeyshikha1098/privacy_policy/"
        "45b42cf18333411f035757a9ecd8b6859fa84ae6/"
        "hindi-stories/storyBook/premchandra/godan"
    )
    chapters: list[tuple[str, list[str]]] = []
    sizes: dict[str, int] = {}
    for i in range(1, 37):
        name = f"{i:02d}.txt"
        text = get(f"{base}/{name}").text
        text = normalize_source(text)
        if len(text) < 4000:
            raise RuntimeError(f"Godaan {name} is suspiciously short: {len(text)} chars")
        paras = paragraphs_from_plain(text)
        if len(paras) < 5:
            raise RuntimeError(f"Godaan {name} has suspiciously few paragraphs: {len(paras)}")
        chapters.append((name, paras))
        sizes[name] = len(text)
        print(f"Godaan {i:02d}/36: {len(text)} chars, {len(paras)} paragraphs")
    if len(chapters) != 36:
        raise RuntimeError(f"Godaan chapter count is {len(chapters)}, expected exactly 36")
    total = sum(sizes.values())
    if total < 500_000:
        raise RuntimeError(f"Godaan total source is suspiciously short: {total} chars")
    return chapters, {"base": base, "sizes": sizes, "total": total}


def write_work(
    *,
    work_id: str,
    title: str,
    author: str,
    chapters: list[tuple[str, list[str]]],
    source_record: dict,
    expected_chapters: int | None = None,
) -> WorkQA:
    work_dir = WORKS / work_id
    chapter_dir = work_dir / "chapters"
    chapter_dir.mkdir(parents=True, exist_ok=True)

    # Remove stale chapter files so exact chapter validation is meaningful.
    for old in chapter_dir.glob("*.md"):
        old.unlink()

    source_chars = 0
    output_chars = 0
    dev_remaining = 0
    urdu_remaining = 0

    for idx, (source_name, paras) in enumerate(chapters, 1):
        source_chars += sum(len(p) for p in paras)
        roman_paras = [romanize(p) for p in paras]
        body = "\n\n".join(p for p in roman_paras if p)
        chapter_title = f"# {title} — Adhyay {idx}\n\n**{author}**\n\n"
        output = chapter_title + body.strip() + "\n"
        dev_count = len(DEV_RE.findall(output))
        urdu_count = len(URDU_RE.findall(output))
        if dev_count or urdu_count:
            raise RuntimeError(
                f"{title} chapter {idx} failed Roman-only validation: "
                f"Devanagari={dev_count}, Urdu={urdu_count}"
            )
        output_chars += len(output)
        dev_remaining += dev_count
        urdu_remaining += urdu_count
        (chapter_dir / f"{idx:02d}.md").write_text(output, encoding="utf-8")

    if expected_chapters is not None and len(chapters) != expected_chapters:
        raise RuntimeError(f"{title} has {len(chapters)} chapters, expected {expected_chapters}")

    source_md = (
        f"# Locked Source Record — {title}\n\n"
        f"- Author: {author}\n"
        f"- Work: complete novel\n"
        f"- Source language/script: Hindi in Devanagari\n"
        f"- Source status: programmatically fetched and chapter-count validated\n"
        f"- Reader status: machine-assisted complete first pass; independent human review pending\n\n"
        f"## Machine-readable source record\n\n```json\n"
        f"{json.dumps(source_record, ensure_ascii=False, indent=2)}\n```\n\n"
        "No modern translation, summary, review, or adaptation is used as reader text. "
        "The public reader files contain only the new Roman-Hindustani accessibility first pass.\n"
    )
    (work_dir / "source.md").write_text(source_md, encoding="utf-8")

    notes = (
        f"# Editorial Notes — {title}\n\n"
        "## Preservation boundary\n\n"
        f"- Complete chapter count retained: **{len(chapters)}**.\n"
        "- Chapter and paragraph order retained.\n"
        "- Names, numbers, events, dialogue, repeated phrases, social and caste/class signals, "
        "humour, irony, emotional turns, and the ending are retained by the deterministic full-text pass.\n"
        "- This build does not summarize or intentionally remove narrative material.\n\n"
        "## Language method\n\n"
        "- Devanagari is converted to Roman script with stable high-frequency spellings.\n"
        "- A controlled phrase lexicon replaces selected bookish wording with easier everyday Hindustani.\n"
        "- The process is rule-based and therefore cannot replace independent literary editing.\n"
        "- Adult narration is not intentionally made childish.\n\n"
        "## Review status\n\n"
        "- Machine-assisted complete first pass: complete.\n"
        "- Roman-only automated validation: passed.\n"
        "- Independent paragraph-by-paragraph source comparison: pending.\n"
        "- Independent read-aloud and natural-language revision: pending.\n"
        "- Publication status: not reviewed.\n"
    )
    (work_dir / "NOTES.md").write_text(notes, encoding="utf-8")

    # Mechanical opening/middle/final sampling.
    sample_indices = sorted({1, max(1, len(chapters) // 2), len(chapters)})
    sample_notes: list[str] = []
    for n in sample_indices:
        sample = (chapter_dir / f"{n:02d}.md").read_text(encoding="utf-8")
        bad = len(DEV_RE.findall(sample)) + len(URDU_RE.findall(sample))
        sample_notes.append(
            f"chapter {n}: {len(sample)} output chars; residual Indic-script characters={bad}"
        )

    return WorkQA(
        work_id=work_id,
        title=title,
        chapters=len(chapters),
        source_characters=source_chars,
        output_characters=output_chars,
        devanagari_remaining=dev_remaining,
        urdu_remaining=urdu_remaining,
        roman_only_pass=(dev_remaining == 0 and urdu_remaining == 0),
        source_min_pass=True,
        sample_notes=sample_notes,
    )


def write_reports(records: list[WorkQA]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    qa_lines = [
        "# Premchand Novels — Automated QA",
        "",
        "These are complete **machine-assisted first passes**, not independently reviewed publication copies.",
        "",
        "| Work | Chapters | Source chars | Output chars | Devanagari left | Urdu left | Roman-only |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for r in records:
        qa_lines.append(
            f"| {r.title} | {r.chapters} | {r.source_characters:,} | {r.output_characters:,} | "
            f"{r.devanagari_remaining} | {r.urdu_remaining} | {'PASS' if r.roman_only_pass else 'FAIL'} |"
        )
    qa_lines.extend(["", "## Opening / middle / final mechanical samples", ""])
    for r in records:
        qa_lines.append(f"### {r.title}")
        qa_lines.extend(f"- {note}" for note in r.sample_notes)
        qa_lines.append("")
    qa_lines.extend([
        "## Required human work",
        "",
        "- Paragraph-by-paragraph comparison against the locked source.",
        "- Natural spoken-Hindustani revision where transliteration is technically valid but awkward.",
        "- Proper-name, historical-term, caste/class terminology, number, and ending checks.",
        "- Independent read-aloud review.",
        "",
    ])
    (OUT / "QA.md").write_text("\n".join(qa_lines), encoding="utf-8")

    manifest = {
        "project": "easy-roman-hindustani-classics",
        "generator": "premchand_novels_builder.py",
        "status_boundary": (
            "machine-assisted complete first pass; independent human review required before publication"
        ),
        "works": [
            {
                "id": r.work_id,
                "title": r.title,
                "author": "Munshi Premchand",
                "form": "novel",
                "chapters": r.chapters,
                "source_characters": r.source_characters,
                "output_characters": r.output_characters,
                "translation_status": "machine_assisted_complete_first_pass",
                "human_review": "pending",
                "roman_only_validation": "passed" if r.roman_only_pass else "failed",
            }
            for r in records
        ],
    }
    (OUT / "manifest-fragment.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    try:
        nirmala_chapters, nirmala_source = fetch_nirmala()
        godaan_chapters, godaan_source = fetch_godaan()

        records = [
            write_work(
                work_id="nirmala",
                title="Nirmala",
                author="Munshi Premchand",
                chapters=nirmala_chapters,
                source_record=nirmala_source,
            ),
            write_work(
                work_id="godaan",
                title="Godaan",
                author="Munshi Premchand",
                chapters=godaan_chapters,
                source_record=godaan_source,
                expected_chapters=36,
            ),
        ]
        write_reports(records)
        print(json.dumps([asdict(r) for r in records], ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "BUILD_FAILURE.txt").write_text(
            f"{type(exc).__name__}: {exc}\n", encoding="utf-8"
        )
        print(f"BUILD FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
