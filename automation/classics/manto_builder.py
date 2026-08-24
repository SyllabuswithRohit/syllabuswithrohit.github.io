#!/usr/bin/env python3
"""Build eight complete Manto stories as easy Roman-Hindustani first passes.

The source is Manto's Urdu text rendered in Devanagari on full-story pages. The
builder slices only the authorial story, applies a controlled easy-language
lexicon, preserves paragraph order, converts to Roman script, and validates
that no Indic script remains. Every output stays marked for human review.
"""

from __future__ import annotations

import json
import re
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent))
from premchand_novels_builder import (  # noqa: E402
    DEV_RE,
    OUT,
    ROOT,
    URDU_RE,
    get,
    normalize_source,
    romanize,
)

WORK_ROOT = OUT / "works" / "manto"

STORIES = [
    {
        "id": "toba-tek-singh",
        "title": "Toba Tek Singh",
        "urls": [
            "https://www.rekhta.org/stories/toba-tek-singh-saadat-hasan-manto-stories?lang=hi",
        ],
        "starts": ["बटवारे के दो-तीन साल बाद", "तक़सीम के दो तीन साल बाद"],
        "min_chars": 7000,
        "content_note": "Partition, institutional confinement, discriminatory language, and death.",
    },
    {
        "id": "khol-do",
        "title": "Khol Do",
        "urls": [
            "https://www.rekhta.org/stories/khol-do-saadat-hasan-manto-stories?lang=hi",
        ],
        "starts": ["अमृतसर से", "स्पेशल ट्रेन अमृतसर से"],
        "min_chars": 3000,
        "content_note": "Partition violence and sexual violence; the source ending is not softened.",
    },
    {
        "id": "thanda-gosht",
        "title": "Thanda Gosht",
        "urls": [
            "https://www.rekhta.org/stories/thanda-gosht-saadat-hasan-manto-stories?lang=hi",
        ],
        "starts": ["ईशर सिंह", "ईश्वर सिंह"],
        "min_chars": 5000,
        "content_note": "Adult sexual material, communal violence, killing, and sexual violence.",
    },
    {
        "id": "bu",
        "title": "Bu",
        "urls": [
            "https://www.rekhta.org/stories/boo-saadat-hasan-manto-stories?lang=hi",
            "https://www.rekhta.org/stories/bu-saadat-hasan-manto-stories?lang=hi",
        ],
        "starts": ["बरसात के यही दिन थे", "बरसात के दिन थे"],
        "min_chars": 5000,
        "content_note": "Adult desire, sex-work context, smell, class, and memory.",
    },
    {
        "id": "kali-shalwar",
        "title": "Kali Shalwar",
        "urls": [
            "https://www.rekhta.org/stories/kaali-shalwaar-saadat-hasan-manto-stories?lang=hi",
            "https://www.rekhta.org/stories/kali-shalwar-saadat-hasan-manto-stories?lang=hi",
        ],
        "starts": ["मुहर्रम का महीना सर पर", "मुहर्रम का महीना सिर पर"],
        "min_chars": 9000,
        "content_note": "Sex-work setting, poverty, adult relationships, and exploitation.",
    },
    {
        "id": "hatak",
        "title": "Hatak",
        "urls": [
            "https://www.rekhta.org/stories/hatak-saadat-hasan-manto-stories?lang=hi",
        ],
        "starts": ["दिन भर की थकी", "दिन-भर की थकी"],
        "min_chars": 7000,
        "content_note": "Sex-work setting, humiliation, alcohol, and emotional abuse.",
    },
    {
        "id": "naya-qanoon",
        "title": "Naya Qanoon",
        "urls": [
            "https://www.rekhta.org/stories/nayaa-qanoon-saadat-hasan-manto-stories?lang=hi",
            "https://www.rekhta.org/stories/naya-qanoon-saadat-hasan-manto-stories?lang=hi",
        ],
        "starts": ["उस्ताद मंगू", "मंगू कोचवान"],
        "min_chars": 7000,
        "content_note": "Colonial racism, political confusion, insults, and police violence.",
    },
    {
        "id": "tetwal-ka-kutta",
        "title": "Tetwal Ka Kutta",
        "urls": [
            "https://www.rekhta.org/stories/tetwaal-ka-kutta-saadat-hasan-manto-stories?lang=hi",
            "https://www.rekhta.org/stories/tetwal-ka-kutta-saadat-hasan-manto-stories?lang=hi",
        ],
        "starts": ["कई दिन से तरफ़ैन", "कई दिन से तरफ़ैन", "कई दिनों से दोनों तरफ"],
        "min_chars": 5000,
        "content_note": "War, military violence, discriminatory speech, and animal death.",
    },
]

