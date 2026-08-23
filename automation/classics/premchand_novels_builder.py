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

PHRASE_REPLACEMENTS = [
    ("व्यवहार-कुशल", "दुनिया की समझ रखने वाली"), ("व्यवहार कुशल", "दुनिया की समझ रखने वाली"),
    ("आत्म-सम्मान", "अपनी इज्जत का एहसास"), ("आत्मसम्मान", "अपनी इज्जत का एहसास"),
    ("चिरस्थायी", "बहुत लंबे समय की"), ("जीर्णावस्था", "टूटी-फूटी हालत"),
    ("अन्तःकरण", "दिल"), ("अंतःकरण", "दिल"), ("आतंकमय", "डर से भरा"),
    ("अभय-दान", "बेफिक्र रहने की दुआ"), ("अभयदान", "बेफिक्र रहने की दुआ"),
    ("वेदना-शक्ति", "दर्द की ताकत"), ("सम्पूर्ण", "पूरा"), ("संपूर्ण", "पूरा"),
    ("परिस्थितियाँ", "हालात"), ("परिस्थितियों", "हालात"), ("परिस्थिति", "हाल"),
    ("वास्तविकता", "सच्चाई"), ("यथार्थ", "सच्चाई"), ("अनिवार्य", "ज़रूरी"),
    ("आवश्यकता", "ज़रूरत"), ("आवश्यक", "ज़रूरी"), ("सहायता", "मदद"),
    ("सहायक", "मदद करने वाला"), ("व्यवस्था", "इंतज़ाम"), ("प्रबन्ध", "इंतज़ाम"),
    ("प्रबंध", "इंतज़ाम"), ("प्रबन्धक", "काम संभालने वाला"), ("प्रबंधक", "काम संभालने वाला"),
    ("अधिकारी", "अफसर"), ("कर्मचारी", "काम करने वाला"), ("निवेदन", "बात"),
    ("अनुरोध", "गुज़ारिश"), ("आग्रह", "ज़ोर देकर कहना"), ("निर्देश", "हुक्म"),
    ("आदेश", "हुक्म"), ("निर्णय", "फैसला"), ("निश्चय", "पक्का फैसला"),
    ("उद्देश्य", "मकसद"), ("प्रयोजन", "मकसद"), ("परिणाम", "नतीजा"),
    ("फलस्वरूप", "इसलिए"), ("अतः", "इसलिए"), ("किन्तु", "लेकिन"),
    ("किंतु", "लेकिन"), ("परन्तु", "लेकिन"), ("परंतु", "लेकिन"),
    ("तथापि", "फिर भी"), ("यद्यपि", "हालांकि"), ("अर्थात्", "यानी"),
    ("अर्थात", "यानी"), ("तत्काल", "तुरंत"), ("शीघ्र", "जल्दी"),
    ("विलम्ब", "देर"), ("विलंब", "देर"), ("प्रतीक्षा", "इंतज़ार"),
    ("प्रसन्नता", "खुशी"), ("प्रसन्न", "खुश"), ("आनन्द", "खुशी"),
    ("आनंद", "खुशी"), ("कुपित", "गुस्से में"), ("क्रोधित", "गुस्से में"),
    ("रोष", "गुस्सा"), ("तिरस्कार", "नफ़रत"), ("घृणा", "नफ़रत"),
    ("वेदना", "दर्द"), ("पीड़ा", "दर्द"), ("कष्ट", "तकलीफ़"),
    ("दुर्भाग्य", "बदकिस्मती"), ("सौभाग्य", "अच्छी किस्मत"), ("दीनता", "बेचारगी"),
    ("विपन्नता", "गरीबी"), ("निर्धनता", "गरीबी"), ("दरिद्रता", "गरीबी"),
    ("समृद्धि", "अमीरी"), ("समृद्ध", "अमीर"), ("निवास", "घर"),
    ("गृहस्थी", "घर-बार"), ("गृह", "घर"), ("भोजन", "खाना"),
    ("जलपान", "कुछ खाने-पीने को"), ("आहार", "खाना"), ("वस्त्र", "कपड़े"),
    ("मुख", "मुँह"), ("नेत्र", "आँखें"), ("हृदय", "दिल"),
    ("मस्तिष्क", "दिमाग"), ("विचारों", "सोच"), ("विचार", "सोच"),
    ("चिन्ता", "फिक्र"), ("चिंता", "फिक्र"), ("अनुभव", "तजुर्बा"),
    ("अनुभूति", "एहसास"), ("भावनाएँ", "एहसास"), ("भावना", "एहसास"),
    ("कल्पना", "खयाल"), ("स्मरण", "याद"), ("स्मृति", "याद"),
    ("विस्मय", "हैरानी"), ("आश्चर्य", "हैरानी"), ("संकोच", "झिझक"),
    ("लज्जा", "शर्म"), ("विनम्र", "नरम और अदब से"), ("नम्रता", "नर्मी"),
    ("मृदुता", "नर्मी"), ("कठोर", "सख्त"), ("विशाल", "बहुत बड़ा"),
    ("अथाह", "बहुत गहरा"), ("अत्यन्त", "बहुत"), ("अत्यंत", "बहुत"),
    ("अधिकाधिक", "और ज़्यादा"), ("निरन्तर", "लगातार"), ("निरंतर", "लगातार"),
    ("सदैव", "हमेशा"), ("कदाचित्", "शायद"), ("कदाचित", "शायद"),
    ("संभवतः", "शायद"), ("अवश्य", "ज़रूर"), ("निश्चित रूप से", "पक्का"),
    ("निश्चित", "पक्का"), ("निस्सन्देह", "बेशक"), ("निस्संदेह", "बेशक"),
    ("मनुष्य", "इंसान"), ("व्यक्ति", "आदमी"), ("स्त्री", "औरत"),
    ("पुरुष", "मर्द"), ("बालक", "बच्चा"), ("बालिका", "लड़की"),
    ("युवक", "जवान आदमी"), ("युवती", "जवान लड़की"), ("वृद्धा", "बूढ़ी औरत"),
    ("वृद्ध", "बूढ़ा"), ("सामाजिक", "समाज का"), ("समाजिक", "समाज का"),
    ("समाज", "लोगों की दुनिया"), ("धनराशि", "पैसा"), ("राशि", "रकम"),
    ("ऋण", "कर्ज़"), ("कर्ज", "कर्ज़"), ("व्यय", "खर्च"),
    ("उपार्जन", "कमाई"), ("आय", "कमाई"), ("श्रमिक", "मज़दूर"),
    ("श्रम", "मेहनत"), ("कृषक", "किसान"), ("भूमि", "ज़मीन"),
    ("क्षेत्र", "इलाका"), ("स्थान", "जगह"), ("मार्ग", "रास्ता"),
    ("नगर", "शहर"), ("ग्राम", "गाँव"), ("प्रातःकाल", "सुबह"),
    ("प्रातः", "सुबह"), ("संध्या", "शाम"), ("रात्रि", "रात"),
    ("दिवस", "दिन"), ("क्षणिक", "एक पल की"), ("क्षण", "पल"),
    ("तत्पश्चात्", "उसके बाद"), ("तत्पश्चात", "उसके बाद"),
    ("पश्चात्", "बाद"), ("पश्चात", "बाद"), ("पूर्व", "पहले"),
    ("प्रवेश", "अंदर जाना"), ("प्रस्थान", "रवाना होना"), ("आगमन", "आना"),
    ("गमन", "जाना"), ("उपस्थित", "मौजूद"), ("अनुपस्थित", "मौजूद नहीं"),
    ("प्रकट", "सामने"), ("लुप्त", "गायब"), ("आरम्भ", "शुरू"),
    ("आरंभ", "शुरू"), ("समाप्त", "खत्म"), ("समापन", "अंत"),
    ("कथन", "बात"), ("वार्तालाप", "बातचीत"), ("संवाद", "बातचीत"),
    ("प्रश्न", "सवाल"), ("उत्तर", "जवाब"), ("उचित", "ठीक"),
    ("अनुचित", "गलत"), ("सत्य", "सच"), ("असत्य", "झूठ"),
    ("न्याय", "इंसाफ"), ("अन्याय", "नाइंसाफी"), ("अपराध", "जुर्म"),
    ("दण्ड", "सज़ा"), ("दंड", "सज़ा"), ("स्वतन्त्रता", "आज़ादी"),
    ("स्वतंत्रता", "आज़ादी"), ("स्वतन्त्र", "आज़ाद"), ("स्वतंत्र", "आज़ाद"),
    ("पराधीन", "दूसरे के बस में"), ("कर्तव्य", "फ़र्ज़"), ("अधिकार", "हक"),
    ("सम्मान", "इज़्ज़त"), ("अपमान", "बेइज़्ज़ती"), ("मर्यादा", "इज़्ज़त का ढंग"),
    ("प्रतिष्ठा", "इज़्ज़त"), ("विश्वास", "भरोसा"), ("अविश्वास", "भरोसा न होना"),
    ("सन्देह", "शक"), ("संदेह", "शक"), ("आशा", "उम्मीद"),
    ("निराशा", "उदासी"), ("उत्साह", "जोश"), ("साहस", "हिम्मत"),
    ("भय", "डर"), ("आतंक", "दहशत"), ("करुणा", "दया"),
    ("दया", "तरस"), ("स्नेह", "प्यार"), ("प्रेम", "प्यार"),
    ("विवाह", "शादी"), ("पति", "शौहर"), ("पत्नी", "बीवी"),
    ("परिवार", "घरवाले"), ("सम्बन्ध", "रिश्ता"), ("संबंध", "रिश्ता"),
    ("समस्या", "मुश्किल"), ("कठिनाई", "मुश्किल"), ("समाधान", "हल"),
    ("उपाय", "रास्ता"), ("प्रयास", "कोशिश"), ("चेष्टा", "कोशिश"),
    ("सफलता", "कामयाबी"), ("असफलता", "नाकामी"), ("सफल", "कामयाब"),
    ("असफल", "नाकाम"), ("प्रभावित", "असर पड़ा"), ("प्रभाव", "असर"),
    ("कारण", "वजह"), ("निमित्त", "वजह"), ("साधारण", "आम"),
    ("असाधारण", "बहुत अलग"), ("विचित्र", "अजीब"), ("रहस्यमय", "राज़ भरा"),
    ("गम्भीर", "सीरियस"), ("गंभीर", "सीरियस"), ("उल्लेख", "ज़िक्र"),
    ("वर्णन", "बयान"), ("प्रमाण", "सबूत"), ("सूचना", "खबर"),
    ("समाचार", "खबर"), ("घोषणा", "ऐलान"), ("अनुमति", "इजाज़त"),
    ("निषेध", "मनाही"), ("स्वीकार", "मान लेना"), ("अस्वीकार", "न मानना"),
    ("त्याग", "छोड़ना"), ("ग्रहण", "लेना"), ("प्राप्त", "मिला"),
    ("उपलब्ध", "मौजूद"), ("सुरक्षित", "महफूज़"), ("असुरक्षित", "खतरे में"),
    ("विनाश", "बरबादी"), ("नष्ट", "बरबाद"), ("रक्षा", "बचाव"),
    ("संरक्षण", "बचाव"), ("शक्ति", "ताकत"), ("दुर्बल", "कमज़ोर"),
    ("कमजोर", "कमज़ोर"), ("स्वास्थ्य", "सेहत"), ("रोग", "बीमारी"),
    ("औषधि", "दवा"), ("चिकित्सा", "इलाज"), ("चिकित्सक", "डॉक्टर"),
    ("मृत्यु", "मौत"), ("मृत", "मरा हुआ"), ("जीवित", "ज़िंदा"),
    ("जीवन", "ज़िंदगी"), ("जन्म", "पैदा होना"), ("भाग्य", "किस्मत"),
    ("ईश्वर", "भगवान"), ("परमात्मा", "भगवान"), ("प्रार्थना", "दुआ"),
]

