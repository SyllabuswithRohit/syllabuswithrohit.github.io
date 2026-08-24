#!/usr/bin/env python3
"""Build complete machine-assisted Roman-Hindustani first passes for three public-domain works."""
from __future__ import annotations

import hashlib
import html
import json
import re
import sys
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

ROOT = Path("generated/long-classics")
UA = "SyllabuswithRohit-public-domain-editorial-builder/1.0"
S = requests.Session()
S.headers.update({"User-Agent": UA, "Accept-Language": "hi,en;q=0.8"})
TIMEOUT = 90
DEV_RE = re.compile(r"[\u0900-\u097f]")
URDU_RE = re.compile(r"[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff]")
DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
URDU_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")

HINDI_EASY = {
    "किन्तु":"लेकिन","किंतु":"लेकिन","परन्तु":"लेकिन","परंतु":"लेकिन","तथापि":"फिर भी",
    "अतः":"इसलिए","अतएव":"इसलिए","प्रातःकाल":"सुबह","प्रातः":"सुबह","सायंकाल":"शाम",
    "सन्ध्या":"शाम","संध्या":"शाम","भोजन":"खाना","जलपान":"कुछ खाना","निवास":"घर",
    "गृहस्थी":"घर-परिवार","गृह":"घर","मुखमण्डल":"चेहरा","मुखमंडल":"चेहरा","मुख":"मुँह",
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
    "सौभाग्य":"अच्छी किस्मत","दुर्भाग्यवश":"बदकिस्मती से","कारण":"वजह","परिणाम":"नतीजा",
    "समाचार":"खबर","सूचना":"खबर","अनुमति":"इजाज़त","निवेदन":"बिनती","अनुरोध":"बिनती",
    "आज्ञा":"हुक्म","निर्देश":"हुक्म","अवकाश":"फुर्सत","प्रयत्न":"कोशिश","प्रयास":"कोशिश",
    "सफल":"कामयाब","असफल":"नाकाम","लज्जा":"शर्म","ग्लानि":"पछतावा","स्वर":"आवाज़",
    "कण्ठ":"गला","कंठ":"गला","मौन":"चुप","निःशब्द":"चुप","वार्तालाप":"बातचीत",
    "संवाद":"बातचीत","मार्ग":"रास्ता","पथ":"रास्ता","गमन":"जाना","प्रस्थान":"रवाना होना",
    "आगमन":"आना","वस्त्र":"कपड़े","आभूषण":"गहने","औषधि":"दवा","चिकित्सक":"डॉक्टर",
    "विद्यालय":"स्कूल","अध्यापक":"टीचर","कार्यालय":"दफ्तर","न्यायालय":"अदालत",
    "धन":"पैसा","राशि":"पैसा","निर्धन":"गरीब","समृद्ध":"अमीर","कठिन":"मुश्किल",
    "सरल":"आसान","उचित":"ठीक","अनुचित":"गलत","विशेष":"खास","साधारण":"आम",
    "प्रकार":"तरह","भाँति":"तरह","भांति":"तरह","क्षणभर":"एक पल","क्षण":"पल",
    "दीर्घ":"लंबा","पूर्व":"पहले","पश्चात्":"बाद","पश्चात":"बाद","अनन्तर":"बाद",
    "अबोध":"नासमझ","बुद्धि":"अकल","चतुर":"होशियार","मूर्ख":"बेवकूफ","मूढ":"बेवकूफ",
    "सन्देह":"शक","संदेह":"शक","विश्वास":"यकीन","आशा":"उम्मीद","निराशा":"मायूसी",
    "सम्मान":"इज़्ज़त","अपमान":"बेइज़्ज़ती","कष्ट":"तकलीफ","यातना":"तकलीफ",
    "प्रेम":"प्यार","स्नेह":"प्यार","घृणा":"नफरत","द्वेष":"नफरत","लाभ":"फायदा",
    "हानि":"नुकसान","सम्पूर्ण":"पूरा","संपूर्ण":"पूरा","प्रत्येक":"हर","समस्त":"सब",
    "किसी प्रकार":"किसी तरह","इस प्रकार":"इस तरह","उस प्रकार":"उस तरह","वर्तमान":"अभी",
    "भविष्य":"आने वाला समय","अतीत":"बीता समय","अवश्य":"ज़रूर","विवश":"मजबूर",
    "परिस्थिति":"हालात","संकट":"मुसीबत","प्रसंग":"बात","उदासीन":"बेपरवाह",
    "स्वाभाविक":"कुदरती","अभिमान":"घमंड","नम्र":"नरम","विनम्र":"नरमी से","संकोच":"झिझक",
    "आश्वासन":"भरोसा","स्मरण":"याद","विस्मृत":"भूल गया","परिचित":"जान-पहचान वाला",
    "अपरिचित":"अनजान","अपराध":"जुर्म","दण्ड":"सज़ा","दंड":"सज़ा","कर्तव्य":"फर्ज़",
    "उत्तरदायित्व":"ज़िम्मेदारी","स्वतन्त्र":"आज़ाद","स्वतंत्र":"आज़ाद","स्वाधीन":"आज़ाद",
    "दासता":"गुलामी","वृद्ध":"बूढ़ा","वृद्धा":"बूढ़ी औरत","युवक":"जवान आदमी",
    "युवती":"जवान लड़की","प्राणी":"जीव","मनुष्य":"इंसान","व्यक्ति":"आदमी",
}
HINDI_EASY_ITEMS = sorted(HINDI_EASY.items(), key=lambda kv: len(kv[0]), reverse=True)

