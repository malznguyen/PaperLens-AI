from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from app.repositories.chroma_repository import ChromaRepositoryError
from app.schemas.indexing import IndexPaperRequest, IndexPaperResponse
from app.services.embedding_service import EmbeddingServiceError
from app.workflows.indexing_workflow import (
    IndexingWorkflow,
    IndexingWorkflowNoContentError,
    IndexingWorkflowStorageError,
    ParsedArtifactInvalidError,
    ParsedArtifactNotFoundError,
)


class IndexingValidationError(ValueError):
    """Raised when an indexing request fails validation."""


class IndexingNotFoundError(RuntimeError):
    """Raised when the requested paper has not been ingested yet."""


class IndexingArtifactError(RuntimeError):
    """Raised when the parsed artifact cannot be used for indexing."""


class IndexingNoContentError(RuntimeError):
    """Raised when no page-aware chunks can be produced from the artifact."""


class IndexingEmbeddingError(RuntimeError):
    """Raised when embeddings cannot be generated."""


class IndexingStorageError(RuntimeError):
    """Raised when local indexing storage fails."""


class IndexingService:
    def __init__(self, workflow: IndexingWorkflow | None = None) -> None:
        self._workflow = workflow or IndexingWorkflow()

    async def index_paper(self, payload: dict[str, Any]) -> IndexPaperResponse:
        request = self._validate_request(payload)

        try:
            return await self._workflow.index_paper(request)
        except ParsedArtifactNotFoundError as exc:
            raise IndexingNotFoundError(str(exc)) from exc
        except ParsedArtifactInvalidError as exc:
            raise IndexingArtifactError(str(exc)) from exc
        except IndexingWorkflowNoContentError as exc:
            raise IndexingNoContentError(str(exc)) from exc
        except EmbeddingServiceError as exc:
            raise IndexingEmbeddingError(str(exc)) from exc
        except (ChromaRepositoryError, IndexingWorkflowStorageError) as exc:
            raise IndexingStorageError(str(exc)) from exc

    def _validate_request(self, payload: dict[str, Any]) -> IndexPaperRequest:
        try:
            return IndexPaperRequest.model_validate(payload)
        except ValidationError as exc:
            raise IndexingValidationError(_format_validation_error(exc)) from exc


indexing_service = IndexingService()


def get_indexing_service() -> IndexingService:
    return indexing_service


def _format_validation_error(exc: ValidationError) -> str:
    error = exc.errors()[0]
    field_path = ".".join(str(part) for part in error.get("loc", []))
    message = error.get("msg", "Invalid request payload.")

    if field_path:
        return f"{field_path}: {message}"
    return message
