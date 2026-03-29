from __future__ import annotations

import re

WORD_RE = re.compile(r"\b\w+\b", re.UNICODE)


def count_words(value: str) -> int:
    return len(WORD_RE.findall(value))
