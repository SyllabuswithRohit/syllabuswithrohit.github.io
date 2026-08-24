#!/usr/bin/env python3
"""Build batch 2 of complete easy Roman-Hindustani Premchand readers.

The source texts are old Hindi transcriptions pinned to an immutable Git commit.
This is a conservative, machine-assisted first pass: paragraph order and all source
content are retained, a small controlled vocabulary is simplified, and Devanagari
is converted to reader-friendly Roman script. Every work remains human-review pending.
"""

from __future__ import annotations

import html
import json
import re
import time
import unicodedata
from pathlib import Path

import requests
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

ROOT = Path("generated/works/premchand")
SOURCE_REPO = "pandeyshikha1098/privacy_policy"
SOURCE_COMMIT = "45b42cf18333411f035757a9ecd8b6859fa84ae6"
RAW_ROOT = f"https://raw.githubusercontent.com/{SOURCE_REPO}/{SOURCE_COMMIT}"
UA = "SyllabuswithRohit-book-collection-batch2/1.0"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA})

WORKS = [
    {"id":"bade-bhai-sahab","title":"Bade Bhai Sahab","path":"hindi-stories/storyBook/premchandra/mansarovar-1/BadeBhaiSahib.txt","blob":"14cc777bd61a9814b6e1dc7d5fe46b360cb8ad08"},
    {"id":"gulli-danda","title":"Gulli Danda","path":"hindi-stories/storyBook/premchandra/mansarovar-1/GulliDanda.txt","blob":"36c58be16360a8e2c6cd32671649577fe4d5e36a"},
    {"id":"nasha","title":"Nasha","path":"hindi-stories/storyBook/premchandra/mansarovar-1/Nasha.txt","blob":"1191e88616e3a18f13198dcb6c3738a808d131d2"},
    {"id":"do-bailon-ki-katha","title":"Do Bailon Ki Katha","path":"hindi-stories/storyBook/premchandra/mansarovar-2/DoBailonKiKatha.txt","blob":"cdbb2357d62ede8487ac049ba6d390a8cf9e7e0c"},
    {"id":"doodh-ka-daam","title":"Doodh Ka Daam","path":"hindi-stories/storyBook/premchandra/mansarovar-2/DhoodKaDaam.txt","blob":"75729b0c696cfa2270ce2d409d4187f2dbdece90"},
    {"id":"lottery","title":"Lottery","path":"hindi-stories/storyBook/premchandra/mansarovar-2/Lottery.txt","blob":"6326b3065aaad0d7ca31aac8f7845cb696000c14"},
    {"id":"mantra","title":"Mantra","path":"hindi-stories/storyBook/premchandra/mansarovar-5/Mantra2.txt","blob":"fec736da299a584dd0795e9c9d7c6e28e7724041"},
    {"id":"sawa-ser-gehun","title":"Sawa Ser Gehun","path":"hindi-stories/storyBook/premchandra/mansarovar-4/SawaSerGehun.txt","blob":"4dff6ce6342a69cd3f2a70f4c8cda51e45bda067"},
    {"id":"prerna","title":"Prerna","path":"hindi-stories/storyBook/premchandra/mansarovar-4/Prerna.txt","blob":"2bee130bb7684064bea03b2dca59def21b0e5d53"},
    {"id":"sujan-bhagat","title":"Sujan Bhagat","path":"hindi-stories/storyBook/premchandra/mansarovar-5/SujanBhagat.txt","blob":"d4814f363ae843ed956e2b73dc45e94a32c55585"},
    {"id":"atmaram","title":"Atmaram","path":"hindi-stories/storyBook/premchandra/mansarovar-7/AatmaRam.txt","blob":"8cbe800664807e38f69c4f0d29409260a4ffca86"},
    {"id":"bade-ghar-ki-beti","title":"Bade Ghar Ki Beti","path":"hindi-stories/storyBook/premchandra/mansarovar-7/BareyGharKiBeti.txt","blob":"8504a2d2999f75aecf161447937c4dff43901b62"},
    {"id":"panch-parmeshwar","title":"Panch Parmeshwar","path":"hindi-stories/storyBook/premchandra/mansarovar-7/PanchParmeshwar.txt","blob":"91194ce1c56d0f95b1bda68454991e784ee28f93"},
    {"id":"juloos","title":"Juloos","path":"hindi-stories/storyBook/premchandra/mansarovar-7/Juloos.txt","blob":"23922a75160e2d3d922300ec9635a24bfd17a10a"},
    {"id":"namak-ka-daroga","title":"Namak Ka Daroga","path":"hindi-stories/storyBook/premchandra/mansarovar-8/NamakKaDaroga.txt","blob":"dba4a3ad99912ab2bea792129ad203cb62a72ec9"},
    {"id":"budhi-kaki","title":"Budhi Kaki","path":"hindi-stories/storyBook/premchandra/mansarovar-8/BudhiKaki.txt","blob":"09d951cc6f646a99e23824b8aa05bfec73d56f14"},
    {"id":"balidan","title":"Balidan","path":"hindi-stories/storyBook/premchandra/mansarovar-8/Balidan.txt","blob":"3f7a950eab0ffceefe82290f351a42e904ed3f19"},
    {"id":"beti-ka-dhan","title":"Beti Ka Dhan","path":"hindi-stories/storyBook/premchandra/mansarovar-8/BetiKaDhan.txt","blob":"ff81ae8c35abec5c53ff0572055b2af07245f493"},
    {"id":"ishwariya-nyay","title":"Ishwariya Nyay","path":"hindi-stories/storyBook/premchandra/mansarovar-5/IshwariyaNyaya.txt","blob":"a639191b1c09d60f0f143a6755ed5fb1052fd582"},
    {"id":"ramleela","title":"Ramleela","path":"hindi-stories/storyBook/premchandra/mansarovar-5/Ramleela.txt","blob":"814a5a0071065090fabadc4668f581d3a09d96f7"},
]

