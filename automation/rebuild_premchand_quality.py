#!/usr/bin/env python3
"""Rebuild Nirmala and Godaan with language-aware Roman Hindi.

This pass preserves every source paragraph and applies only controlled vocabulary
simplification, stable names, script conversion, and spelling normalization.
"""
from __future__ import annotations

import re
import time
from pathlib import Path

import requests
from aksharamukha import transliterate
from bs4 import BeautifulSoup

import build_all_classics as b

S = requests.Session()
S.headers.update({"User-Agent": "SWR-Roman-Hindustani-editorial-builder/3.0"})
ROOT = Path("generated/works/premchand")

NAME_MAP = {
    "उदयभानुलाल": "Udaybhanulal", "उदयभानु लाल": "Udaybhanulal",
    "निर्मला": "Nirmala", "कृष्णा": "Krishna", "कल्याणी": "Kalyani",
    "भालचंद्र": "Bhalchandra", "भालचन्द्र": "Bhalchandra",
    "भुवनमोहन": "Bhuvanmohan", "तोताराम": "Totaram",
    "मंसाराम": "Mansaram", "मन्साराम": "Mansaram",
    "जियाराम": "Jiyaram", "सियाराम": "Siyaram", "रुक्मिणी": "Rukmini",
    "सुधा": "Sudha", "डॉक्टर सिन्हा": "Doctor Sinha", "सिन्हा": "Sinha",
    "होरीराम": "Hori", "होरी": "Hori", "धनिया": "Dhania",
    "गोबर": "Gobar", "झुनिया": "Jhunia", "भोला": "Bhola",
    "हीरा": "Heera", "सोना": "Sona", "रूपा": "Rupa",
    "रायसाहब": "Rai Sahib", "राय साहब": "Rai Sahib",
    "दातादीन": "Datadin", "मातादीन": "Matadin", "सिलिया": "Silia",
    "मेहता": "Mehta", "मालती": "Malati", "खन्ना": "Khanna",
    "गोविंदी": "Govindi", "ओंकारनाथ": "Onkarnath",
    "मिर्जा खुर्शेद": "Mirza Khurshed", "खुर्शेद": "Khurshed",
    "नोहरी": "Nohari", "पुनिया": "Punia", "सोभा": "Sobha",
    "रामसेवक": "Ramsevak", "दुलारी": "Dulari", "मंगरू": "Mangru",
    "पटेश्वरी": "Pateshwari", "झिंगुरी": "Jhinguri",
}

