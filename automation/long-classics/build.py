#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, re, shutil, unicodedata
from pathlib import Path
from urllib.parse import quote, urlencode
import requests
from bs4 import BeautifulSoup
from uroman import Uroman

OUT=Path('automation/long-classics/generated')
WORKS=OUT/'works'
S=requests.Session(); S.headers['User-Agent']='SWR public-domain editorial build/1.0'
UR=Uroman()
DEV=re.compile(r'[\u0900-\u097f]')
URD=re.compile(r'[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff]')
DIG=str.maketrans('०१२३४५६७८९۰۱۲۳۴۵۶۷۸۹','01234567890123456789')
EASY={
'किन्तु':'लेकिन','किंतु':'लेकिन','परन्तु':'लेकिन','परंतु':'लेकिन','तथापि':'फिर भी','अतः':'इसलिए','प्रातः':'सुबह','सायंकाल':'शाम','सन्ध्या':'शाम','संध्या':'शाम','भोजन':'खाना','जलपान':'कुछ खाना','निवास':'घर','गृहस्थी':'घर-परिवार','गृह':'घर','मुखमण्डल':'चेहरा','मुखमंडल':'चेहरा','मुख':'मुँह','नेत्र':'आँख','नयन':'आँख','दृष्टि':'नज़र','हृदय':'दिल','अन्तःकरण':'मन','अंतःकरण':'मन','मस्तिष्क':'दिमाग','क्रोध':'गुस्सा','कुपित':'गुस्से में','प्रसन्न':'खुश','आनन्द':'खुशी','आनंद':'खुशी','विषाद':'उदासी','वेदना':'दर्द','पीड़ा':'दर्द','सहायता':'मदद','आवश्यक':'ज़रूरी','व्यवस्था':'इंतज़ाम','प्रबन्ध':'इंतज़ाम','प्रबंध':'इंतज़ाम','उद्देश्य':'मकसद','विचार':'सोच','अभिलाषा':'चाह','कामना':'चाह','व्यर्थ':'बेकार','प्रतीत':'लगा','विदित':'पता','ज्ञात':'पता','शीघ्र':'जल्दी','तत्काल':'तुरंत','उत्तर':'जवाब','प्रश्न':'सवाल','सम्भव':'मुमकिन','संभव':'मुमकिन','असम्भव':'नामुमकिन','असंभव':'नामुमकिन','निश्चय':'फैसला','निर्णय':'फैसला','आरम्भ':'शुरू','आरंभ':'शुरू','प्रारम्भ':'शुरू','प्रारंभ':'शुरू','समाप्त':'खत्म','समीप':'पास','निकट':'पास','भय':'डर','आश्चर्य':'हैरानी','अत्यन्त':'बहुत','अत्यंत':'बहुत','निरन्तर':'लगातार','निरंतर':'लगातार','सदैव':'हमेशा','सर्वदा':'हमेशा','स्त्री':'औरत','पुरुष':'आदमी','बालक':'लड़का','बालिका':'लड़की','शिशु':'बच्चा','सन्तान':'बच्चा','संतान':'बच्चा','पुत्र':'बेटा','पुत्री':'बेटी','माता':'माँ','दुर्भाग्य':'बदकिस्मती','कारण':'वजह','परिणाम':'नतीजा','समाचार':'खबर','सूचना':'खबर','अनुमति':'इजाज़त','निवेदन':'बिनती','अनुरोध':'बिनती','आज्ञा':'हुक्म','निर्देश':'हुक्म','अवकाश':'फुर्सत','प्रयत्न':'कोशिश','प्रयास':'कोशिश','सफल':'कामयाब','असफल':'नाकाम','लज्जा':'शर्म','स्वर':'आवाज़','कण्ठ':'गला','कंठ':'गला','मौन':'चुप','वार्तालाप':'बातचीत','संवाद':'बातचीत','मार्ग':'रास्ता','पथ':'रास्ता','प्रस्थान':'रवाना होना','आगमन':'आना','वस्त्र':'कपड़े','आभूषण':'गहने','औषधि':'दवा','चिकित्सक':'डॉक्टर','विद्यालय':'स्कूल','अध्यापक':'टीचर','कार्यालय':'दफ्तर','न्यायालय':'अदालत','धन':'पैसा','निर्धन':'गरीब','कठिन':'मुश्किल','सरल':'आसान','उचित':'ठीक','अनुचित':'गलत','विशेष':'खास','साधारण':'आम','प्रकार':'तरह','भाँति':'तरह','भांति':'तरह','क्षण':'पल','पूर्व':'पहले','पश्चात्':'बाद','पश्चात':'बाद','बुद्धि':'अकल','मूर्ख':'बेवकूफ','सन्देह':'शक','संदेह':'शक','विश्वास':'यकीन','आशा':'उम्मीद','सम्मान':'इज़्ज़त','अपमान':'बेइज़्ज़ती','कष्ट':'तकलीफ','प्रेम':'प्यार','स्नेह':'प्यार','घृणा':'नफरत','लाभ':'फायदा','हानि':'नुकसान','सम्पूर्ण':'पूरा','संपूर्ण':'पूरा','प्रत्येक':'हर','समस्त':'सब','वर्तमान':'अभी','व्यक्ति':'आदमी','परिस्थिति':'हाल','भावना':'एहसास','महत्त्वपूर्ण':'ज़रूरी','महत्वपूर्ण':'ज़रूरी','स्वतन्त्र':'आज़ाद','स्वतंत्र':'आज़ाद'}
POST={'nahi':'nahin','nahim':'nahin','naheen':'nahin','vahan':'wahan','vah':'woh','yah':'yeh','accha':'achchha','chahie':'chahiye','bhagvan':'Bhagwan','pyar':'pyaar','zamin':'zameen','admi':'aadmi','insan':'insaan','kintu':'lekin','parantu':'lekin','avashyak':'zaroori','sahayata':'madad','vyavastha':'intezam','prabandh':'intezam','nirdesh':'hukm','aadesh':'hukm','prasann':'khush','krodh':'gussa','hriday':'dil','drishti':'nazar','vichar':'soch','nirnay':'faisla','parinam':'nateeja','uddeshya':'maksad','paristhiti':'haal','vyakti':'aadmi','prashn':'sawaal','uttar':'jawaab','samachar':'khabar','sheeghra':'jaldi','tatkal':'turant','sambhav':'mumkin','asambhav':'namumkin','prarambh':'shuru','aarambh':'shuru','samapt':'khatam','sameep':'paas','nikat':'paas','bhay':'dar','ashcharya':'hairani','atyant':'bahut','sadaiv':'hamesha','stri':'aurat','purush':'aadmi','balak':'ladka','balika':'ladki','santan':'bachcha','mata':'maa','dhan':'paisa','nirdhan':'gareeb','kathin':'mushkil','uchit':'theek','anuchit':'galat','prakar':'tarah','bhanti':'tarah','kshan':'pal','pashchat':'baad','sandeh':'shak','vishwas':'yakeen','samman':'izzat','apmaan':'beizzati','kasht':'takleef','prem':'pyaar','ghrina':'nafrat','labh':'fayda','hani':'nuksan'}

