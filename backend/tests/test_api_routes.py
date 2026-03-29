from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.schemas.chat import ChatResponse
from app.schemas.compare import CompareResponse
from app.schemas.ingest import IngestResponse
from app.schemas.indexing import IndexPaperResponse
from app.schemas.search import SearchPapersResponse
from app.schemas.synthesis import TopicSynthesisResponse
from app.services.chat_service import (
    ChatEvidenceError,
    ChatNotReadyError,
    ChatServiceError,
    get_chat_service,
)
from app.services.compare_service import (
    CompareEvidenceError,
    CompareNotReadyError,
    CompareServiceError,
    get_compare_service,
)
from app.services.indexing_service import (
    IndexingArtifactError,
    IndexingEmbeddingError,
    IndexingNoContentError,
    IndexingNotFoundError,
    IndexingStorageError,
    get_indexing_service,
)
from app.services.ingest_service import (
    IngestProcessingError,
    IngestStorageError,
    IngestTimeoutError,
    IngestUpstreamError,
    get_ingest_service,
)
from app.services.search_service import SearchUpstreamError, SearchValidationError, get_search_service
from app.services.synthesis_service import (
    SynthesisEvidenceError,
    SynthesisNotReadyError,
    SynthesisServiceError,
    get_synthesis_service,
)

SEARCH_PAYLOAD = {
    "query": "vision transformer medical imaging",
    "max_results": 5,
}
INGEST_PAYLOAD = {
    "id": "2401.12345",
    "title": "Vision Transformers for Medical Imaging",
    "pdf_url": "https://arxiv.org/pdf/2401.12345.pdf",
    "source_url": "https://arxiv.org/abs/2401.12345",
    "authors": ["Alice Smith", "Bob Jones"],
    "abstract": "We study transformer variants for medical image analysis.",
    "published_at": "2024-01-10T12:00:00Z",
    "updated_at": "2024-01-15T09:30:00Z",
    "categories": ["cs.CV"],
    "primary_category": "cs.CV",
}
INDEX_PAYLOAD = {"paper_id": "2401.12345"}
CHAT_PAYLOAD = {
    "question": "What limitations are reported for these models?",
    "paper_ids": ["2401.12345"],
    "top_k": 4,
}
COMPARE_PAYLOAD = {
    "paper_ids": ["2401.12345", "2402.67890"],
    "question": "Compare methodology and datasets.",
}
SYNTHESIS_PAYLOAD = {
    "topic": "Vision transformers in medical imaging",
    "paper_ids": ["2401.12345"],
}


class AsyncServiceStub:
    def __init__(
        self,
        method_name: str,
        *,
        result: Any = None,
        error: Exception | None = None,
    ) -> None:
        self._method_name = method_name
        self._result = result
        self._error = error
        self.calls: list[Any] = []

    def __getattr__(self, name: str):
        if name != self._method_name:
            raise AttributeError(name)

        async def method(payload: Any) -> Any:
            self.calls.append(payload)
            if self._error is not None:
                raise self._error
            return self._result

        return method