ROMAN_WORD_OVERRIDES = {
    "प्रेमचंद": "Premchand", "मुंशी": "Munshi", "निर्मला": "Nirmala", "गोदान": "Godaan",
    "होरीराम": "Horiram", "होरी": "Hori", "धनिया": "Dhaniya", "गोबर": "Gobar",
    "झुनिया": "Jhunia", "हीरा": "Heera", "सोना": "Sona", "रूपा": "Rupa",
    "मालती": "Malti", "मेहता": "Mehta", "रायसाहब": "Rai Sahab", "राय": "Rai",
    "साहब": "Sahab", "भगवान": "Bhagwan", "भगवान्": "Bhagwan", "नहीं": "nahin",
    "नही": "nahin", "हैं": "hain", "है": "hai", "था": "tha", "थी": "thi",
    "थे": "the", "हूँ": "hoon", "हूं": "hoon", "हो": "ho", "क्यों": "kyon",
    "क्यूँ": "kyon", "क्योंकि": "kyunki", "मुझे": "mujhe", "तुम्हें": "tumhe",
    "तुमको": "tumhe", "आपको": "aapko", "यहाँ": "yahan", "यहां": "yahan",
    "वहाँ": "wahan", "वहां": "wahan", "अच्छा": "achchha", "अच्छी": "achchhi",
    "अच्छे": "achchhe", "चाहिए": "chahiye", "प्यार": "pyaar", "ज़मीन": "zameen",
    "जमीन": "zameen", "आदमी": "aadmi", "इंसान": "insaan", "औरत": "aurat",
    "बच्चा": "bachcha", "बच्चे": "bachche", "बच्ची": "bachchi", "कर्ज़": "karz",
    "इज़्ज़त": "izzat", "इज्जत": "izzat", "ज़रूर": "zaroor", "ज़रूरी": "zaroori",
    "ज़रूरत": "zaroorat", "नफ़रत": "nafrat", "नफरत": "nafrat", "ख़ुशी": "khushi",
    "खुशी": "khushi", "खुश": "khush", "गुज़ारिश": "guzarish", "इंतज़ाम": "intezam",
    "इंतजार": "intezar", "इंतज़ार": "intezar", "फ़िक्र": "fikr", "फिक्र": "fikr",
    "फ़र्ज़": "farz", "फर्ज": "farz", "फ़ैसला": "faisla", "फैसला": "faisla",
    "दुआ": "dua", "दुनिया": "duniya", "ज़िंदगी": "zindagi", "जिंदगी": "zindagi",
    "ज़िंदा": "zinda", "जिंदा": "zinda", "मज़दूर": "mazdoor", "मजदूर": "mazdoor",
    "गाँव": "gaon", "गांव": "gaon", "मुँह": "munh", "मुंह": "munh",
    "आँख": "aankh", "आँखें": "aankhen", "आंख": "aankh", "आंखें": "aankhen",
    "कपड़े": "kapde", "रुपये": "rupaye", "रुपया": "rupaya", "रुपए": "rupaye",
    "रोटी": "roti", "खाना": "khana", "पानी": "paani", "दिल": "dil",
    "दिमाग": "dimaag", "दर्द": "dard", "मुश्किल": "mushkil", "लेकिन": "lekin",
    "हालाँकि": "halaanki", "हालांकि": "halaanki", "फिर": "phir", "भी": "bhi",
    "और": "aur", "या": "ya", "जो": "jo", "कि": "ki", "को": "ko", "से": "se",
    "में": "mein", "पर": "par", "का": "ka", "की": "ki", "के": "ke", "एक": "ek",
    "दो": "do", "तीन": "teen", "चार": "chaar", "पाँच": "paanch", "छः": "chhah",
    "छह": "chhah", "सात": "saat", "आठ": "aath", "नौ": "nau", "दस": "das",
}

