#!/usr/bin/env python3
"""Build complete machine-assisted Roman-Hindustani first passes.

The pipeline preserves every source paragraph and only performs script conversion,
controlled vocabulary simplification, punctuation cleanup, and chapter/part packaging.
It does not summarize or abridge. All outputs remain human_review: pending.
"""
from __future__ import annotations

import html
import json
import re
import sys
import time
import unicodedata
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Sequence
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

OUT = Path("generated")
WORKS = OUT / "works"
LOGS = OUT / "logs"
UA = "SWR-easy-roman-hindustani-public-domain-builder/2.0 (+editorial accessibility project)"
S = requests.Session()
S.headers.update({"User-Agent": UA, "Accept-Language": "hi,en;q=0.8,ur;q=0.7"})
DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
URDU_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")

HINDI_EASY = {
"किन्तु":"लेकिन","किंतु":"लेकिन","परन्तु":"लेकिन","परंतु":"लेकिन","तथापि":"फिर भी","अतः":"इसलिए","अतएव":"इसलिए","प्रातःकाल":"सुबह","प्रातः":"सुबह","सायंकाल":"शाम","सन्ध्या":"शाम","संध्या":"शाम","रात्रि":"रात","निशा":"रात","दिवस":"दिन","भोजन":"खाना","जलपान":"कुछ खाना","आहार":"खाना","निवास":"घर","गृह":"घर","गृहस्थी":"घर-परिवार","मुखमण्डल":"चेहरा","मुखमंडल":"चेहरा","मुख":"मुँह","नेत्र":"आँख","नयन":"आँख","लोचन":"आँख","दृष्टि":"नज़र","हृदय":"दिल","अन्तःकरण":"मन","अंतःकरण":"मन","मस्तिष्क":"दिमाग","क्रोध":"गुस्सा","कुपित":"गुस्से में","प्रसन्न":"खुश","आनन्द":"खुशी","आनंद":"खुशी","विषाद":"उदासी","सन्ताप":"दुख","संताप":"दुख","वेदना":"दर्द","पीड़ा":"दर्द","सहायता":"मदद","आवश्यक":"ज़रूरी","अत्यावश्यक":"बहुत ज़रूरी","व्यवस्था":"इंतज़ाम","प्रबन्ध":"इंतज़ाम","प्रबंध":"इंतज़ाम","उद्देश्य":"मकसद","प्रयोजन":"मकसद","विचार":"सोच","चिन्तन":"सोच","चिंतन":"सोच","इच्छा":"चाह","अभिलाषा":"चाह","कामना":"चाह","व्यर्थ":"बेकार","निरर्थक":"बेकार","प्रतीत":"लगा","विदित":"पता","ज्ञात":"पता","अज्ञात":"अनजान","शीघ्र":"जल्दी","तुरन्त":"तुरंत","तत्काल":"तुरंत","उत्तर":"जवाब","प्रश्न":"सवाल","सम्भव":"मुमकिन","संभव":"मुमकिन","असम्भव":"नामुमकिन","असंभव":"नामुमकिन","निश्चय":"फैसला","निर्णय":"फैसला","आरम्भ":"शुरू","आरंभ":"शुरू","समाप्त":"खत्म","समीप":"पास","निकट":"पास","भय":"डर","भीति":"डर","आश्चर्य":"हैरानी","विस्मय":"हैरानी","इत्यादि":"वगैरह","पुनः":"फिर","कदापि":"कभी नहीं","अत्यन्त":"बहुत","अत्यंत":"बहुत","विशाल":"बहुत बड़ा","अल्प":"कम","अधिक":"ज़्यादा","निरन्तर":"लगातार","निरंतर":"लगातार","सदैव":"हमेशा","सर्वदा":"हमेशा","कदाचित":"शायद","स्त्री":"औरत","पुरुष":"आदमी","बालक":"लड़का","बालिका":"लड़की","शिशु":"बच्चा","सन्तान":"बच्चा","संतान":"बच्चा","पुत्र":"बेटा","पुत्री":"बेटी","माता":"माँ","जननी":"माँ","पिता":"पिता","भ्राता":"भाई","दुर्भाग्य":"बदकिस्मती","सौभाग्य":"अच्छी किस्मत","दुर्भाग्यवश":"बदकिस्मती से","कारण":"वजह","परिणाम":"नतीजा","समाचार":"खबर","सूचना":"खबर","अनुमति":"इजाज़त","निवेदन":"बिनती","अनुरोध":"बिनती","आज्ञा":"हुक्म","निर्देश":"हुक्म","अवकाश":"फुर्सत","प्रयत्न":"कोशिश","प्रयास":"कोशिश","सफल":"कामयाब","असफल":"नाकाम","लज्जा":"शर्म","ग्लानि":"पछतावा","स्वर":"आवाज़","कण्ठ":"गला","कंठ":"गला","मौन":"चुप","निःशब्द":"चुप","वार्तालाप":"बातचीत","संवाद":"बातचीत","मार्ग":"रास्ता","पथ":"रास्ता","गमन":"जाना","प्रस्थान":"रवाना होना","आगमन":"आना","वस्त्र":"कपड़े","परिधान":"कपड़े","आभूषण":"गहने","औषधि":"दवा","चिकित्सक":"डॉक्टर","वैद्य":"डॉक्टर","विद्यालय":"स्कूल","अध्यापक":"टीचर","कार्यालय":"दफ्तर","न्यायालय":"अदालत","धन":"पैसा","राशि":"पैसा","निर्धन":"गरीब","दरिद्र":"गरीब","समृद्ध":"अमीर","दीन":"बेचारा","कठिन":"मुश्किल","सरल":"आसान","उचित":"ठीक","अनुचित":"गलत","विशेष":"खास","साधारण":"आम","प्रकार":"तरह","भाँति":"तरह","भांति":"तरह","क्षण":"पल","क्षणभर":"एक पल","दीर्घ":"लंबा","पूर्व":"पहले","पश्चात्":"बाद","पश्चात":"बाद","अनन्तर":"बाद","अबोध":"नासमझ","बुद्धि":"अकल","चतुर":"होशियार","मूर्ख":"बेवकूफ","मूढ":"बेवकूफ","सन्देह":"शक","संदेह":"शक","विश्वास":"यकीन","आशा":"उम्मीद","निराशा":"मायूसी","सम्मान":"इज़्ज़त","अपमान":"बेइज़्ज़ती","कष्ट":"तकलीफ","यातना":"तकलीफ","प्रेम":"प्यार","स्नेह":"प्यार","घृणा":"नफरत","द्वेष":"नफरत","लाभ":"फायदा","हानि":"नुकसान","सम्पूर्ण":"पूरा","संपूर्ण":"पूरा","प्रत्येक":"हर","समस्त":"सब","वर्तमान":"अभी","भविष्य":"आने वाला समय","अतीत":"बीता समय","कर्तव्य":"फर्ज़","कर्त्तव्य":"फर्ज़","अपराध":"जुर्म","दण्ड":"सज़ा","दंड":"सज़ा","विवाह":"शादी","वधू":"दुल्हन","वर":"दूल्हा","संबंध":"रिश्ता","सम्बन्ध":"रिश्ता","मित्र":"दोस्त","शत्रु":"दुश्मन","प्राण":"जान","मृत्यु":"मौत","देहान्त":"मौत","देहांत":"मौत","जीवित":"ज़िंदा","मृत":"मरा हुआ","अश्रु":"आँसू","आलिंगन":"गले लगाना","चुम्बन":"चूमना","चुंबन":"चूमना","प्रतीक्षा":"इंतज़ार","स्मरण":"याद","विस्मृत":"भूला","आशंका":"डर","शंका":"शक","विवश":"मजबूर","संकट":"मुसीबत","विपत्ति":"मुसीबत","प्रसंग":"बात","घटना":"बात","चरित्र":"स्वभाव","स्वभावतः":"अपनी आदत से","वास्तव में":"सच में","वस्तुतः":"असल में","संभवतः":"शायद","निःसन्देह":"बेशक","निस्सन्देह":"बेशक","निःसंदेह":"बेशक","अवश्य":"ज़रूर","केवल":"सिर्फ","कदाचित्":"शायद","यद्यपि":"हालाँकि","अर्थात्":"यानी","अर्थात":"यानी","अपितु":"बल्कि","परिस्थिति":"हाल","दशा":"हाल","स्थिति":"हाल","उपेक्षा":"ध्यान न देना","तिरस्कार":"बेइज़्ज़ती","सहानुभूति":"हमदर्दी","करुणा":"दया","दयनीय":"बेचारा","प्रचण्ड":"बहुत तेज़","प्रचंड":"बहुत तेज़","मधुर":"मीठा","कटु":"कड़वा","कर्कश":"कड़वा","शान्त":"शांत","व्याकुल":"बेचैन","उत्सुक":"बेकरार","गम्भीर":"गंभीर","साहस":"हिम्मत","धैर्य":"सब्र","सन्तोष":"संतोष","परिश्रम":"मेहनत","श्रम":"मेहनत","परिश्रमी":"मेहनती","आलसी":"कामचोर","व्यवहार":"बर्ताव","आचरण":"बर्ताव","विनय":"नर्मी","विनम्र":"नरम","निर्दयी":"बेदर्द","क्रूर":"बेदर्द","प्रतिज्ञा":"कसम","शपथ":"कसम","उल्लास":"खुशी","उत्सव":"जश्न","समारोह":"जश्न","प्रसव":"बच्चा पैदा होना","गर्भ":"पेट में बच्चा","रोग":"बीमारी","स्वास्थ्य":"सेहत","उपचार":"इलाज","परामर्श":"सलाह","सुझाव":"सलाह","निर्वाह":"गुज़ारा","जीविका":"रोज़ी","वेतन":"तनख्वाह","ऋण":"कर्ज़","कर्ज":"कर्ज़","मूल्य":"कीमत","व्यय":"खर्च","आय":"कमाई","सम्पत्ति":"जायदाद","संपत्ति":"जायदाद","भूमि":"ज़मीन","कृषक":"किसान","सेवक":"नौकर","स्वामी":"मालिक","अधिकारी":"अफसर","कर्मचारी":"काम करने वाला","पुलिसकर्मी":"पुलिस वाला","पत्र":"चिट्ठी","सन्देश":"पैगाम","संदेश":"पैगाम","उदाहरण":"मिसाल","प्रमाण":"सबूत","साक्षी":"गवाह","विवाद":"झगड़ा","कलह":"झगड़ा","विरोध":"खिलाफ़ होना","विद्रोह":"बगावत","युद्ध":"लड़ाई","संग्राम":"लड़ाई"}

