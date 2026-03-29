import asyncio

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.chat import RetrievedChunk
from app.schemas.compare import CompareRequest, CompareResponse
from app.services.compare_service import get_compare_service
from app.services.generation_service import GenerationUpstreamError
from app.services.retrieval_service import RetrievalNoRelevantChunksError
from app.workflows.compare_workflow import (
    CompareWorkflow,
    CompareWorkflowEvidenceError,
    CompareWorkflowNotReadyError,
)
from app.core.config import Settings


class StubCompareRetrievalService:
    def __init__(
        self,
        responses: dict[str, list[RetrievedChunk]],
        *,
        errors: dict[str, Exception] | None = None,
    ) -> None:
        self._responses = responses
        self._errors = errors or {}
        self.calls: list[dict[str, object]] = []

    async def retrieve_chunks(
        self,
        question: str,
        *,
        paper_ids: list[str] | None = None,
        top_k: int,
    ) -> list[RetrievedChunk]:
        paper_id = paper_ids[0] if paper_ids else "all"
        self.calls.append(
            {
                "question": question,
                "paper_ids": paper_ids,
                "top_k": top_k,
            }
        )
        error = self._errors.get(paper_id)
        if error is not None:
            raise error
        return self._responses[paper_id][:top_k]


class StubRerankingService:
    def __init__(self, *, enabled: bool = False) -> None:
        self.enabled = enabled

    async def rerank_chunks(
        self,
        question: str,
        chunks: list[RetrievedChunk],
        *,
        top_k: int,
    ) -> list[RetrievedChunk]:
        return chunks[:top_k]


