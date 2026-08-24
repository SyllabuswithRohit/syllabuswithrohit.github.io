#!/usr/bin/env python3
"""Run the complete classics builder with AI4Bharat Urdu romanization.

The source-fetching and completeness checks remain in run_builder.py. This wrapper
loads those definitions without executing its final main call, replaces only the
Urdu-script conversion stage, and then runs the same validated build.
"""
from __future__ import annotations

import functools
import re
import unicodedata
from pathlib import Path

from ai4bharat.transliteration import XlitEngine

source_path = Path(__file__).with_name("run_builder.py")
source = source_path.read_text(encoding="utf-8")
marker = "\nb.get = robust_get\n"
if marker not in source:
    raise RuntimeError("run_builder.py structure changed; AI4Bharat wrapper needs review")
prefix, tail = source.split(marker, 1)
# Load all functions and mappings but omit the assignments and final b.main().
namespace: dict[str, object] = {"__name__": "classics_builder_loaded"}
exec(compile(prefix, str(source_path), "exec"), namespace)

b = namespace["b"]
robust_get = namespace["robust_get"]
fetch_wikisource_pages = namespace["fetch_wikisource_pages"]
build_manto_from_wikisource = namespace["build_manto_from_wikisource"]

print("Loading AI4Bharat Urdu transliteration model", flush=True)
urdu_engine = XlitEngine("ur", src_script_type="indic", beam_width=8, rescore=False)

STABLE = {
    "naheen": "nahin", "nahi": "nahin", "kyonke": "kyunki",
    "kyonki": "kyunki", "achha": "achchha", "accha": "achchha",
    "chahye": "chahiye", "chahiyeh": "chahiye", "zamin": "zameen",
    "zameen": "zameen", "admi": "aadmi", "insan": "insaan",
    "yhan": "yahan", "wahan": "wahan", "whan": "wahan",
    "mein": "mein", "mai": "main", "hy": "hai", "hyn": "hain",
    "aurt": "aurat", "pakstan": "Pakistan", "hindustan": "Hindustan",
    "hndostan": "Hindustan", "khuda": "Khuda", "allah": "Allah",
    "mohbt": "mohabbat", "mohabbat": "mohabbat", "dunya": "duniya",
    "dunia": "duniya", "zindgi": "zindagi", "srf": "sirf",
    "mloom": "maloom", "malum": "maloom", "bilkul": "bilkul",
    "liye": "liye", "lie": "liye", "kiye": "kiye", "kie": "kiye",
    "diye": "diye", "die": "diye", "gaye": "gaye", "gie": "gaye",
    "aaye": "aaye", "aie": "aaye", "koi": "koi", "koee": "koi",
}


def normalize_ascii(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.replace("ʾ", "'").replace("ʿ", "'").replace("ə", "a")
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return text


@functools.lru_cache(maxsize=100000)
def romanize_urdu_word(word: str) -> str:
    if not word:
        return word
    common = b.URDU_COMMON.get(word)
    if common:
        return common
    try:
        result = urdu_engine.translit_sentence(word, lang_code="ur")
    except TypeError:
        result = urdu_engine.translit_sentence(word)
    if isinstance(result, dict):
        result = result.get("ur") or next(iter(result.values()), "")
    result = normalize_ascii(str(result)).strip()
    if not result or b.urdu_count(result):
        result = b.urdu_word(word)
    return result


def readable_urdu_to_roman(text: str) -> str:
    text = b.normalize_source(text)
    pieces = re.split(r"(\s+)", text)
    output: list[str] = []
    for piece in pieces:
        if not piece or piece.isspace() or not b.urdu_count(piece):
            output.append(piece)
            continue
        lead_match = re.match(r"^[^\u0600-\u06ff]*", piece)
        trail_match = re.search(r"[^\u0600-\u06ff]*$", piece)
        lead = lead_match.group(0) if lead_match else ""
        trail = trail_match.group(0) if trail_match else ""
        end = len(piece) - len(trail) if trail else len(piece)
        core = piece[len(lead):end]
        output.append(lead + romanize_urdu_word(core) + trail)

    result = "".join(output)
    for old, new in STABLE.items():
        result = re.sub(rf"\b{re.escape(old)}\b", new, result, flags=re.I)
    result = re.sub(r"[^\x00-\x7F]", "", result)
    result = re.sub(r"[ \t]+", " ", result)
    result = re.sub(r" *\n *", "\n", result)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


# Patch both direct Urdu-e-Mualla conversion and the Manto function global.
b.get = robust_get
b.fetch_wikisource_pages = fetch_wikisource_pages
b.urdu_to_roman = readable_urdu_to_roman
namespace["natural_urdu_to_roman"] = readable_urdu_to_roman
# build_manto_from_wikisource retains namespace as its globals, so the reassignment above applies.
b.build_manto = build_manto_from_wikisource

b.main()
