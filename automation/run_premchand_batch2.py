#!/usr/bin/env python3
"""Run the Premchand batch builder with punctuation normalization diagnostics."""

from __future__ import annotations

import re

import build_premchand_batch2 as builder

_base_romanize = builder.romanize


def romanize_with_punctuation_cleanup(text: str) -> str:
    output = _base_romanize(text)
    output = (
        output.replace("।", ".")
        .replace("॥", ".")
        .replace("॰", ".")
        .replace("ऽ", "'")
    )
    # Some source transcriptions contain isolated Vedic/ornamental Devanagari marks.
    # They carry no lexical content and are removed only after ordinary letters have
    # already passed through the transliterator.
    output = re.sub(r"[\u0900-\u0903\u093a-\u094f\u0951-\u0963\u0970-\u097f]", "", output)
    bad = re.search(r"[\u0900-\u097f\u0600-\u06ff]", output)
    if bad:
        raise RuntimeError(
            f"unconverted character U+{ord(bad.group()):04X} {bad.group()!r} remains"
        )
    return output


builder.romanize = romanize_with_punctuation_cleanup

if __name__ == "__main__":
    raise SystemExit(builder.main())
