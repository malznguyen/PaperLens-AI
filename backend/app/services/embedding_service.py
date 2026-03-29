from __future__ import annotations

from functools import lru_cache
from typing import Sequence

from sentence_transformers import SentenceTransformer

from app.core.config import Settings, get_settings


class EmbeddingServiceError(RuntimeError):
    """Raised when embeddings cannot be generated locally."""


@lru_cache(maxsize=4)
def _load_model(model_name: str) -> SentenceTransformer:
    return SentenceTransformer(model_name)


class EmbeddingService:
    def __init__(
        self,
        settings: Settings | None = None,
        model_name: str | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._model_name = model_name or self._settings.embedding_model

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        normalized_texts = [text.strip() for text in texts]
        if not normalized_texts:
            return []

        if any(not text for text in normalized_texts):
            raise EmbeddingServiceError("Cannot generate embeddings for empty chunk text.")

        try:
            model = _load_model(self._model_name)
            embeddings = model.encode(
                normalized_texts,
                batch_size=32,
                show_progress_bar=False,
                normalize_embeddings=True,
                convert_to_numpy=True,
            )
        except Exception as exc:
            raise EmbeddingServiceError(
                f"Failed to generate embeddings with local model '{self._model_name}'."
            ) from exc

        return embeddings.tolist()