ROMAN_EXACT = {
    "maiM":"main","mai.n":"main","meM":"mein","me.n":"mein","haiM":"hain","hai.n":"hain",
    "hUM":"hoon","hU.n":"hoon","nahIM":"nahin","nahiiM":"nahin","kyoM":"kyon","kyA":"kya",
    "yah":"yeh","vaha":"wahan","vah":"woh","isa":"is","usa":"us","eka":"ek","aura":"aur",
    "phira":"phir","lekina":"lekin","agara":"agar","kucha":"kuchh","saba":"sab","ghara":"ghar",
    "dila":"dil","dina":"din","rAta":"raat","loga":"log","bAta":"baat","hAtha":"haath",
    "paira":"pair","AMkha":"aankh","A.nkha":"aankh","mu.nha":"munh","kara":"kar","para":"par",
    "taba":"tab","jaba":"jab","aba":"ab","pasa":"paas","sAtha":"saath","bAda":"baad",
    "bahuta":"bahut","jyAdA":"zyada","thodA":"thoda","apane":"apne","apanA":"apna",
    "apanI":"apni","usane":"usne","unhoMne":"unhone","unhoneM":"unhone","isane":"isne",
    "karane":"karne","rahane":"rehne","kahane":"kehne","acchA":"achchha","achchhA":"achchha",
    "chAhie":"chahiye","bhagavAna":"Bhagwan","pyAra":"pyaar","zamIna":"zameen",
    "AdamI":"aadmi","insAna":"insaan","aurata":"aurat","laDakA":"ladka","laDakI":"ladki",
    "bacchA":"bachcha","choTA":"chhota","baDA":"bada","gAyA":"gaya","gayI":"gayi",
    "huA":"hua","huI":"hui","rahA":"raha","rahI":"rahi","thA":"tha","thI":"thi",
    "karatA":"karta","karatI":"karti","karate":"karte","detA":"deta","detI":"deti",
    "letA":"leta","letI":"leti","jAtA":"jaata","jAtI":"jaati","Ate":"aate","AtA":"aata",
    "AtI":"aati","hotA":"hota","hotI":"hoti","hote":"hote","merA":"mera","merI":"meri",
    "terA":"tera","terI":"teri","tumhArA":"tumhara","hamArA":"hamara","hamArI":"hamari",
    "unheM":"unhein","tumheM":"tumhe","hameM":"hamein","koI":"koi","kauna":"kaun",
    "yahAM":"yahan","vahAM":"wahan","kahAM":"kahan","jahAM":"jahan","kyoMki":"kyunki",
    "isalie":"isliye",
}
SCHWA_KEEP = {"kya","tha","hua","gaya","raha","bada","chhota","pata","maza","dawa","saza","wajah","jagah","hawa","dua","duniya","naya","maya","daya","kala","bhala","poora","aadha","beta","beti","ladka","ladki","bachcha","achchha","apna","apni","mera","tera","hamara","tumhara","kahna","rehna","hona","karna","dena","lena","jana","aana","khana","peena","sona","rona"}

