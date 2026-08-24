#!/usr/bin/env python3
"""Build an OCR-based Roman first pass of Ghalib's Urdu-e-Mualla."""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import quote

import requests

OUT = Path("generated/works/ghalib/urdu-e-mualla")
IDENTIFIER = "in.ernet.dli.2015.435597"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "SyllabuswithRohit-public-domain-editorial/1.0"})

URDU_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
URDU_MAP = {
    "ا": "a", "آ": "aa", "ٱ": "a", "ب": "b", "پ": "p", "ت": "t", "ٹ": "t",
    "ث": "s", "ج": "j", "چ": "ch", "ح": "h", "خ": "kh", "د": "d", "ڈ": "d",
    "ذ": "z", "ر": "r", "ڑ": "r", "ز": "z", "ژ": "zh", "س": "s", "ش": "sh",
    "ص": "s", "ض": "z", "ط": "t", "ظ": "z", "ع": "", "غ": "gh", "ف": "f",
    "ق": "q", "ک": "k", "ك": "k", "گ": "g", "ل": "l", "م": "m", "ن": "n",
    "ں": "n", "و": "o", "ؤ": "o", "ہ": "h", "ه": "h", "ھ": "h", "ء": "",
    "ی": "y", "ي": "y", "ئ": "y", "ے": "e", "ۓ": "e", "ۃ": "h", "ة": "h",
    "َ": "a", "ِ": "i", "ُ": "u", "ّ": "", "ْ": "", "ٰ": "aa", "ٔ": "",
    "۔": ".", "،": ",", "؛": ";", "؟": "?", "؍": "/", "ؔ": "",
}
WORD_FIXES = {
    "mn": "main", "myn": "mein", "men": "mein", "ap": "aap", "he": "hai",
    "hyn": "hain", "hn": "hain", "thy": "thi", "nhyn": "nahin", "nhy": "nahin",
    "ky": "ki", "sy": "se", "aor": "aur", "or": "aur", "yh": "yeh", "wo": "woh",
    "kch": "kuchh", "sb": "sab", "mjh": "mujh", "mjhe": "mujhe", "tm": "tum",
    "ksi": "kisi", "kywn": "kyon", "agr": "agar", "lkn": "lekin", "mgr": "magar",
    "phr": "phir", "yhan": "yahan", "whan": "wahan", "dl": "dil", "bt": "baat",
    "khbr": "khabar", "kht": "khat", "khda": "Khuda", "jnab": "Janab",
    "sahb": "Sahab", "mrza": "Mirza", "ghalb": "Ghalib", "zndgy": "zindagi",
    "zndgi": "zindagi", "dnya": "duniya", "mohbt": "mohabbat", "mhbt": "mohabbat",
    "ghm": "gham", "shhr": "shehar", "ghr": "ghar", "pny": "paani", "aj": "aaj",
    "kl": "kal", "wqt": "waqt", "bht": "bahut", "zyadh": "zyada", "km": "kam",
    "arz": "arz", "jwab": "jawaab", "khyal": "khayal", "khyl": "khayal",
    "malom": "maloom", "mlom": "maloom", "mloom": "maloom", "lkha": "likha",
    "lkhta": "likhta", "prha": "padha", "bhja": "bheja", "aya": "aaya",
    "gya": "gaya", "gye": "gaye", "gyi": "gayi", "hoya": "hua",
}


def get_json(url: str) -> dict:
    response = SESSION.get(url, timeout=180)
    response.raise_for_status()
    return response.json()


def get_text(url: str) -> str:
    response = SESSION.get(url, timeout=300)
    response.raise_for_status()
    return response.content.decode("utf-8", errors="replace")


def fetch_ocr() -> tuple[str, str, str]:
    metadata = get_json(f"https://archive.org/metadata/{IDENTIFIER}")
    candidates = []
    for item in metadata.get("files", []):
        name = item.get("name", "")
        if name.endswith("_djvu.txt"):
            candidates.append((int(item.get("size", 0) or 0), name))
    if not candidates:
        raise RuntimeError("No _djvu.txt OCR file found")
    size, name = max(candidates)
    if size < 300_000:
        raise RuntimeError(f"OCR file is suspiciously short: {size}")
    url = f"https://archive.org/download/{IDENTIFIER}/{quote(name)}"
    return get_text(url), url, name