ROMAN_FIXES = [(r"\bhaiM\b","hain"),(r"\bhUM\b","hoon"),(r"\bnahIM\b","nahin"),(r"\bmaiM\b","main"),(r"\bmeM\b","mein"),(r"\bkyoM\b","kyon"),(r"\bkyA\b","kya"),(r"\byaha\b","yeh"),(r"\bvaha\b","woh"),(r"\byah\b","yeh"),(r"\bvah\b","woh"),(r"\baura\b","aur"),(r"\blekina\b","lekin"),(r"\bagara\b","agar"),(r"\bphira\b","phir"),(r"\beka\b","ek"),(r"\bkucha\b","kuchh"),(r"\bsaba\b","sab"),(r"\bghara\b","ghar"),(r"\bdila\b","dil"),(r"\bdina\b","din"),(r"\bbaata\b","baat"),(r"\bhaatha\b","haath"),(r"\bpaira\b","pair"),(r"\bmuMha\b","munh"),(r"\bmujheM\b","mujhe"),(r"\btumheM\b","tumhe"),(r"\bunheM\b","unhein"),(r"\binheM\b","inhein"),(r"\byahaaM\b","yahan"),(r"\bvahaaM\b","wahan"),(r"\bkahaaM\b","kahan"),(r"\bkauna\b","kaun"),(r"\baba\b","ab"),(r"\btaba\b","tab"),(r"\bjaba\b","jab"),(r"\bkaba\b","kab"),(r"\btuma\b","tum"),(r"\bhama\b","hum"),(r"\bApa\b","aap"),(r"\bkara\b","kar"),(r"\bpara\b","par"),(r"\bisa\b","is"),(r"\busa\b","us")]