# Exact easy-language replacements. These are applied to phrases/whole source
# spellings before Roman conversion. Names, ranks, money, food, clothes, songs,
# slogans, insults, jokes, violence, sexuality, and repeated speech remain.
MANTO_EASY = {
    "अख़लाक़ी क़ैदियों": "जुर्म करने वाले कैदियों",
    "अख़लाक़ी क़ैदियों": "जुर्म करने वाले कैदियों",
    "हुकूमतों": "सरकारों", "हुकूमत": "सरकार",
    "तबादले": "अदला-बदली", "तबादला": "अदला-बदली",
    "ग़ैरमाक़ूल": "बे-समझ", "ग़ैरमाक़ूल": "बे-समझ", "माक़ूल": "समझ में आने वाली",
    "दानिशमंदों": "समझदार लोगों", "फ़ैसले के मुताबिक़": "फैसले के हिसाब से",
    "फ़ैसले के मुताबिक़": "फैसले के हिसाब से", "बिलआख़िर": "आखिर",
    "मुक़र्रर": "तय", "लवाहिक़ीन": "रिश्तेदार", "लवाहिकीन": "रिश्तेदार",
    "हिफ़ाज़त": "देख-रेख", "हिफ़ाज़त": "देख-रेख", "बहरहाल": "जो भी हो",
    "क़रीब-क़रीब": "लगभग", "क़रीब-क़रीब": "लगभग", "तमाम": "सारे",
    "चेमिगोईयां": "बातें और अटकलें", "गौर-ओ-फ़िक्र": "गहरी सोच",
    "ग़ौर-ओ-फ़िक्र": "गहरी सोच", "मुतमइन": "संतुष्ट", "बा'ज़": "कुछ",
    "अक्सरियत": "ज़्यादातर", "क़ातिलों": "हत्यारों", "क़ातिलों": "हत्यारों",
    "वाक़ियात": "घटनाओं", "अख़्बारों": "अखबारों", "गुफ़्तुगू": "बातचीत",
    "नतीजा बरामद": "नतीजा निकाल", "अलाहिदा": "अलग", "महल-ए-वक़ूअ": "ठीक जगह",
    "मुतअल्लिक़": "के बारे में", "मुतअल्लिक़": "के बारे में", "माऊफ़": "सुन्न",
    "गिरफ़्तार": "फँसे", "तक़्सीम": "बँटवारा", "तक़्सीम": "बँटवारा",
    "अर्से": "समय", "मुसलसल": "लगातार", "तक़रीर": "भाषण",
    "नुमूदार": "दिखाई", "दफ़अतन": "अचानक", "यकलख़्त": "अचानक",
    "तर्क कर दी": "छोड़ दी", "चुनांचे": "इसलिए", "ख़ूनख़राबा": "मार-काट",
    "क़रार दे कर": "मानकर", "दीवानगी": "पागलपन", "महबूबा": "प्यारी औरत",
    "मोहब्बत": "प्यार", "ख़ामोश": "चुप", "ख़ामोश": "चुप", "हैसियत": "दर्जा",
    "मसले": "सवाल", "तवील": "लंबे", "जिस्मानी": "बदन की",
    "संजीदगी": "गंभीरता", "क़तअन": "बिल्कुल", "दरयाफ़्त": "पूछ",
    "इस्तेमाल": "काम", "ख़्वाहिश": "चाह", "यक़ीनन": "ज़रूर",
    "हस्ब-ए-आदत": "अपनी आदत के अनुसार", "क़हक़हा": "ठहाका",
    "मिन्नत-समाजत": "बहुत बिनती", "मसरूफ़": "व्यस्त", "बेशुमार": "बहुत से",
    "ख़ैरियत": "ठीक-ठाक", "ख़िदमत": "मदद", "हैरत": "हैरानी",
    "मुकम्मल": "पूरी", "फ़हरिस्तें": "सूचियाँ", "मुहाफ़िज़ दस्ते": "रक्षा करने वाले पुलिस दल",
    "मुहाफ़िज़ दस्ते": "रक्षा करने वाले पुलिस दल", "तरफ़ैन": "दोनों तरफ",
    "इब्तिदाई कार्रवाई": "शुरुआती काम", "रज़ामंद": "तैयार", "रज़ामंद": "तैयार",
    "तन से जुदा": "बदन से अलग", "शोर-ओ-गोगा": "शोर", "हक़ में": "पक्ष में",
    "बाक़ी-मांदा": "बाकी", "मज़ीद": "और", "साकित-ओ-सामित": "बिल्कुल चुप",
    "हलक़": "गला", "फ़लक-शिगाफ़": "आसमान फाड़ती", "ख़ारदार": "काँटेदार",
    "मुतअद्दिद": "कई", "ज़ख़्मी": "घायल", "ज़ख़्मी": "घायल",
    "क़ुव्वतें": "ताकत", "ज़ईफ़": "कमज़ोर", "बरपा": "मचा",
    "होश-ओ-हवास": "होश", "वजूद": "पूरा बदन और मन", "ख़ला": "खालीपन",
    "मुअल्लक़": "लटका", "बग़ैर": "बिना", "रग-ओ-रेशे": "पूरे बदन",
    "ख़ाक छानता": "भटकता", "हाफ़िज़े": "याददाश्त", "हाफ़िज़े": "याददाश्त",
    "बलवाई": "दंगाई", "रज़ाकार": "मदद करने वाले", "रज़ाकार": "मदद करने वाले",
    "जज़्बे": "जोश", "हुलिया": "शक्ल और पहचान", "स्याह": "काले",
    "महफ़ूज़ मुक़ामों": "सुरक्षित जगहों", "महफ़ूज़ मुक़ामों": "सुरक्षित जगहों",
    "वहशत": "डर", "दिलजोई": "देखभाल", "मुख़्तलिफ़": "अलग-अलग",
    "यक ज़बान": "एक साथ", "सुपुर्द": "हवाले", "आहिस्ता": "धीरे",
    "ज़र्द": "पीला", "जुंबिश": "हरकत", "इज़ारबंद": "शलवार का नाड़ा",
    "दाख़िल": "अंदर", "जिस्म": "बदन", "शुब्हा": "शक",
    "अज़्म": "पक्का इरादा", "मुज़ाहमत": "विरोध", "इल्तिजा": "बिनती",
    "नक़ाहत": "कमज़ोरी", "तवज्जो": "ध्यान", "बेरहमी": "निर्दयता",
    "लफ़्ज़": "शब्द", "इल्फ़ाज़": "शब्द", "अल्फ़ाज़": "शब्द",
    "बमुश्किल": "मुश्किल से", "क़िस्म": "तरह", "क़िस्म": "तरह",
    "हर्गिज़": "बिल्कुल नहीं", "तअल्लुक़": "रिश्ता", "तअल्लुक़ात": "रिश्ते",
    "तस्कीन": "सुकून", "महज़ूज़": "खुश", "लम्हाती": "कुछ पल की",
    "मुस्तहकम": "मज़बूत", "आमेज़िश": "मिलावट", "मुक़द्दस": "पवित्र",
    "तअज्जुब": "हैरानी", "हमराह": "साथ", "फ़िज़ा": "हवा और माहौल",
    "असरार": "रहस्य", "पुरअसरार": "रहस्य भरी", "वाज़ेह": "साफ",
    "मग़्मूम": "उदास", "हस्ब-ए-मामूल": "हमेशा की तरह", "जायज़ा": "देखना",
    "मेहरबान": "दयालु", "अकारत": "बेकार", "सरमाया": "शुरू करने का पैसा",
    "हीला": "तरीका", "मशक़्क़त": "मेहनत", "बेतर्तीबी": "बिखरे ढंग",
    "शिद्दत": "तेज़ी", "मनी आर्डर": "डाक से पैसा", "मुलम्मा": "ऊपरी चमक",
    "बेसूद": "बेकार", "मुलाज़िमत": "नौकरी", "जदीद": "नया", "आईन": "कानून",
    "नफ़िज़": "लागू", "नाफ़िज़": "लागू", "सरगर्मियों": "कामों",
    "तहरीक": "आंदोलन", "ख़लत-मलत": "गड़बड़ मिलाकर", "बग़ावत": "विद्रोह",
    "इल्ज़ाम": "आरोप", "मुक़द्दमा": "मुकदमा", "पेशख़ैमा": "पहला संकेत",
    "बेशतर": "ज़्यादातर", "जुमले": "वाक्य", "ज़ेर-ए-असर": "असर में",
    "हक़ारत": "नफरत और नीचा समझने", "अहलियत": "योग्यता", "अहमियत": "महत्त्व",
    "तसव्वुर": "कल्पना", "ग़ैर-मामूली": "बहुत अलग", "रऊनत": "अकड़",
    "ख़ुशपोश": "अच्छे कपड़ों वाले", "आमद-ओ-रफ़्त": "आना-जाना",
    "मक़्सूद": "चाही हुई", "इत्मिनान": "सुकून", "क़यासात": "अटकलें",
    "सई": "कोशिश", "जज़्बात": "भाव", "बेदार": "जाग",
    "तंज़िया": "ताना मारने वाला", "बयक वक़्त": "एक साथ",
    "मस्लिहत": "सोची-समझी वजह", "तौअन-करहन": "मजबूरी में",
    "पेशे नज़र": "याद रखकर", "हौसला-अफ़्ज़ा": "हिम्मत बढ़ाने वाला",
    "शश्दर-ओ-मुतहय्यर": "हक्का-बक्का", "मजमें": "भीड़",
    "हैरतज़दा": "हैरान", "हवालात": "पुलिस की कोठरी", "अंजाम": "अंत",
    "आग़ाज़": "शुरुआत", "बग़लगीर": "गले मिलता", "सरमा": "सर्दी",
    "तफ़रीह": "सैर", "कोफ़्त": "ऊब", "फ़ैसलाकुन": "फैसला करने वाली",
    "बाज़गश्त": "गूँज", "ख़ुनकी": "हल्की ठंड", "अलबत्ता": "हाँ",
    "नागवार": "बुरी", "मुतय्यन": "तैनात", "पुरसोज़": "दर्द भरी",
    "दफ़अतन": "अचानक", "लर्ज़ां": "काँपती", "मुआमला": "मामला",
    "वाबस्ता": "जुड़ी", "हिदायात": "हुक्म", "इबारत": "लिखी बात",
    "ग़द्दारी": "धोखा", "दामन": "नीचे का हिस्सा", "शिस्त": "निशाना",
    "पैवस्त": "धँस", "बौखलाहट": "घबराहट", "मसरूर": "खुश",
    "पर्वा": "परवाह", "तरफ़": "तरफ",
}