URDU_WORDS = {
    "میں":"main","ہے":"hai","ہیں":"hain","ہوں":"hoon","تھا":"tha","تھی":"thi","تھے":"the",
    "نہیں":"nahin","نہ":"na","اور":"aur","کہ":"ki","کا":"ka","کی":"ki","کے":"ke","کو":"ko",
    "سے":"se","پر":"par","یہ":"yeh","وہ":"woh","اس":"is","اُس":"us","ان":"un","ایک":"ek",
    "بھی":"bhi","تو":"to","جو":"jo","جب":"jab","پھر":"phir","اگر":"agar","مگر":"magar",
    "لیکن":"lekin","کیوں":"kyon","کیا":"kya","کون":"kaun","کس":"kis","کچھ":"kuchh","سب":"sab",
    "کوئی":"koi","اپنے":"apne","اپنا":"apna","اپنی":"apni","میرے":"mere","میرا":"mera","میری":"meri",
    "تم":"tum","آپ":"aap","ہم":"hum","مجھے":"mujhe","تمہیں":"tumhe","انہیں":"unhein","اسے":"use",
    "صاحب":"sahab","حضرت":"huzoor","جناب":"janaab","خط":"khat","خطوط":"khat","نامہ":"naama",
    "جواب":"jawab","لکھا":"likha","لکھتے":"likhte","لکھنے":"likhne","لکھیں":"likhein","لکھ":"likh",
    "آیا":"aaya","آئی":"aayi","آئے":"aaye","گیا":"gaya","گئی":"gayi","گئے":"gaye","ہوا":"hua",
    "ہوئی":"hui","ہوئے":"hue","رہا":"raha","رہی":"rahi","رہے":"rahe","کر":"kar","کرتا":"karta",
    "کرتی":"karti","کرتے":"karte","دیا":"diya","دی":"di","دے":"de","لیا":"liya","لی":"li","لے":"le",
    "دن":"din","رات":"raat","سال":"saal","وقت":"waqt","گھر":"ghar","شہر":"shahar","دہلی":"Dilli",
    "کل":"kal","آج":"aaj","اب":"ab","پہلے":"pehle","بعد":"baad","بہت":"bahut","زیادہ":"zyada",
    "کم":"kam","دل":"dil","بات":"baat","خبر":"khabar","حال":"haal","خدا":"Khuda","آدمی":"aadmi",
    "لوگ":"log","دنیا":"duniya","زندگی":"zindagi","دوست":"dost","بھائی":"bhai","بیٹا":"beta",
    "بیٹی":"beti","عورت":"aurat","کتاب":"kitaab","شعر":"sher","غزل":"ghazal","زبان":"zabaan",
    "اردو":"Urdu","فارسی":"Farsi","روپے":"rupaye","غالب":"Ghalib","مرزا":"Mirza","اسد":"Asad",
    "اللہ":"Allah","میاں":"miyan","مولوی":"maulvi","محبت":"mohabbat","عشق":"ishq","غم":"gham",
    "خوش":"khush","خوشی":"khushi","درد":"dard","موت":"maut","زندہ":"zinda","یاد":"yaad",
    "معلوم":"maloom","ضرور":"zaroor","شاید":"shayad","صرف":"sirf","ہر":"har","تمام":"sab",
    "سارا":"saara","دوسرا":"doosra","دوسری":"doosri","طرح":"tarah","طرف":"taraf","بار":"baar",
    "بارے":"baare","ساتھ":"saath","پاس":"paas","دور":"door","یہاں":"yahan","وہاں":"wahan",
    "کہاں":"kahan","جس":"jis","جسے":"jise","جن":"jin","جیسے":"jaise","ایسا":"aisa","ایسی":"aisi",
    "ایسے":"aise","چاہتا":"chahta","چاہتی":"chahti","چاہیے":"chahiye","دیکھا":"dekha","دیکھ":"dekh",
    "سنا":"suna","سن":"sun","کہا":"kaha","کہتے":"kehte","کہنے":"kehne","پڑھا":"padha","پڑھ":"padh",
    "کام":"kaam","پیسہ":"paisa","پیسے":"paise","مکان":"makaan","بازار":"bazaar","انگریز":"Angrez",
    "حکومت":"hukumat","بادشاہ":"badshah","نواب":"nawab","دروازہ":"darwaza","کمرہ":"kamra",
    "صبح":"subah","شام":"shaam","مہینہ":"mahina","تاریخ":"tareekh","بیمار":"beemar","دوائی":"dawai",
    "کھانا":"khana","پانی":"paani","چائے":"chai","شراب":"sharab","کاغذ":"kaagaz","قلم":"qalam",
    "معاف":"maaf","مہربانی":"meharbani","سلام":"salaam","دعا":"dua","جواباً":"jawaban","عرض":"arz",
}
URDU_CHAR = {"ا":"a","آ":"aa","ٱ":"a","ب":"b","پ":"p","ت":"t","ٹ":"t","ث":"s","ج":"j","چ":"ch","ح":"h","خ":"kh","د":"d","ڈ":"d","ذ":"z","ر":"r","ڑ":"r","ز":"z","ژ":"zh","س":"s","ش":"sh","ص":"s","ض":"z","ط":"t","ظ":"z","ع":"a","غ":"gh","ف":"f","ق":"q","ک":"k","ك":"k","گ":"g","ل":"l","م":"m","ن":"n","ں":"n","و":"o","ؤ":"o","ہ":"h","ھ":"h","ۃ":"h","ة":"h","ء":"","ئ":"i","ی":"y","ى":"a","ے":"e","ۓ":"e","ۂ":"e","َ":"a","ِ":"i","ُ":"u","ّ":"","ْ":"","ٰ":"a","ٔ":"","ٕ":"","ـ":""}
NAV_EXACT = {"विकिस्रोत","मुखपृष्ठ","विषयसूची","पिछला अध्याय","अगला अध्याय","निर्मला","संपादन","यह पृष्ठ प्रमाणित है","डाउनलोड","अन्य प्रारूप","पाठ","चर्चा"}