URDU_COMMON = {"اور":"aur","ہے":"hai","ہیں":"hain","تھا":"tha","تھی":"thi","تھے":"the","ہوں":"hoon","نہیں":"nahin","میں":"mein","سے":"se","کو":"ko","کا":"ka","کی":"ki","کے":"ke","نے":"ne","یہ":"yeh","وہ":"woh","جو":"jo","کہ":"ki","اگر":"agar","مگر":"magar","لیکن":"lekin","پھر":"phir","اب":"ab","تب":"tab","جب":"jab","کب":"kab","کیوں":"kyon","کیا":"kya","کون":"kaun","کہاں":"kahan","یہاں":"yahan","وہاں":"wahan","بھی":"bhi","ہی":"hi","ایک":"ek","دو":"do","تین":"teen","سب":"sab","کچھ":"kuchh","کوئی":"koi","اپنے":"apne","اپنی":"apni","اپنا":"apna","اس":"is","اسے":"use","ان":"un","انہیں":"unhein","ہم":"hum","ہمیں":"humein","تم":"tum","تمہیں":"tumhe","آپ":"aap","مجھے":"mujhe","میرا":"mera","میری":"meri","میرے":"mere","تیرا":"tera","تیری":"teri","آدمی":"aadmi","انسان":"insaan","عورت":"aurat","لڑکا":"ladka","لڑکی":"ladki","بچہ":"bachcha","بچے":"bachche","ماں":"maa","باپ":"baap","بھائی":"bhai","بہن":"behen","گھر":"ghar","دل":"dil","بات":"baat","دن":"din","رات":"raat","وقت":"waqt","سال":"saal","زندگی":"zindagi","موت":"maut","خدا":"Khuda","اللہ":"Allah","صاحب":"sahib","جناب":"janab","خط":"khat","چٹھی":"chitthi","جواب":"jawab","خبر":"khabar","نام":"naam","کام":"kaam","پیسہ":"paisa","روپیہ":"rupiya","بہت":"bahut","زیادہ":"zyada","کم":"kam","اچھا":"achchha","اچھی":"achchhi","برا":"bura","بڑی":"badi","بڑا":"bada","چھوٹا":"chhota","نیا":"naya","پرانا":"purana","خوش":"khush","غم":"gham","درد":"dard","محبت":"mohabbat","پیار":"pyaar","نفرت":"nafrat","ڈر":"dar","خوف":"dar","غصہ":"gussa","فکر":"fikr","خیال":"khayal","سوچ":"soch","سوال":"sawal","ضروری":"zaroori","مدد":"madad","آیا":"aaya","آئی":"aayi","آئے":"aaye","گیا":"gaya","گئی":"gayi","گئے":"gaye","دیا":"diya","دی":"di","دئے":"diye","لیا":"liya","لی":"li","لئے":"liye","کہا":"kaha","کہتی":"kehti","کہتے":"kehte","بولا":"bola","بولی":"boli","دیکھا":"dekha","دیکھی":"dekhi","دیکھتے":"dekhte","سنا":"suna","پوچھا":"poochha","چلا":"chala","چلی":"chali","چلے":"chale","رہا":"raha","رہی":"rahi","رہے":"rahe","رکھا":"rakha","کر":"kar","کرتا":"karta","کرتی":"karti","کرتے":"karte","کرنا":"karna","ہونا":"hona","جانا":"jana","آنا":"aana","دینا":"dena","لینا":"lena","دیکھنا":"dekhna","لکھا":"likha","لکھتے":"likhte","پڑھا":"padha","پڑھتے":"padhte","سمجھا":"samjha","سمجھ":"samajh","مرزا":"Mirza","غالب":"Ghalib","اردو":"Urdu","دہلی":"Dilli","دلی":"Dilli"}
URDU_CHARS = {"ا":"a","آ":"aa","أ":"a","إ":"i","ب":"b","پ":"p","ت":"t","ٹ":"t","ث":"s","ج":"j","چ":"ch","ح":"h","خ":"kh","د":"d","ڈ":"d","ذ":"z","ر":"r","ڑ":"r","ز":"z","ژ":"zh","س":"s","ش":"sh","ص":"s","ض":"z","ط":"t","ظ":"z","ع":"","غ":"gh","ف":"f","ق":"q","ک":"k","ك":"k","گ":"g","ل":"l","م":"m","ن":"n","ں":"n","و":"o","ؤ":"o","ہ":"h","ھ":"h","ۃ":"h","ة":"h","ی":"i","ي":"i","ے":"e","ئ":"i","ء":"","ۂ":"e","ۓ":"e","َ":"a","ِ":"i","ُ":"u","ّ":"","ْ":"","ٰ":"aa","ٔ":"","ٓ":"","ـ":""}
NOISE = ["join rekhta","log in","register","synopsis","recitations","tagged under","more by","source :","download","favorite","read now","book information","rekhta foundation","privacy policy","terms of use","about us","contact us","this content is only available","videos","collections","short stories of"]
MANTO = [("toba-tek-singh","Toba Tek Singh","toba-tek-singh-saadat-hasan-manto-stories",2500),("khol-do","Khol Do","khol-do-saadat-hasan-manto-stories",1800),("thanda-gosht","Thanda Gosht","thanda-gosht-saadat-hasan-manto-stories",2500),("bu","Bu","boo-saadat-hasan-manto-stories",3500),("kali-shalwar","Kali Shalwar","kaali-shalwaar-saadat-hasan-manto-stories",7000),("hatak","Hatak","hatak-saadat-hasan-manto-stories",5000),("naya-qanoon","Naya Qanoon","nayaa-qanoon-saadat-hasan-manto-stories",5000),("tetwal-ka-kutta","Tetwal Ka Kutta","tetwaal-ka-kutta-saadat-hasan-manto-stories",3500)]