END_MARKERS = (
    "\nस्रोत :", "\nस्रोत:", "\n## वीडियो", "\nवीडियो", "\nRECITATIONS",
    "\nसंबंधित टैग", "\nMORE BY", "\nऔर पढ़िए", "\nऑडियो", "\nशब्दकोश",
)


def canonical(text: str) -> str:
    text = text.replace("\u093c", "")
    text = text.replace("क़", "क").replace("ख़", "ख").replace("ग़", "ग").replace("ज़", "ज")
    text = text.replace("फ़", "फ").replace("ड़", "ड").replace("ढ़", "ढ")
    return re.sub(r"\s+", " ", text).strip()


def page_text(url: str) -> str:
    html = get(url).text
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.select("script,style,noscript,svg,iframe,nav,footer,header"):
        tag.decompose()
    for br in soup.find_all("br"):
        br.replace_with("\n")
    text = soup.get_text("\n")
    text = text.replace("\r", "")
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text)


def locate_start(text: str, markers: list[str]) -> int:
    for marker in markers:
        pos = text.find(marker)
        if pos >= 0:
            return pos
    ctext = canonical(text)
    for marker in markers:
        cmarker = canonical(marker)
        pos = ctext.find(cmarker)
        if pos >= 0:
            # Canonical text changes length, so recover a nearby original index from the
            # first two words. This is safe because we validate source length afterward.
            words = marker.split()[:2]
            for word in words:
                raw = text.find(word)
                if raw >= 0:
                    return raw
    return -1


