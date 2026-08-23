#!/usr/bin/env python3
"""Run the classics builder with explicit Devanagari normalization."""
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

if __name__ == "__main__":
    classics_builder.main()