@dataclass
class QA:
    id: str; title: str; author: str; units: int; source_chars: int; output_chars: int
    devanagari_remaining: int; urdu_remaining: int; roman_only: bool; status: str; notes: str = ""

def get(url, min_chars=1, retries=4):
    last=None
    for attempt in range(retries):
        try:
            r=S.get(url,timeout=60); r.raise_for_status()
            if len(r.text)<min_chars: raise RuntimeError(f"short response {len(r.text)}")
            return r.text
        except Exception as exc:
            last=exc; time.sleep(2**attempt)
    raise RuntimeError(f"download failed {url}: {last}")

def normalize_source(text):
    text=html.unescape(text).replace("\ufeff","").replace("\u200b","")
    text=text.translate(DEV_DIGITS).translate(URDU_DIGITS); text=unicodedata.normalize("NFC",text)
    text=re.sub(r"[\t\r ]+"," ",text); text=re.sub(r" *\n *","\n",text); text=re.sub(r"\n{3,}","\n\n",text)
    return text.strip()

def replace_words(text,mapping):
    for old in sorted(mapping,key=len,reverse=True):
        text=re.sub(rf"(?<![\w\u0900-\u097f\u0600-\u06ff]){re.escape(old)}(?![\w\u0900-\u097f\u0600-\u06ff])",mapping[old],text)
    return text