EASY_HINDI = {
    "किन्तु":"लेकिन", "किंतु":"लेकिन", "परन्तु":"लेकिन", "परंतु":"लेकिन",
    "तथापि":"फिर भी", "अतः":"इसलिए", "अतएव":"इसलिए", "प्रातःकाल":"सुबह",
    "प्रातः":"सुबह", "सायंकाल":"शाम", "सन्ध्या":"शाम", "संध्या":"शाम",
    "भोजन":"खाना", "जलपान":"कुछ खाना", "निवास":"घर", "गृह":"घर",
    "गृहस्थी":"घर-परिवार", "मुखमण्डल":"चेहरा", "मुखमंडल":"चेहरा",
    "मुख":"मुँह", "नेत्र":"आँख", "नयन":"आँख", "दृष्टि":"नज़र",
    "हृदय":"दिल", "अन्तःकरण":"मन", "अंतःकरण":"मन", "मस्तिष्क":"दिमाग",
    "क्रोध":"गुस्सा", "कुपित":"गुस्से में", "प्रसन्न":"खुश",
    "आनन्द":"खुशी", "आनंद":"खुशी", "विषाद":"उदासी", "वेदना":"दर्द",
    "पीड़ा":"दर्द", "सहायता":"मदद", "आवश्यक":"ज़रूरी", "व्यवस्था":"इंतज़ाम",
    "प्रबन्ध":"इंतज़ाम", "प्रबंध":"इंतज़ाम", "उद्देश्य":"मकसद",
    "प्रयोजन":"काम", "विचार":"सोच", "चिन्ता":"फिक्र", "चिंता":"फिक्र",
    "अभिलाषा":"चाह", "कामना":"चाह", "व्यर्थ":"बेकार", "निरर्थक":"बेकार",
    "प्रतीत":"लगा", "विदित":"पता", "ज्ञात":"पता", "अज्ञात":"अनजान",
    "शीघ्र":"जल्दी", "तुरन्त":"तुरंत", "तत्काल":"तुरंत", "उत्तर":"जवाब",
    "प्रश्न":"सवाल", "सम्भव":"मुमकिन", "संभव":"मुमकिन",
    "असम्भव":"नामुमकिन", "असंभव":"नामुमकिन", "निश्चय":"फैसला",
    "निर्णय":"फैसला", "आरम्भ":"शुरू", "आरंभ":"शुरू", "समाप्त":"खत्म",
    "समीप":"पास", "निकट":"पास", "भय":"डर", "भीति":"डर",
    "आश्चर्य":"हैरानी", "विस्मय":"हैरानी", "इत्यादि":"वगैरह",
    "पुनः":"फिर", "कदापि":"कभी नहीं", "अत्यन्त":"बहुत", "अत्यंत":"बहुत",
    "अल्प":"कम", "अधिक":"ज़्यादा", "निरन्तर":"लगातार", "निरंतर":"लगातार",
    "सदैव":"हमेशा", "सर्वदा":"हमेशा", "कदाचित":"शायद", "स्त्री":"औरत",
    "पुरुष":"आदमी", "बालक":"लड़का", "बालिका":"लड़की", "शिशु":"बच्चा",
    "सन्तान":"बच्चा", "संतान":"बच्चा", "पुत्र":"बेटा", "पुत्री":"बेटी",
    "माता":"माँ", "भ्राता":"भाई", "दुर्भाग्य":"बदकिस्मती",
    "सौभाग्य":"अच्छी किस्मत", "कारण":"वजह", "परिणाम":"नतीजा",
    "समाचार":"खबर", "सूचना":"खबर", "अनुमति":"इजाज़त", "निवेदन":"बिनती",
    "अनुरोध":"बिनती", "आज्ञा":"हुक्म", "निर्देश":"हुक्म", "अवकाश":"फुर्सत",
    "प्रयत्न":"कोशिश", "प्रयास":"कोशिश", "सफल":"कामयाब", "असफल":"नाकाम",
    "लज्जा":"शर्म", "ग्लानि":"पछतावा", "स्वर":"आवाज़", "कण्ठ":"गला",
    "कंठ":"गला", "मौन":"चुप", "निःशब्द":"चुप", "वार्तालाप":"बातचीत",
    "संवाद":"बातचीत", "मार्ग":"रास्ता", "पथ":"रास्ता", "प्रस्थान":"रवाना होना",
    "आगमन":"आना", "वस्त्र":"कपड़े", "आभूषण":"गहने", "औषधि":"दवा",
    "चिकित्सक":"डॉक्टर", "विद्यालय":"स्कूल", "अध्यापक":"टीचर",
    "कार्यालय":"दफ्तर", "न्यायालय":"अदालत", "धन":"पैसा", "राशि":"पैसा",
    "निर्धन":"गरीब", "समृद्ध":"अमीर", "कठिन":"मुश्किल", "सरल":"आसान",
    "उचित":"ठीक", "अनुचित":"गलत", "विशेष":"खास", "साधारण":"आम",
    "प्रकार":"तरह", "भाँति":"तरह", "भांति":"तरह", "क्षण":"पल",
    "क्षणभर":"एक पल", "पूर्व":"पहले", "पश्चात्":"बाद", "पश्चात":"बाद",
    "अनन्तर":"बाद", "अबोध":"नासमझ", "बुद्धि":"समझ", "चतुर":"होशियार",
    "मूर्ख":"बेवकूफ", "सन्देह":"शक", "संदेह":"शक", "विश्वास":"यकीन",
    "आशा":"उम्मीद", "निराशा":"मायूसी", "सम्मान":"इज़्ज़त", "अपमान":"बेइज़्ज़ती",
    "कष्ट":"तकलीफ", "यातना":"तकलीफ", "प्रेम":"प्यार", "स्नेह":"प्यार",
    "घृणा":"नफरत", "द्वेष":"नफरत", "लाभ":"फायदा", "हानि":"नुकसान",
    "सम्पूर्ण":"पूरा", "संपूर्ण":"पूरा", "प्रत्येक":"हर", "समस्त":"सब",
    "किसी प्रकार":"किसी तरह", "इस प्रकार":"इस तरह", "उस प्रकार":"उस तरह",
    "वर्तमान":"अभी", "भविष्य":"आने वाला समय", "अतीत":"बीता समय",
}

