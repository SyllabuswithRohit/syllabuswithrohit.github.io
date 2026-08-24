#!/usr/bin/env python3
"""Build three complete public-domain long-work Roman-Hindustani first-pass bundles."""
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

OUT = Path("generated_bundle")
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "SWR-long-classics-bundle/1.0"})
DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
URDU_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
SCRIPT_RE = re.compile(r"[\u0900-\u097f\u0600-\u06ff]")

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
    "अबोध":"नासमझ","बुद्धि":"अकल","चतुर":"होशियार","मूर्ख":"बेवकूफ",
    "सन्देह":"शक","संदेह":"शक","विश्वास":"यकीन","आशा":"उम्मीद","निराशा":"मायूसी",
    "सम्मान":"इज़्ज़त","अपमान":"बेइज़्ज़ती","कष्ट":"तकलीफ","यातना":"तकलीफ",
    "प्रेम":"प्यार","स्नेह":"प्यार","घृणा":"नफरत","द्वेष":"नफरत","लाभ":"फायदा",
    "हानि":"नुकसान","सम्पूर्ण":"पूरा","संपूर्ण":"पूरा","प्रत्येक":"हर","समस्त":"सब",
}

URDU_MAP = {
    "ا":"a","آ":"aa","أ":"a","إ":"i","ٱ":"a","ء":"","ب":"b","پ":"p","ت":"t","ٹ":"t",
    "ث":"s","ج":"j","چ":"ch","ح":"h","خ":"kh","د":"d","ڈ":"d","ذ":"z","ر":"r","ڑ":"r",
    "ز":"z","ژ":"zh","س":"s","ش":"sh","ص":"s","ض":"z","ط":"t","ظ":"z","ع":"","غ":"gh",
    "ف":"f","ق":"q","ک":"k","ك":"k","گ":"g","ل":"l","م":"m","ن":"n","ں":"n","و":"o",
    "ؤ":"o","ہ":"h","ه":"h","ھ":"h","ی":"y","ي":"y","ے":"e","ئ":"y","ۃ":"h","ۂ":"e",
    "ۓ":"e","َ":"a","ِ":"i","ُ":"u","ّ":"","ْ":"","ٰ":"a","ٔ":"","ٖ":"i","ٗ":"u","ـ":"",
}
URDU_WORDS = {
    "myn":"main","mh":"main","my":"mein","mn":"mein","hy":"hai","hyn":"hain","ny":"ne",
    "ky":"ke","sy":"se","or":"aur","yh":"yeh","wh":"woh","nhyn":"nahin","nhi":"nahin",
    "kr":"kar","kry":"kare","krta":"karta","krty":"karte","krna":"karna","gya":"gaya",
    "gyi":"gayi","gye":"gaye","aya":"aaya","ayi":"aayi","ap":"aap","apko":"aapko",
    "apny":"apne","hm":"ham","tm":"tum","mujhy":"mujhe","tujhy":"tujhe","bht":"bahut",
    "khuda":"Khuda","sahb":"sahab","lkha":"likha","lkh":"likh","khbr":"khabar",
    "dnya":"duniya","zndgi":"zindagi","muhbt":"mohabbat",
}

def req(method: str, url: str, *, attempts: int = 10, **kwargs: Any) -> requests.Response:
    last = None
    for attempt in range(attempts):
        if attempt:
            time.sleep(min(45, 2 * attempt))
        r = SESSION.request(method, url, timeout=120, **kwargs)
        last = r
        if r.status_code in {429,500,502,503,504}:
            retry = r.headers.get("Retry-After","")
            if retry.isdigit():
                time.sleep(min(90,int(retry)))
            continue
        r.raise_for_status()
        return r
    assert last is not None
    last.raise_for_status()
    raise RuntimeError(url)

def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip()+"\n", encoding="utf-8")

def clean_space(text: str) -> str:
    text = text.replace("\r\n","\n").replace("\r","\n")
    text = re.sub(r"[ \t]+$","",text,flags=re.M)
    text = re.sub(r"[ \t]{2,}"," ",text)
    text = re.sub(r"\n{3,}","\n\n",text)
    return text.strip()

