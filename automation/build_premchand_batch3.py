#!/usr/bin/env python3
"""Build batch 3 of complete easy Roman-Hindustani Premchand readers.

The source texts are old Hindi transcriptions pinned to one immutable Git commit.
The builder preserves the full source order, applies a controlled easy-language pass,
and converts the result to Roman script. Outputs are complete machine-assisted first
passes and remain human-review pending.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import build_premchand_batch2 as base

ROOT = Path("generated/works/premchand")
SOURCE_REPO = base.SOURCE_REPO
SOURCE_COMMIT = base.SOURCE_COMMIT
RAW_ROOT = base.RAW_ROOT

WORKS = [
    {"id":"ghar-jamai","title":"Ghar Jamai","path":"hindi-stories/storyBook/premchandra/mansarovar-1/GharJamai.txt","blob":"78de72f6c13fad8df797d4b62ac10cb20f0943d0"},
    {"id":"ghaswali","title":"Ghaswali","path":"hindi-stories/storyBook/premchandra/mansarovar-1/Ghaswali.txt","blob":"f531ad172594ea56b39942966dda294e0ddd7694"},
    {"id":"subhagi","title":"Subhagi","path":"hindi-stories/storyBook/premchandra/mansarovar-1/Subhaagi.txt","blob":"fa4700ec339ac7ecedfac03199a45b81cbf33791"},
    {"id":"swamini","title":"Swamini","path":"hindi-stories/storyBook/premchandra/mansarovar-1/Swamini.txt","blob":"8cab239029a44c88b5d4ddc0f07c16d0da31d449"},
    {"id":"kayar","title":"Kayar","path":"hindi-stories/storyBook/premchandra/mansarovar-1/Kayar.txt","blob":"a96472da4e90ae89e68f30efc1c6291db6aada5e"},
    {"id":"khudai-fauzdar","title":"Khudai Fauzdar","path":"hindi-stories/storyBook/premchandra/mansarovar-2/KhudaiFauzdar.txt","blob":"72b6d23d4d217e535521965637431cf69d22d5ca"},
    {"id":"miss-padma","title":"Miss Padma","path":"hindi-stories/storyBook/premchandra/mansarovar-2/MissPadma.txt","blob":"2ddf24048495f6e87a4137c0e63b41981a3b8f32"},
    {"id":"neur","title":"Neur","path":"hindi-stories/storyBook/premchandra/mansarovar-2/Neur.txt","blob":"b33b74fda3122161ee9ec1c7236a441b824485c1"},
    {"id":"riyasat-ka-diwan","title":"Riyasat Ka Diwan","path":"hindi-stories/storyBook/premchandra/mansarovar-2/RiyasatKaDiwan.txt","blob":"c99f8f992e4f22e8f32a9d010138568d2533e36a"},
    {"id":"mritak-bhoj","title":"Mritak Bhoj","path":"hindi-stories/storyBook/premchandra/mansarovar-4/MritakBhoj.txt","blob":"9dde97bbff0abba89d9b3167f2f1b17b8b65ca06"},
    {"id":"sati","title":"Sati","path":"hindi-stories/storyBook/premchandra/mansarovar-4/Sati.txt","blob":"784a6f9fc12c71988677a133c9a76faab2060b22"},
    {"id":"tagada","title":"Tagada","path":"hindi-stories/storyBook/premchandra/mansarovar-4/Tagada.txt","blob":"adccc75952e9491fb46adb6b72736c63185993f9"},
    {"id":"agni-samadhi","title":"Agni Samadhi","path":"hindi-stories/storyBook/premchandra/mansarovar-5/AgniSamadhi.txt","blob":"83282e2a347bbe420ea8c6ff876c22a1f49adc77"},
    {"id":"kazaki","title":"Kazaki","path":"hindi-stories/storyBook/premchandra/mansarovar-5/Kazaki.txt","blob":"6d618a7871dac403ea14d5184393e5fee213f897"},
    {"id":"pisanhari-ka-kuan","title":"Pisanhari Ka Kuan","path":"hindi-stories/storyBook/premchandra/mansarovar-5/PisanhariKaKuan.txt","blob":"25fbdf4b80950aa2eb1f5f84c19968280e4ae1b6"},
    {"id":"suhag-ki-saree","title":"Suhag Ki Saree","path":"hindi-stories/storyBook/premchandra/mansarovar-7/SuhagKiSaree.txt","blob":"b3d3f64d8cfa336bace05bb6eff37259ba38270a"},
    {"id":"sharab-ki-dukan","title":"Sharab Ki Dukan","path":"hindi-stories/storyBook/premchandra/mansarovar-7/SharabKiDukan.txt","blob":"684e8ac9eb58d823e34581308183353f8637c911"},
    {"id":"patni-se-pati","title":"Patni Se Pati","path":"hindi-stories/storyBook/premchandra/mansarovar-7/PatniSePati.txt","blob":"8743e62d2ae7fbd0eb41afc33687c2d41e16a8e0"},
    {"id":"gareeb-ki-haay","title":"Gareeb Ki Haay","path":"hindi-stories/storyBook/premchandra/mansarovar-8/GareebKiHaay.txt","blob":"861ae14d66a13aa778252361bdc922ce06341c56"},
    {"id":"sajjanta-ka-dand","title":"Sajjanta Ka Dand","path":"hindi-stories/storyBook/premchandra/mansarovar-8/SajjantaKaDand.txt","blob":"b94e1c733b60d959ec00757f3bb5a67ea37ae68d"},
]

base.EASY_HINDI.update({
    "महत्त्व":"अहमियत", "महत्व":"अहमियत", "स्वभाव":"आदत",
    "अध्ययन":"पढ़ाई", "अध्ययनशील":"पढ़ाकू", "अनुभव":"तजुर्बा",
    "सहानुभूति":"हमदर्दी", "दया":"रहम", "अपराध":"जुर्म",
    "दण्ड":"सज़ा", "दंड":"सज़ा", "कर्तव्य":"फ़र्ज़", "धैर्य":"सब्र",
    "आत्मसम्मान":"खुद्दारी", "आत्म-सम्मान":"खुद्दारी",
    "सम्मान":"इज़्ज़त", "अपमान":"बेइज़्ज़ती", "विवश":"मजबूर",
    "विवशता":"मजबूरी", "दीन":"गरीब", "वृद्ध":"बूढ़ा",
    "युवक":"नौजवान", "युवती":"नौजवान लड़की", "कन्या":"लड़की",
    "सज्जन":"भला आदमी", "महाशय":"साहब", "अतिथि":"मेहमान",
    "परिवार":"घरवाले", "सम्पत्ति":"जायदाद", "संपत्ति":"जायदाद",
    "कृषक":"किसान", "श्रम":"मेहनत", "श्रमिक":"मज़दूर",
    "निर्वाह":"गुज़ारा", "जीविका":"रोज़ी", "अभिमान":"घमंड",
    "अहंकार":"घमंड", "ईर्ष्या":"जलन", "संदेह":"शक", "सन्देह":"शक",
    "क्षमा":"माफ़ी", "क्षमाप्रार्थी":"माफ़ी माँगने वाला",
    "प्रेम":"प्यार", "स्नेह":"प्यार", "विरोध":"खिलाफ़त",
    "अन्याय":"ज़ुल्म", "न्याय":"इंसाफ़", "प्राण":"जान",
})

WORD_REPAIRS = {
    "padhanaa":"padhna", "padhane":"padhne", "padhta":"padhta",
    "karanaa":"karna", "karataa":"karta", "karatee":"karti", "karate":"karte",
    "kahataa":"kehta", "kahatee":"kehti", "kahate":"kehte",
    "rahataa":"rehta", "rahatee":"rehti", "rahate":"rehte",
    "jaanaa":"jana", "jaataa":"jata", "jaatee":"jati", "jaate":"jate",
    "aanaa":"aana", "aataa":"aata", "aatee":"aati", "aate":"aate",
    "honaa":"hona", "hotaa":"hota", "hotee":"hoti", "hote":"hote",
    "diyaa":"diya", "liyaa":"liya", "kiyaa":"kiya", "gayaa":"gaya",
    "aayaa":"aaya", "huaa":"hua", "thee":"thi", "thaa":"tha",
    "mujhe":"mujhe", "tumhen":"tumhe", "unhen":"unhe",
    "kyaa":"kya", "kyon":"kyon", "yahaan":"yahan", "vahaan":"wahan",
    "vah":"woh", "ve":"woh", "koee":"koi", "naheen":"nahin",
    "jindagee":"zindagi", "jinadagee":"zindagi", "ijjat":"izzat",
    "jaroor":"zaroor", "jyaadaa":"zyada", "jaraa":"zara",
    "khushee":"khushi", "garib":"gareeb", "gareeb":"gareeb",
    "svaamee":"swami", "svaamini":"swamini", "svabhaav":"aadat",
    "samajh":"samajh", "javaab":"jawab", "savaal":"sawal",
    "roopaye":"rupaye", "rupaye":"rupaye", "paanee":"paani",
    "khaanaa":"khana", "duniyaa":"duniya", "aankhon":"aankhon",
}


def romanize(text: str) -> str:
    text = text.translate(str.maketrans({
        "ऩ":"न", "ऱ":"र", "ऴ":"ल", "क़":"क", "ख़":"ख", "ग़":"ग",
        "ज़":"ज", "ड़":"ड", "ढ़":"ढ", "फ़":"फ", "य़":"य",
    }))
    text = (text.replace("ऑ", "ओ").replace("ऍ", "ए").replace("ऒ", "ओ")
                .replace("ऎ", "ए").replace("ॉ", "ो").replace("ॅ", "े"))
    output = base.romanize(text)
    output = (output.replace("{}", "").replace("{", "").replace("}", "")
                    .replace("।", ".").replace("॥", ".").replace("|", ".")
                    .replace("॰", ".").replace("ऽ", "'"))
    output = re.sub(r"[\u0900-\u0903\u093a-\u094f\u0951-\u0963\u0970-\u097f]", "", output)
    for old, new in sorted(WORD_REPAIRS.items(), key=lambda item: len(item[0]), reverse=True):
        output = re.sub(rf"\b{re.escape(old)}\b", new, output, flags=re.IGNORECASE)
    output = re.sub(r"\s+([,.!?;:])", r"\1", output)
    output = re.sub(r"([,.!?;:])(\S)", r"\1 \2", output)
    output = re.sub(r"[ \t]+", " ", output)
    output = re.sub(r" *\n *", "\n", output)
    output = re.sub(r"\n{3,}", "\n\n", output)
    bad = re.search(r"[\u0900-\u097f\u0600-\u06ff]", output)
    if bad:
        raise RuntimeError(
            f"unconverted character U+{ord(bad.group()):04X} {bad.group()!r} remains"
        )
    return output.strip()


def paragraph_count(text: str) -> int:
    return len([part for part in re.split(r"\n\s*\n", text) if part.strip()])


def main() -> int:
    ROOT.mkdir(parents=True, exist_ok=True)
    qa: list[dict[str, object]] = []
    catalog = [
        "# Premchand Reader Collection — Batch 3",
        "",
        "Twenty complete machine-assisted easy Roman-Hindustani first passes.",
        "Every work remains human-review pending.",
        "",
    ]

    for index, work in enumerate(WORKS, 1):
        source_url = f"{RAW_ROOT}/{work['path']}"
        print(f"[{index:02d}/20] {work['title']}", flush=True)
        raw = base.clean_source(base.fetch_text(source_url))
        if len(raw) < 5000:
            raise RuntimeError(f"source unexpectedly short for {work['title']}: {len(raw)}")

        reader = romanize(raw)
        if len(reader) < len(raw) * 0.25:
            raise RuntimeError(f"reader coverage unexpectedly low for {work['title']}")
        source_paragraphs = paragraph_count(raw)
        reader_paragraphs = paragraph_count(reader)
        if reader_paragraphs < max(1, int(source_paragraphs * 0.80)):
            raise RuntimeError(f"paragraph coverage unexpectedly low for {work['title']}")

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
- Source paragraphs detected: {source_paragraphs}
- Reader paragraphs retained: {reader_paragraphs}
- Source order and ending retained.
- Controlled easy-language substitutions applied before script conversion.
- Roman-only check: passed.
- Translation status: `machine_assisted_complete_first_pass`
- Human source comparison: pending.
- Read-aloud and natural-language editing: pending.
- Publication status: not approved.
"""
        base.write(folder / "translation.md", translation)
        base.write(folder / "source.md", source_record)
        base.write(folder / "NOTES.md", notes)
        catalog.append(f"{index}. [{work['title']}](works/premchand/{work['id']}/translation.md)")
        qa.append({
            "id": work["id"],
            "title": work["title"],
            "source_path": work["path"],
            "source_blob": work["blob"],
            "source_characters": len(raw),
            "reader_characters": len(reader),
            "source_paragraphs": source_paragraphs,
            "reader_paragraphs": reader_paragraphs,
            "roman_only": True,
            "complete_first_pass": True,
            "human_review": "pending",
        })

    base.write(Path("generated/PREMCHAND_BATCH_3.md"), "\n".join(catalog))
    base.write(Path("generated/premchand-batch3-qa.json"), json.dumps({
        "batch": 3,
        "author": "Munshi Premchand",
        "works": qa,
        "count": len(qa),
        "status": "machine_assisted_complete_first_pass",
        "human_review": "pending",
    }, ensure_ascii=False, indent=2))

    if len(qa) != 20:
        raise RuntimeError(f"expected 20 works, built {len(qa)}")
    print("Built and checked 20 complete Premchand reader first passes for Batch 3.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