def get(url,timeout=180):
 for i in range(4):
  try:
   r=S.get(url,timeout=timeout); r.raise_for_status(); return r
  except Exception:
   if i==3: raise

def norm(s):
 s=s.replace('\r','').replace('\ufeff','').replace('\u200c','').replace('\u200d','').replace('\x0c','\n\n').translate(DIG)
 s=re.sub(r'[ \t]+',' ',s); s=re.sub(r'\n{3,}','\n\n',s)
 return s.strip()

def roman(s,dev=True):
 if dev:
  for a,b in sorted(EASY.items(),key=lambda x:len(x[0]),reverse=True): s=s.replace(a,b)
 try: x=UR.romanize_string(s)
 except TypeError: x=UR.romanize_string(s,lcode='hin' if dev else 'urd')
 x=x.replace('“','"').replace('”','"').replace('‘',"'").replace('’',"'").replace('—','--').replace('–','-').replace('…','...')
 x=unicodedata.normalize('NFKD',x).encode('ascii','ignore').decode().translate(DIG)
 def f(m):
  w=m.group(0); z=POST.get(w.lower(),w); return z[:1].upper()+z[1:] if w[:1].isupper() else z
 x=re.sub(r"[A-Za-z]+(?:'[A-Za-z]+)?",f,x)
 x=re.sub(r'[ \t]+',' ',x); x=re.sub(r'\n{3,}','\n\n',x)
 x=''.join(c for c in x if ord(c)<128 or c=='\n')
 return x.strip()

def natural(t):
 z=t.translate(DIG); m=re.findall(r'\d+',z); return (int(m[-1]) if m else 999,z)