@dataclass
class Chapter:
    number: int
    title: str
    source_id: str
    text: str

def sha256(text): return hashlib.sha256(text.encode("utf-8")).hexdigest()

def get(url, *, params=None, min_chars=1, tries=4):
    last = None
    for attempt in range(tries):
        try:
            r = S.get(url, params=params, timeout=TIMEOUT)
            r.raise_for_status()
            r.encoding = r.apparent_encoding or r.encoding or "utf-8"
            if len(r.text) < min_chars:
                raise RuntimeError(f"suspiciously short response ({len(r.text)} chars) from {r.url}")
            return r.text
        except Exception as exc:
            last = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"failed to fetch {url}: {last}")

def normalize_source(text):
    text = html.unescape(text).replace("\r\n", "\n").replace("\r", "\n")
    text = text.translate(DEV_DIGITS).translate(URDU_DIGITS)
    text = unicodedata.normalize("NFC", text).replace("\ufeff", "").replace("\u00ad", "")
    text = re.sub(r"[\t\v\f]+", " ", text)
    text = re.sub(r" +\n", "\n", text)
    return re.sub(r"\n{4,}", "\n\n\n", text).strip()

def paragraphs(text):
    text = normalize_source(text)
    blocks = [re.sub(r"\s*\n\s*", " ", b).strip() for b in re.split(r"\n\s*\n", text)]
    blocks = [b for b in blocks if b]
    if len(blocks) <= 2:
        lines = [x.strip() for x in text.splitlines() if x.strip()]
        if len(lines) > 5: blocks = lines
    return blocks

def easy_hindi(text):
    for old, new in HINDI_EASY_ITEMS: text = text.replace(old, new)
    return text

def strip_diacritics_ascii(text):
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    for a,b in {"’":"'","‘":"'","“":"\"","”":"\"","…":"...","।":".","॥":".","₹":"Rs.","•":"-"}.items(): text=text.replace(a,b)
    return text

def normalize_itrans_token(token):
    if token in ROMAN_EXACT: return ROMAN_EXACT[token]
    t=token
    for old,new in [("R^i","ri"),("R^I","ri"),("L^i","li"),("L^I","li"),("~N","n"),("~n","ny"),(".n","n"),(".m","n"),("M","n"),("Ch","chh"),("Sh","sh"),("Th","th"),("Dh","dh"),("T","t"),("D","d"),("N","n"),("A","aa"),("I","i"),("U","u"),("H","h")]: t=t.replace(old,new)
    t=t.replace("^","").replace("`","").replace("~","").replace(".","").lower()
    repairs={"apane":"apne","apana":"apna","apani":"apni","usane":"usne","isane":"isne","karane":"karne","rahane":"rehne","kahane":"kehne","kahata":"kehta","kahati":"kehti","kahate":"kehte","rahata":"rehta","rahati":"rehti","rahate":"rehte","chahie":"chahiye","achchhaa":"achchha","bhagavaan":"Bhagwan","isalie":"isliye","kyonki":"kyunki"}
    if t in repairs: return repairs[t]
    if len(t)>4 and t.endswith("a") and t not in SCHWA_KEEP and not t.endswith(("iya","aya","uya","ewa","owa")): t=t[:-1]
    return t

