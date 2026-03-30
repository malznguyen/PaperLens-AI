from __future__ import annotations

import json
import logging
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import Settings, get_settings
from app.schemas.chat import GeneratedAnswerPayload, GenerationResult, RetrievedChunk
from app.utils.prompt_utils import build_context_block


class GenerationServiceError(RuntimeError):
    """Base class for answer generation failures."""


class GenerationConfigurationError(GenerationServiceError):
    """Raised when generation is requested without a valid configuration."""


class GenerationTimeoutError(GenerationServiceError):
    """Raised when OpenRouter times out."""


class GenerationUpstreamError(GenerationServiceError):
    """Raised when OpenRouter returns an upstream failure."""


class GenerationMalformedResponseError(GenerationServiceError):
    """Raised when the model response cannot be parsed safely."""


StructuredResponseModel = TypeVar("StructuredResponseModel", bound=BaseModel)
STRUCTURED_FREE_MODEL_FALLBACK = "google/gemma-3n-e4b-it:free"
STRICT_STRUCTURED_MODE = "json_schema"
RELAXED_STRUCTURED_MODE = "json_object"
PROMPT_ONLY_MODE = "prompt_only"
_STRUCTURED_MODE_ORDER = (
    STRICT_STRUCTURED_MODE,
    RELAXED_STRUCTURED_MODE,
    PROMPT_ONLY_MODE,
)
_FALLBACK_STATUS_CODES = {400, 404}
_FALLBACK_ERROR_HINTS = (
    "no endpoints found that can handle the requested parameters",
    "response_format is invalid",
    "must be text or json_object",
)
_JSON_SCHEMA_INCOMPATIBLE_MODELS = {
    "stepfun/step-3.5-flash:free",
}