DIRECT_REPAIRS = {
    "haiM":"hain", "maiM":"main", "meM":"mein", "nahIM":"nahin",
    "hUM":"hoon", "kyoM":"kyon", "kahA.N":"kahan", "yahA.N":"yahan",
    "vahA.N":"wahan", "hA.N":"haan", "aura":"aur", "lekina":"lekin",
    "agara":"agar", "isa":"is", "usa":"us", "eka":"ek", "kucha":"kuchh",
    "saba":"sab", "ghara":"ghar", "dila":"dil", "baata":"baat",
    "haatha":"haath", "aankha":"aankh", "kara":"kar", "para":"par",
    "jaba":"jab", "taba":"tab", "aba":"ab", "kaba":"kab",
}

PHRASE_REPAIRS = [
    (r"\bmujhase\b", "mujhse"), (r"\btumase\b", "tumse"),
    (r"\bhamase\b", "hamse"), (r"\busase\b", "usse"),
    (r"\bjisase\b", "jisse"), (r"\binase\b", "inse"),
    (r"\bunase\b", "unse"), (r"\bapane\b", "apne"),
    (r"\bkarane\b", "karne"), (r"\bkaranaa\b", "karna"),
    (r"\bkahane\b", "kehne"), (r"\bkahataa\b", "kehta"),
    (r"\bkahatee\b", "kehti"), (r"\bkahate\b", "kehte"),
    (r"\brahane\b", "rehne"), (r"\bchalane\b", "chalne"),
    (r"\bsamajhane\b", "samajhne"), (r"\bbachapana\b", "bachpan"),
    (r"\bkarataa\b", "karta"), (r"\bkaratee\b", "karti"),
    (r"\bkarate\b", "karte"), (r"\bjaanaa\b", "jana"),
    (r"\bjaataa\b", "jata"), (r"\bjaatee\b", "jati"),
    (r"\baanaa\b", "aana"), (r"\baataa\b", "aata"),
    (r"\bhotaa\b", "hota"), (r"\bhotee\b", "hoti"),
    (r"\bdekhaa\b", "dekha"), (r"\bbolaa\b", "bola"),
    (r"\bbolatee\b", "bolti"), (r"\bbolate\b", "bolte"),
    (r"\brahaa\b", "raha"), (r"\brahee\b", "rahi"),
    (r"\bthaa\b", "tha"), (r"\bthee\b", "thi"),
    (r"\bkiyaa\b", "kiya"), (r"\bdiyaa\b", "diya"),
    (r"\bliyaa\b", "liya"), (r"\bgayaa\b", "gaya"),
    (r"\baayaa\b", "aaya"), (r"\bhuaa\b", "hua"),
    (r"\bba\.Daa\b", "bada"), (r"\bla\.Dak", "ladak"),
    (r"\bpa\.D", "pad"), (r"\bsaahaba\b", "sahab"),
    (r"\bbhaaee\b", "bhai"), (r"\bvidyaa\b", "padhai"),
]