def clean_ocr(raw: str) -> str:
    raw = unicodedata.normalize("NFKC", raw).translate(URDU_DIGITS)
    lines = []
    for line in raw.splitlines():
        text = line.strip()
        if not text:
            lines.append("")
            continue
        if re.fullmatch(r"[0-9\-–— ]{1,8}", text):
            continue
        if "Digitized by" in text or "Generated at" in text:
            continue
        lines.append(text)
    raw = "\n".join(lines)
    markers = [raw.find(x) for x in ("بنام", "بنامِ", "میر مہدی", "میاں") if raw.find(x) >= 0]
    if markers and min(markers) > 500:
        raw = raw[min(markers):]
    return re.sub(r"\n{3,}", "\n\n", raw).strip()


def romanize(text: str) -> str:
    chars = []
    for char in text:
        if char in URDU_MAP:
            chars.append(URDU_MAP[char])
        elif "\u0600" <= char <= "\u06ff":
            continue
        else:
            chars.append(char)
    output = "".join(chars).replace("ـ", "")
    tokens = re.split(r"(\W+)", output)
    output = "".join(WORD_FIXES.get(token.lower(), token) for token in tokens)
    replacements = {
        r"\bkh\b": "ke", r"\bh\b": "hai", r"\bn\b": "ne", r"\bkr\b": "kar",
        r"\bkry\b": "kare", r"\bkrta\b": "karta", r"\bkrty\b": "karte",
        r"\bkrna\b": "karna", r"\blkh\b": "likh", r"\bapko\b": "aapko",
        r"\bapny\b": "apne", r"\bhum\b": "ham",
    }
    for pattern, value in replacements.items():
        output = re.sub(pattern, value, output)
    output = re.sub(r"[ \t]+", " ", output)
    output = re.sub(r"\s+([,.!?;:])", r"\1", output)
    output = re.sub(r"\n{3,}", "\n\n", output)
    return output.strip()


def paragraphs(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def main() -> None:
    raw, url, filename = fetch_ocr()
    cleaned = clean_ocr(raw)
    source_paragraphs = paragraphs(cleaned)
    if len(source_paragraphs) < 100:
        raise RuntimeError(f"Only {len(source_paragraphs)} paragraphs remained")
    parts_dir = OUT / "parts"
    parts_dir.mkdir(parents=True, exist_ok=True)
    for old in parts_dir.glob("*.md"):
        old.unlink()
    per_part = max(1, (len(source_paragraphs) + 23) // 24)
    blocks = [source_paragraphs[i:i + per_part] for i in range(0, len(source_paragraphs), per_part)]
    index = ["# Urdu-e-Mualla", "", "**Mirza Ghalib**", "", "OCR-based Roman-Hindustani first pass.", ""]
    for number, block in enumerate(blocks, 1):
        output = romanize("\n\n".join(block))
        if re.search(r"[\u0600-\u06ff\u0900-\u097f]", output):
            raise RuntimeError(f"Indic script remains in part {number}")
        path = parts_dir / f"{number:02d}.md"
        write(path, f"# Part {number}\n\n{output}")
        index.append(f"- [Part {number}](parts/{number:02d}.md)")
    write(OUT / "translation.md", "\n".join(index))
    write(OUT / "source.md", f"""# Source Record — Urdu-e-Mualla

- Author: Mirza Ghalib
- Internet Archive identifier: `{IDENTIFIER}`
- OCR file: `{filename}`
- OCR URL: {url}
- Source characters before cleanup: {len(raw)}
- Source paragraphs retained: {len(source_paragraphs)}
""")
    write(OUT / "NOTES.md", f"""# Editorial Notes — Urdu-e-Mualla

- Ordered parts: {len(blocks)}
- Status: `ocr_machine_assisted_complete_first_pass`
- Roman-only automated validation: passed
- Human Urdu and page-image review: pending
- Publication status: not publication-ready
""")
    Path("generated/urdu-e-mualla-build.json").write_text(
        json.dumps({"parts": len(blocks), "paragraphs": len(source_paragraphs), "source_chars": len(raw)}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Built Urdu-e-Mualla in {len(blocks)} parts")


if __name__ == "__main__":
    main()