def extract_story(text: str, starts: list[str], min_chars: int) -> str:
    start = locate_start(text, starts)
    if start < 0:
        raise RuntimeError(f"Opening marker not found; tried: {starts}")
    tail = text[start:]
    cuts = [tail.find(m) for m in END_MARKERS if tail.find(m) > min_chars]
    if cuts:
        tail = tail[:min(cuts)]
    cleaned = []
    skip_exact = {"[Input]", "Read more", "MORE BY", "सुनिए", "Listen", "शेयर", "COPY"}
    for line in tail.splitlines():
        s = line.strip()
        if not s:
            cleaned.append("")
            continue
        if s in skip_exact:
            continue
        if re.fullmatch(r"(स्रोत|वीडियो|ऑडियो|RECITATIONS|MORE BY).*", s, re.I):
            break
        cleaned.append(s)
    story = normalize_source("\n".join(cleaned))
    if len(story) < min_chars:
        raise RuntimeError(f"Extracted story unexpectedly short: {len(story)} < {min_chars}")
    if len(story) > 120000:
        raise RuntimeError(f"Extracted story suspiciously long, likely includes interface text: {len(story)}")
    return story


def easy_source(text: str) -> str:
    for old, new in sorted(MANTO_EASY.items(), key=lambda kv: len(kv[0]), reverse=True):
        text = text.replace(old, new)
    return text


