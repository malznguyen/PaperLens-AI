from __future__ import annotations

import asyncio

from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.schemas.ingest import IngestRequest, IngestResponse, ParsedPaperDocument
from app.services.pdf_service import PdfService
from app.utils.file_utils import (
    build_storage_stem,
    repo_relative_path,
    write_bytes_file,
    write_text_file,
)


class IngestWorkflowStorageError(RuntimeError):
    """Raised when ingest artifacts cannot be read or written."""


class IngestWorkflow:
    def __init__(
        self,
        pdf_service: PdfService | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._pdf_service = pdf_service or PdfService(settings=self._settings)

    async def ingest_paper(self, payload: IngestRequest) -> IngestResponse:
        self._settings.ensure_directories()

        paper_stem = build_storage_stem(payload.id, payload.title)
        pdf_path = self._settings.raw_pdfs_dir / f"{paper_stem}.pdf"
        parsed_path = self._settings.parsed_dir / f"{paper_stem}.json"

        if pdf_path.exists() and parsed_path.exists():
            cached_document = self._load_parsed_document(parsed_path)
            if cached_document is not None:
                return self._build_response(
                    parsed_document=cached_document,
                    parsed_path=parsed_path,
                    status="cached",
                    message="Paper already ingested; using cached artifacts.",
                )

        if not pdf_path.exists():
            pdf_bytes = await self._pdf_service.download_pdf(payload.pdf_url)
            self._write_pdf(pdf_path, pdf_bytes)

        parsed_document = await asyncio.to_thread(self._pdf_service.parse_pdf, pdf_path, payload)
        self._write_parsed_document(parsed_path, parsed_document)

        return self._build_response(
            parsed_document=parsed_document,
            parsed_path=parsed_path,
            status="completed",
            message="Paper ingested and parsed successfully.",
        )

    def _load_parsed_document(self, parsed_path) -> ParsedPaperDocument | None:
        try:
            raw_json = parsed_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise IngestWorkflowStorageError("Failed to read the cached parsed artifact.") from exc

        try:
            return ParsedPaperDocument.model_validate_json(raw_json)
        except ValidationError:
            return None

    def _write_pdf(self, pdf_path, pdf_bytes: bytes) -> None:
        try:
            write_bytes_file(pdf_path, pdf_bytes)
        except OSError as exc:
            raise IngestWorkflowStorageError("Failed to write the downloaded PDF to disk.") from exc

    def _write_parsed_document(
        self,
        parsed_path,
        parsed_document: ParsedPaperDocument,
    ) -> None:
        try:
            write_text_file(
                parsed_path,
                parsed_document.model_dump_json(indent=2),
            )
        except OSError as exc:
            raise IngestWorkflowStorageError("Failed to write the parsed paper JSON to disk.") from exc

    def _build_response(
        self,
        parsed_document: ParsedPaperDocument,
        parsed_path,
        status: str,
        message: str,
    ) -> IngestResponse:
        return IngestResponse(
            paper_id=parsed_document.paper_id,
            status=status,
            pdf_path=parsed_document.pdf_path,
            parsed_path=repo_relative_path(parsed_path),
            page_count=parsed_document.page_count,
            word_count=parsed_document.word_count,
            message=message,
        )
