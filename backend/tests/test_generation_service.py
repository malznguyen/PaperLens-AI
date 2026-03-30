import asyncio

import httpx
import pytest

from app.core.config import Settings
from app.schemas.chat import GeneratedAnswerPayload
from app.services.generation_service import (
    GenerationMalformedResponseError,
    GenerationService,
    STRUCTURED_FREE_MODEL_FALLBACK,
)


class DummyResponse:
    def __init__(
        self,
        payload: dict[str, object],
        *,
        status_code: int = 200,
        text: str | None = None,
    ) -> None:
        self.status_code = status_code
        self._payload = payload
        self.headers = {"content-type": "application/json"}
        self.text = text if text is not None else str(payload)

    def json(self) -> dict[str, object]:
        return self._payload


def test_generate_structured_payload_requests_json_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class CapturingAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            captured["timeout"] = kwargs.get("timeout")

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> bool:
            return False

        async def post(self, url: str, *, headers: dict[str, str], json: dict[str, object]):
            captured["url"] = url
            captured["headers"] = headers
            captured["json"] = json
            return DummyResponse(
                {
                    "choices": [
                        {
                            "message": {
                                "content": '{"answer":"hi","citations":["S1"],"insufficient_evidence":false}'
                            }
                        }
                    ]
                }
            )

    monkeypatch.setattr(httpx, "AsyncClient", CapturingAsyncClient)

    service = GenerationService(
        settings=Settings(
            openrouter_api_key="test-key",
            openrouter_model="openrouter/free",
        )
    )

    result = asyncio.run(
        service.generate_structured_payload(
            [
                {"role": "system", "content": "Follow the schema exactly."},
                {"role": "user", "content": "Answer in JSON."},
            ],
            response_model=GeneratedAnswerPayload,
            temperature=0.1,
            max_tokens=120,
        )
    )

    assert result.answer == "hi"
    assert result.citation_labels == ["S1"]

    payload = captured["json"]
    assert isinstance(payload, dict)
    assert payload["model"] == STRUCTURED_FREE_MODEL_FALLBACK
    assert "reasoning" not in payload
    assert "provider" not in payload
    assert "plugins" not in payload
    assert "response_format" not in payload

    request_messages = payload["messages"]
    assert isinstance(request_messages, list)
    assert request_messages[0]["role"] == "user"
    assert "Follow the schema exactly." in request_messages[0]["content"]
    assert "Answer in JSON." in request_messages[0]["content"]