ROMAN_WORD_FIXES = {
    "mem": "mein", "nahim": "nahin", "naheen": "nahin", "yum": "yun",
    "kyom": "kyon", "kyonki": "kyunki", "kyonke": "kyunki",
    "accha": "achchha", "achha": "achchha", "chahie": "chahiye",
    "admi": "aadmi", "insan": "insaan", "zamin": "zameen",
    "jamin": "zameen", "pyar": "pyaar", "bhagwan": "Bhagwan",
    "muh": "munh", "munh": "munh", "vahan": "wahan", "yaha": "yahan",
    "bari": "badi", "bara": "bada", "bare": "bade", "baron": "badon",
    "larki": "ladki", "larkiyan": "ladkiyan", "larkiyon": "ladkiyon",
    "khari": "khadi", "khara": "khada", "khare": "khade",
    "pari": "padi", "para": "pada", "pare": "pade",
    "chara": "chadha", "charha": "chadha", "urna": "udna", "ur": "ud",
    "garbar": "gadbad", "pakar": "pakad", "chhor": "chhod",
    "tor": "tod", "jor": "jod", "darhi": "daadhi", "ghari": "ghadi",
    "kapra": "kapda", "kapre": "kapde", "thori": "thodi", "thora": "thoda",
    "pahunchi": "pahunchi", "prani": "insaan", "stri": "aurat",
    "purush": "aadmi", "kanya": "ladki", "putra": "beta", "putri": "beti",
    "grih": "ghar", "hriday": "dil", "netra": "aankh", "mukh": "munh",
    "sahayata": "madad", "avashyak": "zaroori", "vyavastha": "intezam",
    "prabandh": "intezam", "prasann": "khush", "krodh": "gussa",
    "shighra": "jaldi", "uttar": "jawab", "prashna": "sawal",
    "sambhav": "mumkin", "asambhav": "namumkin", "nirnay": "faisla",
    "arambh": "shuru", "samapt": "khatm", "nikat": "paas",
    "bhay": "dar", "ashcharya": "hairani", "punah": "phir",
    "atyant": "bahut", "nirantar": "lagatar", "sadaiv": "hamesha",
    "kadachit": "shayad", "nirdhan": "gareeb", "parishram": "mehnat",
    "chikitsak": "doctor", "vidyalaya": "school", "karyalaya": "daftar",
    "nyayalaya": "adalat", "adhikari": "afsar", "samachar": "khabar",
    "anumati": "ijazat", "anurodh": "binti", "nirdesh": "hukm",
    "prayas": "koshish", "saphal": "kaamyab", "asaphal": "naakam",
    "pratiksha": "intezar", "smaran": "yaad", "vivash": "majboor",
    "sankat": "museebat", "vastav": "sach", "keval": "sirf",
    "yadyapi": "halanki", "arthat": "yani", "paristhiti": "haal",
    "sahanubhuti": "hamdardi", "karuna": "daya", "sahas": "himmat",
    "dhairya": "sabr", "vyavahar": "bartav", "vastra": "kapde",
    "aushadhi": "dava", "vetan": "tankhwah", "rin": "karz",
    "mulya": "keemat", "vyay": "kharch", "sampatti": "jaidad",
    "bhumi": "zameen", "krishak": "kisan", "sevak": "naukar",
    "swami": "malik", "patra": "chitthi", "sandesh": "paigam",
    "praman": "saboot", "sakshi": "gawah", "vivad": "jhagda",
}


def get(url: str, **kwargs):
    last = None
    for attempt in range(8):
        try:
            r = S.get(url, timeout=120, **kwargs)
            if r.status_code == 429:
                time.sleep(int(r.headers.get("Retry-After", "10") or 10))
                continue
            r.raise_for_status()
            return r
        except Exception as exc:
            last = exc
            time.sleep(min(60, 3 * 2**attempt))
    raise RuntimeError(f"download failed: {url}: {last}")


def protect_names(text: str) -> str:
    for source, target in sorted(NAME_MAP.items(), key=lambda item: len(item[0]), reverse=True):
        text = text.replace(source, f" ZZNAME{target.replace(' ', 'QQ')}ZZ ")
    return text


def simplify_devanagari(text: str) -> str:
    text = protect_names(b.normalize_source(text))
    for hard, easy in sorted(b.HINDI_EASY.items(), key=lambda item: len(item[0]), reverse=True):
        text = re.sub(rf"(?<![\w\u0900-\u097f]){re.escape(hard)}(?![\w\u0900-\u097f])", easy, text)
    return text


def romanize(text: str) -> str:
    prepared = simplify_devanagari(text)
    output = transliterate.process(
        "Devanagari", "RomanColloquial", prepared,
        pre_options=["RemoveSchwaHindi"],
    )
    output = output.replace("ZZNAME", "").replace("QQ", " ").replace("ZZ", "")
    output = re.sub(r"\b([A-Za-z]+)om\b", r"\1on", output)
    output = re.sub(r"\b([A-Za-z]+)em\b", r"\1en", output)
    for old, new in ROMAN_WORD_FIXES.items():
        output = re.sub(rf"\b{re.escape(old)}\b", new, output, flags=re.I)
    output = re.sub(r"\s+([,.;:!?])", r"\1", output)
    output = re.sub(r"([,.;:!?])(?=[A-Za-z])", r"\1 ", output)
    output = re.sub(r"[ \t]+", " ", output)
    output = re.sub(r" *\n *", "\n", output)
    output = re.sub(r"\n{3,}", "\n\n", output)
    output = re.sub(r"[^\x00-\x7F]", "", output)
    return output.strip()