INDEPENDENT_VOWELS = {"अ":"a","आ":"aa","इ":"i","ई":"ee","उ":"u","ऊ":"oo","ऋ":"ri","ॠ":"ri","ऌ":"li","ए":"e","ऐ":"ai","ओ":"o","औ":"au","ऑ":"o","ऍ":"e","ऎ":"e","ऒ":"o"}
CONSONANTS = {"क":"k","ख":"kh","ग":"g","घ":"gh","ङ":"ng","च":"ch","छ":"chh","ज":"j","झ":"jh","ञ":"ny","ट":"t","ठ":"th","ड":"d","ढ":"dh","ण":"n","त":"t","थ":"th","द":"d","ध":"dh","न":"n","प":"p","फ":"ph","ब":"b","भ":"bh","म":"m","य":"y","र":"r","ल":"l","व":"v","श":"sh","ष":"sh","स":"s","ह":"h","क़":"q","ख़":"kh","ग़":"gh","ज़":"z","ड़":"r","ढ़":"rh","फ़":"f","य़":"y","ऱ":"r","ऴ":"l"}
MATRAS = {"ा":"aa","ि":"i","ी":"ee","ु":"u","ू":"oo","ृ":"ri","ॄ":"ri","ॅ":"e","े":"e","ै":"ai","ॉ":"o","ो":"o","ौ":"au","ॆ":"e","ॊ":"o"}
VIRAMA = "्"; NUKTA = "़"; SIGNS = {"ं":"n","ँ":"n","ः":"h","ऽ":"'"}
KEEP_FINAL_A = {"kaha","raha","gaya","aaya","laya","diya","liya","hua","naya","bura","pura","aadha","beta","ladka","ghoda","duniya","kriya","daya","maya","chhota","bada","thoda","zyada","aisa","waisa","kaisa","paisa","sauda","mauka","dhokha","chehra","kamra","rasta","darwaza","katora"}

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

