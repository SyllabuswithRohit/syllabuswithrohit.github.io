#!/usr/bin/env python3
"""Run the classics builder with explicit source and script normalization."""
from __future__ import annotations

import unicodedata

import indic_transliteration.sanscript as sanscript

_original = sanscript.transliterate


def normalized_transliterate(data, _from, _to, *args, **kwargs):
    if isinstance(data, str):
        data = unicodedata.normalize("NFD", data).replace("\u093c", "")
        data = (
            data.replace("ऑ", "ओ")
            .replace("ॉ", "ो")
            .replace("ऍ", "ए")
            .replace("ॅ", "े")
            .replace("�", "")
        )
    return _original(data, _from, _to, *args, **kwargs)


sanscript.transliterate = normalized_transliterate

# Import only after patching so the builder's `from ... import transliterate`
# binds to the normalized implementation.
import classics_builder  # noqa: E402

classics_builder.transliterate = normalized_transliterate

# The older placeholder identifier no longer exposes a text derivative.  The
# 1908 Toronto scan is the same public-domain work and has an IA plain-text OCR.
_original_archive_ocr = classics_builder.archive_ocr


def normalized_archive_ocr(identifier: str):
    identifiers = (
        ["urduimualla01ghaluoft", identifier]
        if identifier == "urduemualla"
        else [identifier]
    )
    last_error = None
    for candidate in identifiers:
        try:
            return _original_archive_ocr(candidate)
        except Exception as exc:  # preserve the builder's actionable final error
            last_error = exc
    assert last_error is not None
    raise last_error


classics_builder.archive_ocr = normalized_archive_ocr

if __name__ == "__main__":
    classics_builder.main()
