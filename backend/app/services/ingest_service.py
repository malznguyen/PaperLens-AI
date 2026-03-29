from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from app.schemas.ingest import IngestRequest, IngestResponse
from app.services.pdf_service import InvalidPdfError, PdfDownloadError, PdfParseError, PdfTimeoutError
from app.workflows.ingest_workflow import IngestWorkflow, IngestWorkflowStorageError


class IngestValidationError(ValueError):
    """Raised when an ingest request fails validation."""


class IngestTimeoutError(RuntimeError):
    """Raised when the paper PDF cannot be downloaded in time."""


class IngestUpstreamError(RuntimeError):
    """Raised when a remote PDF source cannot be ingested."""


class IngestProcessingError(RuntimeError):
    """Raised when a downloaded PDF cannot be parsed into text."""


class IngestStorageError(RuntimeError):
    """Raised when local storage operations fail."""


class IngestService:
    def __init__(self, workflow: IngestWorkflow | None = None) -> None:
        self._workflow = workflow or IngestWorkflow()

    async def ingest_paper(self, payload: dict[str, Any]) -> IngestResponse:
        request = self._validate_request(payload)

        try:
            return await self._workflow.ingest_paper(request)
        except PdfTimeoutError as exc:
            raise IngestTimeoutError("Timed out while downloading the PDF.") from exc
        except (PdfDownloadError, InvalidPdfError) as exc:
            raise IngestUpstreamError(str(exc)) from exc
        except PdfParseError as exc:
            raise IngestProcessingError(str(exc)) from exc
        except IngestWorkflowStorageError as exc:
            raise IngestStorageError(str(exc)) from exc

    def _validate_request(self, payload: dict[str, Any]) -> IngestRequest:
        try:
            return IngestRequest.model_validate(payload)
        except ValidationError as exc:
            raise IngestValidationError(_format_validation_error(exc)) from exc


ingest_service = IngestService()


def get_ingest_service() -> IngestService:
    return ingest_service


def _format_validation_error(exc: ValidationError) -> str:
    error = exc.errors()[0]
    field_path = ".".join(str(part) for part in error.get("loc", []))
    message = error.get("msg", "Invalid request payload.")

    if field_path:
        return f"{field_path}: {message}"
    return message