FINAL_A_EXCEPTIONS = {
    "kya", "tha", "hua", "gaya", "diya", "liya", "kiya", "raha", "naya",
    "bada", "chhota", "beta", "pita", "mata", "dada", "bhaiya", "duniya",
    "katha", "pooja", "hawa", "dua", "jagah", "wajah", "saza", "maza",
}


def fetch_text(url: str) -> str:
    last: Exception | None = None
    for attempt in range(5):
        try:
            response = SESSION.get(url, timeout=90)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or "utf-8"
            return response.text
        except Exception as exc:  # pragma: no cover - network retry
            last = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"could not fetch {url}: {last}")


def replace_words(text: str, mapping: dict[str, str]) -> str:
    for old in sorted(mapping, key=len, reverse=True):
        text = re.sub(
            rf"(?<![\w\u0900-\u097f]){re.escape(old)}(?![\w\u0900-\u097f])",
            mapping[old],
            text,
        )
    return text


def clean_source(raw: str) -> str:
    raw = html.unescape(unicodedata.normalize("NFKC", raw))
    raw = raw.replace("\ufeff", "").replace("\u200b", "").replace("\xa0", " ")
    raw = raw.translate(str.maketrans("०१२३४५६७८९", "0123456789"))
    raw = re.sub(r"[ \t]+", " ", raw)
    raw = re.sub(r" *\n *", "\n", raw)
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    return raw.strip()


def remove_final_schwa(match: re.Match[str]) -> str:
    word = match.group(0)
    lower = word.lower()
    if lower in FINAL_A_EXCEPTIONS or len(word) <= 3 or word.endswith("aa"):
        return word
    return word[:-1]