def clean_wiki(page_html: str, title: str) -> str:
    soup = BeautifulSoup(page_html, "html.parser")
    for tag in soup.select("table,style,script,nav,.mw-editsection,.noprint,.ws-noexport,.reference,.printfooter"):
        tag.decompose()
    lines = []
    for raw in b.normalize_source(soup.get_text("\n")).splitlines():
        line = raw.strip()
        if not line:
            if lines and lines[-1] != "":
                lines.append("")
        elif line not in {title, "निर्मला", "पिछला पृष्ठ", "अगला पृष्ठ", "विषयसूची"} and not re.fullmatch(r"[\d ]+", line.translate(b.DEV_DIGITS)):
            lines.append(line)
    return "\n".join(lines).strip()


def fetch_nirmala():
    api = "https://hi.wikisource.org/w/api.php"
    data = get(api, params={"action":"query","list":"categorymembers","cmtitle":"Category:निर्मला","cmnamespace":"0","cmlimit":"500","format":"json","formatversion":"2"}).json()
    titles = sorted({x["title"] for x in data["query"]["categorymembers"] if x["title"].startswith("निर्मला/")}, key=b.natural_number)
    if len(titles) != 24:
        raise RuntimeError(f"Nirmala chapter count {len(titles)}")
    result = []
    for index, title in enumerate(titles, 1):
        payload = get(api, params={"action":"parse","page":title,"prop":"text","format":"json","formatversion":"2","redirects":"1"}).json()
        text = clean_wiki(payload["parse"]["text"], title)
        if len(text) < 1500:
            raise RuntimeError(f"short Nirmala chapter {title}: {len(text)}")
        result.append((index, text))
        time.sleep(3)
    return result


def rebuild_nirmala():
    root = ROOT / "nirmala" / "chapters"
    chapters = fetch_nirmala()
    for n, source in chapters:
        b.write(root / f"{n:02d}.md", f"# Nirmala — Adhyay {n}\n\n**Munshi Premchand**\n\n{romanize(source)}")
    return len(chapters)


def rebuild_godaan():
    root = ROOT / "godaan" / "chapters"
    base = "https://raw.githubusercontent.com/pandeyshikha1098/privacy_policy/45b42cf18333411f035757a9ecd8b6859fa84ae6/hindi-stories/storyBook/premchandra/godan"
    for n in range(1, 37):
        source = b.normalize_source(get(f"{base}/{n:02d}.txt").text)
        if len(source) < 5000:
            raise RuntimeError(f"short Godaan chapter {n}: {len(source)}")
        b.write(root / f"{n:02d}.md", f"# Godaan — Adhyay {n}\n\n**Munshi Premchand**\n\n{romanize(source)}")
    return 36


def main():
    n = rebuild_nirmala()
    g = rebuild_godaan()
    samples = []
    for path in [ROOT/"nirmala"/"chapters"/"01.md", ROOT/"nirmala"/"chapters"/"12.md", ROOT/"nirmala"/"chapters"/"24.md", ROOT/"godaan"/"chapters"/"01.md", ROOT/"godaan"/"chapters"/"18.md", ROOT/"godaan"/"chapters"/"36.md"]:
        text = path.read_text(encoding="utf-8")
        residual = len(re.findall(r"[^\x00-\x7F]", text))
        samples.append(f"{path}: chars={len(text)} residual_non_ascii={residual}\n{text[:900]}\n")
        if residual:
            raise RuntimeError(f"non-ASCII content remains in {path}")
    log = Path("generated/logs/premchand-quality.txt")
    log.write_text(f"Nirmala chapters={n}\nGodaan chapters={g}\n\n" + "\n---\n".join(samples), encoding="utf-8")
    print(log.read_text(encoding="utf-8")[:5000])

if __name__ == "__main__":
    main()
