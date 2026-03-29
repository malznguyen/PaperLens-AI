import asyncio

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.chat import ChatRequest, ChatResponse, GenerationResult, RetrievedChunk
from app.services.generation_service import GenerationUpstreamError
from app.services.reranking_service import RerankingServiceError
from app.services.chat_service import get_chat_service
from app.workflows.chat_workflow import ChatWorkflow


class StubRetrievalService:
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
    def __init__(
        self,
        *,
        enabled: bool = True,
        should_fail: bool = False,
    ) -> None:
        self.enabled = enabled
        self.should_fail = should_fail
        self.calls: list[dict[str, object]] = []

    async def rerank_chunks(
        self,
        question: str,
        chunks: list[RetrievedChunk],
        *,
        top_k: int,
    ) -> list[RetrievedChunk]:
        self.calls.append(
            {
                "question": question,
                "top_k": top_k,
                "chunk_ids": [chunk.chunk_id for chunk in chunks],
            }
        )
        if self.should_fail:
            raise RerankingServiceError("reranker unavailable")
        return list(reversed(chunks))[:top_k]


class StubGenerationService:
    def __init__(
        self,
        *,
        result: GenerationResult | None = None,
        error: Exception | None = None,
    ) -> None:
        self._result = result
        self._error = error
        self.calls: list[dict[str, object]] = []

    async def generate_answer(
        self,
        question: str,
        chunks: list[RetrievedChunk],
    ) -> GenerationResult:
        self.calls.append(
            {
                "question": question,
                "chunk_ids": [chunk.chunk_id for chunk in chunks],
            }
        )
        if self._error is not None:
            raise self._error
        assert self._result is not None
        return self._result


def build_chunk(
    *,
    chunk_id: str,
    paper_id: str,
    page_number: int,
    text: str,
    similarity_score: float | None = None,
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
        similarity_score=similarity_score,
    )


def test_chat_workflow_generates_grounded_answer_with_citations() -> None:
    chunks = [
        build_chunk(
            chunk_id="2401.12345-p1-c1",
            paper_id="2401.12345",
            page_number=1,
            text="Vision transformers can underperform when medical datasets are small.",
            similarity_score=0.88,
        ),
        build_chunk(
            chunk_id="2402.67890-p4-c2",
            paper_id="2402.67890",
            page_number=4,
            text="High-resolution medical imaging can make transformer training memory-intensive.",
            similarity_score=0.82,
        ),
    ]
    workflow = ChatWorkflow(
        retrieval_service=StubRetrievalService(chunks),
        reranking_service=StubRerankingService(enabled=False),
        generation_service=StubGenerationService(
            result=GenerationResult(
                answer="The retrieved papers point to small-data sensitivity and computational cost.",
                citation_labels=["S1", "S2"],
            )
        ),
    )

    response = asyncio.run(
        workflow.answer_question(
            ChatRequest(
                question="What are the main limitations of vision transformers for medical image classification?",
                top_k=2,
            )
        )
    )

    assert response.status == "completed"
    assert response.answer is not None
    assert "Sources:" in response.answer
    assert response.citations[0].paper_id == "2401.12345"
    assert response.citations[0].label == "S1"
    assert response.citations[1].page_number == 4
    assert response.retrieved_chunks[0].label == "S1"


def test_chat_workflow_returns_evidence_when_generation_fails() -> None:
    chunks = [
        build_chunk(
            chunk_id="2401.12345-p2-c1",
            paper_id="2401.12345",
            page_number=2,
            text="Patch tokenization can remove clinically subtle findings.",
        )
    ]
    workflow = ChatWorkflow(
        retrieval_service=StubRetrievalService(chunks),
        reranking_service=StubRerankingService(enabled=False),
        generation_service=StubGenerationService(
            error=GenerationUpstreamError("upstream failed")
        ),
    )

    response = asyncio.run(
        workflow.answer_question(
            ChatRequest(
                question="Why can vision transformers miss subtle features?",
                top_k=1,
            )
        )
    )

    assert response.status == "partial"
    assert response.answer is None
    assert response.message == "Evidence retrieved, but answer generation failed."
    assert response.citations[0].chunk_id == "2401.12345-p2-c1"
    assert response.retrieved_chunks[0].page_number == 2


def test_chat_workflow_falls_back_to_retrieval_order_when_reranker_fails() -> None:
    chunks = [
        build_chunk(
            chunk_id="2401.12345-p1-c1",
            paper_id="2401.12345",
            page_number=1,
            text="First retrieved chunk.",
        ),
        build_chunk(
            chunk_id="2401.12345-p2-c1",
            paper_id="2401.12345",
            page_number=2,
            text="Second retrieved chunk.",
        ),
    ]
    workflow = ChatWorkflow(
        retrieval_service=StubRetrievalService(chunks),
        reranking_service=StubRerankingService(should_fail=True),
        generation_service=StubGenerationService(
            result=GenerationResult(
                answer="The evidence comes from the retrieved order after reranking fallback.",
                citation_labels=["S1"],
            )
        ),
    )

    response = asyncio.run(
        workflow.answer_question(
            ChatRequest(
                question="Does the reranking layer fail safely?",
                top_k=2,
            )
        )
    )

    assert response.status == "completed"
    assert response.retrieved_chunks[0].chunk_id == "2401.12345-p1-c1"
    assert response.retrieved_chunks[1].chunk_id == "2401.12345-p2-c1"


def test_chat_route_rejects_blank_questions_with_400() -> None:
    app.dependency_overrides = {}
    client = TestClient(app)

    response = client.post("/api/chat", json={"question": "   "})

    assert response.status_code == 400
    assert response.json() == {"detail": "question: Value error, Must not be blank."}


def test_chat_route_returns_response_shape_for_successful_generation() -> None:
    app.dependency_overrides = {}
    response_payload = ChatResponse(
        status="completed",
        question="What are the trade-offs?",
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
        message="Answer generated successfully.",
    )

    class StubChatService:
        async def answer_question(self, payload):
            return response_payload

    app.dependency_overrides[get_chat_service] = lambda: StubChatService()
    client = TestClient(app)

    response = client.post("/api/chat", json={"question": "What are the trade-offs?"})

    assert response.status_code == 200
    assert response.json()["citations"][0]["page_number"] == 3
    assert response.json()["retrieved_chunks"][0]["chunk_id"] == "2401.12345-p3-c1"
    assert response.json()["message"] == "Answer generated successfully."
    app.dependency_overrides = {}