def replace_words(text: str) -> str:
    for old in sorted(HINDI_EASY,key=len,reverse=True):
        text = re.sub(
            rf"(?<![\w\u0900-\u097f]){re.escape(old)}(?![\w\u0900-\u097f])",
            HINDI_EASY[old], text
        )
    return text

def roman_hi(text: str) -> str:
    text = (
        unicodedata.normalize("NFKC",text).translate(DEV_DIGITS).replace("�","")
        .replace("ऑ","ओ").replace("ॉ","ो").replace("ऍ","ए").replace("ॅ","े").replace("़","")
    )
    text = replace_words(text)
    out = transliterate(text,sanscript.DEVANAGARI,sanscript.ITRANS)
    for old,new in [
        ("RRi","ri"),("RRI","ree"),("LLi","li"),("Ch","chh"),("Th","th"),("Dh","dh"),
        ("T","t"),("D","d"),("~N","n"),("~n","n"),("Sh","sh"),("S","sh"),("j~n","gy"),
        ("A","aa"),("I","ee"),("U","oo"),("M","n"),("H","h"),(".a",""),(".n","n"),("~","")
    ]:
        out=out.replace(old,new)
    fixes = {
        "haiM":"hain","hai.n":"hain","hUM":"hoon","nahIM":"nahin","meM":"mein","maiM":"main",
        "kyoM":"kyon","yah":"yeh","vah":"woh","unheM":"unhein","tumheM":"tumhein",
        "aura":"aur","phira":"phir","lekina":"lekin","agara":"agar","isa":"is","usa":"us",
        "eka":"ek","kucha":"kuchh","saba":"sab","ghara":"ghar","dila":"dil","dina":"din",
        "raata":"raat","loga":"log","baata":"baat","haatha":"haath","paira":"pair","kara":"kar",
    }
    for old,new in fixes.items():
        out=re.sub(rf"\b{re.escape(old)}\b",new,out)
    for pat,repl in [
        (r"\bkaranaa\b","karna"),(r"\bkarataa\b","karta"),(r"\bkaratee\b","karti"),
        (r"\bkahataa\b","kehta"),(r"\bkahatee\b","kehti"),(r"\bjaanaa\b","jana"),
        (r"\bjaataa\b","jata"),(r"\bjaatee\b","jati"),(r"\baanaa\b","aana"),
        (r"\bhotaa\b","hota"),(r"\bhotee\b","hoti"),(r"\bdekhaa\b","dekha"),
        (r"\bbolaa\b","bola"),(r"\brahaa\b","raha"),(r"\brahee\b","rahi"),
        (r"\bthaa\b","tha"),(r"\bthee\b","thi"),(r"\bkiyaa\b","kiya"),
        (r"\bdiyaa\b","diya"),(r"\bliyaa\b","liya"),(r"\bgayaa\b","gaya"),
        (r"\baayaa\b","aaya"),(r"\bhuaa\b","hua")
    ]:
        out=re.sub(pat,repl,out,flags=re.I)
    return clean_space(out)

def roman_ur(text: str) -> str:
    text=unicodedata.normalize("NFKC",text).translate(URDU_DIGITS)
    out="".join(URDU_MAP.get(ch,"" if "\u0600"<=ch<="\u06ff" else ch) for ch in text)
    tokens=re.split(r"([^A-Za-z]+)",out)
    out="".join(URDU_WORDS.get(tok.lower(),tok) for tok in tokens)
    out=re.sub(r"\s+([,.!?;:])",r"\1",out)
    return clean_space(out)

def assert_roman(text: str, label: str) -> None:
    m=SCRIPT_RE.search(text)
    if m:
        raise RuntimeError(f"Indic character in {label}: U+{ord(m.group()):04X}")
    if len(text)<100:
        raise RuntimeError(f"Too short: {label}")

