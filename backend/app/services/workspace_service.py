from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.repositories.chroma_repository import (
    ChromaRepository,
    ChromaRepositoryError,
    IndexedPaperSnapshot,
)
from app.schemas.indexing import IndexCacheRecord
from app.schemas.ingest import ParsedPaperDocument
from app.schemas.workspace import (
    WorkspacePaper,
    WorkspacePaperStatus,
    WorkspaceResponse,
    WorkspaceSummary,
)
from app.utils.file_utils import repo_relative_path


class WorkspaceStateError(RuntimeError):
    """Raised when workspace state cannot be assembled from local artifacts."""


@dataclass(frozen=True)
class ParsedArtifactSnapshot:
    path: Path
    document: ParsedPaperDocument
    modified_at: float


@dataclass(frozen=True)
class IndexCacheSnapshot:
    path: Path
    record: IndexCacheRecord
    modified_at: float


class WorkspaceService:
    def __init__(
        self,
        settings: Settings | None = None,
        chroma_repository: ChromaRepository | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._chroma_repository = chroma_repository or ChromaRepository(settings=self._settings)

    async def get_workspace(self) -> WorkspaceResponse:
        return await asyncio.to_thread(self._build_workspace)

    def _build_workspace(self) -> WorkspaceResponse:
        self._settings.ensure_directories()

        parsed_artifacts = self._load_parsed_artifacts()
        index_cache_records = self._load_index_cache_records()
        indexed_papers = self._load_indexed_papers()

        all_paper_ids = (
            set(parsed_artifacts)
            | set(index_cache_records)
            | set(indexed_papers)
        )

        paper_rows: list[tuple[WorkspacePaper, float]] = []
        total_chunk_count = 0

        for paper_id in all_paper_ids:
            parsed_snapshot = parsed_artifacts.get(paper_id)
            cache_snapshot = index_cache_records.get(paper_id)
            chroma_snapshot = indexed_papers.get(paper_id)

            cached_chunk_count = cache_snapshot.record.chunk_count if cache_snapshot else 0
            indexed_chunk_count = chroma_snapshot.chunk_count if chroma_snapshot else 0
            chunk_count = indexed_chunk_count if indexed_chunk_count > 0 else cached_chunk_count
            is_ingested = parsed_snapshot is not None
            is_indexed = chunk_count > 0

            if is_indexed:
                total_chunk_count += chunk_count

            title = paper_id
            authors: list[str] = []
            categories: list[str] = []
            primary_category: str | None = None
            pdf_path: str | None = None
            parsed_path: str | None = None
            page_count = 0
            word_count = 0
            source_url: str | None = None
            collection_name: str | None = None

            if parsed_snapshot is not None:
                document = parsed_snapshot.document
                title = document.title
                authors = document.authors
                categories = document.categories
                primary_category = document.primary_category
                pdf_path = document.pdf_path
                parsed_path = repo_relative_path(parsed_snapshot.path)
                page_count = document.page_count
                word_count = document.word_count
                source_url = document.source_url

            if chroma_snapshot is not None:
                title = chroma_snapshot.paper_title or title
                source_url = chroma_snapshot.source_url or source_url
                pdf_path = chroma_snapshot.pdf_path or pdf_path

            if cache_snapshot is not None:
                collection_name = cache_snapshot.record.collection_name
            elif is_indexed:
                collection_name = self._chroma_repository.collection_name

            latest_activity = max(
                parsed_snapshot.modified_at if parsed_snapshot is not None else 0.0,
                cache_snapshot.modified_at if cache_snapshot is not None else 0.0,
            )

            paper_rows.append(
                (
                    WorkspacePaper(
                        paper_id=paper_id,
                        title=title,
                        authors=authors,
                        categories=categories,
                        primary_category=primary_category,
                        status=WorkspacePaperStatus(
                            ingested=is_ingested,
                            indexed=is_indexed,
                        ),
                        pdf_path=pdf_path,
                        parsed_path=parsed_path,
                        page_count=page_count,
                        word_count=word_count,
                        chunk_count=chunk_count,
                        source_url=source_url,
                        collection_name=collection_name,
                    ),
                    latest_activity,
                )
            )

        paper_rows.sort(
            key=lambda item: (
                not item[0].status.indexed,
                not item[0].status.ingested,
                -item[1],
                item[0].title.lower(),
                item[0].paper_id,
            )
        )

        papers = [paper for paper, _ in paper_rows]

        return WorkspaceResponse(
            summary=WorkspaceSummary(
                total_paper_count=len(papers),
                ingested_paper_count=sum(1 for paper in papers if paper.status.ingested),
                indexed_paper_count=sum(1 for paper in papers if paper.status.indexed),
                total_chunk_count=total_chunk_count,
            ),
            papers=papers,
        )

    def _load_parsed_artifacts(self) -> dict[str, ParsedArtifactSnapshot]:
        try:
            parsed_paths = sorted(self._settings.parsed_dir.glob("*.json"))
        except OSError as exc:
            raise WorkspaceStateError("Failed to inspect parsed paper artifacts.") from exc

        parsed_artifacts: dict[str, ParsedArtifactSnapshot] = {}
        for parsed_path in parsed_paths:
            document = self._load_parsed_document(parsed_path)
            if document is None:
                continue

            parsed_artifacts[document.paper_id] = ParsedArtifactSnapshot(
                path=parsed_path,
                document=document,
                modified_at=self._get_modified_at(parsed_path),
            )

        return parsed_artifacts

    def _load_index_cache_records(self) -> dict[str, IndexCacheSnapshot]:
        try:
            cache_paths = sorted(self._settings.indexing_cache_dir.glob("*.json"))
        except OSError as exc:
            raise WorkspaceStateError("Failed to inspect indexing cache artifacts.") from exc

        cache_records: dict[str, IndexCacheSnapshot] = {}
        for cache_path in cache_paths:
            record = self._load_index_cache_record(cache_path)
            if record is None:
                continue

            cache_records[record.paper_id] = IndexCacheSnapshot(
                path=cache_path,
                record=record,
                modified_at=self._get_modified_at(cache_path),
            )

        return cache_records

    def _load_indexed_papers(self) -> dict[str, IndexedPaperSnapshot]:
        try:
            indexed_papers = self._chroma_repository.list_indexed_papers()
        except ChromaRepositoryError as exc:
            raise WorkspaceStateError("Failed to inspect indexed chunk metadata.") from exc

        return {snapshot.paper_id: snapshot for snapshot in indexed_papers}

    def _load_parsed_document(self, parsed_path: Path) -> ParsedPaperDocument | None:
        try:
            raw_json = parsed_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise WorkspaceStateError("Failed to read a parsed paper artifact.") from exc

        try:
            return ParsedPaperDocument.model_validate_json(raw_json)
        except ValidationError:
            return None

    def _load_index_cache_record(self, cache_path: Path) -> IndexCacheRecord | None:
        try:
            raw_json = cache_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise WorkspaceStateError("Failed to read an indexing cache artifact.") from exc

        try:
            return IndexCacheRecord.model_validate_json(raw_json)
        except ValidationError:
            return None

    def _get_modified_at(self, path: Path) -> float:
        try:
            return path.stat().st_mtime
        except OSError:
            return 0.0


workspace_service = WorkspaceService()


def get_workspace_service() -> WorkspaceService:
    return workspace_service
