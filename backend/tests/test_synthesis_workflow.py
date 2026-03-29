import asyncio

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app
from app.schemas.chat import RetrievedChunk
from app.schemas.synthesis import TopicSynthesisRequest, TopicSynthesisResponse
from app.services.generation_service import GenerationUpstreamError
from app.services.synthesis_service import get_synthesis_service
from app.workflows.synthesis_workflow import (
    SynthesisWorkflow,
    SynthesisWorkflowNotReadyError,
)


class StubSynthesisRetrievalService:
    def __init__(self, chunks: list[RetrievedChunk]) -> None:
        self._chunks = chunks
        self.calls: list[dict[str, object]] = []

    async def retrieve_chunks(
        self,
        question: str,
        *,
        paper_ids: list[str] | None = None,
        top_k: int,
    ) -> list[RetrievedChunk]:
        self.calls.append(
            {
                "question": question,
                "paper_ids": paper_ids,
                "top_k": top_k,
            }
        )
        return self._chunks[:top_k]


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
        similarity_score=0.88,
    )


def build_settings() -> Settings:
    return Settings(
        reranking_enabled=False,
        synthesis_top_k=3,
        enable_metrics_collection=True,
    )


def test_synthesis_workflow_generates_grounded_topic_summary_with_meta() -> None:
    workflow = SynthesisWorkflow(
        retrieval_service=StubSynthesisRetrievalService(
            [
                build_chunk(
                    chunk_id="2401.12345-p1-c1",
                    paper_id="2401.12345",
                    page_number=1,
                    text="Vision transformers are increasingly adapted to medical image classification.",
                ),
                build_chunk(
                    chunk_id="2402.67890-p3-c1",
                    paper_id="2402.67890",
                    page_number=3,
                    text="Hybrid architectures remain common when data efficiency is a concern.",
                ),
            ]
        ),
        reranking_service=StubRerankingService(enabled=False),
        generation_service=StubStructuredGenerationService(
            payload={
                "topic": "Vision transformers for medical image classification",
                "overview": "The retrieved papers show growing use of transformer-based models, but hybrid designs remain common.",
                "themes": [
                    "Transformer-based medical image classifiers",
                    "Hybrid CNN-transformer modeling",
                ],
                "trends": [
                    "Greater adoption of transformer backbones",
                    "Continued concern around data efficiency",
                ],
                "open_challenges": [
                    "Small labeled datasets remain a challenge.",
                ],
                "research_gaps": [
                    "Cross-dataset generalization is not consistently addressed.",
                ],
                "future_directions": [
                    "Evaluate architectures across broader medical imaging domains.",
                ],
                "citations": ["S1", "S2"],
                "insufficient_evidence": False,
            }
        ),
        chroma_repository=FakeChromaRepository({"2401.12345": 2, "2402.67890": 2}),
        settings=build_settings(),
    )

    response = asyncio.run(
        workflow.summarize_topic(
            TopicSynthesisRequest(
                topic="Vision transformers for medical image classification",
                paper_ids=["2401.12345", "2402.67890"],
            )
        )
    )

    assert response.status == "completed"
    assert response.topic == "Vision transformers for medical image classification"
    assert len(response.themes) == 2
    assert response.citations[0].label == "S1"
    assert response.retrieved_chunks[1].paper_id == "2402.67890"
    assert response.meta is not None
    assert response.meta.status == "completed"
    assert response.meta.retrieved_chunk_count == 2


def test_synthesis_workflow_returns_partial_response_when_generation_fails() -> None:
    workflow = SynthesisWorkflow(
        retrieval_service=StubSynthesisRetrievalService(
            [
                build_chunk(
                    chunk_id="2401.12345-p2-c1",
                    paper_id="2401.12345",
                    page_number=2,
                    text="Retrieved evidence for synthesis.",
                )
            ]
        ),
        reranking_service=StubRerankingService(enabled=False),
        generation_service=StubStructuredGenerationService(
            error=GenerationUpstreamError("upstream failed")
        ),
        chroma_repository=FakeChromaRepository({"2401.12345": 2}),
        settings=build_settings(),
    )

    response = asyncio.run(
        workflow.summarize_topic(
            TopicSynthesisRequest(paper_ids=["2401.12345"])
        )
    )

    assert response.status == "partial"
    assert response.overview is None
    assert response.citations[0].chunk_id == "2401.12345-p2-c1"
    assert response.meta is not None
    assert response.meta.status == "partial"


def test_synthesis_workflow_rejects_unindexed_papers() -> None:
    workflow = SynthesisWorkflow(
        retrieval_service=StubSynthesisRetrievalService([]),
        reranking_service=StubRerankingService(enabled=False),
        generation_service=StubStructuredGenerationService(payload={}),
        chroma_repository=FakeChromaRepository({"2401.12345": 0}),
        settings=build_settings(),
    )

    try:
        asyncio.run(
            workflow.summarize_topic(
                TopicSynthesisRequest(paper_ids=["2401.12345"])
            )
        )
    except SynthesisWorkflowNotReadyError as exc:
        assert "2401.12345" in str(exc)
    else:
        raise AssertionError("Expected SynthesisWorkflowNotReadyError")


def test_synthesis_route_rejects_missing_topic_and_paper_ids() -> None:
    app.dependency_overrides = {}
    client = TestClient(app)

    response = client.post("/api/summarize-topic", json={})

    assert response.status_code == 400
    assert "Provide a topic" in response.json()["detail"]


def test_synthesis_route_returns_success_shape() -> None:
    app.dependency_overrides = {}

    response_payload = TopicSynthesisResponse(
        status="completed",
        topic="Medical vision transformers",
        overview="Grounded synthesis overview.",
        themes=["Theme A"],
        trends=["Trend A"],
        open_challenges=["Challenge A"],
        research_gaps=["Gap A"],
        future_directions=["Direction A"],
        citations=[
            {
                "label": "S1",
                "paper_id": "2401.12345",
                "paper_title": "Paper 2401.12345",
                "page_number": 5,
                "chunk_id": "2401.12345-p5-c1",
                "source_url": "https://arxiv.org/abs/2401.12345",
            }
        ],
        retrieved_chunks=[
            {
                "label": "S1",
                "chunk_id": "2401.12345-p5-c1",
                "paper_id": "2401.12345",
                "paper_title": "Paper 2401.12345",
                "page_number": 5,
                "chunk_index": 0,
                "page_chunk_index": 0,
                "source_url": "https://arxiv.org/abs/2401.12345",
                "pdf_path": "backend/data/raw_pdfs/2401.12345.pdf",
                "text": "Synthesis evidence text.",
                "word_count": 3,
                "start_word_index": 0,
                "end_word_index": 3,
                "similarity_score": 0.8,
            }
        ],
        meta={
            "retrieval_ms": 8,
            "reranking_ms": 0,
            "generation_ms": 18,
            "total_ms": 30,
            "retrieved_chunk_count": 1,
            "citation_count": 1,
            "status": "completed",
        },
        message="Topic synthesis generated successfully.",
    )

    class StubSynthesisService:
        async def summarize_topic(self, payload):
            return response_payload

    app.dependency_overrides[get_synthesis_service] = lambda: StubSynthesisService()
    client = TestClient(app)

    response = client.post(
        "/api/summarize-topic",
        json={"topic": "Medical vision transformers"},
    )

    assert response.status_code == 200
    assert response.json()["topic"] == "Medical vision transformers"
    assert response.json()["meta"]["retrieved_chunk_count"] == 1
    assert response.json()["citations"][0]["chunk_id"] == "2401.12345-p5-c1"
    app.dependency_overrides = {}
