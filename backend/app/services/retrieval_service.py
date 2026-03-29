from __future__ import annotations

import asyncio

from app.repositories.chroma_repository import ChromaRepository, ChromaRepositoryError
from app.schemas.chat import RetrievedChunk
from app.services.embedding_service import EmbeddingService, EmbeddingServiceError


class RetrievalNoIndexedPapersError(RuntimeError):
    """Raised when no indexed chunks are available for retrieval."""


class RetrievalNoRelevantChunksError(RuntimeError):
    """Raised when retrieval does not return any relevant chunks."""


class RetrievalServiceError(RuntimeError):
    """Raised when retrieval infrastructure fails."""


class RetrievalService:
    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        chroma_repository: ChromaRepository | None = None,
    ) -> None:
        self._embedding_service = embedding_service or EmbeddingService()
        self._chroma_repository = chroma_repository or ChromaRepository()

    async def retrieve_chunks(
        self,
        question: str,
        *,
        paper_ids: list[str] | None = None,
        top_k: int,
    ) -> list[RetrievedChunk]:
        normalized_question = question.strip()
        if not normalized_question:
            raise ValueError("Question must not be blank.")

        try:
            indexed_chunk_count = await asyncio.to_thread(
                self._chroma_repository.count_chunks,
                paper_ids or None,
            )
        except ChromaRepositoryError as exc:
            raise RetrievalServiceError(str(exc)) from exc

        if indexed_chunk_count == 0:
            if paper_ids:
                raise RetrievalNoIndexedPapersError(
                    "No indexed chunks are available for the requested paper IDs yet."
                )
            raise RetrievalNoIndexedPapersError(
                "No indexed papers are available yet. Index one or more papers before starting a chat."
            )

        try:
            question_embeddings = await asyncio.to_thread(
                self._embedding_service.embed_documents,
                [normalized_question],
            )
        except EmbeddingServiceError as exc:
            raise RetrievalServiceError(str(exc)) from exc

        if not question_embeddings:
            raise RetrievalServiceError("Failed to generate a query embedding for chat retrieval.")

        try:
            chunks = await asyncio.to_thread(
                self._chroma_repository.query_chunks,
                question_embeddings[0],
                top_k,
                paper_ids or None,
            )
        except ChromaRepositoryError as exc:
            raise RetrievalServiceError(str(exc)) from exc

        if not chunks:
            if paper_ids:
                raise RetrievalNoRelevantChunksError(
                    "No relevant chunks were retrieved for this question within the requested paper IDs."
                )
            raise RetrievalNoRelevantChunksError(
                "No relevant chunks were retrieved for this question. Try indexing more papers or narrowing the question."
            )

        return chunks
