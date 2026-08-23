#!/usr/bin/env python3
"""One-shot public-domain accessibility builder.

Produces complete, ordered, Roman-only machine-assisted first passes for the
three long units and three remaining Manto stories. No output is marked reviewed.
"""
from __future__ import annotations

import html
import json
import re
import time
import unicodedata
from pathlib import Path
from typing import Iterable

import requests
from bs4 import BeautifulSoup
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

OUT = Path("generated")
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "SWR-public-domain-accessibility-builder/1.0"})
DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
URDU_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")

HINDI_EASY = {
    "किन्तु":"लेकिन","किंतु":"लेकिन","परन्तु":"लेकिन","परंतु":"लेकिन","तथापि":"फिर भी",
    "अतः":"इसलिए","अतएव":"इसलिए","प्रातःकाल":"सुबह","प्रातः":"सुबह","सायंकाल":"शाम",
    "सन्ध्या":"शाम","संध्या":"शाम","भोजन":"खाना","जलपान":"कुछ खाना","निवास":"घर",
    "गृह":"घर","गृहस्थी":"घर-परिवार","मुखमण्डल":"चेहरा","मुखमंडल":"चेहरा","मुख":"मुँह",
    "नेत्र":"आँख","नयन":"आँख","दृष्टि":"नज़र","हृदय":"दिल","अन्तःकरण":"मन",
    "अंतःकरण":"मन","मस्तिष्क":"दिमाग","क्रोध":"गुस्सा","कुपित":"गुस्से में",
    "प्रसन्न":"खुश","आनन्द":"खुशी","आनंद":"खुशी","विषाद":"उदासी","सन्ताप":"दुख",
    "संताप":"दुख","वेदना":"दर्द","पीड़ा":"दर्द","सहायता":"मदद","आवश्यक":"ज़रूरी",
    "व्यवस्था":"इंतज़ाम","प्रबन्ध":"इंतज़ाम","प्रबंध":"इंतज़ाम","उद्देश्य":"मकसद",
    "प्रयोजन":"काम","विचार":"सोच","चिन्तन":"सोच","चिंतन":"सोच","अभिलाषा":"चाह",
    "कामना":"चाह","व्यर्थ":"बेकार","निरर्थक":"बेकार","प्रतीत":"लगा","विदित":"पता",
    "ज्ञात":"पता","अज्ञात":"अनजान","शीघ्र":"जल्दी","तुरन्त":"तुरंत","तत्काल":"तुरंत",
    "उत्तर":"जवाब","प्रश्न":"सवाल","सम्भव":"मुमकिन","संभव":"मुमकिन",
    "असम्भव":"नामुमकिन","असंभव":"नामुमकिन","निश्चय":"फैसला","निर्णय":"फैसला",
    "आरम्भ":"शुरू","आरंभ":"शुरू","समाप्त":"खत्म","समीप":"पास","निकट":"पास",
    "भय":"डर","भीति":"डर","आश्चर्य":"हैरानी","विस्मय":"हैरानी","इत्यादि":"वगैरह",
    "पुनः":"फिर","कदापि":"कभी नहीं","अत्यन्त":"बहुत","अत्यंत":"बहुत","विशाल":"बहुत बड़ा",
    "अल्प":"कम","अधिक":"ज़्यादा","निरन्तर":"लगातार","निरंतर":"लगातार","सदैव":"हमेशा",
    "सर्वदा":"हमेशा","कदाचित":"शायद","स्त्री":"औरत","पुरुष":"आदमी","बालक":"लड़का",
    "बालिका":"लड़की","शिशु":"बच्चा","सन्तान":"बच्चा","संतान":"बच्चा","पुत्र":"बेटा",
    "पुत्री":"बेटी","माता":"माँ","भ्राता":"भाई","दुर्भाग्य":"बदकिस्मती",
    "सौभाग्य":"अच्छी किस्मत","कारण":"वजह","परिणाम":"नतीजा","समाचार":"खबर",
    "सूचना":"खबर","अनुमति":"इजाज़त","निवेदन":"बिनती","अनुरोध":"बिनती","आज्ञा":"हुक्म",
    "निर्देश":"हुक्म","अवकाश":"फुर्सत","प्रयत्न":"कोशिश","प्रयास":"कोशिश",
    "सफल":"कामयाब","असफल":"नाकाम","लज्जा":"शर्म","ग्लानि":"पछतावा","स्वर":"आवाज़",
    "कण्ठ":"गला","कंठ":"गला","मौन":"चुप","निःशब्द":"चुप","वार्तालाप":"बातचीत",
    "संवाद":"बातचीत","मार्ग":"रास्ता","पथ":"रास्ता","प्रस्थान":"रवाना होना",
    "आगमन":"आना","वस्त्र":"कपड़े","आभूषण":"गहने","औषधि":"दवा","चिकित्सक":"डॉक्टर",
    "विद्यालय":"स्कूल","अध्यापक":"टीचर","कार्यालय":"दफ्तर","न्यायालय":"अदालत",
    "धन":"पैसा","राशि":"पैसा","निर्धन":"गरीब","समृद्ध":"अमीर","कठिन":"मुश्किल",
    "सरल":"आसान","उचित":"ठीक","अनुचित":"गलत","विशेष":"खास","साधारण":"आम",
    "प्रकार":"तरह","भाँति":"तरह","भांति":"तरह","क्षण":"पल","क्षणभर":"एक पल",
    "दीर्घ":"लंबा","पूर्व":"पहले","पश्चात्":"बाद","पश्चात":"बाद","अनन्तर":"बाद",
    "अबोध":"नासमझ","बुद्धि":"अकल","चतुर":"होशियार","मूर्ख":"बेवकूफ","सन्देह":"शक",
    "संदेह":"शक","विश्वास":"यकीन","आशा":"उम्मीद","निराशा":"मायूसी",
    "सम्मान":"इज़्ज़त","अपमान":"बेइज़्ज़ती","कष्ट":"तकलीफ","यातना":"तकलीफ",
    "प्रेम":"प्यार","स्नेह":"प्यार","घृणा":"नफरत","द्वेष":"नफरत","लाभ":"फायदा",
    "हानि":"नुकसान","सम्पूर्ण":"पूरा","संपूर्ण":"पूरा","प्रत्येक":"हर","समस्त":"सब",
    "किसी प्रकार":"किसी तरह","इस प्रकार":"इस तरह","उस प्रकार":"उस तरह",
}