def romanize_devanagari(text):
    raw=transliterate(easy_hindi(text), sanscript.DEVANAGARI, sanscript.ITRANS)
    chunks=re.split(r"([A-Za-z~.^`]+)",raw)
    for i in range(1,len(chunks),2): chunks[i]=normalize_itrans_token(chunks[i])
    out=strip_diacritics_ascii("".join(chunks))
    out=re.sub(r"[ \t]+"," ",out)
    out=re.sub(r"\s+([,.;:!?])",r"\1",out)
    out=re.sub(r"([,.;:!?])([^\s\n\"'])",r"\1 \2",out)
    return out.strip()

def romanize_urdu_word(word):
    punct="،۔؟!؛:()[]{}\"'“”‘’ "
    bare=word.strip(punct)
    prefix=word[:len(word)-len(word.lstrip(punct))]
    suffix=word[len(word.rstrip(punct)):]
    if bare in URDU_WORDS: return prefix+URDU_WORDS[bare]+suffix
    out="".join(URDU_CHAR.get(ch,ch if ord(ch)<128 else "") for ch in bare)
    return prefix+re.sub(r"(.)\1{2,}",r"\1\1",out)+suffix

def romanize_urdu(text):
    out=[]
    for chunk in re.split(r"(\s+)",normalize_source(text)):
        out.append(chunk if chunk.isspace() or not URDU_RE.search(chunk) else romanize_urdu_word(chunk))
    text=strip_diacritics_ascii("".join(out))
    return re.sub(r"\s+([,.;:!?])",r"\1",re.sub(r"[ \t]+"," ",text)).strip()

def assert_roman(text,label):
    d,u=len(DEV_RE.findall(text)),len(URDU_RE.findall(text))
    if d or u: raise RuntimeError(f"{label}: residual Indic script, Devanagari={d}, Urdu={u}")

def write(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text.rstrip()+"\n",encoding="utf-8")

def natural_number(s):
    m=re.search(r"(\d{1,3})",s.translate(DEV_DIGITS))
    return int(m.group(1)) if m else 9999

def fetch_nirmala_wikisource():
    api="https://hi.wikisource.org/w/api.php"
    params={"action":"query","list":"allpages","apprefix":"निर्मला/","apnamespace":0,"aplimit":"max","format":"json","formatversion":2}
    data=json.loads(get(api,params=params,min_chars=50)); titles=[x["title"] for x in data.get("query",{}).get("allpages",[])]
    while "continue" in data:
        params.update(data["continue"]); data=json.loads(get(api,params=params,min_chars=50)); titles.extend(x["title"] for x in data.get("query",{}).get("allpages",[]))
    titles=sorted(set(titles),key=lambda x:(natural_number(x),x)); candidates=[t for t in titles if natural_number(t)<9999]
    chapters=[]
    for title in candidates:
        payload=json.loads(get(api,params={"action":"parse","page":title,"prop":"text","format":"json","formatversion":2},min_chars=100))
        soup=BeautifulSoup(payload.get("parse",{}).get("text",""),"html.parser")
        for tag in soup.select("script,style,table,nav,.mw-editsection,.navbox,.sistersitebox,sup.reference,.printfooter"): tag.decompose()
        pieces=[]; root=soup.select_one(".mw-parser-output") or soup
        for node in root.select("p,blockquote"):
            txt=" ".join(node.get_text(" ",strip=True).split())
            if not txt or txt in NAV_EXACT or any(txt.startswith(x) for x in ("यह पृष्ठ","विकिस्रोत से","पिछला","अगला")): continue
            pieces.append(txt)
        source="\n\n".join(pieces)
        if len(source)>=1500: chapters.append(Chapter(natural_number(title),"",title,source))
    if len(chapters)<20 or sum(len(c.text) for c in chapters)<180000: raise RuntimeError(f"Wikisource Nirmala incomplete: {len(chapters)} chapters, {sum(len(c.text) for c in chapters)} chars")
    chapters.sort(key=lambda c:c.number)
    return [Chapter(i,f"Adhyay {i}",c.source_id,c.text) for i,c in enumerate(chapters,1)]

