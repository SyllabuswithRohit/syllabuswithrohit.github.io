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
            lines.append(f"{target}={out}")
        except Exception as exc:
            lines.append(f"{target}=ERROR {type(exc).__name__}: {exc}")
    lines.append("")
path = Path("generated/logs/translit-samples.txt")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("\n".join(lines), encoding="utf-8")
print(path.read_text(encoding="utf-8"))