MANTO_EASY = {
    "हुकूमतों":"सरकारों","हुकूमत":"सरकार","तबादला":"अदला-बदली","तबादले":"अदला-बदली",
    "दानिशमंदों":"समझदार लोगों","बिलआख़िर":"आखिर","बिलआख़िर":"आखिर","मुक़र्रर":"तय",
    "लवाहिक़ीन":"रिश्तेदार","लवाहिकीन":"रिश्तेदार","हिफ़ाज़त":"देख-रेख","हिफ़ाज़त":"देख-रेख",
    "बहरहाल":"जो भी हो","क़रीब-क़रीब":"लगभग","क़रीब-क़रीब":"लगभग","तमाम":"सारे",
    "गौर-ओ-फ़िक्र":"गहरी सोच","ग़ौर-ओ-फ़िक्र":"गहरी सोच","मुतमइन":"संतुष्ट","अक्सरियत":"ज़्यादातर",
    "वाक़ियात":"घटनाओं","अख़्बारों":"अखबारों","गुफ़्तुगू":"बातचीत","अलाहिदा":"अलग",
    "मुतअल्लिक़":"के बारे में","मुतअल्लिक़":"के बारे में","माऊफ़":"सुन्न","तक़्सीम":"बँटवारा",
    "तक़्सीम":"बँटवारा","अर्से":"समय","मुसलसल":"लगातार","तक़रीर":"भाषण",
    "दफ़अतन":"अचानक","यकलख़्त":"अचानक","चुनांचे":"इसलिए","ख़ूनख़राबा":"मार-काट",
    "दीवानगी":"पागलपन","महबूबा":"प्यारी औरत","मोहब्बत":"प्यार","ख़ामोश":"चुप",
    "ख़ामोश":"चुप","हैसियत":"दर्जा","मसले":"सवाल","तवील":"लंबे","लहज़े":"पल",
    "जिस्मानी":"बदन की","तकलीफ़":"दर्द","संजीदगी":"गंभीरता","दरयाफ़्त":"पूछ",
    "मसरूफ़":"व्यस्त","बेशुमार":"बहुत से","ख़ैरियत":"ठीक-ठाक","ख़िदमत":"मदद",
    "हैरत":"हैरानी","बौखला":"घबरा","मुकम्मल":"पूरी","फ़हरिस्तें":"सूचियाँ",
    "तरफ़ैन":"दोनों तरफ","इब्तिदाई कार्रवाई":"शुरुआती काम","रज़ामंद":"तैयार",
    "रज़ामंद":"तैयार","शोर-ओ-गोगा":"शोर","बाक़ी-मांदा":"बाकी","मज़ीद":"और",
    "साकित-ओ-सामित":"बिल्कुल चुप","हलक़":"गला","फ़लक-शिगाफ़":"आसमान फाड़ती",
    "ख़ारदार":"काँटेदार","मुतअद्दिद":"कई","ज़ख़्मी":"घायल","ज़ख़्मी":"घायल",
    "क़ुव्वतें":"ताकत","होश-ओ-हवास":"होश","वजूद":"पूरा बदन और मन","ख़ला":"खालीपन",
    "मुअल्लक़":"लटका","बग़ैर":"बिना","हाफ़िज़े":"याददाश्त","हाफ़िज़े":"याददाश्त",
    "इत्मिनान":"सुकून","मुख़्तलिफ़":"अलग-अलग","मख़्तलिफ़":"अलग-अलग","निगाह":"नज़र",
    "अजीब-ओ-ग़रीब":"बहुत अजीब","मुतवातिर":"लगातार","इंतिहाई":"बहुत","एहसास":"महसूस",
    "इज़हार":"बताना","मुआमला":"मामला","मुआमले":"मामले","इस्तेमाल":"काम",
}

