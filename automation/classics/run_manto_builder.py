#!/usr/bin/env python3
"""Normalized entrypoint for the eight-story Manto builder.

Rekhta's rendered DOM may expose individual words on separate lines. This wrapper
reconstructs prose paragraphs, normalizes mixed nukta spellings before controlled
vocabulary replacement, and uses the reader-oriented Roman converter.
"""

from __future__ import annotations

import re

import manto_builder as builder
from reader_roman import romanize_devanagari

_base_extract = builder.extract_story


def paragraph_preserving_extract(text: str, starts: list[str], min_chars: int) -> str:
    story = _base_extract(text, starts, min_chars)
    blocks = [block.strip() for block in re.split(r"\n\s*\n", story) if block.strip()]
    rebuilt = []
    for block in blocks:
        # Join DOM word/phrase lines inside a source paragraph; keep blank-line
        # boundaries between paragraphs.
        rebuilt.append(re.sub(r"\s*\n\s*", " ", block).strip())
    result = "\n\n".join(rebuilt).strip()
    if len(result) < int(min_chars * 0.85):
        raise RuntimeError(
            f"Paragraph reconstruction unexpectedly reduced source: {len(result)} < {min_chars * 0.85:.0f}"
        )
    return result


def canonical_easy_source(text: str) -> str:
    # Rekhta uses both precomposed nukta letters and base letters plus a combining
    # nukta. Canonicalize both source and lexicon keys so the same difficult word
    # is replaced consistently.
    normalized = builder.canonical(text)
    for old, new in sorted(builder.MANTO_EASY.items(), key=lambda item: len(item[0]), reverse=True):
        normalized = normalized.replace(builder.canonical(old), new)
    return normalized


builder.extract_story = paragraph_preserving_extract
builder.easy_source = canonical_easy_source
builder.romanize = romanize_devanagari

stale = builder.OUT / "MANTO_BUILD_FAILURE.txt"
if stale.exists():
    stale.unlink()

raise SystemExit(builder.main())
