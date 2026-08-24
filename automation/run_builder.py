#!/usr/bin/env python3
"""Rate-limit-safe entry point for build_all_classics."""
from __future__ import annotations

import json
import re
import time
from typing import Any

import build_all_classics as b


def request(method: str, url: str, **kwargs: Any):
    last = None
    for attempt in range(8):
        try:
            r = b.S.request(method, url, timeout=120, **kwargs)
            if r.status_code in {429, 500, 502, 503, 504}:
                delay = int(r.headers.get("Retry-After", "0") or 0) or min(60, 3 * (2 ** attempt))
                print(f"retry {r.status_code} {url} after {delay}s", flush=True)
                time.sleep(delay)
                continue
            r.raise_for_status()
            return r
        except Exception as exc:
            last = exc
            time.sleep(min(60, 3 * (2 ** attempt)))
    raise RuntimeError(f"request failed after retries: {url}: {last}")


def robust_get(url: str, min_chars: int = 1, retries: int = 4) -> str:
    r = request("GET", url)
    if len(r.text) < min_chars:
        raise RuntimeError(f"suspiciously short response {len(r.text)} chars: {url}")
    return r.text


def fetch_wikisource_pages(category: str, prefix: str):
    api = "https://hi.wikisource.org/w/api.php"
    data = request("GET", api, params={
        "action": "query", "list": "categorymembers",
        "cmtitle": f"Category:{category}", "cmnamespace": "0",
        "cmlimit": "500", "format": "json", "formatversion": "2",
        "maxlag": "5",
    }).json()
    titles = sorted(
        {x["title"] for x in data["query"]["categorymembers"] if x["title"].startswith(prefix + "/")},
        key=b.natural_number,
    )
    # One POST replaces 24 separate parse requests and avoids Wikimedia rate limiting.
    payload = {
        "action": "query", "prop": "extracts", "explaintext": "1",
        "exsectionformat": "plain", "titles": "|".join(titles),
        "format": "json", "formatversion": "2", "maxlag": "5",
    }
    result = request("POST", api, data=payload).json()
    found = {p["title"]: p.get("extract", "") for p in result["query"]["pages"]}
    pages = []
    for title in titles:
        text = b.normalize_source(found.get(title, ""))
        lines = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                if lines and lines[-1] != "":
                    lines.append("")
                continue
            if line in {"पिछला पृष्ठ", "अगला पृष्ठ", "विषयसूची", "निर्मला"}:
                continue
            if re.fullmatch(r"[\d ]+", line):
                continue
            lines.append(line)
        text = "\n".join(lines).strip()
        if len(text) < 1500:
            raise RuntimeError(f"Wikisource extract too short: {title}: {len(text)} chars")
        pages.append((b.natural_number(title), title, text))
    return pages


b.get = robust_get
b.fetch_wikisource_pages = fetch_wikisource_pages
b.main()