class StubStructuredGenerationService:
    def __init__(
        self,
        *,
        payload: dict[str, object] | None = None,
        error: Exception | None = None,
    ) -> None:
        self._payload = payload
        self._error = error
        self.calls: list[dict[str, object]] = []

    async def generate_structured_payload(
        self,
        messages,
        *,
        response_model,
        temperature: float,
        max_tokens: int,
    ):
        self.calls.append(
            {
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        )
        if self._error is not None:
            raise self._error
        assert self._payload is not None
        return response_model.model_validate(self._payload)


class FakeChromaRepository:
    def __init__(self, counts: dict[str, int]) -> None:
        self._counts = counts

    def count_chunks_for_paper(self, paper_id: str) -> int:
        return self._counts.get(paper_id, 0)


def build_chunk(
    *,
    chunk_id: str,
    paper_id: str,
    page_number: int,
    text: str,
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        paper_id=paper_id,
        paper_title=f"Paper {paper_id}",
        page_number=page_number,
        chunk_index=0,
        page_chunk_index=0,
        source_url=f"https://arxiv.org/abs/{paper_id}",
        pdf_path=f"backend/data/raw_pdfs/{paper_id}.pdf",
        text=text,
        word_count=len(text.split()),
        start_word_index=0,
        end_word_index=len(text.split()),
        similarity_score=0.9,
    )


def build_settings() -> Settings:
    return Settings(
        reranking_enabled=False,
        compare_top_k_per_paper=1,
        enable_metrics_collection=True,
    )


def test_compare_workflow_generates_grounded_comparison_with_meta() -> None:
    settings = build_settings()
    retrieval_service = StubCompareRetrievalService(
        {
            "2401.12345": [
                build_chunk(
                    chunk_id="2401.12345-p2-c1",
                    paper_id="2401.12345",
                    page_number=2,
                    text="This paper uses a transformer encoder on retinal scans and evaluates on EyePACS.",
                )
            ],
            "2402.67890": [
                build_chunk(
                    chunk_id="2402.67890-p4-c1",
                    paper_id="2402.67890",
                    page_number=4,
                    text="This study fine-tunes a hybrid CNN-transformer and reports experiments on ChestX-ray14.",
                )
            ],
        }
    )
    generation_service = StubStructuredGenerationService(
        payload={
            "summary": "Both papers use transformer-based image models, but they differ in dataset focus and model setup.",
            "comparison_table": [
                {
                    "paper_id": "2401.12345",
                    "paper_title": "Paper 2401.12345",
                    "objective": "Detect retinal disease from fundus images.",
                    "methodology": "Transformer encoder on retinal scans.",
                    "dataset": "EyePACS.",
                    "strengths": "Direct focus on retinal imaging.",
                    "limitations": "Not stated in retrieved evidence.",
                    "key_contribution": "Applies a transformer encoder to retinal screening.",
                },
                {
                    "paper_id": "2402.67890",
                    "paper_title": "Paper 2402.67890",
                    "objective": "Classify chest X-rays with a hybrid architecture.",
                    "methodology": "Hybrid CNN-transformer fine-tuning.",
                    "dataset": "ChestX-ray14.",
                    "strengths": "Combines convolutional and transformer features.",
                    "limitations": "Not stated in retrieved evidence.",
                    "key_contribution": "Adapts a hybrid vision architecture to chest imaging.",
                },
            ],
            "citations": ["S1", "S2"],
            "insufficient_evidence": False,
        }
    )
    workflow = CompareWorkflow(
        retrieval_service=retrieval_service,
        reranking_service=StubRerankingService(enabled=False),
        generation_service=generation_service,
        chroma_repository=FakeChromaRepository({"2401.12345": 4, "2402.67890": 3}),
        settings=settings,
    )

    response = asyncio.run(
        workflow.compare_papers(
            CompareRequest(
                paper_ids=["2401.12345", "2402.67890"],
                question="Compare methodology and datasets.",
            )
        )
    )

    assert response.status == "completed"
    assert response.summary is not None
    assert len(response.comparison_table) == 2
    assert response.comparison_table[0].paper_id == "2401.12345"
    assert response.comparison_table[1].dataset == "ChestX-ray14."
    assert response.citations[0].label == "S1"
    assert response.retrieved_chunks[0].label == "S1"
    assert response.meta is not None
    assert response.meta.status == "completed"
    assert response.meta.retrieved_chunk_count == 2
    assert response.meta.citation_count == 2


def test_compare_workflow_returns_partial_response_when_generation_fails() -> None:
    settings = build_settings()
    workflow = CompareWorkflow(
        retrieval_service=StubCompareRetrievalService(
            {
                "2401.12345": [
                    build_chunk(
                        chunk_id="2401.12345-p1-c1",
                        paper_id="2401.12345",
                        page_number=1,
                        text="Retinal classification setup.",
                    )
                ],
                "2402.67890": [
                    build_chunk(
                        chunk_id="2402.67890-p3-c1",
                        paper_id="2402.67890",
                        page_number=3,
                        text="Chest X-ray classification setup.",
                    )
                ],
            }
        ),
        reranking_service=StubRerankingService(enabled=False),
        generation_service=StubStructuredGenerationService(
            error=GenerationUpstreamError("upstream failed")
        ),
        chroma_repository=FakeChromaRepository({"2401.12345": 2, "2402.67890": 2}),
        settings=settings,
    )

    response = asyncio.run(
        workflow.compare_papers(
            CompareRequest(paper_ids=["2401.12345", "2402.67890"])
        )
    )

    assert response.status == "partial"
    assert response.summary is None
    assert len(response.comparison_table) == 2
    assert response.citations[0].chunk_id == "2401.12345-p1-c1"
    assert response.retrieved_chunks[1].paper_id == "2402.67890"
    assert response.meta is not None
    assert response.meta.status == "partial"


def test_compare_workflow_rejects_unindexed_papers() -> None:
    workflow = CompareWorkflow(
        retrieval_service=StubCompareRetrievalService({}),
        reranking_service=StubRerankingService(enabled=False),
        generation_service=StubStructuredGenerationService(payload={}),
        chroma_repository=FakeChromaRepository({"2401.12345": 2, "2402.67890": 0}),
        settings=build_settings(),
    )

    try:
        asyncio.run(
            workflow.compare_papers(
                CompareRequest(paper_ids=["2401.12345", "2402.67890"])
            )
        )
    except CompareWorkflowNotReadyError as exc:
        assert "2402.67890" in str(exc)
    else:
        raise AssertionError("Expected CompareWorkflowNotReadyError")


def test_compare_workflow_rejects_papers_without_usable_evidence() -> None:
    workflow = CompareWorkflow(
        retrieval_service=StubCompareRetrievalService(
            {
                "2401.12345": [
                    build_chunk(
                        chunk_id="2401.12345-p1-c1",
                        paper_id="2401.12345",
                        page_number=1,
                        text="First indexed paper evidence.",
                    )
                ]
            },
            errors={
                "2402.67890": RetrievalNoRelevantChunksError("no evidence"),
            },
        ),
        reranking_service=StubRerankingService(enabled=False),
        generation_service=StubStructuredGenerationService(payload={}),
        chroma_repository=FakeChromaRepository({"2401.12345": 2, "2402.67890": 2}),
        settings=build_settings(),
    )

    try:
        asyncio.run(
            workflow.compare_papers(
                CompareRequest(paper_ids=["2401.12345", "2402.67890"])
            )
        )
    except CompareWorkflowEvidenceError as exc:
        assert "2402.67890" in str(exc)
    else:
        raise AssertionError("Expected CompareWorkflowEvidenceError")


def test_compare_route_rejects_invalid_paper_count() -> None:
    app.dependency_overrides = {}
    client = TestClient(app)

    response = client.post("/api/compare", json={"paper_ids": ["2401.12345"]})

    assert response.status_code == 400
    assert "at least 2" in response.json()["detail"]


def test_compare_route_returns_success_shape() -> None:
    app.dependency_overrides = {}

    response_payload = CompareResponse(
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
        citations=[
            {
                "label": "S1",
                "paper_id": "2401.12345",
                "paper_title": "Paper 2401.12345",
                "page_number": 2,
                "chunk_id": "2401.12345-p2-c1",
                "source_url": "https://arxiv.org/abs/2401.12345",
            }
        ],
        retrieved_chunks=[
            {
                "label": "S1",
                "chunk_id": "2401.12345-p2-c1",
                "paper_id": "2401.12345",
                "paper_title": "Paper 2401.12345",
                "page_number": 2,
                "chunk_index": 0,
                "page_chunk_index": 0,
                "source_url": "https://arxiv.org/abs/2401.12345",
                "pdf_path": "backend/data/raw_pdfs/2401.12345.pdf",
                "text": "Grounded comparison evidence.",
                "word_count": 3,
                "start_word_index": 0,
                "end_word_index": 3,
                "similarity_score": 0.9,
            }
        ],
        meta={
            "retrieval_ms": 10,
            "reranking_ms": 0,
            "generation_ms": 20,
            "total_ms": 35,
            "retrieved_chunk_count": 1,
            "citation_count": 1,
            "status": "completed",
        },
        message="Comparison generated successfully.",
    )

    class StubCompareService:
        async def compare_papers(self, payload):
            return response_payload

    app.dependency_overrides[get_compare_service] = lambda: StubCompareService()
    client = TestClient(app)

    response = client.post(
        "/api/compare",
        json={"paper_ids": ["2401.12345", "2402.67890"]},
    )

    assert response.status_code == 200
    assert response.json()["comparison_table"][0]["paper_id"] == "2401.12345"
    assert response.json()["meta"]["citation_count"] == 1
    assert response.json()["retrieved_chunks"][0]["chunk_id"] == "2401.12345-p2-c1"
    app.dependency_overrides = {}