@dataclass
class StoryQA:
    work_id: str
    title: str
    source_url: str
    source_characters: int
    output_characters: int
    devanagari_remaining: int
    urdu_remaining: int
    roman_only_pass: bool


def build_story(item: dict) -> StoryQA:
    errors = []
    source_story = None
    source_url = None
    for url in item["urls"]:
        try:
            raw = page_text(url)
            source_story = extract_story(raw, item["starts"], item["min_chars"])
            source_url = url
            break
        except Exception as exc:
            errors.append(f"{url}: {type(exc).__name__}: {exc}")
            time.sleep(2)
    if source_story is None or source_url is None:
        raise RuntimeError(" | ".join(errors))

    reader = romanize(easy_source(source_story))
    output = f"# {item['title']}\n\n**Saadat Hasan Manto**\n\n{reader.strip()}\n"
    dev = len(DEV_RE.findall(output))
    urdu = len(URDU_RE.findall(output))
    if dev or urdu:
        raise RuntimeError(f"Roman-only check failed: Devanagari={dev}, Urdu={urdu}")
    if len(output) < int(len(source_story) * 0.55):
        raise RuntimeError(f"Output/source ratio suspiciously low: {len(output)}/{len(source_story)}")

    work = WORK_ROOT / item["id"]
    work.mkdir(parents=True, exist_ok=True)
    (work / "translation.md").write_text(output, encoding="utf-8")
    (work / "source.md").write_text(
        f"# Locked Source Record — {item['title']}\n\n"
        f"- Author: Saadat Hasan Manto\n"
        f"- Work: complete short story\n"
        f"- Locked base language: Manto's Urdu text rendered in Devanagari\n"
        f"- Source URL: {source_url}\n"
        f"- Story opening marker: `{item['starts'][0]}`\n"
        f"- Source characters retained before conversion: {len(source_story)}\n"
        f"- Source status: locked for a machine-assisted complete first pass\n"
        f"- Human source review: pending\n\n"
        "The translation is newly produced from the underlying Manto text. Modern translations, "
        "summaries, recordings, introductions, recommendations, and site interface text are not copied.\n",
        encoding="utf-8",
    )
    (work / "NOTES.md").write_text(
        f"# Editorial Notes — {item['title']}\n\n"
        f"## Content note\n\n{item['content_note']}\n\n"
        "## Preservation and language\n\n"
        f"- Complete ordered source characters before conversion: {len(source_story)}.\n"
        "- Difficult Urdu vocabulary receives controlled everyday replacements.\n"
        "- Names, ranks, money, clothes, food, songs, slogans, insults, jokes, violence, sexuality, "
        "repetition, uncertainty, and the ending remain.\n"
        "- No scene is intentionally censored, shortened, modernized, or relocated.\n"
        "- Roman-only automated validation: passed.\n"
        "- Status: `machine_assisted_complete_first_pass`.\n"
        "- Independent Urdu paragraph comparison and read-aloud review: pending.\n"
        "- Publication status: not reviewed.\n",
        encoding="utf-8",
    )
    return StoryQA(item["id"], item["title"], source_url, len(source_story), len(output), dev, urdu, True)