def devanagari_to_roman(text):
    out=transliterate(replace_words(normalize_source(text),HINDI_EASY),sanscript.DEVANAGARI,sanscript.ITRANS)
    for a,b in [("RRi","ri"),("RRI","ree"),("LLi","li"),("LLI","lee"),("~N","n"),("~n","n"),("JN","gy"),("j~n","gy"),("Ch","chh"),("Sh","sh"),("Th","th"),("Dh","dh"),("T","t"),("D","d"),("N","n"),("A","aa"),("I","ee"),("U","oo"),("M","n"),("H","h"),(".n","n"),(".m","n"),(".a",""),("|",".")]: out=out.replace(a,b)
    for p,r in ROMAN_FIXES: out=re.sub(p,r,out)
    def clean(m):
        w=m.group(0)
        if len(w)>=4 and w.lower() not in {"rama","sita","gaya","diya","liya","naya","maya"}:
            w=re.sub(r"([bcdfghjklmnpqrstvwxyz])a([nrlv])aa$",r"\1\2a",w,flags=re.I)
            if re.search(r"[bcdfghjklmnpqrstvwxyz]a$",w,re.I) and not w.lower().endswith("aa"): w=w[:-1]
        return w
    out=re.sub(r"[A-Za-z][A-Za-z'.-]*",clean,out)
    out=re.sub(r"\s+([,.;:!?])",r"\1",out); out=re.sub(r"([,.;:!?])(?=[A-Za-z])",r"\1 ",out)
    out=re.sub(r"[ \t]+"," ",out); out=re.sub(r" *\n *","\n",out); out=re.sub(r"\n{3,}","\n\n",out)
    for old,new in {"nahi":"nahin","kyonki":"kyunki","acchha":"achchha","accha":"achchha","chahie":"chahiye","zamin":"zameen","jamin":"zameen","adami":"aadmi","insana":"insaan","bhagavan":"Bhagwan","vahan":"wahan"}.items(): out=re.sub(rf"\b{old}\b",new,out,flags=re.I)
    return out.strip()

def urdu_word(word):
    if word in URDU_COMMON:return URDU_COMMON[word]
    lead=re.match(r"^[^\u0600-\u06ff]*",word).group(0); trail=re.search(r"[^\u0600-\u06ff]*$",word).group(0)
    core=word[len(lead):len(word)-len(trail) if trail else None]
    if core in URDU_COMMON:return lead+URDU_COMMON[core]+trail
    return lead+"".join(URDU_CHARS.get(ch,ch if ord(ch)<128 else "") for ch in core)+trail

def urdu_to_roman(text):
    text=normalize_source(text)
    for old in sorted(URDU_COMMON,key=len,reverse=True):
        if " " in old:text=text.replace(old,URDU_COMMON[old])
    out="".join(p if p.isspace() else urdu_word(p) for p in re.split(r"(\s+)",text))
    return re.sub(r"\n{3,}","\n\n",re.sub(r"[ \t]+"," ",out)).strip()