ROMAN_FIX = {
    "haiM":"hain","hUM":"hoon","nahIM":"nahin","meM":"mein","maiM":"main",
    "kyA":"kya","kyoM":"kyon","yah":"yeh","vah":"woh","unheM":"unhein",
    "tumheM":"tumhein","aura":"aur","phira":"phir","lekina":"lekin","agara":"agar",
    "isa":"is","usa":"us","eka":"ek","kucha":"kuchh","saba":"sab","ghara":"ghar",
    "dila":"dil","dina":"din","raata":"raat","loga":"log","baata":"baat",
    "haatha":"haath","paira":"pair","aankha":"aankh","kara":"kar","para":"par",
    "se":"se","ko":"ko","ki":"ki","kaa":"ka","ke":"ke","thaa":"tha","thee":"thi",
}

URDU_CHARS = {
    "ا":"a","آ":"aa","ب":"b","پ":"p","ت":"t","ٹ":"t","ث":"s","ج":"j","چ":"ch",
    "ح":"h","خ":"kh","د":"d","ڈ":"d","ذ":"z","ر":"r","ڑ":"r","ز":"z","ژ":"zh",
    "س":"s","ش":"sh","ص":"s","ض":"z","ط":"t","ظ":"z","ع":"a","غ":"gh","ف":"f",
    "ق":"q","ک":"k","گ":"g","ل":"l","م":"m","ن":"n","ں":"n","و":"o","ؤ":"o",
    "ہ":"h","ھ":"h","ء":"","ی":"i","ے":"e","ئ":"i","ۃ":"h","ۂ":"e",
    "َ":"a","ِ":"i","ُ":"u","ّ":"","ْ":"","ٰ":"aa","ۓ":"e","ۂ":"e",
}
URDU_WORDS = {
    "اور":"aur","میں":"main","ہے":"hai","ہیں":"hain","تھا":"tha","تھی":"thi","تھے":"the",
    "نہیں":"nahin","کہ":"ki","کے":"ke","کی":"ki","کا":"ka","کو":"ko","سے":"se","پر":"par",
    "یہ":"yeh","وہ":"woh","ایک":"ek","کیا":"kya","کچھ":"kuchh","بھی":"bhi","جو":"jo",
    "اپنے":"apne","اپنی":"apni","اپنا":"apna","مجھے":"mujhe","تم":"tum","آپ":"aap",
    "دل":"dil","بات":"baat","خط":"khat","صاحب":"sahab","مرزا":"Mirza","غالب":"Ghalib",
    "خدا":"Khuda","دنیا":"duniya","آدمی":"aadmi","دوست":"dost","آج":"aaj","کل":"kal",
    "اب":"ab","پھر":"phir","لیکن":"lekin","اگر":"agar","بہت":"bahut","گھر":"ghar",
}

