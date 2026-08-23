#!/usr/bin/env python3
"""Build complete Roman first-pass artifacts for Nirmala, Godaan, Urdu-e-Mualla."""
from __future__ import annotations

import html
import json
import re
import time
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

OUT = Path("generated")
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "SWR-public-domain-accessibility-builder/3.0 "
                  "(https://github.com/SyllabuswithRohit)"
})
DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
URDU_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
INDIC_RE = re.compile(r"[\u0900-\u097f\u0600-\u06ff]")

HINDI_EASY = {
    "किन्तु":"लेकिन","किंतु":"लेकिन","परन्तु":"लेकिन","परंतु":"लेकिन","तथापि":"फिर भी",
    "अतः":"इसलिए","अतएव":"इसलिए","प्रातःकाल":"सुबह","प्रातः":"सुबह",
    "सायंकाल":"शाम","सन्ध्या":"शाम","संध्या":"शाम","भोजन":"खाना",
    "जलपान":"कुछ खाना","निवास":"घर","गृहस्थी":"घर-परिवार","गृह":"घर",
    "मुखमण्डल":"चेहरा","मुखमंडल":"चेहरा","मुख":"मुँह","नेत्र":"आँख","नयन":"आँख",
    "दृष्टि":"नज़र","हृदय":"दिल","अन्तःकरण":"मन","अंतःकरण":"मन",
    "मस्तिष्क":"दिमाग","क्रोध":"गुस्सा","कुपित":"गुस्से में","प्रसन्न":"खुश",
    "आनन्द":"खुशी","आनंद":"खुशी","विषाद":"उदासी","सन्ताप":"दुख","संताप":"दुख",
    "वेदना":"दर्द","पीड़ा":"दर्द","सहायता":"मदद","आवश्यक":"ज़रूरी",
    "व्यवस्था":"इंतज़ाम","प्रबन्ध":"इंतज़ाम","प्रबंध":"इंतज़ाम",
    "उद्देश्य":"मकसद","प्रयोजन":"काम","विचार":"सोच","चिन्तन":"सोच",
    "चिंतन":"सोच","अभिलाषा":"चाह","कामना":"चाह","व्यर्थ":"बेकार",
    "निरर्थक":"बेकार","प्रतीत":"लगा","विदित":"पता","ज्ञात":"पता",
    "अज्ञात":"अनजान","शीघ्र":"जल्दी","तुरन्त":"तुरंत","तत्काल":"तुरंत",
    "उत्तर":"जवाब","प्रश्न":"सवाल","सम्भव":"मुमकिन","संभव":"मुमकिन",
    "असम्भव":"नामुमकिन","असंभव":"नामुमकिन","निश्चय":"फैसला","निर्णय":"फैसला",
    "आरम्भ":"शुरू","आरंभ":"शुरू","समाप्त":"खत्म","समीप":"पास","निकट":"पास",
    "भय":"डर","भीति":"डर","आश्चर्य":"हैरानी","विस्मय":"हैरानी",
    "इत्यादि":"वगैरह","पुनः":"फिर","कदापि":"कभी नहीं","अत्यन्त":"बहुत",
    "अत्यंत":"बहुत","विशाल":"बहुत बड़ा","अल्प":"कम","अधिक":"ज़्यादा",
    "निरन्तर":"लगातार","निरंतर":"लगातार","सदैव":"हमेशा","सर्वदा":"हमेशा",
    "कदाचित":"शायद","स्त्री":"औरत","पुरुष":"आदमी","बालक":"लड़का",
    "बालिका":"लड़की","शिशु":"बच्चा","सन्तान":"बच्चा","संतान":"बच्चा",
    "पुत्र":"बेटा","पुत्री":"बेटी","माता":"माँ","भ्राता":"भाई",
    "दुर्भाग्य":"बदकिस्मती","सौभाग्य":"अच्छी किस्मत","कारण":"वजह",
    "परिणाम":"नतीजा","समाचार":"खबर","सूचना":"खबर","अनुमति":"इजाज़त",
    "निवेदन":"बिनती","अनुरोध":"बिनती","आज्ञा":"हुक्म","निर्देश":"हुक्म",
    "अवकाश":"फुर्सत","प्रयत्न":"कोशिश","प्रयास":"कोशिश","सफल":"कामयाब",
    "असफल":"नाकाम","लज्जा":"शर्म","ग्लानि":"पछतावा","स्वर":"आवाज़",
    "कण्ठ":"गला","कंठ":"गला","मौन":"चुप","निःशब्द":"चुप",
    "वार्तालाप":"बातचीत","संवाद":"बातचीत","मार्ग":"रास्ता","पथ":"रास्ता",
    "प्रस्थान":"रवाना होना","आगमन":"आना","वस्त्र":"कपड़े","आभूषण":"गहने",
    "औषधि":"दवा","चिकित्सक":"डॉक्टर","विद्यालय":"स्कूल","अध्यापक":"टीचर",
    "कार्यालय":"दफ्तर","न्यायालय":"अदालत","धन":"पैसा","राशि":"पैसा",
    "निर्धन":"गरीब","समृद्ध":"अमीर","कठिन":"मुश्किल","सरल":"आसान",
    "उचित":"ठीक","अनुचित":"गलत","विशेष":"खास","साधारण":"आम",
    "प्रकार":"तरह","भाँति":"तरह","भांति":"तरह","क्षण":"पल",
    "क्षणभर":"एक पल","दीर्घ":"लंबा","पूर्व":"पहले","पश्चात्":"बाद",
    "पश्चात":"बाद","अनन्तर":"बाद","अबोध":"नासमझ","बुद्धि":"अकल",
    "चतुर":"होशियार","मूर्ख":"बेवकूफ","सन्देह":"शक","संदेह":"शक",
    "विश्वास":"यकीन","आशा":"उम्मीद","निराशा":"मायूसी",
    "सम्मान":"इज़्ज़त","अपमान":"बेइज़्ज़ती","कष्ट":"तकलीफ",
    "यातना":"तकलीफ","प्रेम":"प्यार","स्नेह":"प्यार","घृणा":"नफरत",
    "द्वेष":"नफरत","लाभ":"फायदा","हानि":"नुकसान","सम्पूर्ण":"पूरा",
    "संपूर्ण":"पूरा","प्रत्येक":"हर","समस्त":"सब",
}

