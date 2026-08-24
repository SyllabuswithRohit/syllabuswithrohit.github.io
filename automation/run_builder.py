#!/usr/bin/env python3
"""Rate-limit-safe entry point for build_all_classics."""
from __future__ import annotations

import re
import time
from typing import Any

import build_all_classics as b


def request(method: str, url: str, **kwargs: Any):
    """Make a request with Wikimedia-friendly retry and backoff."""
    last = None
    for attempt in range(8):
        try:
            response = b.S.request(method, url, timeout=120, **kwargs)
            if response.status_code in {429, 500, 502, 503, 504}:
                retry_after = int(response.headers.get("Retry-After", "0") or 0)
                delay = retry_after or min(90, 4 * (2 ** attempt))
                print(
                    f"retry {response.status_code} {url} after {delay}s",
                    flush=True,
                )
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
        raise RuntimeError(
            f"suspiciously short response {len(response.text)} chars: {url}"
        )
    return response.text


def clean_wikisource_html(page_html: str, title: str) -> str:
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
        if line in {
            "पिछला पृष्ठ",
            "अगला पृष्ठ",
            "विषयसूची",
            "निर्मला",
            title,
        }:
            continue
        if re.fullmatch(r"[\d ]+", line.translate(b.DEV_DIGITS)):
            continue
        if line.startswith("यह पृष्ठ अंतिम बार") or line.startswith("यह पाठ"):
            continue
        lines.append(line)

    return "\n".join(lines).strip()


def fetch_wikisource_pages(category: str, prefix: str):
    """Fetch all Nirmala chapters with paced parse calls.

    TextExtracts is empty for transcluded Wikisource proofread pages, so this uses
    action=parse. Calls are deliberately spaced and every 429 respects Retry-After.
    """
    api = "https://hi.wikisource.org/w/api.php"
    data = request(
        "GET",
        api,
        params={
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmnamespace": "0",
            "cmlimit": "500",
            "format": "json",
            "formatversion": "2",
            "maxlag": "5",
        },
    ).json()
    titles = sorted(
        {
            item["title"]
            for item in data["query"]["categorymembers"]
            if item["title"].startswith(prefix + "/")
        },
        key=b.natural_number,
    )
    if len(titles) != 24:
        raise RuntimeError(
            f"expected 24 {prefix} chapter titles, received {len(titles)}: {titles}"
        )

    pages = []
    for index, title in enumerate(titles, start=1):
        print(f"Wikisource {index:02d}/{len(titles)}: {title}", flush=True)
        response = request(
            "GET",
            api,
            params={
                "action": "parse",
                "page": title,
                "prop": "text",
                "format": "json",
                "formatversion": "2",
                "maxlag": "5",
                "redirects": "1",
            },
        )
        payload = response.json()
        if "error" in payload:
            raise RuntimeError(f"Wikisource parse error for {title}: {payload['error']}")
        page_html = payload.get("parse", {}).get("text", "")
        text = clean_wikisource_html(page_html, title)
        if len(text) < 1500 or b.dev_count(text) < 800:
            raise RuntimeError(
                f"Wikisource chapter too short after cleanup: {title}: "
                f"{len(text)} chars, {b.dev_count(text)} Devanagari chars"
            )
        pages.append((b.natural_number(title), title, text))
        # The public runner shares an IP pool. A three-second gap avoids bursts.
        time.sleep(3.0)
    return pages


b.get = robust_get
b.fetch_wikisource_pages = fetch_wikisource_pages
b.main()
