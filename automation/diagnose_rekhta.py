#!/usr/bin/env python3
"""Inspect Rekhta HTML for embedded story data without reproducing the story."""
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

URL = "https://www.rekhta.org/stories/toba-tek-singh-saadat-hasan-manto-stories?lang=hi"
OUT = Path("generated/logs/rekhta-diagnostic.txt")
OUT.parent.mkdir(parents=True, exist_ok=True)

html = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=90).text
soup = BeautifulSoup(html, "html.parser")
lines: list[str] = [f"url={URL}", f"html_chars={len(html)}", f"script_count={len(soup.find_all('script'))}", ""]

needles = ["__NEXT_DATA__", "__NUXT__", "storyContent", "readContent", "initialState", "apollo", "dehydratedState", "pageProps", "toba", "टेक", "سنگھ"]
for needle in needles:
    lines.append(f"contains[{needle}]={needle.lower() in html.lower()}")
lines.append("")

for i, script in enumerate(soup.find_all("script")):
    text = script.string or script.get_text(" ") or ""
    attrs = {k: v for k, v in script.attrs.items() if k in {"id", "type", "src"}}
    indic = len(re.findall(r"[\u0900-\u097f\u0600-\u06ff]", text))
    urls = sorted(set(re.findall(r"https?://[^\"'<>\\ ]+|/[A-Za-z0-9_./?=&%-]*(?:api|story|content)[A-Za-z0-9_./?=&%-]*", text, re.I)))[:30]
    lines.append(f"SCRIPT {i}: attrs={attrs!r} chars={len(text)} indic={indic} urls={urls!r}")
    if text.strip().startswith(("{", "[")):
        try:
            obj = json.loads(text)
            if isinstance(obj, dict):
                lines.append(f"  json_keys={list(obj)[:80]!r}")
            else:
                lines.append(f"  json_type={type(obj).__name__} len={len(obj)}")
        except Exception as exc:
            lines.append(f"  json_error={type(exc).__name__}: {exc}")
    if indic:
        snippets = []
        for match in re.finditer(r".{0,160}[\u0900-\u097f\u0600-\u06ff].{0,500}", text, re.S):
            snip = re.sub(r"\s+", " ", match.group(0))[:700]
            if snip not in snippets:
                snippets.append(snip)
            if len(snippets) == 8:
                break
        for snip in snippets:
            lines.append("  INDIC_SNIPPET=" + snip.encode("unicode_escape").decode("ascii"))

lines.append("\nHTML attributes containing likely data keys:")
for tag in soup.find_all(True):
    hit = {k: v for k, v in tag.attrs.items() if any(n.lower() in k.lower() for n in ["story", "content", "data", "read"])}
    if hit:
        lines.append(f"{tag.name}: {str(hit)[:1200]}")

lines.append("\nReferenced likely endpoints/assets:")
refs = set()
for tag in soup.find_all(["script", "link", "a"]):
    ref = tag.get("src") or tag.get("href")
    if ref and any(x in ref.lower() for x in ["api", "story", "content", "_next", "bundle", "main"]):
        refs.add(urljoin(URL, ref))
for ref in sorted(refs):
    lines.append(ref)

OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(OUT)
