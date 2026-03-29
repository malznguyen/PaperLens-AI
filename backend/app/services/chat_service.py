from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.retrieval_service import (
    RetrievalNoIndexedPapersError,
    RetrievalNoRelevantChunksError,
    RetrievalServiceError,
)
from app.workflows.chat_workflow import ChatWorkflow


class ChatValidationError(ValueError):
    """Raised when a chat request payload is invalid."""


class ChatNotReadyError(RuntimeError):
    """Raised when no indexed papers are available for retrieval."""


class ChatEvidenceError(RuntimeError):
    """Raised when retrieval returns no grounded evidence."""


class ChatServiceError(RuntimeError):
    """Raised when the chat workflow cannot complete a retrieval-first run."""


class ChatService:
    def __init__(
        self,
        workflow: ChatWorkflow | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._workflow = workflow or ChatWorkflow(settings=self._settings)

    async def answer_question(self, payload: dict[str, Any]) -> ChatResponse:
        request = self._validate_request(payload)

        top_k = request.top_k or self._settings.retrieval_top_k_default
        if top_k < 1 or top_k > self._settings.retrieval_top_k_max:
            raise ChatValidationError(
                f"top_k must be between 1 and {self._settings.retrieval_top_k_max}."
            )

        request = request.model_copy(update={"top_k": top_k})

        try:
            return await self._workflow.answer_question(request)
        except RetrievalNoIndexedPapersError as exc:
            raise ChatNotReadyError(str(exc)) from exc
        except RetrievalNoRelevantChunksError as exc:
            raise ChatEvidenceError(str(exc)) from exc
        except RetrievalServiceError as exc:
            raise ChatServiceError(str(exc)) from exc

    def _validate_request(self, payload: dict[str, Any]) -> ChatRequest:
        try:
            return ChatRequest.model_validate(payload)
        except ValidationError as exc:
            raise ChatValidationError(_format_validation_error(exc)) from exc


chat_service = ChatService()


def get_chat_service() -> ChatService:
    return chat_service


def _format_validation_error(exc: ValidationError) -> str:
    error = exc.errors()[0]
    field_path = ".".join(str(part) for part in error.get("loc", []))
    message = error.get("msg", "Invalid request payload.")

    if field_path:
        return f"{field_path}: {message}"
    return message