def test_generate_structured_payload_keeps_explicit_model(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class CapturingAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> bool:
            return False

        async def post(self, url: str, *, headers: dict[str, str], json: dict[str, object]):
            captured["json"] = json
            return DummyResponse(
                {
                    "choices": [
                        {
                            "message": {
                                "content": '{"answer":"hi","citations":[],"insufficient_evidence":false}'
                            }
                        }
                    ]
                }
            )

    monkeypatch.setattr(httpx, "AsyncClient", CapturingAsyncClient)

    service = GenerationService(
        settings=Settings(
            openrouter_api_key="test-key",
            openrouter_model="openai/gpt-4.1-mini",
        )
    )

    asyncio.run(
        service.generate_structured_payload(
            [{"role": "user", "content": "Answer in JSON."}],
            response_model=GeneratedAnswerPayload,
            temperature=0.1,
            max_tokens=120,
        )
    )

    payload = captured["json"]
    assert isinstance(payload, dict)
    assert payload["model"] == "openai/gpt-4.1-mini"
    assert payload["reasoning"] == {"effort": "none", "exclude": True}
    assert payload["provider"] == {"require_parameters": True}
    assert payload["plugins"] == [{"id": "response-healing"}]

    response_format = payload["response_format"]
    assert isinstance(response_format, dict)
    assert response_format["type"] == "json_schema"

    json_schema = response_format["json_schema"]
    assert isinstance(json_schema, dict)
    assert json_schema["name"] == "GeneratedAnswerPayload"
    assert json_schema["strict"] is True

    schema = json_schema["schema"]
    assert isinstance(schema, dict)
    properties = schema["properties"]
    assert isinstance(properties, dict)
    assert "citations" in properties
    assert "citation_labels" not in properties


def test_generate_structured_payload_starts_with_json_object_for_known_incompatible_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_payloads: list[dict[str, object]] = []

    class CapturingAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> bool:
            return False

        async def post(self, url: str, *, headers: dict[str, str], json: dict[str, object]):
            captured_payloads.append(json)
            return DummyResponse(
                {
                    "choices": [
                        {
                            "message": {
                                "content": '{"answer":"hi","citations":["S1"],"insufficient_evidence":false}'
                            }
                        }
                    ]
                }
            )

    monkeypatch.setattr(httpx, "AsyncClient", CapturingAsyncClient)

    service = GenerationService(
        settings=Settings(
            openrouter_api_key="test-key",
            openrouter_model="stepfun/step-3.5-flash:free",
        )
    )

    result = asyncio.run(
        service.generate_structured_payload(
            [{"role": "user", "content": "Answer in JSON."}],
            response_model=GeneratedAnswerPayload,
            temperature=0.1,
            max_tokens=120,
        )
    )

    assert result.answer == "hi"
    assert len(captured_payloads) == 1
    assert captured_payloads[0]["response_format"] == {"type": "json_object"}
    assert captured_payloads[0]["plugins"] == [{"id": "response-healing"}]
    assert "provider" not in captured_payloads[0]
    assert "reasoning" not in captured_payloads[0]


def test_generate_structured_payload_falls_back_to_json_object_when_schema_route_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_payloads: list[dict[str, object]] = []

    class CapturingAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> bool:
            return False

        async def post(self, url: str, *, headers: dict[str, str], json: dict[str, object]):
            captured_payloads.append(json)
            if len(captured_payloads) == 1:
                return DummyResponse(
                    {
                        "error": {
                            "message": "No endpoints found that can handle the requested parameters.",
                            "code": 404,
                        }
                    },
                    status_code=404,
                    text=(
                        '{"error":{"message":"No endpoints found that can handle the requested '
                        'parameters.","code":404}}'
                    ),
                )

            return DummyResponse(
                {
                    "choices": [
                        {
                            "message": {
                                "content": '{"answer":"hi","citations":["S1"],"insufficient_evidence":false}'
                            }
                        }
                    ]
                }
            )

    monkeypatch.setattr(httpx, "AsyncClient", CapturingAsyncClient)

    service = GenerationService(
        settings=Settings(
            openrouter_api_key="test-key",
            openrouter_model="openai/gpt-4.1-mini",
        )
    )

    result = asyncio.run(
        service.generate_structured_payload(
            [{"role": "user", "content": "Answer in JSON."}],
            response_model=GeneratedAnswerPayload,
            temperature=0.1,
            max_tokens=120,
        )
    )

    assert result.answer == "hi"
    assert result.citation_labels == ["S1"]
    assert len(captured_payloads) == 2

    strict_payload = captured_payloads[0]
    assert strict_payload["response_format"]["type"] == "json_schema"
    assert strict_payload["provider"] == {"require_parameters": True}
    assert strict_payload["plugins"] == [{"id": "response-healing"}]

    relaxed_payload = captured_payloads[1]
    assert relaxed_payload["response_format"] == {"type": "json_object"}
    assert relaxed_payload["plugins"] == [{"id": "response-healing"}]
    assert "provider" not in relaxed_payload
    assert "reasoning" not in relaxed_payload


def test_generate_structured_payload_falls_back_to_prompt_only_when_json_object_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_payloads: list[dict[str, object]] = []

    class CapturingAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> bool:
            return False

        async def post(self, url: str, *, headers: dict[str, str], json: dict[str, object]):
            captured_payloads.append(json)
            if len(captured_payloads) == 1:
                return DummyResponse(
                    {
                        "error": {
                            "message": "No endpoints found that can handle the requested parameters.",
                            "code": 404,
                        }
                    },
                    status_code=404,
                    text=(
                        '{"error":{"message":"No endpoints found that can handle the requested '
                        'parameters.","code":404}}'
                    ),
                )

            if len(captured_payloads) == 2:
                return DummyResponse(
                    {
                        "error": {
                            "message": "Request param: response_format is invalid, recommended val is: must be text or json_object",
                            "code": 400,
                        }
                    },
                    status_code=400,
                    text=(
                        '{"error":{"message":"Request param: response_format is invalid, recommended '
                        'val is: must be text or json_object","code":400}}'
                    ),
                )

            return DummyResponse(
                {
                    "choices": [
                        {
                            "message": {
                                "content": '{"answer":"hi","citations":[],"insufficient_evidence":false}'
                            }
                        }
                    ]
                }
            )

    monkeypatch.setattr(httpx, "AsyncClient", CapturingAsyncClient)

    service = GenerationService(
        settings=Settings(
            openrouter_api_key="test-key",
            openrouter_model="openai/gpt-4.1-mini",
        )
    )

    result = asyncio.run(
        service.generate_structured_payload(
            [{"role": "user", "content": "Answer in JSON."}],
            response_model=GeneratedAnswerPayload,
            temperature=0.1,
            max_tokens=120,
        )
    )

    assert result.answer == "hi"
    assert result.citation_labels == []
    assert len(captured_payloads) == 3
    assert captured_payloads[0]["response_format"]["type"] == "json_schema"
    assert captured_payloads[1]["response_format"] == {"type": "json_object"}
    assert "response_format" not in captured_payloads[2]
    assert "provider" not in captured_payloads[2]
    assert "plugins" not in captured_payloads[2]


def test_generate_structured_payload_remembers_relaxed_mode_after_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_payloads: list[dict[str, object]] = []

    class CapturingAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> bool:
            return False

        async def post(self, url: str, *, headers: dict[str, str], json: dict[str, object]):
            captured_payloads.append(json)
            if len(captured_payloads) == 1:
                return DummyResponse(
                    {
                        "error": {
                            "message": "No endpoints found that can handle the requested parameters.",
                            "code": 404,
                        }
                    },
                    status_code=404,
                    text=(
                        '{"error":{"message":"No endpoints found that can handle the requested '
                        'parameters.","code":404}}'
                    ),
                )

            return DummyResponse(
                {
                    "choices": [
                        {
                            "message": {
                                "content": '{"answer":"hi","citations":[],"insufficient_evidence":false}'
                            }
                        }
                    ]
                }
            )

    monkeypatch.setattr(httpx, "AsyncClient", CapturingAsyncClient)

    service = GenerationService(
        settings=Settings(
            openrouter_api_key="test-key",
            openrouter_model="openai/gpt-4.1-mini",
        )
    )

    first_result = asyncio.run(
        service.generate_structured_payload(
            [{"role": "user", "content": "Answer in JSON."}],
            response_model=GeneratedAnswerPayload,
            temperature=0.1,
            max_tokens=120,
        )
    )
    second_result = asyncio.run(
        service.generate_structured_payload(
            [{"role": "user", "content": "Answer in JSON again."}],
            response_model=GeneratedAnswerPayload,
            temperature=0.1,
            max_tokens=120,
        )
    )

    assert first_result.answer == "hi"
    assert second_result.answer == "hi"
    assert len(captured_payloads) == 3
    assert captured_payloads[0]["response_format"]["type"] == "json_schema"
    assert captured_payloads[1]["response_format"] == {"type": "json_object"}
    assert captured_payloads[2]["response_format"] == {"type": "json_object"}


def test_extract_message_content_rejects_reasoning_without_final_message() -> None:
    with pytest.raises(
        GenerationMalformedResponseError,
        match="reasoning tokens without a final assistant message",
    ):
        GenerationService._extract_message_content(
            {
                "choices": [
                    {
                        "message": {
                            "content": None,
                            "reasoning": "Thinking through the answer.",
                        }
                    }
                ]
            }
        )