def nirmala():
 api='https://hi.wikisource.org/w/api.php'; q={'action':'query','list':'allpages','apprefix':'निर्मला/','apnamespace':'0','aplimit':'max','format':'json','formatversion':'2'}
 data=get(api+'?'+urlencode(q)).json(); pages=[]
 while 1:
  pages += [x['title'] for x in data['query']['allpages']]
  if 'continue' not in data: break
  q.update(data['continue']); data=get(api+'?'+urlencode(q)).json()
 pages=[p for p in pages if re.search(r'\d+',p.translate(DIG))]; pages=sorted(dict.fromkeys(pages),key=natural)
 if not 20<=len(pages)<=40: raise RuntimeError(f'Nirmala pages={len(pages)}')
 out=[]
 for p in pages:
  d=get(api+'?'+urlencode({'action':'parse','page':p,'prop':'text','format':'json','formatversion':'2','redirects':'1'})).json(); soup=BeautifulSoup(d['parse']['text'],'html.parser'); root=soup.select_one('.mw-parser-output') or soup
  for n in root.select('script,style,table,.mw-editsection,.navbox,.metadata,sup.reference,.noprint,figure'): n.decompose()
  ps=[]
  for n in root.find_all(['p','blockquote','h2','h3']):
   t=' '.join(n.stripped_strings); t=re.sub(r'\[\s*\d+\s*\]','',t)
   if t and not re.search(r'(विकिस्रोत|wikisource)',t,re.I): ps.append(t)
  t=norm('\n\n'.join(ps))
  if len(t)<700: raise RuntimeError(f'short Nirmala page {p}: {len(t)}')
  out.append((p,t))
 if sum(len(t) for _,t in out)<120000: raise RuntimeError('short Nirmala total')
 return out,'Hindi Wikisource chapter pages under Nirmala/'

def split_numbered(t,n):
 t=norm(t); ms=[(int(m.group(1)),m) for m in re.finditer(r'(?m)^\s*(\d{1,3})\s*[\.।]\s*$',t)]; seq=[]; want=1
 for x,m in ms:
  if x==want: seq.append((x,m)); want+=1
  if want==n+1: break
 if len(seq)!=n:return []
 return [(str(x),t[m.end():(seq[i+1][1].start() if i+1<len(seq) else len(t))].strip()) for i,(x,m) in enumerate(seq)]

def godaan():
 u='https://raw.githubusercontent.com/ranvirp/LLMLearn/e8a13b4f480b4c5024f9cb07a15e34632f89a7be/hindillm/godaan.txt'; t=get(u).text; ch=split_numbered(t,36)
 if len(ch)!=36 or any(len(x)<3000 for _,x in ch):
  b='https://raw.githubusercontent.com/pandeyshikha1098/privacy_policy/45b42cf18333411f035757a9ecd8b6859fa84ae6/hindi-stories/storyBook/premchandra/godan/{:02d}.txt'; ch=[]
  for i in range(1,37): ch.append((str(i),norm(get(b.format(i)).text)))
  u=b.replace('{:02d}','01..36')
 if sum(len(x) for _,x in ch)<450000: raise RuntimeError('short Godaan total')
 return ch,u

def write_novel(wid,title,chapters,source):
 b=WORKS/'premchand'/wid; (b/'chapters').mkdir(parents=True,exist_ok=True); idx=[f'# {title}','','**Munshi Premchand**','']; sc=oc=0
 for i,(_,src) in enumerate(chapters,1):
  sc+=len(src); r=roman(src,True); oc+=len(r)
  if DEV.search(r) or URD.search(r) or len(r)<len(src)*.4: raise RuntimeError(f'{title} chapter {i} validation')
  fn=f'{i:02d}.md'; (b/'chapters'/fn).write_text(f'# {title} — Adhyay {i}\n\n**Munshi Premchand**\n\n{r}\n'); idx.append(f'{i}. [Adhyay {i}](chapters/{fn})')
 (b/'translation.md').write_text('\n'.join(idx)+'\n'); (b/'source.md').write_text(f'# Locked Source Record — {title}\n\n- Author: Munshi Premchand\n- Source: {source}\n- Chapter count: {len(chapters)}\n- Source characters: {sc}\n- Status: locked machine-assisted first pass\n'); (b/'NOTES.md').write_text(f'# Editorial Notes — {title}\n\nComplete ordered Roman-Hindustani first pass saved in {len(chapters)} chapter files. Names, numbers, paragraph order, dialogue, social signals, repeated phrases, and ending are retained from the extracted source. Human paragraph-by-paragraph and read-aloud review is pending. Not publication-ready.\n')
 return {'work':title,'units':len(chapters),'source_chars':sc,'output_chars':oc,'status':'machine_assisted_complete_first_pass'}

