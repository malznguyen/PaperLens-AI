from __future__ import annotations

from app.core.config import Settings, get_settings
from app.schemas.ingest import ParsedPaperDocument
from app.schemas.indexing import IndexedChunk
from app.utils.chunk_utils import normalize_whitespace, split_text_into_word_windows
from app.utils.hash_utils import build_chunk_id
from app.utils.text_utils import count_words


class ChunkingService:
    def __init__(
        self,
        settings: Settings | None = None,
        chunk_size_words: int | None = None,
        chunk_overlap_words: int | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._chunk_size_words = chunk_size_words or self._settings.chunk_size_words
        self._chunk_overlap_words = (
            chunk_overlap_words
            if chunk_overlap_words is not None
            else self._settings.chunk_overlap_words
        )

    def chunk_document(
        self,
        document: ParsedPaperDocument,
        *,
        content_hash: str,
    ) -> list[IndexedChunk]:
        chunks: list[IndexedChunk] = []
        chunk_index = 0

        for page in sorted(document.pages, key=lambda item: item.page_number):
            normalized_page_text = normalize_whitespace(page.text)
            if not normalized_page_text:
                continue

            page_windows = split_text_into_word_windows(
                normalized_page_text,
                chunk_size_words=self._chunk_size_words,
                chunk_overlap_words=self._chunk_overlap_words,
            )

            for page_chunk_index, window in enumerate(page_windows):
                word_count = count_words(window.text)
                if word_count == 0:
                    continue

                chunks.append(
                    IndexedChunk(
                        chunk_id=build_chunk_id(
                            document.paper_id,
                            page.page_number,
                            chunk_index,
                            window.text,
                        ),
                        paper_id=document.paper_id,
                        paper_title=document.title,
                        page_number=page.page_number,
                        chunk_index=chunk_index,
                        page_chunk_index=page_chunk_index,
                        source_url=document.source_url,
                        pdf_path=document.pdf_path,
                        text=window.text,
                        word_count=word_count,
                        content_hash=content_hash,
                        start_word_index=window.start_word_index,
                        end_word_index=window.end_word_index,
                    )
                )
                chunk_index += 1

        return chunks
