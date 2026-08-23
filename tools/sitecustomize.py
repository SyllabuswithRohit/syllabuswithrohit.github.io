"""Runtime normalization for the temporary classics builder.

Python imports this module automatically when `tools/classics_builder.py` is
executed.  It normalizes Devanagari nukta variants before the transliteration
library sees them, without changing source order or deleting prose.
"""
from __future__ import annotations

import unicodedata

try:
    import indic_transliteration.sanscript as _sanscript

    _original_transliterate = _sanscript.transliterate

    def _normalized_transliterate(data, _from, _to, *args, **kwargs):
        if isinstance(data, str):
            # Decompose every precomposed nukta letter and remove only the
            # combining nukta sign.  Also normalize rare modern vowel signs
            # that the library can otherwise pass through unchanged.
            data = unicodedata.normalize("NFD", data).replace("\u093c", "")
            data = (
                data.replace("ऑ", "ओ")
                .replace("ॉ", "ो")
                .replace("ऍ", "ए")
                .replace("ॅ", "े")
                .replace("�", "")
            )
        return _original_transliterate(data, _from, _to, *args, **kwargs)

    _sanscript.transliterate = _normalized_transliterate
except Exception:
    # The dependency is installed immediately before the builder runs.  If it
    # is unavailable during an unrelated Python invocation, do nothing.
    pass