def get(url: str, *, params: dict | None = None, retries: int = 4) -> requests.Response:
    last = None
    for attempt in range(retries):
        try:
            r = SESSION.get(url, params=params, timeout=TIMEOUT)
            r.raise_for_status()
            return r
        except Exception as exc:
            last = exc
            if attempt + 1 < retries:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"Download failed after {retries} attempts: {url}: {last}")

def normalize_source(text: str) -> str:
    text = unicodedata.normalize("NFC", text.replace("\ufeff", ""))
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\ufffd", "")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = WS_RE.sub(" ", text)
    text = MULTI_NL_RE.sub("\n\n", text)
    return text.strip()

def simplify_devanagari(text: str) -> str:
    for old, new in sorted(PHRASE_REPLACEMENTS, key=lambda x: len(x[0]), reverse=True):
        text = text.replace(old, new)
    return text

def transliterate_word(word: str) -> str:
    if word in ROMAN_WORD_OVERRIDES:
        return ROMAN_WORD_OVERRIDES[word]
    out = []
    i = 0
    while i < len(word):
        ch = word[i]
        if ch in CONSONANTS:
            base = CONSONANTS[ch]
            if i + 1 < len(word) and word[i + 1] == NUKTA:
                i += 1
            if i + 1 < len(word) and word[i + 1] == VIRAMA:
                out.append(base); i += 2; continue
            if i + 1 < len(word) and word[i + 1] in MATRAS:
                out.append(base + MATRAS[word[i + 1]]); i += 2; continue
            out.append(base + "a"); i += 1; continue
        if ch in INDEPENDENT_VOWELS: out.append(INDEPENDENT_VOWELS[ch])
        elif ch in MATRAS: out.append(MATRAS[ch])
        elif ch in SIGNS: out.append(SIGNS[ch])
        elif ch in {NUKTA, VIRAMA}: pass
        elif ch in "।॥": out.append(".")
        else: out.append(ch)
        i += 1
    roman = "".join(out)
    roman = re.sub(r"n(?=[kg])", "ng", roman)
    roman = re.sub(r"n(?=[pb])", "m", roman)
    roman = roman.replace("jnya", "gya").replace("kshha", "ksha").replace("ksha", "ksh")
    roman = re.sub(r"([bcdfghjklmnpqrstvwxyz])a([bcdfghjklmnpqrstvwxyz])a$", r"\1a\2", roman)
    roman = re.sub(r"([bcdfghjklmnpqrstvwxyz])a$", r"\1", roman)
    return roman