class GenerationService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._logger = logging.getLogger(__name__)
        self._preferred_structured_mode_by_model: dict[str, str] = {}

    async def generate_answer(
        self,
        question: str,
        chunks: list[RetrievedChunk],
    ) -> GenerationResult:
        if not chunks:
            raise GenerationMalformedResponseError("Cannot generate an answer without retrieved context.")

        if not self._settings.openrouter_api_key:
            raise GenerationConfigurationError(
                "OPENROUTER_API_KEY is not configured for grounded answer generation."
            )

        generated_payload = await self.generate_structured_payload(
            self._build_messages(question, chunks),
            response_model=GeneratedAnswerPayload,
            temperature=0.1,
            max_tokens=900,
        )
        return GenerationResult(
            answer=generated_payload.answer,
            citation_labels=generated_payload.citation_labels,
            insufficient_evidence=generated_payload.insufficient_evidence,
        )

    async def generate_structured_payload(
        self,
        messages: list[dict[str, str]],
        *,
        response_model: type[StructuredResponseModel],
        temperature: float,
        max_tokens: int,
    ) -> StructuredResponseModel:
        if not messages:
            raise GenerationMalformedResponseError("Cannot generate a structured payload without prompt messages.")

        response_payload = await self._request_completion(
            messages,
            response_model=response_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = self._extract_message_content(response_payload)
        try:
            return self._parse_structured_payload(content, response_model)
        except GenerationMalformedResponseError:
            self._logger.warning(
                "generation_response_parse_failed",
                extra={
                    "response_model": response_model.__name__,
                    "content_length": len(content),
                    "content_preview": content[:500],
                },
            )
            raise

    async def _request_completion(
        self,
        messages: list[dict[str, str]],
        *,
        response_model: type[BaseModel] | None = None,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        if not self._settings.openrouter_api_key:
            raise GenerationConfigurationError(
                "OPENROUTER_API_KEY is not configured for grounded answer generation."
            )

        timeout = httpx.Timeout(self._settings.openrouter_timeout_seconds)
        endpoint = f"{self._settings.openrouter_base_url.rstrip('/')}/chat/completions"

        request_attempts = self._build_request_attempts(
            messages,
            response_model=response_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response: httpx.Response | None = None
                final_request_attempt: dict[str, Any] | None = None
                for index, request_attempt in enumerate(request_attempts):
                    final_request_attempt = request_attempt
                    response = await client.post(
                        endpoint,
                        headers={
                            "Authorization": f"Bearer {self._settings.openrouter_api_key}",
                            "Content-Type": "application/json",
                        },
                        json=request_attempt["payload"],
                    )

                    if index == len(request_attempts) - 1:
                        break

                    if not self._should_retry_with_relaxed_structure(
                        response,
                        request_mode=request_attempt["mode"],
                    ):
                        break

                    self._remember_structured_mode(
                        request_attempt["payload"]["model"],
                        request_attempts[index + 1]["mode"],
                    )

                    self._logger.info(
                        "generation_request_fallback",
                        extra={
                            "request_mode": request_attempt["mode"],
                            "fallback_mode": request_attempts[index + 1]["mode"],
                            "model": request_attempt["payload"]["model"],
                            "status_code": response.status_code,
                        },
                    )
        except httpx.TimeoutException as exc:
            raise GenerationTimeoutError("OpenRouter timed out while generating the grounded answer.") from exc
        except httpx.HTTPError as exc:
            raise GenerationUpstreamError("OpenRouter could not be reached for grounded answer generation.") from exc

        assert response is not None
        assert final_request_attempt is not None
        if response.status_code < 400:
            self._remember_structured_mode(
                final_request_attempt["payload"]["model"],
                final_request_attempt["mode"],
            )
        return self._parse_completion_response(response)

    def _build_request_attempts(
        self,
        messages: list[dict[str, str]],
        *,
        response_model: type[BaseModel] | None,
        temperature: float,
        max_tokens: int,
    ) -> list[dict[str, Any]]:
        base_payload = {
            "model": self._select_model(response_model),
            "messages": self._select_messages(messages, response_model),
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_model is None:
            return [{"mode": PROMPT_ONLY_MODE, "payload": base_payload}]

        if base_payload["model"] == STRUCTURED_FREE_MODEL_FALLBACK:
            return [{"mode": PROMPT_ONLY_MODE, "payload": base_payload}]

        strict_payload = dict(base_payload)
        strict_payload["reasoning"] = {
            "effort": "none",
            "exclude": True,
        }
        strict_payload["response_format"] = self._build_response_format(response_model)
        strict_payload["provider"] = {"require_parameters": True}
        strict_payload["plugins"] = [{"id": "response-healing"}]

        relaxed_payload = dict(base_payload)
        relaxed_payload["response_format"] = {"type": "json_object"}
        relaxed_payload["plugins"] = [{"id": "response-healing"}]

        payload_by_mode = {
            STRICT_STRUCTURED_MODE: strict_payload,
            RELAXED_STRUCTURED_MODE: relaxed_payload,
            PROMPT_ONLY_MODE: base_payload,
        }
        request_modes = self._resolve_request_modes(base_payload["model"])
        return [{"mode": mode, "payload": payload_by_mode[mode]} for mode in request_modes]

    def _resolve_request_modes(self, model: str) -> list[str]:
        preferred_mode = self._preferred_structured_mode_by_model.get(
            model,
            self._default_structured_mode_for_model(model),
        )
        start_index = _STRUCTURED_MODE_ORDER.index(preferred_mode)
        return list(_STRUCTURED_MODE_ORDER[start_index:])

    @staticmethod
    def _default_structured_mode_for_model(model: str) -> str:
        if model in _JSON_SCHEMA_INCOMPATIBLE_MODELS:
            return RELAXED_STRUCTURED_MODE
        return STRICT_STRUCTURED_MODE

    def _remember_structured_mode(self, model: str, mode: str) -> None:
        self._preferred_structured_mode_by_model[model] = mode

    def _should_retry_with_relaxed_structure(
        self,
        response: httpx.Response,
        *,
        request_mode: str,
    ) -> bool:
        if request_mode == PROMPT_ONLY_MODE:
            return False

        if response.status_code not in _FALLBACK_STATUS_CODES:
            return False

        response_text = response.text.lower()
        return any(error_hint in response_text for error_hint in _FALLBACK_ERROR_HINTS)

    @staticmethod
    def _parse_completion_response(response: httpx.Response) -> dict[str, Any]:
        if response.status_code == 408:
            raise GenerationTimeoutError("OpenRouter timed out while generating the grounded answer.")

        if response.status_code in {429, 502, 503, 504}:
            raise GenerationUpstreamError(
                "OpenRouter is temporarily unavailable for grounded answer generation."
            )

        if response.status_code >= 400:
            raise GenerationUpstreamError(
                f"OpenRouter returned an error ({response.status_code}) during answer generation."
            )

        try:
            return response.json()
        except ValueError as exc:
            raise GenerationMalformedResponseError("OpenRouter returned invalid JSON.") from exc

    def _build_messages(self, question: str, chunks: list[RetrievedChunk]) -> list[dict[str, str]]:
        context_block = build_context_block(
            chunks,
            max_chunk_chars=self._settings.generation_chunk_char_limit,
        )
        return [
            {
                "role": "system",
                "content": (
                    "You are PaperLens AI, a grounded academic research assistant. "
                    "Answer only from the retrieved context. "
                    "Do not use outside knowledge. "
                    "If the evidence is insufficient, say so directly. "
                    "Do not invent citations or claim support that is not present. "
                    "Return strict JSON only, with this shape: "
                    '{"answer":"...","citations":["S1","S2"],"insufficient_evidence":false}. '
                    "The answer must be one short paragraph of at most 120 words. "
                    "Do not restate the question, do not quote long passages, and do not repeat the context. "
                    "The citations array must contain only citation labels that appear in the context. "
                    "Do not include markdown fences or extra commentary."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question:\n{question}\n\n"
                    "Retrieved context:\n"
                    f"{context_block}\n\n"
                    "Write a concise academic answer grounded only in this evidence."
                ),
            },
        ]

    @staticmethod
    def _extract_message_content(response_payload: dict[str, Any]) -> str:
        choices = response_payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise GenerationMalformedResponseError("OpenRouter returned no completion choices.")

        message = choices[0].get("message", {})
        content = message.get("content")

        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            text_parts: list[str] = []
            for item in content:
                if not isinstance(item, dict):
                    continue
                if item.get("type") != "text":
                    continue
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    text_parts.append(text.strip())

            if text_parts:
                return "\n".join(text_parts)

        if content is None and (message.get("reasoning") or message.get("reasoning_details")):
            logging.getLogger(__name__).warning(
                "generation_response_missing_final_content",
                extra={
                    "has_reasoning": bool(message.get("reasoning") or message.get("reasoning_details")),
                    "reasoning_preview": str(message.get("reasoning") or "")[:500],
                },
            )
            raise GenerationMalformedResponseError(
                "OpenRouter returned reasoning tokens without a final assistant message."
            )

        raise GenerationMalformedResponseError("OpenRouter returned an unsupported message content shape.")

    @staticmethod
    def _parse_generated_payload(content: str) -> GeneratedAnswerPayload:
        return GenerationService._parse_structured_payload(content, GeneratedAnswerPayload)

    @staticmethod
    def _parse_structured_payload(
        content: str,
        response_model: type[StructuredResponseModel],
    ) -> StructuredResponseModel:
        normalized = content.strip()
        if normalized.startswith("```"):
            normalized = normalized.strip("`").strip()
            if normalized.lower().startswith("json"):
                normalized = normalized[4:].strip()

        if not normalized.startswith("{"):
            start_index = normalized.find("{")
            end_index = normalized.rfind("}")
            if start_index == -1 or end_index == -1 or end_index <= start_index:
                raise GenerationMalformedResponseError("Model response did not contain a JSON object.")
            normalized = normalized[start_index : end_index + 1]

        try:
            payload = json.loads(normalized)
        except json.JSONDecodeError as exc:
            raise GenerationMalformedResponseError("Model response was not valid JSON.") from exc

        try:
            return response_model.model_validate(payload)
        except ValidationError as exc:
            raise GenerationMalformedResponseError("Model response JSON was missing required fields.") from exc

    @staticmethod
    def _build_response_format(response_model: type[BaseModel]) -> dict[str, Any]:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": response_model.__name__,
                "strict": True,
                "schema": response_model.model_json_schema(by_alias=True),
            },
        }

    def _select_model(self, response_model: type[BaseModel] | None) -> str:
        if response_model is not None and self._settings.openrouter_model == "openrouter/free":
            return STRUCTURED_FREE_MODEL_FALLBACK
        return self._settings.openrouter_model

    def _select_messages(
        self,
        messages: list[dict[str, str]],
        response_model: type[BaseModel] | None,
    ) -> list[dict[str, str]]:
        if response_model is not None and self._settings.openrouter_model == "openrouter/free":
            return self._collapse_system_messages(messages)
        return messages

    @staticmethod
    def _collapse_system_messages(messages: list[dict[str, str]]) -> list[dict[str, str]]:
        system_parts: list[str] = []
        remaining_messages: list[dict[str, str]] = []

        for message in messages:
            role = message.get("role")
            content = message.get("content", "")
            if role == "system":
                if content.strip():
                    system_parts.append(content.strip())
                continue
            remaining_messages.append(message)

        if not system_parts:
            return messages

        system_block = "\n\n".join(system_parts)
        if not remaining_messages:
            return [{"role": "user", "content": system_block}]

        first_message = dict(remaining_messages[0])
        first_content = first_message.get("content", "").strip()
        first_message["content"] = f"{system_block}\n\n{first_content}" if first_content else system_block

        return [first_message, *remaining_messages[1:]]
