import asyncio

import pytest

from app.schemas.chat import RetrievedChunk
from app.services.embedding_service import EmbeddingServiceError
from app.services.retrieval_service import (
    RetrievalNoIndexedPapersError,
    RetrievalNoRelevantChunksError,
    RetrievalService,
    RetrievalServiceError,
)


class FakeEmbeddingService:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        return [[0.25, 0.75]]


class FailingEmbeddingService:
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        raise EmbeddingServiceError("embedding backend unavailable")


class FakeChromaRepository:
    def __init__(
        self,
        *,
        count: int,
        chunks: list[RetrievedChunk] | None = None,
    ) -> None:
        self._count = count
        self._chunks = list(chunks or [])
        self.count_calls: list[list[str] | None] = []
        self.query_calls: list[dict[str, object]] = []

    def count_chunks(self, paper_ids: list[str] | None = None) -> int:
        self.count_calls.append(paper_ids)
        return self._count

    def query_chunks(
        self,
        query_embedding: list[float],
        limit: int,
        paper_ids: list[str] | None = None,
    ) -> list[RetrievedChunk]:
        self.query_calls.append(
            {
                "query_embedding": list(query_embedding),
                "limit": limit,
                "paper_ids": paper_ids,
            }
        )
        return self._chunks[:limit]


def build_chunk(
    *,
    chunk_id: str = "2401.12345-p1-c1",
    paper_id: str = "2401.12345",
    page_number: int = 1,
    text: str = "Vision transformers struggle with data efficiency in small medical datasets.",
    similarity_score: float | None = 0.91,
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        paper_id=paper_id,
        paper_title="Medical ViT Limitations",
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


def test_retrieve_chunks_returns_similarity_results_with_provenance() -> None:
    embedding_service = FakeEmbeddingService()
    chroma_repository = FakeChromaRepository(
        count=2,
        chunks=[
            build_chunk(),
            build_chunk(
                chunk_id="2402.67890-p4-c2",
                paper_id="2402.67890",
                page_number=4,
                text="Large patch sizes can remove clinically subtle features.",
                similarity_score=0.84,
            ),
        ],
    )
    service = RetrievalService(
        embedding_service=embedding_service,
        chroma_repository=chroma_repository,
    )

    result = asyncio.run(
        service.retrieve_chunks(
            "What are the main limitations of vision transformers for medical imaging?",
            top_k=2,
        )
    )

    assert len(result) == 2
    assert result[0].chunk_id == "2401.12345-p1-c1"
    assert result[0].paper_title == "Medical ViT Limitations"
    assert result[0].page_number == 1
    assert result[0].similarity_score == pytest.approx(0.91)
    assert embedding_service.calls == [
        ["What are the main limitations of vision transformers for medical imaging?"]
    ]
    assert chroma_repository.query_calls[0]["limit"] == 2


def test_retrieve_chunks_restricts_query_to_requested_paper_ids() -> None:
    chroma_repository = FakeChromaRepository(count=1, chunks=[build_chunk()])
    service = RetrievalService(
        embedding_service=FakeEmbeddingService(),
        chroma_repository=chroma_repository,
    )

    asyncio.run(
        service.retrieve_chunks(
            "Target a specific indexed paper.",
            paper_ids=["2401.12345"],
            top_k=3,
        )
    )

    assert chroma_repository.count_calls == [["2401.12345"]]
    assert chroma_repository.query_calls[0]["paper_ids"] == ["2401.12345"]


def test_retrieve_chunks_raises_when_no_indexed_papers_are_available() -> None:
    service = RetrievalService(
        embedding_service=FakeEmbeddingService(),
        chroma_repository=FakeChromaRepository(count=0),
    )

    with pytest.raises(RetrievalNoIndexedPapersError):
        asyncio.run(service.retrieve_chunks("Any grounded question", top_k=4))


def test_retrieve_chunks_raises_when_no_relevant_chunks_are_found() -> None:
    service = RetrievalService(
        embedding_service=FakeEmbeddingService(),
        chroma_repository=FakeChromaRepository(count=2, chunks=[]),
    )

    with pytest.raises(RetrievalNoRelevantChunksError):
        asyncio.run(service.retrieve_chunks("Any grounded question", top_k=4))


def test_retrieve_chunks_wraps_embedding_failures_as_service_errors() -> None:
    service = RetrievalService(
        embedding_service=FailingEmbeddingService(),
        chroma_repository=FakeChromaRepository(count=2, chunks=[build_chunk()]),
    )

    with pytest.raises(RetrievalServiceError, match="embedding backend unavailable"):
        asyncio.run(service.retrieve_chunks("Any grounded question", top_k=4))
