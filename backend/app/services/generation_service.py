from __future__ import annotations

import json
from typing import Any

import httpx
from pydantic import ValidationError

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


class GenerationService:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

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

        payload = {
            "model": self._settings.openrouter_model,
            "messages": self._build_messages(question, chunks),
            "temperature": 0.1,
            "max_tokens": 500,
        }

        timeout = httpx.Timeout(self._settings.openrouter_timeout_seconds)
        endpoint = f"{self._settings.openrouter_base_url.rstrip('/')}/chat/completions"

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    endpoint,
                    headers={
                        "Authorization": f"Bearer {self._settings.openrouter_api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
        except httpx.TimeoutException as exc:
            raise GenerationTimeoutError("OpenRouter timed out while generating the grounded answer.") from exc
        except httpx.HTTPError as exc:
            raise GenerationUpstreamError("OpenRouter could not be reached for grounded answer generation.") from exc

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
            response_payload = response.json()
        except ValueError as exc:
            raise GenerationMalformedResponseError("OpenRouter returned invalid JSON.") from exc

        content = self._extract_message_content(response_payload)
        generated_payload = self._parse_generated_payload(content)
        return GenerationResult(
            answer=generated_payload.answer,
            citation_labels=generated_payload.citation_labels,
            insufficient_evidence=generated_payload.insufficient_evidence,
            model=response_payload.get("model"),
        )

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

        raise GenerationMalformedResponseError("OpenRouter returned an unsupported message content shape.")

    @staticmethod
    def _parse_generated_payload(content: str) -> GeneratedAnswerPayload:
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
            return GeneratedAnswerPayload.model_validate(payload)
        except ValidationError as exc:
            raise GenerationMalformedResponseError("Model response JSON was missing required fields.") from exc
