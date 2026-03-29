from __future__ import annotations

from typing import Any

import chromadb

from app.core.config import Settings, get_settings
from app.schemas.indexing import IndexedChunk


class ChromaRepositoryError(RuntimeError):
    """Raised when Chroma operations fail."""


class ChromaRepository:
    def __init__(
        self,
        settings: Settings | None = None,
        client: Any | None = None,
        collection_name: str | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._collection_name = collection_name or self._settings.chroma_collection_name
        self._client = client or chromadb.PersistentClient(path=str(self._settings.chroma_dir))
        self._collection = None

    @property
    def collection_name(self) -> str:
        return self._collection_name

    def replace_paper_chunks(
        self,
        chunks: list[IndexedChunk],
        embeddings: list[list[float]],
    ) -> None:
        if len(chunks) != len(embeddings):
            raise ChromaRepositoryError("Chunk and embedding counts do not match.")

        paper_id = chunks[0].paper_id if chunks else None
        collection = self._get_collection()

        try:
            if paper_id is not None:
                collection.delete(where={"paper_id": paper_id})

            if chunks:
                collection.upsert(
                    ids=[chunk.chunk_id for chunk in chunks],
                    documents=[chunk.text for chunk in chunks],
                    embeddings=embeddings,
                    metadatas=[chunk.to_chroma_metadata() for chunk in chunks],
                )
        except Exception as exc:
            raise ChromaRepositoryError("Failed to write indexed chunks to Chroma.") from exc

    def count_chunks_for_paper(self, paper_id: str) -> int:
        collection = self._get_collection()

        try:
            result = collection.get(where={"paper_id": paper_id})
        except Exception as exc:
            raise ChromaRepositoryError("Failed to read indexed chunks from Chroma.") from exc

        ids = result.get("ids", [])
        return len(ids)

    def _get_collection(self):
        if self._collection is None:
            try:
                self._collection = self._client.get_or_create_collection(
                    name=self._collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
            except Exception as exc:
                raise ChromaRepositoryError("Failed to open the Chroma collection.") from exc

        return self._collection