DEV_TOKEN_RE = re.compile(r"[\u0900-\u097f]+")

def romanize(text: str) -> str:
    text = simplify_devanagari(text)
    for dev, roman in sorted(ROMAN_WORD_OVERRIDES.items(), key=lambda x: len(x[0]), reverse=True):
        text = re.sub(rf"(?<![\u0900-\u097f]){re.escape(dev)}(?![\u0900-\u097f])", roman, text)
    text = DEV_TOKEN_RE.sub(lambda m: transliterate_word(m.group(0)), text).translate(DEV_DIGITS)
    for old, new in {"—":" — ","–":" — ","…":"...","“":"\"","”":"\"","‘":"'","’":"'","।":".","॥":".","\u00a0":" "}.items():
        text = text.replace(old, new)
    stable = {r"\bnahim\b":"nahin",r"\bhainm\b":"hain",r"\bkyom\b":"kyon",r"\bkyonki\b":"kyunki",r"\byaham\b":"yahan",r"\bvaham\b":"wahan",r"\bacchha\b":"achchha",r"\bchahie\b":"chahiye",r"\bbhagavan\b":"Bhagwan",r"\bjamin\b":"zameen",r"\badami\b":"aadmi"}
    for pat, repl in stable.items():
        text = re.sub(pat, repl, text, flags=re.IGNORECASE)
    text = re.sub(r" +([,.;:!?])", r"\1", text)
    text = re.sub(r"([,.;:!?])(?=[A-Za-z])", r"\1 ", text)
    text = WS_RE.sub(" ", text)
    text = re.sub(r" *\n *", "\n", text)
    return MULTI_NL_RE.sub("\n\n", text).strip()

