#!/usr/bin/env python3
"""Normalized entrypoint for the Premchand novels builder.

Some Godaan source files preserve their complete text in only four large blank-line
blocks while still using single newlines for dialogue and paragraph boundaries.
This wrapper accepts that source layout without weakening character-count or
chapter-count validation.
"""

from __future__ import annotations

import re
from pathlib import Path

import premchand_novels_builder as builder


def robust_paragraphs_from_plain(text: str) -> list[str]:
    text = builder.normalize_source(text)
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    if len(blocks) < 5:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if lines:
            return lines
    return blocks


builder.paragraphs_from_plain = robust_paragraphs_from_plain

# Remove stale diagnostics only when beginning a fresh, auditable run. A new
# failure file is written by builder.main if this invocation fails.
stale = builder.OUT / "BUILD_FAILURE.txt"
if stale.exists():
    stale.unlink()

raise SystemExit(builder.main())