def split_nirmala_ia(raw):
    text=normalize_source(raw)
    positions=[text.find(s) for s in ("यों तो बाबू उदयभानुलाल","यों तो बाबू उदयभानु","बाबू उदयभानुलाल") if text.find(s)>=0]
    if positions: text=text[min(positions):]
    matches=list(re.finditer(r"(?m)^\s*(?:अध्याय\s*)?(\d{1,2})\s*[.।:-]?\s*$",text)); chunks=[]
    if len(matches)>=20:
        for i,m in enumerate(matches):
            chunk=text[m.end():(matches[i+1].start() if i+1<len(matches) else len(text))].strip()
            if len(chunk)>1000: chunks.append(chunk)
    else:
        ps=paragraphs(text); target=max(8000,sum(map(len,ps))//30); cur=[]; count=0
        for p in ps:
            cur.append(p); count+=len(p)
            if count>=target: chunks.append("\n\n".join(cur)); cur=[]; count=0
        if cur: chunks.append("\n\n".join(cur))
    if len(chunks)<20 or sum(map(len,chunks))<180000: raise RuntimeError(f"IA Nirmala split incomplete: {len(chunks)} parts, {sum(map(len,chunks))} chars")
    return [Chapter(i,f"Adhyay {i}","IA:in.ernet.dli.2015.342406",t) for i,t in enumerate(chunks,1)]

def fetch_nirmala():
    try: return fetch_nirmala_wikisource(),"Hindi Wikisource chapter pages (MediaWiki API)"
    except Exception as first:
        url="https://archive.org/download/in.ernet.dli.2015.342406/2015.342406.Nirmala_djvu.txt"
        return split_nirmala_ia(get(url,min_chars=180000)),f"Internet Archive OCR fallback in.ernet.dli.2015.342406; Wikisource error: {first}"

def fetch_godaan():
    base="https://raw.githubusercontent.com/pandeyshikha1098/privacy_policy/45b42cf18333411f035757a9ecd8b6859fa84ae6/hindi-stories/storyBook/premchandra/godan/{:02d}.txt"
    chapters=[]
    for n in range(1,37):
        url=base.format(n); text=normalize_source(get(url,min_chars=3000))
        if len(DEV_RE.findall(text))<1000: raise RuntimeError(f"Godaan chapter {n} invalid: {url}")
        chapters.append(Chapter(n,f"Adhyay {n}",url,text))
    return chapters

def render_dev_work(work_id,title,author,chapters,source_note):
    out_root=ROOT/"works"/"premchand"/work_id; records=[]; ts=to=tsp=top=0
    for c in chapters:
        src_ps=paragraphs(c.text)
        if len(src_ps)<5: raise RuntimeError(f"{title} chapter {c.number}: only {len(src_ps)} paragraphs")
        rom_ps=[romanize_devanagari(p) for p in src_ps]; body="\n\n".join(rom_ps)
        md=f"# {title} — Adhyay {c.number}\n\n**{author}**\n\n{body}\n"; assert_roman(md,f"{title} chapter {c.number}")
        if len(body)<len(c.text)*.35: raise RuntimeError(f"{title} chapter {c.number}: output too short")
        write(out_root/"chapters"/f"{c.number:02d}.md",md)
        records.append({"chapter":c.number,"source_id":c.source_id,"source_chars":len(c.text),"source_paragraphs":len(src_ps),"output_chars":len(body),"output_paragraphs":len(rom_ps),"sha256_source":sha256(c.text),"sha256_output":sha256(body),"residual_devanagari":0,"residual_urdu":0})
        ts+=len(c.text); to+=len(body); tsp+=len(src_ps); top+=len(rom_ps)
    index=[f"# {title}\n\n**{author}**\n","## Adhyay"]+[f"- [Adhyay {c.number}](chapters/{c.number:02d}.md)" for c in chapters]
    write(out_root/"translation.md","\n".join(index))
    write(out_root/"source.md",f"# Locked Source Record — {title}\n\n- Author: {author}\n- Form: complete novel\n- Source method: {source_note}\n- Chapters retained: {len(chapters)}\n- Total cleaned source characters: {ts}\n- Source status: locked for machine-assisted first pass\n\nThe reader files preserve chapter order and every retained source paragraph. Website, scan, and repository boilerplate are excluded.\n")
    write(out_root/"NOTES.md",f"# Editorial Notes — {title}\n\n## Status\n\n- Complete ordered machine-assisted Roman-Hindustani first pass generated.\n- Roman-script validation passed.\n- Independent paragraph comparison and read-aloud review remain pending.\n- This is not marked publication-ready.\n\n## Method\n\nThe source was processed paragraph by paragraph. A controlled easy-Hindi replacement pass was applied before Roman transliteration. No paragraph was intentionally summarized or omitted. Long and bookish wording still needs human editorial refinement where automatic simplification could not safely preserve exact meaning.\n")
    mid=chapters[len(chapters)//2].number
    return {"id":f"premchand-{work_id}","title":title,"author":author,"form":"novel","chapter_count":len(chapters),"source_chars":ts,"output_chars":to,"source_paragraphs":tsp,"output_paragraphs":top,"roman_only":True,"records":records,"samples":{"opening":(out_root/"chapters"/"01.md").read_text(encoding="utf-8")[:800],"middle":(out_root/"chapters"/f"{mid:02d}.md").read_text(encoding="utf-8")[:800],"final":(out_root/"chapters"/f"{chapters[-1].number:02d}.md").read_text(encoding="utf-8")[-800:]}}

def fetch_urdu_mualla():
    errors=[]
    for ident in ("in.ernet.dli.2015.435597","urduemualla"):
        try:
            meta=json.loads(get(f"https://archive.org/metadata/{ident}",min_chars=100)); files=meta.get("files",[])
            candidates=[f for f in files if str(f.get("name","")).endswith("_djvu.txt") and int(f.get("size",0) or 0)>100000]
            if not candidates: raise RuntimeError("no substantial _djvu.txt")
            f=max(candidates,key=lambda x:int(x.get("size",0) or 0)); name=f["name"]
            url=f"https://archive.org/download/{ident}/{requests.utils.quote(name)}"
            return get(url,min_chars=100000),url,{"identifier":ident,"filename":name,"size":f.get("size"),"md5":f.get("md5"),"metadata":meta.get("metadata",{})}
        except Exception as exc: errors.append(f"{ident}: {exc}")
    raise RuntimeError("Urdu-e-Mualla unavailable: "+" | ".join(errors))

def clean_urdu_ocr(text):
    keep=[]
    for line in normalize_source(text).splitlines():
        s=" ".join(line.split()); low=s.lower()
        if any(x in low for x in ("digital library of india","archive.org","scanned by","generated by")) or re.fullmatch(r"[-_=* .]{4,}",s or " "): continue
        keep.append(s)
    return re.sub(r"\n{4,}","\n\n\n","\n".join(keep)).strip()

def split_safe_parts(ps,target=18000):
    parts=[]; cur=[]; n=0
    for p in ps:
        cur.append(p); n+=len(p); boundary=bool(re.search(r"(?:فقط|غالب|اسد|والسلام|دعاگو|مخلص)\s*[۔.!]?$",p))
        if n>=target and (boundary or n>=int(target*1.35)): parts.append(cur); cur=[]; n=0
    if cur: parts.append(cur)
    return parts

def render_urdu_mualla():
    raw,url,meta=fetch_urdu_mualla(); cleaned=clean_urdu_ocr(raw)
    if len(cleaned)<100000 or len(URDU_RE.findall(cleaned))<50000: raise RuntimeError("Urdu-e-Mualla OCR suspicious")
    ps=paragraphs(cleaned); parts=split_safe_parts(ps)
    if len(parts)<8: raise RuntimeError(f"Urdu-e-Mualla only {len(parts)} parts")
    root=ROOT/"works"/"ghalib"/"urdu-e-mualla"; records=[]; total=0
    for i,src in enumerate(parts,1):
        rom=[romanize_urdu(p) for p in src]; body="\n\n".join(rom); md=f"# Urdu-e-Mualla — Hissa {i}\n\n**Mirza Ghalib**\n\n{body}\n"; assert_roman(md,f"Urdu-e-Mualla {i}"); write(root/"parts"/f"{i:02d}.md",md)
        records.append({"part":i,"source_chars":sum(map(len,src)),"source_paragraphs":len(src),"output_chars":len(body),"output_paragraphs":len(rom),"sha256_output":sha256(body),"residual_urdu":0,"residual_devanagari":0}); total+=len(body)
    write(root/"translation.md","\n".join(["# Urdu-e-Mualla","","**Mirza Ghalib**","","## Hisse"]+[f"- [Hissa {i}](parts/{i:02d}.md)" for i in range(1,len(parts)+1)]))
    m=meta.get("metadata",{})
    write(root/"source.md",f"# Locked Source Record — Urdu-e-Mualla\n\n- Author: Mirza Ghalib\n- Internet Archive identifier: `{meta['identifier']}`\n- OCR file: `{meta['filename']}`\n- OCR file size: {meta.get('size')} bytes\n- OCR MD5: `{meta.get('md5')}`\n- Recorded title: {m.get('title')}\n- Recorded date: {m.get('date')}\n- Source URL: {url}\n- Cleaned OCR characters retained: {len(cleaned)}\n- Ordered reader parts: {len(parts)}\n\nThis is a complete recoverable OCR-based first pass. The old scan itself must be compared page by page before publication. Uncertain OCR was preserved rather than silently invented or deleted.\n")
    write(root/"NOTES.md","# Editorial Notes — Urdu-e-Mualla\n\n## Status\n\n- OCR-machine-assisted complete ordered first pass generated.\n- Reader parts contain Roman script only.\n- Human comparison against page images is pending.\n- Not publication-ready.\n\n## Important limitation\n\nUrdu normally omits many short vowels, and the source OCR contains recognition errors. A controlled high-frequency word map was used, with conservative character-level transliteration for unknown words. Unknown or damaged wording was not creatively reconstructed. Human Urdu review is essential.\n")
    mid=(len(parts)+1)//2
    return {"id":"ghalib-urdu-e-mualla","title":"Urdu-e-Mualla","author":"Mirza Ghalib","form":"letters_collection","part_count":len(parts),"source_chars":len(cleaned),"source_paragraphs":len(ps),"output_chars":total,"roman_only":True,"records":records,"samples":{"opening":(root/"parts"/"01.md").read_text(encoding="utf-8")[:800],"middle":(root/"parts"/f"{mid:02d}.md").read_text(encoding="utf-8")[:800],"final":(root/"parts"/f"{len(parts):02d}.md").read_text(encoding="utf-8")[-800:]}}

def qa_markdown(items):
    lines=["# Long Classics QA","","These files are complete machine-assisted first passes. They remain human-review pending.","","| Work | Units | Source chars | Output chars | Source paras | Roman only |","|---|---:|---:|---:|---:|---|"]
    for x in items: lines.append(f"| {x['title']} | {x.get('chapter_count',x.get('part_count'))} | {x['source_chars']} | {x['output_chars']} | {x['source_paragraphs']} | yes |")
    for x in items:
        lines += ["",f"## {x['title']}","",f"- ID: `{x['id']}`","- Roman-only validation: passed","- Independent human source comparison: pending","","### Opening sample","","```text",x['samples']['opening'],"```","","### Middle sample","","```text",x['samples']['middle'],"```","","### Final sample","","```text",x['samples']['final'],"```"]
    return "\n".join(lines)

def main():
    ROOT.mkdir(parents=True,exist_ok=True); items=[]
    nirmala,nsource=fetch_nirmala(); items.append(render_dev_work("nirmala","Nirmala","Munshi Premchand",nirmala,nsource))
    items.append(render_dev_work("godaan","Godaan","Munshi Premchand",fetch_godaan(),"Pinned public GitHub transcription, 36 chapter files at commit 45b42cf18333411f035757a9ecd8b6859fa84ae6"))
    items.append(render_urdu_mualla()); write(ROOT/"QA.md",qa_markdown(items))
    manifest={"project":"easy-roman-hindustani-classics-long-build","generated_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"works":[{"id":x['id'],"title":x['title'],"author":x['author'],"form":x['form'],"translation_status":"ocr_machine_assisted_complete_first_pass" if x['id']=="ghalib-urdu-e-mualla" else "machine_assisted_complete_first_pass","human_review":"pending","repository_transfer":"generated_runner_branch","unit_count":x.get('chapter_count',x.get('part_count')),"source_chars":x['source_chars'],"output_chars":x['output_chars'],"roman_only":True} for x in items]}
    write(ROOT/"manifest-fragment.json",json.dumps(manifest,ensure_ascii=False,indent=2)); print(json.dumps(manifest,ensure_ascii=False,indent=2))

if __name__=="__main__":
    try: main()
    except Exception as exc:
        print(f"BUILD FAILED: {type(exc).__name__}: {exc}",file=sys.stderr); raise
