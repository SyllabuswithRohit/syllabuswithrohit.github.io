#!/usr/bin/env python3
"""Rate-limit-safe and source-verified entry point for all classics."""
from __future__ import annotations

import functools
import re
import time
import unicodedata
from typing import Any
from urllib.parse import quote

import build_all_classics as b

try:
    from aksharamukha import transliterate as akshara
except Exception:  # pragma: no cover - workflow installs it, fallback stays auditable
    akshara = None


def request(method: str, url: str, **kwargs: Any):
    """Make a request with Wikimedia-friendly retry and backoff."""
    last = None
    for attempt in range(8):
        try:
            response = b.S.request(method, url, timeout=120, **kwargs)
            if response.status_code in {429, 500, 502, 503, 504}:
                retry_after = int(response.headers.get("Retry-After", "0") or 0)
                delay = retry_after or min(90, 4 * (2 ** attempt))
                print(f"retry {response.status_code} {url} after {delay}s", flush=True)
                time.sleep(delay)
                continue
            response.raise_for_status()
            return response
        except Exception as exc:  # noqa: BLE001 - retain final actionable error
            last = exc
            delay = min(90, 4 * (2 ** attempt))
            print(f"request error {url}: {exc}; retrying in {delay}s", flush=True)
            time.sleep(delay)
    raise RuntimeError(f"request failed after retries: {url}: {last}")


def robust_get(url: str, min_chars: int = 1, retries: int = 4) -> str:
    response = request("GET", url)
    if len(response.text) < min_chars:
        raise RuntimeError(f"suspiciously short response {len(response.text)} chars: {url}")
    return response.text


def clean_hindi_wikisource_html(page_html: str, title: str) -> str:
    soup = b.BeautifulSoup(page_html, "html.parser")
    for tag in soup.select(
        ".mw-editsection, style, script, table, .noprint, .ws-noexport, "
        ".mw-cite-backlink, .reference, .mw-references-wrap, nav"
    ):
        tag.decompose()

    lines: list[str] = []
    for raw_line in b.normalize_source(soup.get_text("\n")).splitlines():
        line = raw_line.strip()
        if not line:
            if lines and lines[-1] != "":
                lines.append("")
            continue
        if line in {"पिछला पृष्ठ", "अगला पृष्ठ", "विषयसूची", "निर्मला", title}:
            continue
        if re.fullmatch(r"[\d ]+", line.translate(b.DEV_DIGITS)):
            continue
        if line.startswith("यह पृष्ठ अंतिम बार") or line.startswith("यह पाठ"):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def fetch_wikisource_pages(category: str, prefix: str):
    """Fetch all 24 Nirmala chapters through paced MediaWiki parse calls."""
    api = "https://hi.wikisource.org/w/api.php"
    data = request(
        "GET",
        api,
        params={
            "action": "query", "list": "categorymembers",
            "cmtitle": f"Category:{category}", "cmnamespace": "0",
            "cmlimit": "500", "format": "json", "formatversion": "2",
            "maxlag": "5",
        },
    ).json()
    titles = sorted(
        {item["title"] for item in data["query"]["categorymembers"] if item["title"].startswith(prefix + "/")},
        key=b.natural_number,
    )
    if len(titles) != 24:
        raise RuntimeError(f"expected 24 {prefix} chapter titles, received {len(titles)}: {titles}")

    pages = []
    for index, title in enumerate(titles, start=1):
        print(f"Wikisource {index:02d}/{len(titles)}: {title}", flush=True)
        payload = request(
            "GET", api,
            params={
                "action": "parse", "page": title, "prop": "text",
                "format": "json", "formatversion": "2", "maxlag": "5",
                "redirects": "1",
            },
        ).json()
        if "error" in payload:
            raise RuntimeError(f"Wikisource parse error for {title}: {payload['error']}")
        text = clean_hindi_wikisource_html(payload.get("parse", {}).get("text", ""), title)
        if len(text) < 1500 or b.dev_count(text) < 800:
            raise RuntimeError(
                f"Wikisource chapter too short after cleanup: {title}: "
                f"{len(text)} chars, {b.dev_count(text)} Devanagari chars"
            )
        pages.append((b.natural_number(title), title, text))
        time.sleep(3.0)
    return pages