def dev_count(t):return len(re.findall(r"[\u0900-\u097f]",t))
def urdu_count(t):return len(re.findall(r"[\u0600-\u06ff]",t))
def write(path,text):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text.rstrip()+"\n",encoding="utf-8")
def natural_number(title):
    m=re.search(r"(\d+)\s*$",title.translate(DEV_DIGITS));return int(m.group(1)) if m else 9999

def fetch_wikisource_pages(category,prefix):
    titles=[];cont=None
    while True:
        params={"action":"query","list":"categorymembers","cmtitle":f"Category:{category}","cmnamespace":"0","cmlimit":"500","format":"json","formatversion":"2"}
        if cont:params["cmcontinue"]=cont
        d=S.get("https://hi.wikisource.org/w/api.php",params=params,timeout=60).json();titles += [x["title"] for x in d["query"]["categorymembers"] if x["title"].startswith(prefix+"/")]
        cont=d.get("continue",{}).get("cmcontinue")
        if not cont:break
    pages=[]
    for title in sorted(set(titles),key=natural_number):
        r=S.get("https://hi.wikisource.org/w/api.php",params={"action":"parse","page":title,"prop":"text","format":"json","formatversion":"2"},timeout=60);r.raise_for_status()
        soup=BeautifulSoup(r.json()["parse"]["text"],"html.parser")
        for tag in soup.select(".mw-editsection,style,script,table,.noprint,.ws-noexport"):tag.decompose()
        lines=[]
        for ln in normalize_source(soup.get_text("\n")).splitlines():
            ln=ln.strip()
            if not ln:
                if lines and lines[-1]!="":lines.append("")
            elif ln not in {"पिछला पृष्ठ","अगला पृष्ठ","विषयसूची","निर्मला"} and not re.fullmatch(r"[\d ]+",ln):lines.append(ln)
        text="\n".join(lines).strip()
        if len(text)<1500:raise RuntimeError(f"Wikisource chapter too short {title}: {len(text)}")
        pages.append((natural_number(title),title,text));time.sleep(.15)
    return pages

def build_nirmala():
    pages=fetch_wikisource_pages("निर्मला","निर्मला")
    if len(pages)!=24:raise RuntimeError(f"Nirmala expected 24 chapters, got {len(pages)}")
    root=WORKS/"premchand"/"nirmala";sc=oc=0
    for n,t,src in pages:
        sc+=len(src);rom=devanagari_to_roman(src);oc+=len(rom);write(root/"chapters"/f"{n:02d}.md",f"# Nirmala — Adhyay {n}\n\n**Munshi Premchand**\n\n{rom}")
    write(root/"source.md","# Locked Source Record — Nirmala\n\n- Author: Munshi Premchand\n- Complete novel: 24 chapters\n- Base text: Hindi Wikisource category `Nirmala`; chapter pages 1–24 fetched through the MediaWiki API.\n- Source status: locked for this machine-assisted first pass.\n\nSite navigation and scan furniture are excluded. No modern translation is used.\n")
    write(root/"NOTES.md","# Editorial Notes — Nirmala\n\nThe complete 24-chapter sequence is retained. This is a deterministic machine-assisted accessibility first pass, not a summary. It needs independent paragraph comparison, terminology review, and read-aloud review.\n\nStatus: `machine_assisted_complete_first_pass`; `human_review: pending`.\n")
    combined="".join(p.read_text() for p in sorted((root/"chapters").glob("*.md")));return QA("premchand-nirmala","Nirmala","Premchand",24,sc,oc,dev_count(combined),urdu_count(combined),dev_count(combined)==0 and urdu_count(combined)==0,"machine_assisted_complete_first_pass")