def romanize(text: str) -> str:
    text = replace_words(text, EASY_HINDI)
    out = transliterate(text, sanscript.DEVANAGARI, sanscript.ITRANS)

    for old, new in DIRECT_REPAIRS.items():
        out = re.sub(rf"\b{re.escape(old)}\b", new, out)

    ordered = [
        (".Dh", "dh"), (".Th", "th"), (".D", "d"), (".T", "t"),
        ("RRi", "ri"), ("RRI", "ree"), ("LLi", "li"),
        ("~N", "n"), ("~n", "n"), (".N", "n"), (".n", "n"),
        ("Ch", "chh"), ("Th", "th"), ("Dh", "dh"),
        ("Sh", "sh"), ("shh", "sh"), ("j~n", "gy"),
        ("A", "aa"), ("I", "ee"), ("U", "oo"),
        ("T", "t"), ("D", "d"), ("N", "n"), ("S", "sh"),
        ("M", "n"), ("H", "h"), (".a", ""), ("~", ""),
    ]
    for old, new in ordered:
        out = out.replace(old, new)

    for pattern, replacement in PHRASE_REPAIRS:
        out = re.sub(pattern, replacement, out, flags=re.IGNORECASE)

    # Remove the normally silent inherent final schwa, while protecting common a-ending words.
    out = re.sub(r"\b[A-Za-z][A-Za-z.]*a\b", remove_final_schwa, out)
    out = out.replace("q", "k")
    out = re.sub(r"\.{2,}", "...", out)
    out = re.sub(r"[ \t]+", " ", out)
    out = re.sub(r" *\n *", "\n", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ROOT.mkdir(parents=True, exist_ok=True)
    qa: list[dict[str, object]] = []
    catalog = [
        "# Premchand Reader Collection — Batch 2",
        "",
        "Twenty complete machine-assisted Roman-Hindustani first passes.",
        "Every work remains human-review pending.",
        "",
    ]

    for index, work in enumerate(WORKS, 1):
        source_url = f"{RAW_ROOT}/{work['path']}"
        print(f"[{index:02d}/20] {work['title']}", flush=True)
        raw = clean_source(fetch_text(source_url))
        if len(raw) < 5000:
            raise RuntimeError(f"source unexpectedly short for {work['title']}: {len(raw)}")

        reader = romanize(raw)
        if re.search(r"[\u0900-\u097f\u0600-\u06ff]", reader):
            raise RuntimeError(f"non-Roman script remains in {work['title']}")
        if len(reader) < len(raw) * 0.25:
            raise RuntimeError(f"reader coverage unexpectedly low for {work['title']}")

        folder = ROOT / str(work["id"])
        translation = f"# {work['title']}\n\n**Munshi Premchand**\n\n{reader}\n"
        source_record = f"""# Locked Source Record — {work['title']}

- Author: Munshi Premchand
- Form: short story
- Base language: Hindi in Devanagari
- Source repository: `{SOURCE_REPO}`
- Immutable source commit: `{SOURCE_COMMIT}`
- Source path: `{work['path']}`
- Source blob SHA: `{work['blob']}`
- Raw source: {source_url}

No modern translation is copied. The reader text is a new machine-assisted accessibility first pass.
"""
        notes = f"""# Editorial Notes — {work['title']}

- Complete source characters processed: {len(raw)}
- Roman reader characters saved: {len(reader)}
- Source order and paragraph sequence retained.
- Controlled easy-language substitutions applied before script conversion.
- Roman-only check: passed.
- Translation status: `machine_assisted_complete_first_pass`
- Human source comparison: pending.
- Read-aloud and natural-language editing: pending.
- Publication status: not approved.
"""
        write(folder / "translation.md", translation)
        write(folder / "source.md", source_record)
        write(folder / "NOTES.md", notes)
        catalog.append(f"{index}. [{work['title']}](works/premchand/{work['id']}/translation.md)")
        qa.append({
            "id": work["id"],
            "title": work["title"],
            "source_path": work["path"],
            "source_blob": work["blob"],
            "source_characters": len(raw),
            "reader_characters": len(reader),
            "roman_only": True,
            "complete_first_pass": True,
            "human_review": "pending",
        })

    write(Path("generated/PREMCHAND_BATCH_2.md"), "\n".join(catalog))
    write(Path("generated/premchand-batch2-qa.json"), json.dumps({
        "batch": 2,
        "author": "Munshi Premchand",
        "works": qa,
        "count": len(qa),
        "status": "machine_assisted_complete_first_pass",
        "human_review": "pending",
    }, ensure_ascii=False, indent=2))

    if len(qa) != 20:
        raise RuntimeError(f"expected 20 works, built {len(qa)}")
    print("Built and checked 20 complete Premchand reader first passes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
