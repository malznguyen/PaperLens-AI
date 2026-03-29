from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.schemas.compare import CompareRequest, CompareResponse
from app.workflows.compare_workflow import (
    CompareWorkflow,
    CompareWorkflowError,
    CompareWorkflowEvidenceError,
    CompareWorkflowNotReadyError,
)


class CompareValidationError(ValueError):
    """Raised when a compare request payload is invalid."""


class CompareNotReadyError(RuntimeError):
    """Raised when one or more requested papers are not indexed yet."""


class CompareEvidenceError(RuntimeError):
    """Raised when comparison cannot be grounded with usable evidence."""


class CompareServiceError(RuntimeError):
    """Raised when the compare workflow cannot complete."""


class CompareService:
    def __init__(
        self,
        workflow: CompareWorkflow | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._workflow = workflow or CompareWorkflow(settings=self._settings)

    async def compare_papers(self, payload: dict[str, Any]) -> CompareResponse:
        request = self._validate_request(payload)

        if len(request.paper_ids) > self._settings.compare_max_papers:
            raise CompareValidationError(
                f"paper_ids must contain no more than {self._settings.compare_max_papers} unique values."
            )

        try:
            return await self._workflow.compare_papers(request)
        except CompareWorkflowNotReadyError as exc:
            raise CompareNotReadyError(str(exc)) from exc
        except CompareWorkflowEvidenceError as exc:
            raise CompareEvidenceError(str(exc)) from exc
        except CompareWorkflowError as exc:
            raise CompareServiceError(str(exc)) from exc

    @staticmethod
    def _validate_request(payload: dict[str, Any]) -> CompareRequest:
        try:
            return CompareRequest.model_validate(payload)
        except ValidationError as exc:
            raise CompareValidationError(_format_validation_error(exc)) from exc


compare_service = CompareService()


def get_compare_service() -> CompareService:
    return compare_service


def _format_validation_error(exc: ValidationError) -> str:
    error = exc.errors()[0]
    field_path = ".".join(str(part) for part in error.get("loc", []))
    message = error.get("msg", "Invalid request payload.")

    if field_path:
        return f"{field_path}: {message}"
    return message