def build_godaan():
    root=WORKS/"premchand"/"godaan";base="https://raw.githubusercontent.com/pandeyshikha1098/privacy_policy/45b42cf18333411f035757a9ecd8b6859fa84ae6/hindi-stories/storyBook/premchandra/godan";sc=oc=0
    for n in range(1,37):
        src=normalize_source(get(f"{base}/{n:02d}.txt",5000));sc+=len(src);rom=devanagari_to_roman(src);oc+=len(rom);write(root/"chapters"/f"{n:02d}.md",f"# Godaan — Adhyay {n}\n\n**Munshi Premchand**\n\n{rom}")
    write(root/"source.md","# Locked Source Record — Godaan\n\n- Author: Munshi Premchand\n- Complete novel: 36 chapters\n- Source repository: `pandeyshikha1098/privacy_policy`\n- Immutable commit: `45b42cf18333411f035757a9ecd8b6859fa84ae6`\n- Files: `godan/01.txt` through `36.txt`.\n")
    write(root/"NOTES.md","# Editorial Notes — Godaan\n\nAll 36 source chapters are retained in order. This is a machine-assisted accessibility first pass and needs full human source comparison, terminology review, and read-aloud review.\n\nStatus: `machine_assisted_complete_first_pass`; `human_review: pending`.\n")
    combined="".join(p.read_text() for p in sorted((root/"chapters").glob("*.md")));return QA("premchand-godaan","Godaan","Premchand",36,sc,oc,dev_count(combined),urdu_count(combined),dev_count(combined)==0 and urdu_count(combined)==0,"machine_assisted_complete_first_pass")

def leaf_blocks(soup):
    out=[]
    for node in soup.find_all(string=True):
        if node.parent and node.parent.name in {"script","style","noscript","svg"}:continue
        t=normalize_source(str(node));low=t.lower()
        if dev_count(t)>=8 and len(t)>20 and not any(x in low for x in NOISE):out.append(t)
    seen=set();return [x for x in out if not (re.sub(r"\s+"," ",x) in seen or seen.add(re.sub(r"\s+"," ",x)))]

def extract_rekhta(url,title,min_chars):
    raw=get(url,3000);soup=BeautifulSoup(raw,"html.parser");cands=[]
    for sel in ["#storyContent","#readContent",".story-content",".storyPageContent",".contentBody","article","main"]:
        for tag in soup.select(sel):cands.append("\n\n".join(leaf_blocks(BeautifulSoup(str(tag),"html.parser"))))
    cands.append("\n\n".join(leaf_blocks(soup)));cands=[normalize_source(x) for x in cands if len(x)>=min_chars]
    if not cands:write(LOGS/(re.sub(r"[^a-z0-9]+","-",title.lower())+".html"),raw);raise RuntimeError(f"Rekhta extraction too short: {title}")
    src=max(cands,key=len);lines=[]
    for s in src.splitlines():
        s=s.strip();low=s.lower()
        if not s:
            if lines and lines[-1]!="":lines.append("")
        elif not any(x in low for x in NOISE) and low not in {title.lower(),"saadat hasan manto","सआदत हसन मंटो","सआदत हसन मन्टो"}:lines.append(s)
    src="\n".join(lines).strip()
    if len(src)<min_chars or dev_count(src)<min_chars//3:raise RuntimeError(f"Rekhta extraction too short after cleanup: {title}: {len(src)}")
    return src,url

def build_manto():
    q=[]
    for wid,title,slug,minc in MANTO:
        src,url=extract_rekhta(f"https://www.rekhta.org/stories/{slug}?lang=hi",title,minc);rom=devanagari_to_roman(src);root=WORKS/"manto"/wid
        write(root/"translation.md",f"# {title}\n\n**Saadat Hasan Manto**\n\n{rom}")
        write(root/"source.md",f"# Locked Source Record — {title}\n\n- Author: Saadat Hasan Manto\n- Complete short story\n- Base author-text page: `{url}`\n- Synopsis, navigation, recordings, tags, account prompts, and branding excluded.\n")
        write(root/"NOTES.md",f"# Editorial Notes — {title}\n\nThe full extracted story sequence is retained. Manto's directness, satire, violence, sexuality, class signals, repetitions, and ending must not be softened in human review.\n\nStatus: `machine_assisted_complete_first_pass`; `human_review: pending`.\n")
        q.append(QA(f"manto-{wid}",title,"Saadat Hasan Manto",1,len(src),len(rom),dev_count(rom),urdu_count(rom),dev_count(rom)==0 and urdu_count(rom)==0,"machine_assisted_complete_first_pass"))
    return q

def fetch_urdu():
    d=json.loads(get("https://archive.org/metadata/urduemualla",10));files=d.get("files",[]);names=[f.get("name","") for f in files];pref=[n for n in names if n.endswith("_djvu.txt")]+[n for n in names if n.endswith(".txt") and "meta" not in n.lower()]
    if not pref:raise RuntimeError("No OCR text in urduemualla")
    sizes={f.get("name",""):int(f.get("size",0) or 0) for f in files};name=max(pref,key=lambda n:sizes.get(n,0));url="https://archive.org/download/urduemualla/"+quote(name);raw=normalize_source(get(url,50000));lines=[]
    for s in raw.splitlines():
        s=s.strip();low=s.lower()
        if not s:
            if lines and lines[-1]!="":lines.append("")
        elif not any(x in low for x in ["digitized by","internet archive","scanningcenter","bookreader","copyright"]) and not re.fullmatch(r"[\d\-–— .]+",s):lines.append(s)
    text="\n".join(lines).strip()
    if urdu_count(text)<20000:raise RuntimeError(f"Too little Urdu OCR: {urdu_count(text)}")
    return text,url,name

