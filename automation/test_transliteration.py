#!/usr/bin/env python3
from pathlib import Path

from aksharamukha import transliterate

samples = {
    "hindi": "यूं तो बाबू उदयभानुलाल के परिवार में बीसों ही प्राणी थे; कोई ममेरा भाई था, कोई फुफेरा। बड़ी का नाम निर्मला और छोटी का कृष्णा था।",
    "urdu": "بٹوارے کے دو تین سال بعد پاکستان اور ہندوستان کی حکومتوں کو خیال آیا کہ پاگلوں کا تبادلہ بھی ہونا چاہیے۔",
}
lines = []
for name, text in samples.items():
    lines.append(f"## {name}\nSOURCE={text}")
    for target in ["RomanColloquial", "RomanReadable", "IAST", "ITRANS"]:
        try:
            kwargs = {"pre_options": ["RemoveSchwaHindi"]} if name == "hindi" else {}
            out = transliterate.process("Devanagari" if name == "hindi" else "Urdu", target, text, **kwargs)
            lines.append(f"Aksharamukha-{target}={out}")
        except Exception as exc:
            lines.append(f"Aksharamukha-{target}=ERROR {type(exc).__name__}: {exc}")
    lines.append("")

try:
    from ai4bharat.transliteration import XlitEngine

    urdu_engine = XlitEngine("ur", src_script_type="indic", beam_width=8, rescore=False)
    for text in [
        samples["urdu"],
        "معلوم نہیں یہ بات معقول تھی یا غیر معقول، بہرحال دانش مندوں کے فیصلے کے مطابق ادھر ادھر اونچی سطح کی کانفرنسیں ہوئیں۔",
        "بشن سنگھ نے فضل دین کو ایک نظر دیکھا اور کچھ بڑبڑانے لگا۔",
    ]:
        try:
            result = urdu_engine.translit_sentence(text, lang_code="ur")
            lines.append(f"AI4Bharat-SOURCE={text}\nAI4Bharat-RESULT={result}\n")
        except Exception as exc:
            lines.append(f"AI4Bharat-ERROR={type(exc).__name__}: {exc}\n")
except Exception as exc:
    lines.append(f"AI4Bharat-INIT-ERROR={type(exc).__name__}: {exc}\n")

path = Path("generated/logs/translit-samples.txt")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("\n".join(lines), encoding="utf-8")
print(path.read_text(encoding="utf-8"))