MANTO = [
    ("hatak","Hatak","https://www.rekhta.org/stories/hatak-saadat-hasan-manto-stories?lang=hi",["दिन भर की थकी","सौगंधी"]),
    ("naya-qanoon","Naya Qanoon","https://www.rekhta.org/stories/nayaa-qanoon-saadat-hasan-manto-stories?lang=hi",["उस्ताद मंगू"]),
    ("tetwal-ka-kutta","Tetwal Ka Kutta","https://www.rekhta.org/stories/tetwaal-ka-kutta-saadat-hasan-manto-stories?lang=hi",["कई दिन से तरफ़ैन","कई दिन से तरफ़ैन","कई दिन से दोनों"]),
]


def get(url: str, *, tries: int = 4) -> requests.Response:
    err = None
    for n in range(tries):
        try:
            r = SESSION.get(url, timeout=60)
            r.raise_for_status()
            return r
        except Exception as exc:
            err = exc
            time.sleep(2 ** n)
    raise RuntimeError(f"download failed: {url}: {err}")


def get_json(url: str, **params):
    r = SESSION.get(url, params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def replace_words(text: str, mapping: dict[str,str]) -> str:
    for old in sorted(mapping, key=len, reverse=True):
        text = text.replace(old, mapping[old])
    return text


def normalize_roman(out: str) -> str:
    out = out.replace("RRi","ri").replace("RRI","ree").replace("LLi","li")
    out = out.replace("Ch","chh").replace("Th","th").replace("Dh","dh")
    out = out.replace("T","t").replace("D","d").replace("N","n")
    out = out.replace("~n","n").replace("~N","n").replace("Sh","sh").replace("S","sh")
    out = out.replace("j~n","gy").replace("A","aa").replace("I","ee").replace("U","oo")
    out = out.replace("M","n").replace("H","h").replace(".a","").replace(".n","n").replace("~","")
    for old,new in ROMAN_FIX.items():
        out = re.sub(rf"\b{re.escape(old)}\b", new, out)
    repairs = {
        "karanaa":"karna","karataa":"karta","karatee":"karti","karate":"karte",
        "kahataa":"kehta","kahatee":"kehti","kahate":"kehte","jaanaa":"jana",
        "jaataa":"jata","jaatee":"jati","aanaa":"aana","aataa":"aata",
        "hotaa":"hota","hotee":"hoti","dekhaa":"dekha","bolaa":"bola",
        "bolatee":"bolti","bolate":"bolte","rahaa":"raha","rahee":"rahi",
        "kiyaa":"kiya","diyaa":"diya","liyaa":"liya","gayaa":"gaya","aayaa":"aaya",
        "huaa":"hua","pa.Daa":"pada","ba.Daa":"bada","la.Dak":"ladak",
    }
    for old,new in repairs.items():
        out = re.sub(rf"\b{re.escape(old)}\b",new,out,flags=re.I)
    out = re.sub(r"\s+([,.!?;:])",r"\1",out)
    out = re.sub(r"[ \t]+"," ",out)
    out = re.sub(r" *\n *","\n",out)
    out = re.sub(r"\n{3,}","\n\n",out)
    return out.strip()


def roman_hi(text: str, extra: dict[str,str] | None = None) -> str:
    text = unicodedata.normalize("NFKC",text).translate(DEV_DIGITS).replace("�","")
    text = replace_words(text,HINDI_EASY)
    if extra:
        text = replace_words(text,extra)
    return normalize_roman(transliterate(text,sanscript.DEVANAGARI,sanscript.ITRANS))


def roman_ur(text: str) -> str:
    text = unicodedata.normalize("NFKC",text).translate(URDU_DIGITS)
    parts = re.split(r"([\s\W]+)",text)
    out=[]
    for token in parts:
        if token in URDU_WORDS:
            out.append(URDU_WORDS[token]); continue
        if re.search(r"[\u0600-\u06ff]",token):
            out.append("".join(URDU_CHARS.get(ch,"") if "\u0600"<=ch<="\u06ff" else ch for ch in token))
        else:
            out.append(token)
    s="".join(out)
    s=re.sub(r"\bkr\b","kar",s); s=re.sub(r"\bh\b","hai",s); s=re.sub(r"\bn\b","ne",s)
    s=re.sub(r"[ \t]+"," ",s); s=re.sub(r"\n{3,}","\n\n",s)
    return s.strip()


def assert_roman(path: Path):
    t=path.read_text(encoding="utf-8")
    m=re.search(r"[\u0900-\u097f\u0600-\u06ff]",t)
    if m: raise RuntimeError(f"Indic script remains in {path}: U+{ord(m.group()):04X}")


def natural_num(title: str) -> int:
    m=re.search(r"\d+",title.translate(DEV_DIGITS).rsplit("/",1)[-1])
    return int(m.group()) if m else 9999


def clean_wikisource(title: str) -> str:
    data=get_json("https://hi.wikisource.org/w/api.php",action="parse",page=title,prop="text",format="json",formatversion=2,disableeditsection=1)
    soup=BeautifulSoup(data["parse"]["text"],"html.parser")
    for tag in soup.select("script,style,table,.mw-editsection,.noprint,.ws-noexport,.references,sup.reference,.navbox,.licenseContainer,.ws-summary"):
        tag.decompose()
    for br in soup.find_all("br"): br.replace_with("\n")
    text=html.unescape(soup.get_text("\n"))
    lines=[]
    for line in text.splitlines():
        s=line.strip()
        if not s: lines.append(""); continue
        if s in {"डाउनलोड","विकिस्रोत से","स्रोत","संपादित करें"}: continue
        if s.startswith(("←","→","श्रेणी:")): continue
        lines.append(s)
    return re.sub(r"\n{3,}","\n\n","\n".join(lines)).strip()


def build_nirmala(qa: dict):
    titles=[]; cont=None
    while True:
        p=dict(action="query",list="allpages",apprefix="निर्मला/",apnamespace=0,aplimit="max",format="json",formatversion=2)
        if cont: p["apcontinue"]=cont
        data=get_json("https://hi.wikisource.org/w/api.php",**p)
        titles += [x["title"] for x in data["query"]["allpages"]]
        if "continue" not in data: break
        cont=data["continue"]["apcontinue"]
    titles=sorted({t for t in titles if natural_num(t)<9999},key=natural_num)
    if len(titles)<20: raise RuntimeError(f"Nirmala chapters too few: {len(titles)}")
    root=OUT/"works/premchand/nirmala"; total=0; index=["# Nirmala","","**Munshi Premchand**","","Complete machine-assisted first Roman-Hindustani reader pass.",""]
    for t in titles:
        n=natural_num(t); raw=clean_wikisource(t); total+=len(raw)
        if len(raw)<500: raise RuntimeError(f"Nirmala chapter {n} too short")
        path=root/"chapters"/f"{n:02d}.md"; write(path,f"# Chapter {n}\n\n{roman_hi(raw)}"); assert_roman(path)
        index.append(f"- [Chapter {n}](chapters/{n:02d}.md)")
    write(root/"translation.md","\n".join(index)); assert_roman(root/"translation.md")
    write(root/"source.md",f"# Locked Source Record — Nirmala\n\n- Author: Munshi Premchand\n- Complete Hindi Wikisource chapter set: {len(titles)} chapters\n- Source prefix: `निर्मला/`\n- Source characters processed: {total}\n- Status: source locked for machine-assisted first pass\n- Human source review: pending\n")
    write(root/"NOTES.md","# Editorial Notes — Nirmala\n\nThe complete chapter sequence has been retained. Vocabulary was simplified conservatively before Roman conversion. Names, relationships, money, customs, suspicion, illness, deaths, and the ending remain in source order.\n\nStatus: `machine_assisted_complete_first_pass`\n\nIndependent paragraph comparison and read-aloud review: pending.\n")
    qa["nirmala"]={"source_chars":total,"units":len(titles),"status":"machine_assisted_complete_first_pass"}


def godaan_source() -> tuple[str,list[str]]:
    api="https://api.github.com/repos/pandeyshikha1098/privacy_policy/contents/hindi-stories/storyBook/premchandra/godan?ref=45b42cf18333411f035757a9ecd8b6859fa84ae6"
    items=get(api).json(); files=sorted([x for x in items if x.get("name","").endswith(".txt")],key=lambda x:x["name"])
    if not files: raise RuntimeError("No Godaan source files")
    chunks=[]
    for f in files:
        tx=get(f["download_url"]).text
        if len(tx)<1000: raise RuntimeError(f"Godaan source file too short: {f['name']}")
        chunks.append(tx)
    return "\n\n".join(chunks),[f["name"] for f in files]


def split_chapters(raw: str) -> list[tuple[int,str]]:
    raw=raw.translate(DEV_DIGITS)
    pieces=re.split(r"(?m)^\s*(?:अध्याय\s*)?([0-9]{1,2})[.]?\s*$",raw)
    out=[]
    for i in range(1,len(pieces)-1,2):
        try:n=int(pieces[i])
        except:continue
        body=pieces[i+1].strip()
        if 1<=n<=60 and len(body)>500: out.append((n,body))
    # Keep the first occurrence of each chapter number.
    seen={};
    for n,b in out:
        if n not in seen: seen[n]=b
    return sorted(seen.items())


def split_blocks(raw: str,target=16):
    ps=[p.strip() for p in re.split(r"\n\s*\n",raw) if p.strip()]
    per=max(1,(len(ps)+target-1)//target)
    return [(i+1,"\n\n".join(ps[i:i+per])) for i in range(0,len(ps),per)]


def build_godaan(qa: dict):
    raw,names=godaan_source(); raw=raw.replace("�","")
    if len(raw)<250000: raise RuntimeError(f"Godaan source short: {len(raw)}")
    units=split_chapters(raw)
    mode="chapters"
    if len(units)<30:
        units=split_blocks(raw,16); mode="ordered-parts"
    root=OUT/"works/premchand/godaan"; index=["# Godaan","","**Munshi Premchand**","","Complete machine-assisted first Roman-Hindustani reader pass.",""]
    folder="chapters" if mode=="chapters" else "parts"
    for n,body in units:
        path=root/folder/f"{n:02d}.md"; write(path,f"# {'Chapter' if mode=='chapters' else 'Part'} {n}\n\n{roman_hi(body)}"); assert_roman(path)
        index.append(f"- [{'Chapter' if mode=='chapters' else 'Part'} {n}]({folder}/{n:02d}.md)")
    write(root/"translation.md","\n".join(index)); assert_roman(root/"translation.md")
    write(root/"source.md",f"# Locked Source Record — Godaan\n\n- Author: Munshi Premchand\n- Public source repository commit: `45b42cf18333411f035757a9ecd8b6859fa84ae6`\n- Source files joined in order: {', '.join(names)}\n- Source characters processed: {len(raw)}\n- Reader division mode: {mode}\n- Human scan comparison: pending\n")
    write(root/"NOTES.md",f"# Editorial Notes — Godaan\n\nThe complete downloaded source was retained in order and converted to Roman Hindustani in {len(units)} {mode}. No paragraph was intentionally removed. Village and city plots, money, debts, caste, land, labour, gender, politics, illness, deaths, and the final godaan scene remain in source order.\n\nStatus: `machine_assisted_complete_first_pass`\n\nIndependent scan comparison and read-aloud review: pending.\n")
    qa["godaan"]={"source_chars":len(raw),"units":len(units),"division":mode,"status":"machine_assisted_complete_first_pass"}


def archive_ocr(identifier: str) -> tuple[str,str]:
    meta=get(f"https://archive.org/metadata/{identifier}").json(); fs=meta.get("files",[])
    cand=[f for f in fs if f.get("name","").endswith("_djvu.txt")]
    if not cand: cand=[f for f in fs if f.get("name","").endswith(".txt") and "meta" not in f.get("name","").lower()]
    if not cand: raise RuntimeError(f"No OCR text for {identifier}")
    best=max(cand,key=lambda f:int(f.get("size",0) or 0)); name=best["name"]
    url=f"https://archive.org/download/{identifier}/{requests.utils.quote(name)}"
    return get(url).text,url


def clean_urdu(raw: str) -> str:
    raw=unicodedata.normalize("NFKC",raw)
    lines=[]
    for line in raw.splitlines():
        s=line.strip()
        if not s: lines.append(""); continue
        if re.fullmatch(r"[0-9۰-۹\-–— ]{1,8}",s): continue
        if "Digitized by" in s or "Generated at" in s: continue
        lines.append(s)
    return re.sub(r"\n{3,}","\n\n","\n".join(lines)).strip()


def build_urdu(qa: dict):
    raw,url=archive_ocr("urduemualla")
    if len(raw)<100000: raw,url=archive_ocr("in.ernet.dli.2015.435597")
    raw=clean_urdu(raw)
    if len(raw)<100000: raise RuntimeError(f"Urdu-e-Mualla OCR short: {len(raw)}")
    ps=[p.strip() for p in re.split(r"\n\s*\n",raw) if p.strip()]
    if len(ps)<100: raise RuntimeError(f"Urdu OCR paragraphs too few: {len(ps)}")
    per=max(1,(len(ps)+23)//24); blocks=[ps[i:i+per] for i in range(0,len(ps),per)]
    root=OUT/"works/ghalib/urdu-e-mualla"; index=["# Urdu-e-Mualla","","**Mirza Ghalib**","","Complete OCR-based machine-assisted Roman first pass.",""]
    for i,block in enumerate(blocks,1):
        path=root/"parts"/f"{i:02d}.md"; write(path,f"# Part {i}\n\n{roman_ur(chr(10).join(block))}"); assert_roman(path)
        index.append(f"- [Part {i}](parts/{i:02d}.md)")
    write(root/"translation.md","\n".join(index)); assert_roman(root/"translation.md")
    write(root/"source.md",f"# Locked Source Record — Urdu-e-Mualla\n\n- Author: Mirza Ghalib\n- Public-domain OCR source: {url}\n- OCR characters processed: {len(raw)}\n- Ordered OCR paragraphs: {len(ps)}\n- Human Urdu source review: pending\n")
    write(root/"NOTES.md",f"# Editorial Notes — Urdu-e-Mualla\n\nThe full selected old-edition OCR was retained in order and divided into {len(blocks)} bounded parts. Nastaliq OCR and automatic vowel recovery are imperfect. Letter boundaries, names, dates, Persian quotations, missing vowels, and OCR errors require line-by-line Urdu review.\n\nStatus: `ocr_machine_assisted_complete_first_pass`\n\nPublication status: not reviewed.\n")
    qa["urdu-e-mualla"]={"source_chars":len(raw),"paragraphs":len(ps),"units":len(blocks),"status":"ocr_machine_assisted_complete_first_pass"}


def page_text(url: str) -> str:
    soup=BeautifulSoup(get(url).text,"html.parser")
    for tag in soup.select("script,style,noscript,svg,iframe"): tag.decompose()
    for br in soup.find_all("br"): br.replace_with("\n")
    t=soup.get_text("\n")
    t=re.sub(r"[ \t]{2,}"," ",t); t=re.sub(r"\n{3,}","\n\n",t)
    return t


def extract_story(text: str,markers: list[str]) -> str:
    positions=[text.find(m) for m in markers if text.find(m)>=0]
    if not positions: raise RuntimeError(f"Manto opening not found: {markers}")
    tail=text[min(positions):]
    ends=[]
    for m in ("\nस्रोत :","\nस्रोत:","\nवीडियो","\nRECITATIONS","\nसंबंधित टैग","\nMORE BY"):
        x=tail.find(m)
        if x>1000: ends.append(x)
    if ends: tail=tail[:min(ends)]
    tail=re.sub(r"\n{3,}","\n\n",tail).strip()
    if len(tail)<2500: raise RuntimeError(f"Manto extraction short: {len(tail)}")
    return tail


def build_manto(qa: dict):
    for wid,title,url,markers in MANTO:
        raw=extract_story(page_text(url),markers)
        root=OUT/f"works/manto/{wid}"; out=roman_hi(raw,MANTO_EASY)
        write(root/"translation.md",f"# {title}\n\n**Saadat Hasan Manto**\n\n{out}"); assert_roman(root/"translation.md")
        write(root/"source.md",f"# Locked Source Record — {title}\n\n- Author: Saadat Hasan Manto\n- Complete author text rendered in Devanagari from the Rekhta story page\n- Source: {url}\n- Source characters processed: {len(raw)}\n- Human Urdu comparison: pending\n")
        write(root/"NOTES.md",f"# Editorial Notes — {title}\n\nThe complete extracted story sequence was retained. Difficult Urdu vocabulary received conservative everyday replacements before Roman conversion. No scene, violence, insult, social detail, repetition, or ending was intentionally censored or shortened.\n\nStatus: `machine_assisted_complete_first_pass`\n\nIndependent paragraph review and read-aloud review: pending.\n")
        qa[wid]={"source_chars":len(raw),"units":1,"status":"machine_assisted_complete_first_pass"}


def main():
    OUT.mkdir(parents=True,exist_ok=True); qa={}
    build_nirmala(qa); build_godaan(qa); build_urdu(qa); build_manto(qa)
    for path in OUT.rglob("*.md"): assert_roman(path)
    qa["validation"]={"markdown_files":len(list(OUT.rglob("*.md"))),"residual_indic_chars":0}
    write(OUT/"QA.json",json.dumps(qa,ensure_ascii=False,indent=2))
    print(json.dumps(qa,ensure_ascii=False,indent=2))

if __name__=="__main__": main()
