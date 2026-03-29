from __future__ import annotations

from app.schemas.chat import RetrievedChunk
from app.utils.chunk_utils import normalize_whitespace


def truncate_text_for_prompt(text: str, max_chars: int) -> str:
    normalized = normalize_whitespace(text)
    if len(normalized) <= max_chars:
        return normalized

    truncated = normalized[: max_chars - 3].rstrip()
    if " " in truncated:
        truncated = truncated.rsplit(" ", 1)[0]
    return truncated.rstrip() + "..."


def select_context_chunks(
    chunks: list[RetrievedChunk],
    *,
    max_chunk_chars: int,
    max_context_chars: int,
) -> list[RetrievedChunk]:
    selected_chunks: list[RetrievedChunk] = []
    current_length = 0

    for chunk in chunks:
        chunk_block = render_chunk_for_prompt(chunk, max_chunk_chars=max_chunk_chars)
        if selected_chunks and current_length + len(chunk_block) > max_context_chars:
            break

        selected_chunks.append(chunk)
        current_length += len(chunk_block)

    return selected_chunks or chunks[:1]


def build_context_block(
    chunks: list[RetrievedChunk],
    *,
    max_chunk_chars: int,
) -> str:
    return "\n\n".join(
        render_chunk_for_prompt(chunk, max_chunk_chars=max_chunk_chars)
        for chunk in chunks
    )


def render_chunk_for_prompt(
    chunk: RetrievedChunk,
    *,
    max_chunk_chars: int,
) -> str:
    return (
        f"[{chunk.label}]\n"
        f"paper_id: {chunk.paper_id}\n"
        f"paper_title: {chunk.paper_title}\n"
        f"page_number: {chunk.page_number}\n"
        f"chunk_id: {chunk.chunk_id}\n"
        f"source_url: {chunk.source_url}\n"
        f"text: {truncate_text_for_prompt(chunk.text, max_chunk_chars)}"
    )