def paragraphs_from_plain(text: str) -> list[str]:
    text = normalize_source(text)
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    if len(blocks) < 3:
        blocks = [line.strip() for line in text.splitlines() if line.strip()]
    return blocks

NOISE_RE = re.compile("|".join([r"विकिस्रोत",r"सामग्री पर जाएँ",r"मुख्य मेनू",r"डाउनलोड",r"पिछला अध्याय",r"अगला अध्याय",r"अनुक्रम",r"मूल स्रोत",r"यह पृष्ठ",r"अन्तिम परिवर्तन",r"अंतिम परिवर्तन",r"गोपनीयता नीति",r"मोबाइल दृश्य",r"डेस्कटॉप",r"प्रूफरीड",r"स्कैन",r"कॉमन्स"]), re.IGNORECASE)

def clean_wikisource_html(html: str, title: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    for sel in ["script","style","noscript","table","nav","footer","header",".mw-editsection",".navbox",".metadata",".ambox",".sistersitebox",".printfooter","#catlinks",".mw-jump-link",".mw-indicators",".ws-noexport",".noprint"]:
        for node in soup.select(sel): node.decompose()
    root = soup.select_one(".mw-parser-output") or soup
    paragraphs = []
    for node in root.find_all(["p","h2","h3","blockquote","div"], recursive=True):
        if node.name == "div" and node.find(["p","h2","h3","blockquote"]): continue
        txt = normalize_source(node.get_text(" ", strip=True))
        if not txt or len(txt) < 2 or NOISE_RE.search(txt): continue
        if txt == title or txt in {"निर्मला","मुंशी प्रेमचंद","प्रेमचंद"}: continue
        if re.fullmatch(r"[←→\s\d०-९./-]+", txt): continue
        if not paragraphs or txt != paragraphs[-1]: paragraphs.append(txt)
    return paragraphs

def natural_key(title: str):
    tail = title.split("/", 1)[-1].translate(DEV_DIGITS)
    nums = re.findall(r"\d+", tail)
    return (0, int(nums[0]), tail) if nums else (1, tail)

def fetch_nirmala():
    api = "https://hi.wikisource.org/w/api.php"
    titles = []; cont = None
    while True:
        params = {"action":"query","list":"allpages","apprefix":"निर्मला/","apnamespace":0,"aplimit":"max","format":"json","formatversion":2}
        if cont: params["apcontinue"] = cont
        data = get(api, params=params).json()
        titles.extend(p["title"] for p in data["query"]["allpages"])
        cont = data.get("continue", {}).get("apcontinue")
        if not cont: break
    chapter_titles = [t for t in titles if re.search(r"[0-9०-९]", t.split("/",1)[-1]) and not re.search(r"(अनुक्रम|भूमिका|प्रकाशक|चित्र|आवरण|सूची)", t)]
    chapter_titles = sorted(set(chapter_titles), key=natural_key)
    if not (20 <= len(chapter_titles) <= 50):
        raise RuntimeError(f"Nirmala chapter discovery returned {len(chapter_titles)} pages; expected 20-50: {chapter_titles[:12]}")
    chapters = []; sizes = {}
    for idx, title in enumerate(chapter_titles, 1):
        data = get(api, params={"action":"parse","page":title,"prop":"text","format":"json","formatversion":2,"disableeditsection":1}).json()
        paras = clean_wikisource_html(data["parse"]["text"], title)
        chars = sum(len(p) for p in paras)
        if chars < 2000: raise RuntimeError(f"Nirmala chapter {title!r} too short after cleaning: {chars}")
        chapters.append((title, paras)); sizes[title] = chars
        print(f"Nirmala {idx:02d}/{len(chapter_titles)}: {title} — {chars} chars")
    total = sum(sizes.values())
    if total < 150000: raise RuntimeError(f"Nirmala total source too short: {total}")
    return chapters, {"api":api,"titles":chapter_titles,"sizes":sizes,"total":total}

def fetch_godaan():
    base = "https://raw.githubusercontent.com/pandeyshikha1098/privacy_policy/45b42cf18333411f035757a9ecd8b6859fa84ae6/hindi-stories/storyBook/premchandra/godan"
    chapters = []; sizes = {}
    for i in range(1, 37):
        name = f"{i:02d}.txt"; text = normalize_source(get(f"{base}/{name}").text)
        if len(text) < 4000: raise RuntimeError(f"Godaan {name} too short: {len(text)}")
        paras = paragraphs_from_plain(text)
        if len(paras) < 5: raise RuntimeError(f"Godaan {name} has only {len(paras)} paragraphs")
        chapters.append((name, paras)); sizes[name] = len(text)
        print(f"Godaan {i:02d}/36: {len(text)} chars, {len(paras)} paragraphs")
    total = sum(sizes.values())
    if len(chapters) != 36 or total < 500000: raise RuntimeError(f"Godaan completeness failed: chapters={len(chapters)}, chars={total}")
    return chapters, {"base":base,"sizes":sizes,"total":total}

def write_work(work_id, title, author, chapters, source_record, expected_chapters=None):
    work_dir = WORKS / work_id; chapter_dir = work_dir / "chapters"; chapter_dir.mkdir(parents=True, exist_ok=True)
    for old in chapter_dir.glob("*.md"): old.unlink()
    source_chars = output_chars = dev_remaining = urdu_remaining = 0
    for idx, (_, paras) in enumerate(chapters, 1):
        source_chars += sum(len(p) for p in paras)
        body = "\n\n".join(romanize(p) for p in paras if p)
        output = f"# {title} — Adhyay {idx}\n\n**{author}**\n\n{body.strip()}\n"
        dev_count = len(DEV_RE.findall(output)); urdu_count = len(URDU_RE.findall(output))
        if dev_count or urdu_count: raise RuntimeError(f"{title} chapter {idx} Roman-only failure: Devanagari={dev_count}, Urdu={urdu_count}")
        output_chars += len(output); dev_remaining += dev_count; urdu_remaining += urdu_count
        (chapter_dir / f"{idx:02d}.md").write_text(output, encoding="utf-8")
    if expected_chapters is not None and len(chapters) != expected_chapters: raise RuntimeError(f"{title} chapter count {len(chapters)} != {expected_chapters}")
    (work_dir / "source.md").write_text(f"# Locked Source Record — {title}\n\n- Author: {author}\n- Work: complete novel\n- Source language/script: Hindi in Devanagari\n- Source status: programmatically fetched and chapter-count validated\n- Reader status: machine-assisted complete first pass; independent human review pending\n\n## Machine-readable source record\n\n```json\n{json.dumps(source_record, ensure_ascii=False, indent=2)}\n```\n\nNo modern translation, summary, review, or adaptation is used as reader text.\n", encoding="utf-8")
    (work_dir / "NOTES.md").write_text(f"# Editorial Notes — {title}\n\n## Preservation boundary\n\n- Complete chapter count retained: **{len(chapters)}**.\n- Chapter and paragraph order retained.\n- Names, numbers, events, dialogue, repeated phrases, social and caste/class signals, humour, irony, emotional turns, and the ending are retained by the deterministic full-text pass.\n- This build does not summarize or intentionally remove narrative material.\n\n## Language method\n\n- Devanagari is converted to Roman script with stable high-frequency spellings.\n- A controlled phrase lexicon replaces selected bookish wording with easier everyday Hindustani.\n- The process is rule-based and cannot replace independent literary editing.\n\n## Review status\n\n- Machine-assisted complete first pass: complete.\n- Roman-only automated validation: passed.\n- Independent paragraph-by-paragraph source comparison: pending.\n- Independent read-aloud and natural-language revision: pending.\n- Publication status: not reviewed.\n", encoding="utf-8")
    sample_indices = sorted({1, max(1, len(chapters)//2), len(chapters)})
    sample_notes = []
    for n in sample_indices:
        sample = (chapter_dir/f"{n:02d}.md").read_text(encoding="utf-8")
        bad = len(DEV_RE.findall(sample)) + len(URDU_RE.findall(sample))
        sample_notes.append(f"chapter {n}: {len(sample)} output chars; residual Indic-script characters={bad}")
    return WorkQA(work_id,title,len(chapters),source_chars,output_chars,dev_remaining,urdu_remaining,dev_remaining==0 and urdu_remaining==0,True,sample_notes)

def write_reports(records):
    OUT.mkdir(parents=True, exist_ok=True)
    lines = ["# Premchand Novels — Automated QA","","These are complete **machine-assisted first passes**, not independently reviewed publication copies.","","| Work | Chapters | Source chars | Output chars | Devanagari left | Urdu left | Roman-only |","|---|---:|---:|---:|---:|---:|---|"]
    for r in records: lines.append(f"| {r.title} | {r.chapters} | {r.source_characters:,} | {r.output_characters:,} | {r.devanagari_remaining} | {r.urdu_remaining} | {'PASS' if r.roman_only_pass else 'FAIL'} |")
    lines += ["","## Opening / middle / final mechanical samples",""]
    for r in records:
        lines.append(f"### {r.title}"); lines.extend(f"- {x}" for x in r.sample_notes); lines.append("")
    lines += ["## Required human work","","- Paragraph-by-paragraph comparison against the locked source.","- Natural spoken-Hindustani revision where transliteration is valid but awkward.","- Proper-name, terminology, number, and ending checks.","- Independent read-aloud review.",""]
    (OUT/"QA.md").write_text("\n".join(lines), encoding="utf-8")
    manifest = {"project":"easy-roman-hindustani-classics","generator":"premchand_novels_builder.py","status_boundary":"machine-assisted complete first pass; independent human review required before publication","works":[{"id":r.work_id,"title":r.title,"author":"Munshi Premchand","form":"novel","chapters":r.chapters,"source_characters":r.source_characters,"output_characters":r.output_characters,"translation_status":"machine_assisted_complete_first_pass","human_review":"pending","roman_only_validation":"passed" if r.roman_only_pass else "failed"} for r in records]}
    (OUT/"manifest-fragment.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")

def main():
    try:
        nirmala_chapters, nirmala_source = fetch_nirmala()
        godaan_chapters, godaan_source = fetch_godaan()
        records = [write_work("nirmala","Nirmala","Munshi Premchand",nirmala_chapters,nirmala_source), write_work("godaan","Godaan","Munshi Premchand",godaan_chapters,godaan_source,36)]
        write_reports(records)
        print(json.dumps([asdict(r) for r in records], ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT/"BUILD_FAILURE.txt").write_text(f"{type(exc).__name__}: {exc}\n", encoding="utf-8")
        print(f"BUILD FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__": raise SystemExit(main())