def natural(title: str) -> int:
    tail=title.rsplit("/",1)[-1].translate(DEV_DIGITS)
    m=re.search(r"\d+",tail)
    return int(m.group()) if m else 9999

def nirmala() -> dict[str,Any]:
    api="https://hi.wikisource.org/w/api.php"
    data=req("GET",api,params={
        "action":"query","list":"allpages","apprefix":"निर्मला/","apnamespace":0,
        "aplimit":"max","format":"json","formatversion":2
    }).json()
    titles=sorted(
        {x["title"] for x in data["query"]["allpages"] if natural(x["title"])!=9999},
        key=natural
    )
    if len(titles)<20:
        raise RuntimeError(f"Nirmala titles: {len(titles)}")
    extracts={}
    for start in range(0,len(titles),12):
        batch=titles[start:start+12]
        q=req("POST",api,data={
            "action":"query","prop":"extracts","explaintext":1,"redirects":1,
            "titles":"|".join(batch),"format":"json","formatversion":2
        }).json()
        for page in q["query"]["pages"]:
            if "missing" not in page:
                extracts[page["title"]]=page.get("extract","")
        time.sleep(2)
    sections=["# Nirmala","","**Munshi Premchand**",""]
    source=[]
    total=0
    for title in titles:
        raw=extracts.get(title,"")
        if len(raw)<700:
            q=req("GET",api,params={
                "action":"parse","page":title,"prop":"text","format":"json","formatversion":2
            }).json()
            soup=BeautifulSoup(q["parse"]["text"],"html.parser")
            for tag in soup.select("script,style,table,.mw-editsection,.noprint,.ws-noexport,.navbox"):
                tag.decompose()
            raw=html.unescape(soup.get_text("\n"))
        raw=clean_space(raw)
        if len(raw)<700:
            raise RuntimeError(f"Short Nirmala chapter {title}")
        n=natural(title)
        total+=len(raw)
        sections += [f"## Chapter {n}","",roman_hi(raw),""]
        source.append(f"- Chapter {n}: https://hi.wikisource.org/wiki/{quote(title,safe='/')}")
    text="\n".join(sections)
    assert_roman(text,"Nirmala")
    root=OUT/"premchand/nirmala"
    write(root/"translation.md",text)
    write(root/"source.md",
        "# Locked Source Record — Nirmala\n\n- Author: Munshi Premchand\n- Work: complete novel\n"
        f"- Chapters processed: {len(titles)}\n- Source characters: {total}\n"
        "- Base: Hindi Wikisource scan-linked transcriptions\n- Human scan comparison: pending\n\n"
        +"\n".join(source))
    write(root/"NOTES.md",
        "# Editorial Notes — Nirmala\n\n- Complete source-order machine-assisted Roman first pass.\n"
        "- Roman-only and chapter-count checks passed.\n- Human paragraph comparison and read-aloud review: pending.\n")
    return {"units":len(titles),"source_chars":total,"output_chars":len(text)}

def godaan() -> dict[str,Any]:
    base=(
        "https://raw.githubusercontent.com/pandeyshikha1098/privacy_policy/"
        "45b42cf18333411f035757a9ecd8b6859fa84ae6/"
        "hindi-stories/storyBook/premchandra/godan"
    )
    sections=["# Godaan","","**Munshi Premchand**",""]
    total=0
    for n in range(1,37):
        raw=req("GET",f"{base}/{n:02d}.txt").text.replace("�","")
        if len(raw)<1000:
            raise RuntimeError(f"Short Godaan {n}")
        total+=len(raw)
        sections += [f"## Chapter {n}","",roman_hi(raw),""]
    text="\n".join(sections)
    assert_roman(text,"Godaan")
    root=OUT/"premchand/godaan"
    write(root/"translation.md",text)
    write(root/"source.md",
        "# Locked Source Record — Godaan\n\n- Author: Munshi Premchand\n- Work: complete novel\n"
        "- Source repository commit: `45b42cf18333411f035757a9ecd8b6859fa84ae6`\n"
        "- Files: `01.txt` through `36.txt`\n"
        f"- Source characters: {total}\n- Human scan comparison: pending\n")
    write(root/"NOTES.md",
        "# Editorial Notes — Godaan\n\n- Complete 36-chapter source-order machine-assisted Roman first pass.\n"
        "- Roman-only and chapter-count checks passed.\n- Human source comparison and read-aloud review: pending.\n")
    return {"units":36,"source_chars":total,"output_chars":len(text)}

