from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.schemas.synthesis import TopicSynthesisRequest, TopicSynthesisResponse
from app.workflows.synthesis_workflow import (
    SynthesisWorkflow,
    SynthesisWorkflowError,
    SynthesisWorkflowEvidenceError,
    SynthesisWorkflowNotReadyError,
)


class SynthesisValidationError(ValueError):
    """Raised when a topic synthesis request payload is invalid."""


class SynthesisNotReadyError(RuntimeError):
    """Raised when synthesis is requested before the papers are indexed."""


class SynthesisEvidenceError(RuntimeError):
    """Raised when no grounded evidence can be assembled for synthesis."""


class SynthesisServiceError(RuntimeError):
    """Raised when the synthesis workflow cannot complete."""


class SynthesisService:
    def __init__(
        self,
        workflow: SynthesisWorkflow | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._workflow = workflow or SynthesisWorkflow(settings=self._settings)

    async def summarize_topic(self, payload: dict[str, Any]) -> TopicSynthesisResponse:
        request = self._validate_request(payload)

        try:
            return await self._workflow.summarize_topic(request)
        except SynthesisWorkflowNotReadyError as exc:
            raise SynthesisNotReadyError(str(exc)) from exc
        except SynthesisWorkflowEvidenceError as exc:
            raise SynthesisEvidenceError(str(exc)) from exc
        except SynthesisWorkflowError as exc:
            raise SynthesisServiceError(str(exc)) from exc

    @staticmethod
    def _validate_request(payload: dict[str, Any]) -> TopicSynthesisRequest:
        try:
            return TopicSynthesisRequest.model_validate(payload)
        except ValidationError as exc:
            raise SynthesisValidationError(_format_validation_error(exc)) from exc


synthesis_service = SynthesisService()


def get_synthesis_service() -> SynthesisService:
    return synthesis_service


def _format_validation_error(exc: ValidationError) -> str:
    error = exc.errors()[0]
    field_path = ".".join(str(part) for part in error.get("loc", []))
    message = error.get("msg", "Invalid request payload.")

    if field_path:
        return f"{field_path}: {message}"
    return message