MANTO_WIKI_TITLES = {
    "Toba Tek Singh": ["ٹوبہ ٹیک سنگھ", "ٹوبہ ٹیک سنگھ (افسانہ)"],
    "Khol Do": ["کھول دو", "کھول دو (افسانہ)"],
    "Thanda Gosht": ["ٹھنڈا گوشت (افسانہ)", "ٹھنڈا گوشت"],
    "Bu": ["بو (افسانہ)", "بو"],
    "Kali Shalwar": ["کالی شلوار (افسانہ)", "کالی شلوار"],
    "Hatak": ["ہتک (افسانہ)", "ہتک"],
    "Naya Qanoon": ["نیا قانون (افسانہ)", "نیا قانون"],
    "Tetwal Ka Kutta": ["ٹیٹوال کا کتا", "ٹیٹوال کا کتا (افسانہ)"],
}

URDU_META_LINES = {
    "سعادت حسن منٹو", "ویکی ماخذ سے", "ڈاؤنلوڈ", "زبانیں شامل کریں",
    "صفحہ", "مطالعہ", "ترمیم", "تاریخچہ", "سانچہ:PD-Pakistan",
}


def clean_urdu_wikisource_html(page_html: str, page_title: str) -> str:
    soup = b.BeautifulSoup(page_html, "html.parser")
    for tag in soup.select(
        "style, script, table, nav, .mw-editsection, .noprint, .ws-noexport, "
        ".mw-cite-backlink, .reference, .mw-references-wrap, .sistersitebox, "
        ".licenseContainer, .printfooter"
    ):
        tag.decompose()

    lines: list[str] = []
    for raw_line in b.normalize_source(soup.get_text("\n")).splitlines():
        line = raw_line.strip()
        if not line:
            if lines and lines[-1] != "":
                lines.append("")
            continue
        if line == page_title or line in URDU_META_LINES:
            continue
        if line.startswith(("اخذ کردہ از", "زمرہ جات", "اس صفحہ میں آخری بار", "تمام متن")):
            break
        if re.fullmatch(r"[\d۰-۹٠-٩ .()\-–—]+", line):
            continue
        if line.startswith("←") or line.startswith("→"):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def mediawiki_search_titles(query_text: str) -> list[str]:
    api = "https://ur.wikisource.org/w/api.php"
    payload = request(
        "GET", api,
        params={
            "action": "query", "list": "search", "srsearch": query_text,
            "srnamespace": "0", "srlimit": "20", "format": "json",
            "formatversion": "2", "maxlag": "5",
        },
    ).json()
    return [item["title"] for item in payload.get("query", {}).get("search", [])]