def archive_ocr(identifier: str) -> tuple[str,str]:
    meta=req("GET",f"https://archive.org/metadata/{identifier}").json()
    candidates=[f for f in meta.get("files",[]) if f.get("name","").endswith("_djvu.txt")]
    if not candidates:
        candidates=[f for f in meta.get("files",[]) if f.get("name","").endswith(".txt")]
    if not candidates:
        raise RuntimeError("No OCR")
    best=max(candidates,key=lambda f:int(f.get("size",0) or 0))
    name=best["name"]
    url=f"https://archive.org/download/{identifier}/{quote(name)}"
    return req("GET",url).text,url

def urdu_mualla() -> dict[str,Any]:
    raw,url=archive_ocr("urduemualla")
    if len(raw)<100000:
        raw,url=archive_ocr("in.ernet.dli.2015.435597")
    lines=[]
    for line in unicodedata.normalize("NFKC",raw).splitlines():
        s=line.strip()
        if not s:
            lines.append("")
        elif re.fullmatch(r"[0-9۰-۹\-–— ]{1,8}",s):
            continue
        elif "Digitized by" in s or "Generated at" in s:
            continue
        else:
            lines.append(s)
    raw=clean_space("\n".join(lines))
    ps=[p.strip() for p in re.split(r"\n\s*\n",raw) if p.strip()]
    if len(raw)<80000 or len(ps)<80:
        raise RuntimeError(f"Urdu OCR short {len(raw)} {len(ps)}")
    per=max(1,(len(ps)+23)//24)
    blocks=[ps[i:i+per] for i in range(0,len(ps),per)]
    sections=["# Urdu-e-Mualla","","**Mirza Ghalib**",""]
    for n,block in enumerate(blocks,1):
        sections += [f"## Part {n}","",roman_ur("\n\n".join(block)),""]
    text="\n".join(sections)
    assert_roman(text,"Urdu-e-Mualla")
    root=OUT/"ghalib/urdu-e-mualla"
    write(root/"translation.md",text)
    write(root/"source.md",
        "# Locked Source Record — Urdu-e-Mualla\n\n- Author: Mirza Ghalib\n"
        f"- Public-domain old OCR: {url}\n- OCR characters: {len(raw)}\n"
        f"- Ordered parts: {len(blocks)}\n- Human scan comparison: pending\n")
    write(root/"NOTES.md",
        "# Editorial Notes — Urdu-e-Mualla\n\n- Complete selected-old-OCR-order Roman first pass.\n"
        "- Nastaliq OCR, vowels, letter boundaries, names and dates require line-by-line Urdu review.\n"
        "- Roman-only and part-count checks passed. Publication status: not reviewed.\n")
    return {"units":len(blocks),"source_chars":len(raw),"output_chars":len(text)}

def main() -> None:
    OUT.mkdir(parents=True,exist_ok=True)
    qa={"nirmala":nirmala(),"godaan":godaan(),"urdu-e-mualla":urdu_mualla()}
    write(OUT/"QA.json",json.dumps(qa,ensure_ascii=False,indent=2))
    write(OUT/"QA.md",
        "# Long Classics Bundle QA\n\n"
        f"- Nirmala chapters: {qa['nirmala']['units']}\n"
        f"- Godaan chapters: {qa['godaan']['units']}\n"
        f"- Urdu-e-Mualla parts: {qa['urdu-e-mualla']['units']}\n"
        "- Roman-only checks: passed\n- Human review: pending\n- Publication-ready: no\n")
    print(json.dumps(qa,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