def split_parts(text,maxc=24000):
    parts=[];cur=[];n=0
    for p in re.split(r"\n\s*\n",text):
        if cur and n+len(p)>maxc:parts.append("\n\n".join(cur));cur=[];n=0
        cur.append(p);n+=len(p)+2
    if cur:parts.append("\n\n".join(cur))
    return parts

def build_urdu():
    src,url,name=fetch_urdu();root=WORKS/"ghalib"/"urdu-e-mualla";parts=split_parts(src);oc=0
    for i,p in enumerate(parts,1):rom=urdu_to_roman(p);oc+=len(rom);write(root/"parts"/f"{i:03d}.md",f"# Urdu-e-Mualla — Hissa {i}\n\n**Mirza Ghalib**\n\n{rom}")
    write(root/"source.md",f"# Locked Source Record — Urdu-e-Mualla\n\n- Author: Mirza Ghalib\n- Base Internet Archive item: `urduemualla`\n- OCR file: `{name}`\n- Download: `{url}`\n- Scan furniture excluded; no recent translation copied.\n")
    write(root/"NOTES.md","# Editorial Notes — Urdu-e-Mualla\n\nSource order is retained and split only at paragraph boundaries. Unvowelled Urdu OCR makes this the least publication-ready unit. Every part needs scan comparison, letter-boundary, date, addressee, name, and natural-language review.\n\nStatus: `machine_assisted_complete_first_pass`; `human_review: pending`.\n")
    combined="".join(p.read_text() for p in sorted((root/"parts").glob("*.md")));return QA("ghalib-urdu-e-mualla","Urdu-e-Mualla","Mirza Ghalib",len(parts),len(src),oc,dev_count(combined),urdu_count(combined),dev_count(combined)==0 and urdu_count(combined)==0,"machine_assisted_complete_first_pass","OCR transliteration requires intensive human review")

def reports(qs):
    rows=["# Classics Build QA","","All statuses are machine-assisted first passes, not publication approval.","","| Work | Units | Source chars | Output chars | Devanagari left | Urdu left | Roman-only | Status |","|---|---:|---:|---:|---:|---:|:---:|---|"];fail=[]
    for q in qs:rows.append(f"| {q.author} — {q.title} | {q.units} | {q.source_chars} | {q.output_chars} | {q.devanagari_remaining} | {q.urdu_remaining} | {'yes' if q.roman_only else 'NO'} | {q.status} |")
    rows += ["","## Validation",""]
    for q in qs:
        ratio=q.output_chars/max(q.source_chars,1);ok=q.roman_only and ratio>.35 and q.output_chars>1000;rows.append(f"- **{q.id}:** {'pass' if ok else 'FAIL'}; output/source ratio `{ratio:.3f}`. {q.notes}")
        if not ok:fail.append(q.id)
    write(OUT/"QA.md","\n".join(rows));write(OUT/"manifest-fragment.json",json.dumps({"project":"easy-roman-hindustani-classics","works":[{"id":q.id,"author":q.author,"title":q.title,"units":q.units,"source_chars":q.source_chars,"output_chars":q.output_chars,"translation_status":q.status,"human_review":"pending","roman_only":q.roman_only} for q in qs]},ensure_ascii=False,indent=2))
    if fail:raise RuntimeError("validation failed: "+", ".join(fail))

def main():
    OUT.mkdir(parents=True,exist_ok=True);LOGS.mkdir(parents=True,exist_ok=True);qs=[]
    print("Building Nirmala",flush=True);qs.append(build_nirmala())
    print("Building Godaan",flush=True);qs.append(build_godaan())
    print("Building Manto",flush=True);qs.extend(build_manto())
    print("Building Urdu-e-Mualla",flush=True);qs.append(build_urdu())
    reports(qs);print(json.dumps([asdict(q) for q in qs],ensure_ascii=False,indent=2))
if __name__=="__main__":
    try:main()
    except Exception as exc:
        LOGS.mkdir(parents=True,exist_ok=True);write(LOGS/"failure.txt",f"{type(exc).__name__}: {exc}\n");raise
