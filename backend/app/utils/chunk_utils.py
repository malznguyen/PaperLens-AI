from __future__ import annotations

import re
from dataclasses import dataclass

WHITESPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class WordChunkWindow:
    text: str
    start_word_index: int
    end_word_index: int


def normalize_whitespace(value: str) -> str:
    return WHITESPACE_RE.sub(" ", value).strip()


def split_text_into_word_windows(
    text: str,
    chunk_size_words: int,
    chunk_overlap_words: int,
) -> list[WordChunkWindow]:
    normalized_text = normalize_whitespace(text)
    if not normalized_text:
        return []

    if chunk_size_words <= 0:
        raise ValueError("chunk_size_words must be greater than zero.")

    safe_overlap = max(0, min(chunk_overlap_words, chunk_size_words - 1))
    step = max(1, chunk_size_words - safe_overlap)
    words = normalized_text.split(" ")
    windows: list[WordChunkWindow] = []
    start = 0

    while start < len(words):
        end = min(start + chunk_size_words, len(words))
        chunk_words = words[start:end]
        if chunk_words:
            windows.append(
                WordChunkWindow(
                    text=" ".join(chunk_words),
                    start_word_index=start,
                    end_word_index=end,
                )
            )

        if end >= len(words):
            break

        start += step

    return windows