URDU_MAP = {
    "ا":"a","آ":"aa","أ":"a","إ":"i","ٱ":"a","ء":"",
    "ب":"b","پ":"p","ت":"t","ٹ":"t","ث":"s","ج":"j","چ":"ch",
    "ح":"h","خ":"kh","د":"d","ڈ":"d","ذ":"z","ر":"r","ڑ":"r",
    "ز":"z","ژ":"zh","س":"s","ش":"sh","ص":"s","ض":"z","ط":"t",
    "ظ":"z","ع":"","غ":"gh","ف":"f","ق":"q","ک":"k","ك":"k",
    "گ":"g","ل":"l","م":"m","ن":"n","ں":"n","و":"o","ؤ":"o",
    "ہ":"h","ه":"h","ھ":"h","ی":"y","ي":"y","ے":"e","ئ":"y",
    "ۃ":"h","ۂ":"e","ۓ":"e","َ":"a","ِ":"i","ُ":"u","ّ":"",
    "ْ":"","ٰ":"a","ٔ":"","ٖ":"i","ٗ":"u","ـ":"",
}
URDU_WORDS = {
    "myn":"main","mh":"main","my":"mein","mn":"mein","hy":"hai","hyn":"hain",
    "nhyn":"nahin","nhi":"nahin","yh":"yeh","wh":"woh","ky":"ke","sy":"se",
    "ny":"ne","or":"aur","kr":"kar","kry":"kare","krta":"karta",
    "krty":"karte","krna":"karna","gya":"gaya","gyi":"gayi","gye":"gaye",
    "ap":"aap","apko":"aapko","apny":"apne","hm":"ham","tm":"tum",
    "mujhy":"mujhe","tujhy":"tujhe","bht":"bahut","khuda":"Khuda",
    "sahb":"sahab","lkha":"likha","lkh":"likh","khbr":"khabar",
    "dnya":"duniya","zndgi":"zindagi","muhbt":"mohabbat","dya":"diya",
}