@pytest.mark.parametrize(
    ("provider", "method_name", "path", "payload", "error", "expected_status", "expected_detail"),
    [
        (
            get_search_service,
            "search_papers",
            "/api/search-papers",
            SEARCH_PAYLOAD,
            SearchValidationError("Query must not be empty."),
            400,
            "Query must not be empty.",
        ),
        (
            get_search_service,
            "search_papers",
            "/api/search-papers",
            SEARCH_PAYLOAD,
            SearchUpstreamError("Failed to fetch papers from arXiv."),
            502,
            "Failed to fetch papers from arXiv.",
        ),
        (
            get_ingest_service,
            "ingest_paper",
            "/api/ingest",
            INGEST_PAYLOAD,
            IngestTimeoutError("Timed out while downloading the PDF."),
            504,
            "Timed out while downloading the PDF.",
        ),
        (
            get_ingest_service,
            "ingest_paper",
            "/api/ingest",
            INGEST_PAYLOAD,
            IngestUpstreamError("Failed to download the PDF."),
            502,
            "Failed to download the PDF.",
        ),
        (
            get_ingest_service,
            "ingest_paper",
            "/api/ingest",
            INGEST_PAYLOAD,
            IngestProcessingError("Unable to parse this PDF."),
            422,
            "Unable to parse this PDF.",
        ),
        (
            get_ingest_service,
            "ingest_paper",
            "/api/ingest",
            INGEST_PAYLOAD,
            IngestStorageError("Failed to persist ingest artifacts."),
            500,
            "Failed to persist ingest artifacts.",
        ),
        (
            get_indexing_service,
            "index_paper",
            "/api/index-paper",
            INDEX_PAYLOAD,
            IndexingNotFoundError("Parsed artifact not found for paper '2401.12345'."),
            404,
            "Parsed artifact not found for paper '2401.12345'.",
        ),
        (
            get_indexing_service,
            "index_paper",
            "/api/index-paper",
            INDEX_PAYLOAD,
            IndexingNoContentError("Parsed artifact does not contain usable page-aware text to index."),
            422,
            "Parsed artifact does not contain usable page-aware text to index.",
        ),
        (
            get_indexing_service,
            "index_paper",
            "/api/index-paper",
            INDEX_PAYLOAD,
            IndexingArtifactError("Parsed artifact is invalid and could not be indexed."),
            500,
            "Parsed artifact is invalid and could not be indexed.",
        ),
        (
            get_indexing_service,
            "index_paper",
            "/api/index-paper",
            INDEX_PAYLOAD,
            IndexingEmbeddingError("Embedding model unavailable."),
            500,
            "Embedding model unavailable.",
        ),
        (
            get_indexing_service,
            "index_paper",
            "/api/index-paper",
            INDEX_PAYLOAD,
            IndexingStorageError("Failed to write the indexing cache metadata."),
            500,
            "Failed to write the indexing cache metadata.",
        ),
        (
            get_chat_service,
            "answer_question",
            "/api/chat",
            CHAT_PAYLOAD,
            ChatNotReadyError("No indexed papers are available yet."),
            404,
            "No indexed papers are available yet.",
        ),
        (
            get_chat_service,
            "answer_question",
            "/api/chat",
            CHAT_PAYLOAD,
            ChatEvidenceError("No relevant chunks were retrieved for this question."),
            422,
            "No relevant chunks were retrieved for this question.",
        ),
        (
            get_chat_service,
            "answer_question",
            "/api/chat",
            CHAT_PAYLOAD,
            ChatServiceError("Retrieval infrastructure failed."),
            500,
            "Retrieval infrastructure failed.",
        ),
        (
            get_compare_service,
            "compare_papers",
            "/api/compare",
            COMPARE_PAYLOAD,
            CompareNotReadyError("These paper IDs are not indexed yet: 2402.67890."),
            404,
            "These paper IDs are not indexed yet: 2402.67890.",
        ),
        (
            get_compare_service,
            "compare_papers",
            "/api/compare",
            COMPARE_PAYLOAD,
            CompareEvidenceError("Paper 2402.67890 does not have enough usable evidence for this comparison request."),
            422,
            "Paper 2402.67890 does not have enough usable evidence for this comparison request.",
        ),
        (
            get_compare_service,
            "compare_papers",
            "/api/compare",
            COMPARE_PAYLOAD,
            CompareServiceError("Comparison workflow failed."),
            500,
            "Comparison workflow failed.",
        ),
        (
            get_synthesis_service,
            "summarize_topic",
            "/api/summarize-topic",
            SYNTHESIS_PAYLOAD,
            SynthesisNotReadyError("These paper IDs are not indexed yet: 2401.12345."),
            404,
            "These paper IDs are not indexed yet: 2401.12345.",
        ),
        (
            get_synthesis_service,
            "summarize_topic",
            "/api/summarize-topic",
            SYNTHESIS_PAYLOAD,
            SynthesisEvidenceError("No relevant chunks were retrieved for this question."),
            422,
            "No relevant chunks were retrieved for this question.",
        ),
        (
            get_synthesis_service,
            "summarize_topic",
            "/api/summarize-topic",
            SYNTHESIS_PAYLOAD,
            SynthesisServiceError("Synthesis workflow failed."),
            500,
            "Synthesis workflow failed.",
        ),
    ],
)
def test_api_routes_map_service_errors_to_expected_http_status(
    client: TestClient,
    provider,
    method_name: str,
    path: str,
    payload: dict[str, Any],
    error: Exception,
    expected_status: int,
    expected_detail: str,
) -> None:
    from app.main import app

    stub_service = AsyncServiceStub(method_name, error=error)
    app.dependency_overrides[provider] = lambda: stub_service

    response = client.post(path, json=payload)

    assert response.status_code == expected_status
    assert response.json() == {"detail": expected_detail}
    assert len(stub_service.calls) == 1