def urdu():
 ident='in.ernet.dli.2015.435597'; md=get('https://archive.org/metadata/'+ident).json(); fs=[f for f in md['files'] if f.get('name','').endswith('_djvu.txt')]; f=max(fs,key=lambda x:int(x.get('size') or 0)); raw=get('https://archive.org/download/'+ident+'/'+quote(f['name']),240).content
 if f.get('md5') and hashlib.md5(raw).hexdigest()!=f['md5']: raise RuntimeError('OCR checksum')
 t=norm(raw.decode('utf-8','replace')); lines=[]
 for l in t.splitlines():
  z=' '.join(l.split())
  if not z: lines.append(''); continue
  if re.fullmatch(r'[\d\s.\-\[\]()]+',z) or re.search(r'(internet archive|digital library)',z,re.I): continue
  lines.append(z)
 t=norm('\n'.join(lines))
 if len(t)<250000: raise RuntimeError('short Urdu OCR')
 ps=[p for p in re.split(r'\n\s*\n',t) if p.strip()]; chunks=[]; cur=[]; n=0
 for p in ps:
  if cur and n+len(p)>14000: chunks.append('\n\n'.join(cur));cur=[];n=0
  cur.append(p);n+=len(p)+2
 if cur:chunks.append('\n\n'.join(cur))
 rt='\n\n'.join(roman(x,False) for x in chunks); ps=[p for p in re.split(r'\n\s*\n',rt) if p.strip()]; parts=[];cur=[];n=0
 for p in ps:
  if cur and n+len(p)>24000: parts.append('\n\n'.join(cur));cur=[];n=0
  cur.append(p);n+=len(p)+2
 if cur:parts.append('\n\n'.join(cur))
 if len(parts)<8: raise RuntimeError('too few Urdu parts')
 b=WORKS/'ghalib/urdu-e-mualla';(b/'parts').mkdir(parents=True,exist_ok=True);idx=['# Urdu-e-Mualla','','**Mirza Ghalib**',''];oc=0
 for i,r in enumerate(parts,1):
  if DEV.search(r) or URD.search(r): raise RuntimeError(f'Urdu part {i} script leak')
  oc+=len(r);fn=f'{i:02d}.md';(b/'parts'/fn).write_text(f'# Urdu-e-Mualla — Hissa {i}\n\n**Mirza Ghalib**\n\n{r}\n');idx.append(f'{i}. [Hissa {i}](parts/{fn})')
 (b/'translation.md').write_text('\n'.join(idx)+'\n');(b/'source.md').write_text(f'# Locked Source Record — Urdu-e-Mualla\n\n- Author: Mirza Ghalib\n- Internet Archive identifier: `{ident}`\n- OCR file: `{f["name"]}`\n- OCR bytes: {len(raw)}\n- OCR MD5: `{hashlib.md5(raw).hexdigest()}`\n- Status: locked OCR first pass\n');(b/'NOTES.md').write_text(f'# Editorial Notes — Urdu-e-Mualla\n\nComplete recoverable OCR order saved as {len(parts)} Roman-script parts. Parts are paragraph-safe size divisions, not claimed as authoritative letter boundaries. Urdu OCR, vowels, punctuation, names, and editorial boundaries require page-image review. Human review pending; not publication-ready.\n')
 return {'work':'Urdu-e-Mualla','units':len(parts),'source_chars':len(t),'output_chars':oc,'status':'ocr_machine_assisted_complete_first_pass'}

def main():
 if OUT.exists():shutil.rmtree(OUT)
 OUT.mkdir(parents=True);qa=[];a,s=nirmala();qa.append(write_novel('nirmala','Nirmala',a,s));a,s=godaan();qa.append(write_novel('godaan','Godaan',a,s));qa.append(urdu())
 q=['# Long-Work QA','','All three works are complete machine-assisted first passes and remain `human_review: pending`.','', '| Work | Units | Source chars | Output chars | Status |','|---|---:|---:|---:|---|']
 for x in qa:q.append(f'| {x["work"]} | {x["units"]} | {x["source_chars"]} | {x["output_chars"]} | {x["status"]} |')
 q+=['','- Ordered source sequence retained.','- Roman-only validation passed.','- Minimum source-length and output-ratio checks passed.','- Independent source comparison and read-aloud review remain pending.']
 (OUT/'QA.md').write_text('\n'.join(q)+'\n');(OUT/'manifest-fragment.json').write_text(json.dumps(qa,indent=2));print(json.dumps(qa))
if __name__=='__main__':main()