def request(method: str, url: str, **kwargs: Any) -> requests.Response:
    last = None
    for attempt in range(12):
        if attempt:
            time.sleep(min(60, 2 + attempt * 3))
        r = SESSION.request(method, url, timeout=120, **kwargs)
        last = r
        if r.status_code in {429, 500, 502, 503, 504}:
            retry = r.headers.get("Retry-After", "")
            if retry.isdigit():
                time.sleep(min(90, int(retry)))
            continue
        r.raise_for_status()
        return r
    assert last is not None
    last.raise_for_status()
    raise RuntimeError(f"request retries exhausted: {url}")

def get_json(url: str, **params: Any) -> dict[str, Any]:
    return request("GET", url, params=params).json()

def post_json(url: str, **data: Any) -> dict[str, Any]:
    return request("POST", url, data=data).json()

def get_text(url: str, minimum: int = 1000) -> str:
    text = request("GET", url).text
    if len(text) < minimum:
        raise RuntimeError(f"source too short ({len(text)}): {url}")
    return text

def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")

def clean_space(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+$", "", text, flags=re.M)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()

def replace_words(text: str, mapping: dict[str, str]) -> str:
    for old in sorted(mapping, key=len, reverse=True):
        text = re.sub(rf"(?<![\w\u0900-\u097f]){re.escape(old)}(?![\w\u0900-\u097f])", mapping[old], text)
    return text

def roman_hi(text: str) -> str:
    text = (unicodedata.normalize("NFKC", text).translate(DEV_DIGITS)
            .replace("�", "").replace("ऑ", "ओ").replace("ॉ", "ो")
            .replace("ऍ", "ए").replace("ॅ", "े").replace("़", ""))
    text = replace_words(text, HINDI_EASY)
    out = transliterate(text, sanscript.DEVANAGARI, sanscript.ITRANS)
    for a, b in [("RRi","ri"),("RRI","ree"),("LLi","li"),("Ch","chh"),
                 ("Th","th"),("Dh","dh"),("T","t"),("D","d"),("~N","n"),
                 ("~n","n"),("Sh","sh"),("S","sh"),("j~n","gy"),("GY","gy"),
                 ("A","aa"),("I","ee"),("U","oo"),("M","n"),("H","h"),
                 (".a",""),(".n","n"),("~","")]:
        out = out.replace(a, b)
    repairs = {"hai.n":"hain","haiM":"hain","huuM":"hoon","hUM":"hoon",
               "nahIM":"nahin","nahiiM":"nahin","meM":"mein","maiM":"main",
               "kyoM":"kyon","kyo.n":"kyon","yah":"yeh","vah":"woh",
               "unheM":"unhein","tumheM":"tumhein","aura":"aur","phira":"phir",
               "lekina":"lekin","agara":"agar","isa":"is","usa":"us","eka":"ek",
               "kucha":"kuchh","saba":"sab","ghara":"ghar","dila":"dil",
               "dina":"din","raata":"raat","loga":"log","baata":"baat",
               "haatha":"haath","paira":"pair","aankha":"aankh","kara":"kar"}
    for old, new in repairs.items():
        out = re.sub(rf"\b{re.escape(old)}\b", new, out, flags=re.I)
    for pat, repl in [(r"\bkaranaa\b","karna"),(r"\bkarataa\b","karta"),
                      (r"\bkaratee\b","karti"),(r"\bkarate\b","karte"),
                      (r"\bkahataa\b","kehta"),(r"\bkahatee\b","kehti"),
                      (r"\bkahate\b","kehte"),(r"\bjaanaa\b","jana"),
                      (r"\bjaataa\b","jata"),(r"\bjaatee\b","jati"),
                      (r"\baanaa\b","aana"),(r"\baataa\b","aata"),
                      (r"\bhotaa\b","hota"),(r"\bhotee\b","hoti"),
                      (r"\bdekhaa\b","dekha"),(r"\bbolaa\b","bola"),
                      (r"\brahaa\b","raha"),(r"\brahee\b","rahi"),
                      (r"\bthaa\b","tha"),(r"\bthee\b","thi"),
                      (r"\bkiyaa\b","kiya"),(r"\bdiyaa\b","diya"),
                      (r"\bliyaa\b","liya"),(r"\bgayaa\b","gaya"),
                      (r"\baayaa\b","aaya"),(r"\bhuaa\b","hua"),
                      (r"\bladaaee\b","ladai"),(r"\bpa\.Daa\b","pada"),
                      (r"\bba\.Daa\b","bada"),(r"\bla\.Dak","ladak")]:
        out = re.sub(pat, repl, out, flags=re.I)
    return clean_space(out)

def roman_ur(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).translate(URDU_DIGITS)
    chars = []
    for ch in text:
        if ch in URDU_MAP:
            chars.append(URDU_MAP[ch])
        elif "\u0600" <= ch <= "\u06ff":
            continue
        else:
            chars.append(ch)
    tokens = re.split(r"([^A-Za-z]+)", "".join(chars))
    out = "".join(URDU_WORDS.get(t.lower(), t) for t in tokens)
    out = re.sub(r"\s+([,.!?;:])", r"\1", out)
    return clean_space(out)

def assert_roman(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    m = INDIC_RE.search(text)
    if m:
        raise RuntimeError(f"Indic script remains in {path}: U+{ord(m.group()):04X}")
    if len(text.strip()) < 40:
        raise RuntimeError(f"reader file too short: {path}")

def natural_number(title: str) -> int:
    tail = title.rsplit("/", 1)[-1].translate(DEV_DIGITS)
    m = re.search(r"\d+", tail)
    return int(m.group()) if m else 9999

def fetch_nirmala() -> list[tuple[int, str, str]]:
    api = "https://hi.wikisource.org/w/api.php"
    titles = []
    cont = None
    while True:
        params: dict[str, Any] = {"action":"query","list":"allpages","apprefix":"निर्मला/",
                                  "apnamespace":0,"aplimit":"max","format":"json",
                                  "formatversion":2,"maxlag":5}
        if cont:
            params["apcontinue"] = cont
        data = get_json(api, **params)
        titles.extend(x["title"] for x in data["query"]["allpages"])
        if "continue" not in data:
            break
        cont = data["continue"]["apcontinue"]
    titles = sorted({t for t in titles if natural_number(t) != 9999}, key=natural_number)
    if len(titles) < 20:
        raise RuntimeError(f"expected >=20 Nirmala chapters, found {len(titles)}")
    extracts: dict[str, str] = {}
    for start in range(0, len(titles), 8):
        batch = titles[start:start+8]
        data = post_json(api, action="query", prop="extracts", explaintext=1,
                         exsectionformat="plain", redirects=1, titles="|".join(batch),
                         format="json", formatversion=2, maxlag=5)
        for page in data.get("query", {}).get("pages", []):
            if "missing" not in page:
                extracts[page["title"]] = page.get("extract", "")
        time.sleep(2.5)
    chapters = []
    for title in titles:
        raw = extracts.get(title, "")
        if len(raw) < 700:
            data = get_json(api, action="parse", page=title, prop="text", format="json",
                            formatversion=2, disableeditsection=1, maxlag=5)
            soup = BeautifulSoup(data["parse"]["text"], "html.parser")
            for tag in soup.select("script,style,table,.mw-editsection,.noprint,.ws-noexport,.references,sup.reference,.navbox,.licenseContainer,.ws-summary"):
                tag.decompose()
            for br in soup.find_all("br"):
                br.replace_with("\n")
            raw = html.unescape(soup.get_text("\n"))
            time.sleep(4)
        lines = []
        for line in raw.splitlines():
            s = line.strip()
            if not s:
                lines.append("")
            elif s not in {"डाउनलोड","विकिस्रोत से","स्रोत","संपादित करें"} and not s.startswith(("←","→","श्रेणी:","निर्मला.djvu")):
                lines.append(s)
        raw = clean_space("\n".join(lines))
        if len(raw) < 700:
            raise RuntimeError(f"Nirmala chapter too short: {title} ({len(raw)})")
        chapters.append((natural_number(title), title, raw))
    return chapters

def build_nirmala(qa: dict[str, Any]) -> None:
    root = OUT / "works/premchand/nirmala"
    chapters = fetch_nirmala()
    index = ["# Nirmala","","**Munshi Premchand**","","Complete machine-assisted easy Roman-Hindustani first pass.",""]
    sources, source_chars, output_chars = [], 0, 0
    for n, title, raw in chapters:
        source_chars += len(raw)
        path = root / "chapters" / f"{n:02d}.md"
        write(path, f"# Chapter {n}\n\n{roman_hi(raw)}")
        assert_roman(path)
        output_chars += len(path.read_text(encoding="utf-8"))
        index.append(f"- [Chapter {n}](chapters/{n:02d}.md)")
        sources.append(f"- Chapter {n}: https://hi.wikisource.org/wiki/{quote(title, safe='/')}")
    write(root/"translation.md", "\n".join(index)); assert_roman(root/"translation.md")
    write(root/"source.md", "# Locked Source Record — Nirmala\n\n- Author: Munshi Premchand\n- Work: complete novel\n- Source: Hindi Wikisource chapter transcriptions linked to an old scan\n" + f"- Chapters processed: {len(chapters)}\n- Source characters: {source_chars}\n- Independent scan comparison: pending\n\n## Chapter records\n\n" + "\n".join(sources) + "\n")
    write(root/"NOTES.md", "# Editorial Notes — Nirmala\n\n" + f"- Complete ordered chapters saved: {len(chapters)}\n- Source paragraphs retained in order.\n- Status: `machine_assisted_complete_first_pass`\n- Automated Roman-only and sequence validation: passed.\n- Independent paragraph comparison and read-aloud review: pending.\n")
    qa["nirmala"] = {"source_chars":source_chars,"output_chars":output_chars,"units":len(chapters),"status":"machine_assisted_complete_first_pass"}

def build_godaan(qa: dict[str, Any]) -> None:
    root = OUT / "works/premchand/godaan"
    base = "https://raw.githubusercontent.com/pandeyshikha1098/privacy_policy/45b42cf18333411f035757a9ecd8b6859fa84ae6/hindi-stories/storyBook/premchandra/godan"
    index = ["# Godaan","","**Munshi Premchand**","","Complete machine-assisted easy Roman-Hindustani first pass.",""]
    source_chars = output_chars = 0
    for n in range(1, 37):
        raw = get_text(f"{base}/{n:02d}.txt", 1000).replace("�","")
        source_chars += len(raw)
        path = root / "chapters" / f"{n:02d}.md"
        write(path, f"# Chapter {n}\n\n{roman_hi(raw)}")
        assert_roman(path)
        output_chars += len(path.read_text(encoding="utf-8"))
        index.append(f"- [Chapter {n}](chapters/{n:02d}.md)")
        time.sleep(.3)
    write(root/"translation.md", "\n".join(index)); assert_roman(root/"translation.md")
    write(root/"source.md", "# Locked Source Record — Godaan\n\n- Author: Munshi Premchand\n- Work: complete novel\n- Public source commit: `45b42cf18333411f035757a9ecd8b6859fa84ae6`\n" + f"- Source files processed: 01.txt through 36.txt\n- Source characters: {source_chars}\n- Independent scan comparison: pending\n")
    write(root/"NOTES.md", "# Editorial Notes — Godaan\n\n- Complete ordered chapters saved: 36\n- Every source file retained in order.\n- Status: `machine_assisted_complete_first_pass`\n- Automated Roman-only and chapter-count validation: passed.\n- Independent scan comparison and read-aloud review: pending.\n")
    qa["godaan"] = {"source_chars":source_chars,"output_chars":output_chars,"units":36,"status":"machine_assisted_complete_first_pass"}

def archive_ocr(identifier: str) -> tuple[str, str]:
    meta = get_json(f"https://archive.org/metadata/{identifier}")
    files = meta.get("files", [])
    candidates = [f for f in files if f.get("name","").endswith("_djvu.txt")]
    if not candidates:
        candidates = [f for f in files if f.get("name","").endswith(".txt") and "meta" not in f.get("name","").lower()]
    if not candidates:
        raise RuntimeError(f"no OCR text for {identifier}")
    best = max(candidates, key=lambda f:int(f.get("size",0) or 0))
    url = f"https://archive.org/download/{identifier}/{quote(best['name'])}"
    return get_text(url, 25000), url

def clean_urdu(raw: str) -> str:
    raw = unicodedata.normalize("NFKC", raw)
    lines = []
    for line in raw.splitlines():
        s = line.strip()
        if not s:
            lines.append("")
        elif not re.fullmatch(r"[0-9۰-۹\-–— ]{1,8}", s) and not any(x.lower() in s.lower() for x in ("Digitized by","Generated at","Internet Archive")):
            lines.append(s)
    raw = clean_space("\n".join(lines))
    positions = [raw.find(x) for x in ("بنام","بنامِ","میر مہدی","میاں") if raw.find(x)>=0]
    if positions:
        first = min(positions)
        if 500 < first < len(raw)//3:
            raw = raw[first:]
    return raw

def build_urdu(qa: dict[str, Any]) -> None:
    root = OUT / "works/ghalib/urdu-e-mualla"
    raw, url = archive_ocr("urduemualla")
    if len(raw) < 100000:
        raw, url = archive_ocr("in.ernet.dli.2015.435597")
    raw = clean_urdu(raw)
    paras = [p.strip() for p in re.split(r"\n\s*\n", raw) if p.strip()]
    if len(raw) < 80000 or len(paras) < 80:
        raise RuntimeError(f"Urdu OCR failed checks: {len(raw)} chars, {len(paras)} paragraphs")
    per = max(1, (len(paras)+23)//24)
    blocks = [paras[i:i+per] for i in range(0,len(paras),per)]
    index = ["# Urdu-e-Mualla","","**Mirza Ghalib**","","Complete old-OCR-based machine-assisted Roman first pass.",""]
    output_chars = 0
    for n, block in enumerate(blocks,1):
        path = root / "parts" / f"{n:02d}.md"
        write(path, f"# Part {n}\n\n{roman_ur(chr(10).join(block))}")
        assert_roman(path)
        output_chars += len(path.read_text(encoding="utf-8"))
        index.append(f"- [Part {n}](parts/{n:02d}.md)")
    write(root/"translation.md", "\n".join(index)); assert_roman(root/"translation.md")
    write(root/"source.md", "# Locked Source Record — Urdu-e-Mualla\n\n- Author: Mirza Asadullah Khan Ghalib\n- Work: collection of Urdu letters\n" + f"- Public-domain old-edition OCR: {url}\n- OCR characters retained: {len(raw)}\n- Ordered OCR paragraphs: {len(paras)}\n- Independent scan comparison: pending\n")
    write(root/"NOTES.md", "# Editorial Notes — Urdu-e-Mualla\n\n" + f"- Selected old-edition OCR retained in {len(blocks)} ordered parts.\n- Nastaliq OCR and automatic vowel recovery are imperfect.\n- Status: `ocr_machine_assisted_complete_first_pass`\n- Automated Roman-only and part-sequence validation: passed.\n- Line-by-line Urdu and scan-image review: pending.\n")
    qa["urdu-e-mualla"] = {"source_chars":len(raw),"output_chars":output_chars,"units":len(blocks),"ocr_paragraphs":len(paras),"status":"ocr_machine_assisted_complete_first_pass"}

def main() -> None:
    qa: dict[str, Any] = {}
    build_nirmala(qa)
    build_godaan(qa)
    build_urdu(qa)
    files = list(OUT.rglob("*.md"))
    for path in files:
        assert_roman(path)
    qa["validation"] = {"markdown_files":len(files),"residual_indic_chars":0,"godaan_chapters":len(list((OUT/"works/premchand/godaan/chapters").glob("*.md"))),"nirmala_chapters":len(list((OUT/"works/premchand/nirmala/chapters").glob("*.md"))),"urdu_parts":len(list((OUT/"works/ghalib/urdu-e-mualla/parts").glob("*.md")))}
    write(OUT/"QA.json", json.dumps(qa, ensure_ascii=False, indent=2))
    print(json.dumps(qa, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