@pytest.mark.parametrize(
    ("path", "payload", "expected_status", "detail_fragment"),
    [
        (
            "/api/search-papers",
            {"query": "vision transformers", "max_results": 26},
            422,
            "less than or equal to 25",
        ),
        (
            "/api/ingest",
            {**INGEST_PAYLOAD, "pdf_url": "not-a-valid-url"},
            400,
            "pdf_url must be a valid HTTP or HTTPS URL",
        ),
        (
            "/api/index-paper",
            {"paper_id": "   "},
            400,
            "Must not be blank",
        ),
        (
            "/api/chat",
            {"question": "What changed?", "top_k": 99},
            400,
            "top_k must be between 1 and 12",
        ),
        (
            "/api/compare",
            {"paper_ids": ["2401.12345"]},
            400,
            "at least 2 unique paper IDs",
        ),
        (
            "/api/summarize-topic",
            {},
            400,
            "Provide a topic, one or more paper IDs, or both",
        ),
    ],
)
def test_major_api_routes_reject_invalid_requests_before_remote_work(
    client: TestClient,
    path: str,
    payload: dict[str, Any],
    expected_status: int,
    detail_fragment: str,
) -> None:
    response = client.post(path, json=payload)

    assert response.status_code == expected_status
    detail = response.json()["detail"]
    if isinstance(detail, str):
        assert detail_fragment in detail
    else:
        assert detail
        first_message = detail[0]["msg"]
        assert detail_fragment in first_message