def write_reports(records: list[StoryQA], failures: list[str]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Manto Stories — Automated QA", "",
        "These files are complete machine-assisted first passes and require independent human review.", "",
        "| Work | Source chars | Output chars | Devanagari left | Urdu left | Roman-only |", 
        "|---|---:|---:|---:|---:|---|",
    ]
    for r in records:
        lines.append(f"| {r.title} | {r.source_characters:,} | {r.output_characters:,} | {r.devanagari_remaining} | {r.urdu_remaining} | PASS |")
    if failures:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {f}" for f in failures)
    (OUT / "MANTO_QA.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest = {
        "project": "easy-roman-hindustani-classics",
        "generator": "manto_builder.py",
        "works": [
            {
                "id": r.work_id, "title": r.title, "author": "Saadat Hasan Manto",
                "form": "short_story", "source_characters": r.source_characters,
                "output_characters": r.output_characters,
                "translation_status": "machine_assisted_complete_first_pass",
                "human_review": "pending", "roman_only_validation": "passed",
            }
            for r in records
        ],
        "failures": failures,
    }
    (OUT / "manto-manifest-fragment.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    records = []
    failures = []
    for item in STORIES:
        try:
            record = build_story(item)
            records.append(record)
            print(json.dumps(asdict(record), ensure_ascii=False))
        except Exception as exc:
            msg = f"{item['title']}: {type(exc).__name__}: {exc}"
            failures.append(msg)
            print(msg, file=sys.stderr)
    write_reports(records, failures)
    if failures:
        (OUT / "MANTO_BUILD_FAILURE.txt").write_text("\n".join(failures) + "\n", encoding="utf-8")
        return 1
    stale = OUT / "MANTO_BUILD_FAILURE.txt"
    if stale.exists():
        stale.unlink()
    print("Built all eight complete Manto first-pass reader files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