def fetch_urdu_wikisource_story(title: str, minimum: int) -> tuple[str, str, str]:
    """Pick the fullest exact author-text page and reject wrappers or stubs."""
    api = "https://ur.wikisource.org/w/api.php"
    candidates = list(MANTO_WIKI_TITLES[title])
    urdu_title = candidates[0].split(" (")[0]
    for found in mediawiki_search_titles(f'intitle:"{urdu_title}" "سعادت حسن منٹو"'):
        if found not in candidates and urdu_title in found:
            candidates.append(found)

    scored: list[tuple[int, str, str]] = []
    for candidate in candidates:
        payload = request(
            "GET", api,
            params={
                "action": "parse", "page": candidate, "prop": "text",
                "format": "json", "formatversion": "2", "redirects": "1",
                "maxlag": "5",
            },
        ).json()
        if "error" in payload:
            continue
        text = clean_urdu_wikisource_html(payload.get("parse", {}).get("text", ""), candidate)
        score = b.urdu_count(text)
        print(f"Urdu Wikisource candidate {title}: {candidate}: {len(text)} chars / {score} Urdu", flush=True)
        scored.append((score, candidate, text))
        time.sleep(1.5)

    if not scored:
        raise RuntimeError(f"no Urdu Wikisource candidate resolved for {title}")
    score, candidate, text = max(scored, key=lambda item: item[0])
    required_urdu = max(900, minimum // 2)
    if len(text) < minimum or score < required_urdu:
        details = [(s, c, len(t)) for s, c, t in scored]
        raise RuntimeError(
            f"Urdu Wikisource story too short for {title}: selected {candidate}; "
            f"chars={len(text)}, Urdu={score}, candidates={details}"
        )
    url = "https://ur.wikisource.org/wiki/" + quote(candidate.replace(" ", "_"))
    return text, url, candidate


def ascii_fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.replace("ʾ", "'").replace("ʿ", "'").replace("ə", "a")


@functools.lru_cache(maxsize=100000)
def romanize_urdu_token(token: str) -> str:
    if token in b.URDU_COMMON:
        return b.URDU_COMMON[token]
    if akshara is not None:
        for target in ("RomanColloquial", "RomanReadable", "ITRANS"):
            try:
                converted = akshara.process("Urdu", target, token)
                if converted and not b.urdu_count(converted):
                    return ascii_fold(converted)
            except Exception:
                continue
    return b.urdu_word(token)


def natural_urdu_to_roman(text: str) -> str:
    """Romanize Urdu with a controlled high-frequency lexicon and context engine."""
    text = b.normalize_source(text)
    pieces = re.split(r"(\s+)", text)
    output: list[str] = []
    for piece in pieces:
        if not piece or piece.isspace():
            output.append(piece)
            continue
        if not b.urdu_count(piece):
            output.append(piece)
            continue
        lead_match = re.match(r"^[^\u0600-\u06ff]*", piece)
        trail_match = re.search(r"[^\u0600-\u06ff]*$", piece)
        lead = lead_match.group(0) if lead_match else ""
        trail = trail_match.group(0) if trail_match else ""
        end = len(piece) - len(trail) if trail else len(piece)
        core = piece[len(lead):end]
        output.append(lead + romanize_urdu_token(core) + trail)

    result = "".join(output)
    replacements = {
        "naheen": "nahin", "nahi": "nahin", "kyonke": "kyunki",
        "kyonki": "kyunki", "achha": "achchha", "accha": "achchha",
        "chahye": "chahiye", "zameen": "zameen", "admi": "aadmi",
        "insan": "insaan", "yhan": "yahan", "whan": "wahan",
        "mn": "mein", "hy": "hai", "hyn": "hain", "aurt": "aurat",
    }
    for old, new in replacements.items():
        result = re.sub(rf"\b{re.escape(old)}\b", new, result, flags=re.I)
    result = re.sub(r"[^\x00-\x7F]", lambda m: "" if unicodedata.category(m.group(0)).startswith("M") else m.group(0), result)
    result = re.sub(r"[ \t]+", " ", result)
    result = re.sub(r" *\n *", "\n", result)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def build_manto_from_wikisource():
    qa = []
    for work_id, title, _slug, minimum in b.MANTO:
        source, url, page_title = fetch_urdu_wikisource_story(title, minimum)
        roman = natural_urdu_to_roman(source)
        root = b.WORKS / "manto" / work_id
        b.write(root / "translation.md", f"# {title}\n\n**Saadat Hasan Manto**\n\n{roman}")
        b.write(
            root / "source.md",
            f"# Locked Source Record — {title}\n\n"
            "- Author: Saadat Hasan Manto\n"
            "- Work: complete original Urdu short story\n"
            f"- Urdu Wikisource page: `{page_title}`\n"
            f"- Source URL: `{url}`\n"
            "- Source status: locked for this machine-assisted first pass.\n\n"
            "Navigation, templates, licensing furniture, categories, and site branding are excluded. "
            "No modern translation or paraphrase is used.\n",
        )
        b.write(
            root / "NOTES.md",
            f"# Editorial Notes — {title}\n\n"
            "The complete source sequence and ending are retained. The Roman-Hindustani file is an "
            "uncensored machine-assisted accessibility first pass. Violence, sexuality, Partition trauma, "
            "class signals, satire, repetition, and ambiguity must remain intact during human review.\n\n"
            "Status: `machine_assisted_complete_first_pass`; `human_review: pending`.\n",
        )
        qa.append(
            b.QA(
                f"manto-{work_id}", title, "Saadat Hasan Manto", 1,
                len(source), len(roman), b.dev_count(roman), b.urdu_count(roman),
                b.dev_count(roman) == 0 and b.urdu_count(roman) == 0,
                "machine_assisted_complete_first_pass",
                "Original Urdu Wikisource text; uncensored; full human line review required",
            )
        )
    return qa


b.get = robust_get
b.fetch_wikisource_pages = fetch_wikisource_pages
b.urdu_to_roman = natural_urdu_to_roman
b.build_manto = build_manto_from_wikisource
b.main()