def test_chat_route_returns_grounded_response_payload(client: TestClient) -> None:
    from app.main import app

    response_payload = ChatResponse(
        status="completed",
        question=CHAT_PAYLOAD["question"],
        answer="Short grounded answer.\n\nSources:\n[S1] Paper 2401.12345 (2401.12345), p. 3",
        citations=[
            {
                "label": "S1",
                "paper_id": "2401.12345",
                "paper_title": "Paper 2401.12345",
                "page_number": 3,
                "chunk_id": "2401.12345-p3-c1",
                "source_url": "https://arxiv.org/abs/2401.12345",
            }
        ],
        retrieved_chunks=[
            {
                "label": "S1",
                "chunk_id": "2401.12345-p3-c1",
                "paper_id": "2401.12345",
                "paper_title": "Paper 2401.12345",
                "page_number": 3,
                "chunk_index": 0,
                "page_chunk_index": 0,
                "source_url": "https://arxiv.org/abs/2401.12345",
                "pdf_path": "backend/data/raw_pdfs/2401.12345.pdf",
                "text": "Grounded evidence text.",
                "word_count": 3,
                "start_word_index": 0,
                "end_word_index": 3,
                "similarity_score": 0.9,
            }
        ],
        meta={
            "retrieval_ms": 8,
            "reranking_ms": 0,
            "generation_ms": 19,
            "total_ms": 31,
            "retrieved_chunk_count": 1,
            "citation_count": 1,
            "status": "completed",
        },
        message="Answer generated successfully.",
    )
    app.dependency_overrides[get_chat_service] = lambda: AsyncServiceStub(
        "answer_question",
        result=response_payload,
    )

    response = client.post("/api/chat", json=CHAT_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["citations"][0]["page_number"] == 3
    assert body["retrieved_chunks"][0]["chunk_id"] == "2401.12345-p3-c1"
    assert body["meta"]["citation_count"] == 1


@pytest.mark.parametrize(
    ("provider", "method_name", "path", "payload", "response_payload", "expected_field", "expected_value"),
    [
        (
            get_search_service,
            "search_papers",
            "/api/search-papers",
            SEARCH_PAYLOAD,
            SearchPapersResponse(
                query=SEARCH_PAYLOAD["query"],
                count=1,
                results=[
                    {
                        "id": "2401.12345",
                        "title": "Vision Transformers for Medical Imaging",
                        "authors": ["Alice Smith"],
                        "abstract": "Transformer-based medical imaging study.",
                        "published_at": "2024-01-10T12:00:00Z",
                        "updated_at": "2024-01-15T09:30:00Z",
                        "categories": ["cs.CV"],
                        "pdf_url": "https://arxiv.org/pdf/2401.12345.pdf",
                        "source_url": "https://arxiv.org/abs/2401.12345",
                        "primary_category": "cs.CV",
                    }
                ],
            ),
            ("results", 0, "id"),
            "2401.12345",
        ),
        (
            get_ingest_service,
            "ingest_paper",
            "/api/ingest",
            INGEST_PAYLOAD,
            IngestResponse(
                paper_id="2401.12345",
                status="completed",
                pdf_path="backend/data/raw_pdfs/2401.12345.pdf",
                parsed_path="backend/data/parsed/2401.12345.json",
                page_count=12,
                word_count=4321,
                message="Paper ingested and parsed successfully.",
            ),
            ("status",),
            "completed",
        ),
        (
            get_indexing_service,
            "index_paper",
            "/api/index-paper",
            INDEX_PAYLOAD,
            IndexPaperResponse(
                paper_id="2401.12345",
                status="completed",
                chunk_count=42,
                collection_name="paper_chunks",
                message="Paper indexed successfully.",
            ),
            ("chunk_count",),
            42,
        ),
        (
            get_compare_service,
            "compare_papers",
            "/api/compare",
            COMPARE_PAYLOAD,
            CompareResponse(
                status="completed",
                summary="Grounded comparison summary.",
                comparison_table=[
                    {
                        "paper_id": "2401.12345",
                        "paper_title": "Paper 2401.12345",
                        "objective": "Objective.",
                        "methodology": "Method.",
                        "dataset": "Dataset.",
                        "strengths": "Strength.",
                        "limitations": "Limitation.",
                        "key_contribution": "Contribution.",
                    }
                ],
                citations=[],
                retrieved_chunks=[],
                message="Comparison generated successfully.",
            ),
            ("comparison_table", 0, "paper_id"),
            "2401.12345",
        ),
        (
            get_synthesis_service,
            "summarize_topic",
            "/api/summarize-topic",
            SYNTHESIS_PAYLOAD,
            TopicSynthesisResponse(
                status="completed",
                topic="Vision transformers in medical imaging",
                overview="Grounded synthesis overview.",
                themes=["Theme A"],
                trends=["Trend A"],
                open_challenges=["Challenge A"],
                research_gaps=["Gap A"],
                future_directions=["Direction A"],
                citations=[],
                retrieved_chunks=[],
                message="Topic synthesis generated successfully.",
            ),
            ("topic",),
            "Vision transformers in medical imaging",
        ),
    ],
)
def test_main_api_routes_return_expected_response_shapes(
    client: TestClient,
    provider,
    method_name: str,
    path: str,
    payload: dict[str, Any],
    response_payload: Any,
    expected_field: tuple[Any, ...],
    expected_value: Any,
) -> None:
    from app.main import app

    app.dependency_overrides[provider] = lambda: AsyncServiceStub(
        method_name,
        result=response_payload,
    )

    response = client.post(path, json=payload)

    assert response.status_code == 200
    body: Any = response.json()
    for key in expected_field:
        body = body[key]
    assert body == expected_value
