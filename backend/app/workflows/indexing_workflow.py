from __future__ import annotations

import asyncio
from pathlib import Path

from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.repositories.chroma_repository import ChromaRepository
from app.schemas.ingest import ParsedPaperDocument
from app.schemas.indexing import IndexCacheRecord, IndexedChunk, IndexPaperRequest, IndexPaperResponse
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.utils.file_utils import build_storage_stem, write_text_file
from app.utils.hash_utils import compute_parsed_document_hash


class ParsedArtifactNotFoundError(FileNotFoundError):
    """Raised when a parsed paper artifact cannot be found for indexing."""


class ParsedArtifactInvalidError(RuntimeError):
    """Raised when a parsed paper artifact exists but is invalid."""


class IndexingWorkflowNoContentError(RuntimeError):
    """Raised when a parsed artifact has no page-aware text that can be indexed."""


class IndexingWorkflowStorageError(RuntimeError):
    """Raised when indexing cache artifacts cannot be read or written."""


class IndexingWorkflow:
    def __init__(
        self,
        chunking_service: ChunkingService | None = None,
        embedding_service: EmbeddingService | None = None,
        chroma_repository: ChromaRepository | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._chunking_service = chunking_service or ChunkingService(settings=self._settings)
        self._embedding_service = embedding_service or EmbeddingService(settings=self._settings)
        self._chroma_repository = chroma_repository or ChromaRepository(settings=self._settings)

    async def index_paper(self, payload: IndexPaperRequest) -> IndexPaperResponse:
        self._settings.ensure_directories()

        parsed_path = self._resolve_parsed_path(payload.paper_id)
        parsed_document = self._load_parsed_document(parsed_path)
        content_hash = compute_parsed_document_hash(parsed_document)
        cached_record = self._load_index_cache(payload.paper_id)

        if cached_record is not None and cached_record.content_hash == content_hash:
            stored_chunk_count = await asyncio.to_thread(
                self._chroma_repository.count_chunks_for_paper,
                payload.paper_id,
            )
            if stored_chunk_count == cached_record.chunk_count and stored_chunk_count > 0:
                return IndexPaperResponse(
                    paper_id=payload.paper_id,
                    status="cached",
                    chunk_count=stored_chunk_count,
                    collection_name=self._chroma_repository.collection_name,
                    message="Paper already indexed; using cached vectors.",
                )

        chunks = self._build_chunks(parsed_document, content_hash)
        embeddings = await asyncio.to_thread(
            self._embedding_service.embed_documents,
            [chunk.text for chunk in chunks],
        )

        await asyncio.to_thread(self._chroma_repository.replace_paper_chunks, chunks, embeddings)
        self._write_index_cache(
            payload.paper_id,
            IndexCacheRecord(
                paper_id=payload.paper_id,
                content_hash=content_hash,
                chunk_count=len(chunks),
                collection_name=self._chroma_repository.collection_name,
            ),
        )

        return IndexPaperResponse(
            paper_id=payload.paper_id,
            status="completed",
            chunk_count=len(chunks),
            collection_name=self._chroma_repository.collection_name,
            message="Paper indexed successfully.",
        )

    def _resolve_parsed_path(self, paper_id: str) -> Path:
        parsed_path = self._settings.parsed_dir / f"{build_storage_stem(paper_id)}.json"
        if not parsed_path.exists():
            raise ParsedArtifactNotFoundError(
                f"Parsed artifact not found for paper '{paper_id}'. Ingest the paper before indexing it."
            )
        return parsed_path

    def _load_parsed_document(self, parsed_path: Path) -> ParsedPaperDocument:
        try:
            raw_json = parsed_path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise ParsedArtifactNotFoundError("Parsed artifact could not be found.") from exc
        except OSError as exc:
            raise IndexingWorkflowStorageError("Failed to read the parsed paper artifact.") from exc

        try:
            return ParsedPaperDocument.model_validate_json(raw_json)
        except ValidationError as exc:
            raise ParsedArtifactInvalidError(
                "Parsed artifact is invalid and could not be indexed."
            ) from exc

    def _load_index_cache(self, paper_id: str) -> IndexCacheRecord | None:
        cache_path = self._index_cache_path(paper_id)
        if not cache_path.exists():
            return None

        try:
            raw_json = cache_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise IndexingWorkflowStorageError("Failed to read the indexing cache metadata.") from exc

        try:
            return IndexCacheRecord.model_validate_json(raw_json)
        except ValidationError:
            return None

    def _write_index_cache(self, paper_id: str, record: IndexCacheRecord) -> None:
        try:
            write_text_file(
                self._index_cache_path(paper_id),
                record.model_dump_json(indent=2),
            )
        except OSError as exc:
            raise IndexingWorkflowStorageError("Failed to write the indexing cache metadata.") from exc

    def _index_cache_path(self, paper_id: str) -> Path:
        return self._settings.indexing_cache_dir / f"{build_storage_stem(paper_id)}.json"

    def _build_chunks(
        self,
        parsed_document: ParsedPaperDocument,
        content_hash: str,
    ) -> list[IndexedChunk]:
        chunks = self._chunking_service.chunk_document(parsed_document, content_hash=content_hash)
        if not chunks:
            raise IndexingWorkflowNoContentError(
                "Parsed artifact does not contain usable page-aware text to index."
            )
        return chunks
