#!/usr/bin/env python3
"""Normalized entrypoint for the Premchand novels builder.

This wrapper accepts sparse source paragraph layouts without dropping text and
uses the reader-oriented Roman-Hindustani converter rather than the rough
fallback transliterator in the base fetcher.
"""

from __future__ import annotations

import re

import premchand_novels_builder as builder
from reader_roman import romanize_devanagari


def robust_paragraphs_from_plain(text: str) -> list[str]:
    text = builder.normalize_source(text)
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    if len(blocks) < 5:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if lines:
            return lines
    return blocks


def safe_reader_roman(text: str) -> str:
    output = romanize_devanagari(text)
    # Preserve rare/old Devanagari signs by converting each residual token with
    # the project's explicit fallback rather than deleting it.
    output = builder.DEV_TOKEN_RE.sub(
        lambda match: builder.transliterate_word(match.group(0)), output
    )
    output = output.replace("़", "")
    return output


builder.paragraphs_from_plain = robust_paragraphs_from_plain
builder.romanize = safe_reader_roman

# Remove stale diagnostics only when beginning a fresh, auditable run. A new
# failure file is written by builder.main if this invocation fails.
stale = builder.OUT / "BUILD_FAILURE.txt"
if stale.exists():
    stale.unlink()

raise SystemExit(builder.main())
