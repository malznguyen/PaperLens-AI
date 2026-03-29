from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import chromadb
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.schemas.chat import RetrievedChunk
from app.schemas.indexing import IndexedChunk


class ChromaRepositoryError(RuntimeError):
    """Raised when Chroma operations fail."""


@dataclass(frozen=True)
class IndexedPaperSnapshot:
    paper_id: str
    paper_title: str | None
    source_url: str | None
    pdf_path: str | None
    chunk_count: int


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
        return self.count_chunks([paper_id])

    def count_chunks(self, paper_ids: list[str] | None = None) -> int:
        collection = self._get_collection()

        try:
            where_filter = self._build_where_filter(paper_ids)
            if where_filter is None:
                return int(collection.count())

            result = collection.get(where=where_filter)
        except Exception as exc:
            raise ChromaRepositoryError("Failed to read indexed chunks from Chroma.") from exc

        ids = result.get("ids", [])
        return len(ids)

    def query_chunks(
        self,
        query_embedding: list[float],
        limit: int,
        paper_ids: list[str] | None = None,
    ) -> list[RetrievedChunk]:
        if limit <= 0:
            return []

        collection = self._get_collection()
        query_kwargs: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": limit,
            "include": ["documents", "metadatas", "distances"],
        }

        where_filter = self._build_where_filter(paper_ids)
        if where_filter is not None:
            query_kwargs["where"] = where_filter

        try:
            result = collection.query(**query_kwargs)
        except Exception as exc:
            raise ChromaRepositoryError("Failed to query indexed chunks from Chroma.") from exc

        return self._build_retrieved_chunks(result)

    def list_indexed_papers(self) -> list[IndexedPaperSnapshot]:
        collection = self._get_collection()

        try:
            result = collection.get(include=["metadatas"])
        except Exception as exc:
            raise ChromaRepositoryError("Failed to inspect indexed papers in Chroma.") from exc

        metadatas = result.get("metadatas") or []
        snapshots: dict[str, IndexedPaperSnapshot] = {}

        for metadata in metadatas:
            if not isinstance(metadata, dict):
                continue

            paper_id = metadata.get("paper_id")
            if not isinstance(paper_id, str) or not paper_id.strip():
                continue

            normalized_paper_id = paper_id.strip()
            current = snapshots.get(normalized_paper_id)
            chunk_count = 1 if current is None else current.chunk_count + 1

            paper_title = metadata.get("paper_title")
            source_url = metadata.get("source_url")
            pdf_path = metadata.get("pdf_path")

            snapshots[normalized_paper_id] = IndexedPaperSnapshot(
                paper_id=normalized_paper_id,
                paper_title=(
                    str(paper_title)
                    if isinstance(paper_title, str)
                    else current.paper_title if current else None
                ),
                source_url=(
                    str(source_url)
                    if isinstance(source_url, str)
                    else current.source_url if current else None
                ),
                pdf_path=(
                    str(pdf_path)
                    if isinstance(pdf_path, str)
                    else current.pdf_path if current else None
                ),
                chunk_count=chunk_count,
            )

        return list(snapshots.values())

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

    def _build_retrieved_chunks(self, result: dict[str, Any]) -> list[RetrievedChunk]:
        ids = (result.get("ids") or [[]])[0]
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]

        chunks: list[RetrievedChunk] = []
        for index, chunk_id in enumerate(ids):
            metadata = metadatas[index] if index < len(metadatas) else {}
            document = documents[index] if index < len(documents) else ""
            distance = distances[index] if index < len(distances) else None

            similarity_score = None
            if distance is not None:
                similarity_score = max(-1.0, min(1.0, 1.0 - float(distance)))

            try:
                chunks.append(
                    RetrievedChunk(
                        chunk_id=chunk_id,
                        paper_id=str(metadata["paper_id"]),
                        paper_title=str(metadata["paper_title"]),
                        page_number=int(metadata["page_number"]),
                        chunk_index=int(metadata["chunk_index"]),
                        page_chunk_index=int(metadata["page_chunk_index"]),
                        source_url=str(metadata["source_url"]),
                        pdf_path=str(metadata["pdf_path"]),
                        text=str(document),
                        word_count=int(metadata["word_count"]),
                        start_word_index=int(metadata["start_word_index"]),
                        end_word_index=int(metadata["end_word_index"]),
                        similarity_score=similarity_score,
                    )
                )
            except (KeyError, TypeError, ValueError, ValidationError) as exc:
                raise ChromaRepositoryError(
                    "Indexed chunk metadata in Chroma is invalid for chat retrieval."
                ) from exc

        return chunks

    @staticmethod
    def _build_where_filter(paper_ids: list[str] | None) -> dict[str, Any] | None:
        if not paper_ids:
            return None

        if len(paper_ids) == 1:
            return {"paper_id": paper_ids[0]}

        return {"paper_id": {"$in": paper_ids}}
