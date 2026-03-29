from __future__ import annotations

import asyncio
from functools import lru_cache

from sentence_transformers import CrossEncoder

from app.core.config import Settings, get_settings
from app.schemas.chat import RetrievedChunk


class RerankingServiceError(RuntimeError):
    """Raised when reranking cannot be completed and the caller should fall back."""


@lru_cache(maxsize=2)
def _load_reranker(model_name: str) -> CrossEncoder:
    return CrossEncoder(model_name)


class RerankingService:
    def __init__(
        self,
        settings: Settings | None = None,
        model_name: str | None = None,
        enabled: bool | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._model_name = model_name or self._settings.reranker_model
        self._enabled = self._settings.reranking_enabled if enabled is None else enabled

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def rerank_chunks(
        self,
        question: str,
        chunks: list[RetrievedChunk],
        *,
        top_k: int,
    ) -> list[RetrievedChunk]:
        if not self._enabled or len(chunks) <= 1:
            return chunks[:top_k]

        try:
            scores = await asyncio.to_thread(self._score_chunks, question, chunks)
        except Exception as exc:
            raise RerankingServiceError(
                f"Failed to rerank retrieved chunks with local model '{self._model_name}'."
            ) from exc

        reranked = sorted(zip(chunks, scores), key=lambda item: item[1], reverse=True)
        return [chunk for chunk, _ in reranked[:top_k]]

    def _score_chunks(self, question: str, chunks: list[RetrievedChunk]) -> list[float]:
        model = _load_reranker(self._model_name)
        predictions = model.predict(
            [(question, chunk.text) for chunk in chunks],
            show_progress_bar=False,
        )
        return [float(score) for score in predictions]
