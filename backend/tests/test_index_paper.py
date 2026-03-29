import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import ROOT_DIR, get_settings
from app.main import app
from app.schemas.ingest import ParsedPage, ParsedPaperDocument
from app.services.indexing_service import IndexingService, get_indexing_service
from app.utils.file_utils import build_storage_stem
from app.utils.text_utils import count_words
from app.workflows.indexing_workflow import IndexingWorkflow

SAMPLE_PAPER_ID = "2401.12345"


class FakeEmbeddingService:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        return [[float(index), float(len(text))] for index, text in enumerate(texts, start=1)]


class RecordingChromaRepository:
    def __init__(self, collection_name: str = "paper_chunks") -> None:
        self.collection_name = collection_name
        self.replace_calls: list[dict[str, object]] = []
        self.paper_chunk_counts: dict[str, int] = {}

    def replace_paper_chunks(self, chunks, embeddings) -> None:
        self.replace_calls.append(
            {
                "chunks": list(chunks),
                "embeddings": list(embeddings),
            }
        )

        if chunks:
            self.paper_chunk_counts[chunks[0].paper_id] = len(chunks)

    def count_chunks_for_paper(self, paper_id: str) -> int:
        return self.paper_chunk_counts.get(paper_id, 0)


@pytest.fixture(autouse=True)
def clear_dependency_overrides() -> None:
    app.dependency_overrides = {}
    yield
    app.dependency_overrides = {}


@pytest.fixture()
def isolated_indexing_storage() -> None:
    settings = get_settings()
    original_paths = {
        "data_dir": settings.data_dir,
        "raw_pdfs_dir": settings.raw_pdfs_dir,
        "parsed_dir": settings.parsed_dir,
        "cache_dir": settings.cache_dir,
        "chroma_dir": settings.chroma_dir,
    }

    test_data_dir = ROOT_DIR / "backend" / "data" / "pytest-indexing"
    settings.data_dir = test_data_dir
    settings.raw_pdfs_dir = test_data_dir / "raw_pdfs"
    settings.parsed_dir = test_data_dir / "parsed"
    settings.cache_dir = test_data_dir / "cache"
    settings.chroma_dir = test_data_dir / "chroma"
    settings.ensure_directories()

    yield

    shutil.rmtree(test_data_dir, ignore_errors=True)

    for field_name, original_value in original_paths.items():
        setattr(settings, field_name, original_value)


def build_document(page_texts: list[str], *, paper_id: str = SAMPLE_PAPER_ID) -> ParsedPaperDocument:
    full_text = "\n\n".join(text.strip() for text in page_texts if text.strip())
    return ParsedPaperDocument(
        paper_id=paper_id,
        title="Indexing Pipeline Test Paper",
        authors=["Alice Smith", "Bob Jones"],
        abstract="Indexing workflow fixture.",
        published_at="2024-01-10T12:00:00Z",
        updated_at="2024-01-15T09:30:00Z",
        categories=["cs.AI"],
        primary_category="cs.AI",
        source_url=f"https://arxiv.org/abs/{paper_id}",
        pdf_url=f"https://arxiv.org/pdf/{paper_id}.pdf",
        pdf_path=f"backend/data/raw_pdfs/{paper_id}.pdf",
        page_count=len(page_texts),
        character_count=len(full_text),
        word_count=count_words(full_text),
        pages=[
            ParsedPage(page_number=index, text=text)
            for index, text in enumerate(page_texts, start=1)
        ],
        full_text=full_text,
    )


def write_parsed_document(document: ParsedPaperDocument) -> Path:
    settings = get_settings()
    parsed_path = settings.parsed_dir / f"{build_storage_stem(document.paper_id)}.json"
    parsed_path.parent.mkdir(parents=True, exist_ok=True)
    parsed_path.write_text(document.model_dump_json(indent=2), encoding="utf-8")
    return parsed_path


def build_indexing_service(
    *,
    embedding_service: FakeEmbeddingService | None = None,
    chroma_repository: RecordingChromaRepository | None = None,
) -> tuple[IndexingService, FakeEmbeddingService, RecordingChromaRepository]:
    embedding = embedding_service or FakeEmbeddingService()
    chroma = chroma_repository or RecordingChromaRepository()
    service = IndexingService(
        workflow=IndexingWorkflow(
            embedding_service=embedding,
            chroma_repository=chroma,
        )
    )
    return service, embedding, chroma


def index_cache_path(paper_id: str) -> Path:
    settings = get_settings()
    return settings.indexing_cache_dir / f"{build_storage_stem(paper_id)}.json"


def test_index_paper_indexes_parsed_artifact_and_writes_cache(isolated_indexing_storage) -> None:
    write_parsed_document(
        build_document(
            [
                "Vision transformers improve medical image classification across several benchmarks.",
                "The retrieval layer needs chunk provenance to support future grounded answers.",
            ]
        )
    )
    service, embedding_service, chroma_repository = build_indexing_service()
    app.dependency_overrides[get_indexing_service] = lambda: service
    client = TestClient(app)

    response = client.post("/api/index-paper", json={"paper_id": SAMPLE_PAPER_ID})

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "paper_id": SAMPLE_PAPER_ID,
        "status": "completed",
        "chunk_count": 2,
        "collection_name": "paper_chunks",
        "message": "Paper indexed successfully.",
    }
    assert len(embedding_service.calls) == 1
    assert len(chroma_repository.replace_calls) == 1

    stored_chunks = chroma_repository.replace_calls[0]["chunks"]
    first_chunk = stored_chunks[0]
    assert first_chunk.paper_id == SAMPLE_PAPER_ID
    assert first_chunk.paper_title == "Indexing Pipeline Test Paper"
    assert first_chunk.page_number == 1
    assert first_chunk.source_url == f"https://arxiv.org/abs/{SAMPLE_PAPER_ID}"
    assert first_chunk.pdf_path == f"backend/data/raw_pdfs/{SAMPLE_PAPER_ID}.pdf"
    assert first_chunk.word_count > 0

    cache_payload = json.loads(index_cache_path(SAMPLE_PAPER_ID).read_text(encoding="utf-8"))
    assert cache_payload["paper_id"] == SAMPLE_PAPER_ID
    assert cache_payload["chunk_count"] == 2
    assert cache_payload["collection_name"] == "paper_chunks"


def test_index_paper_returns_not_found_when_parsed_artifact_is_missing(
    isolated_indexing_storage,
) -> None:
    service, _, _ = build_indexing_service()
    app.dependency_overrides[get_indexing_service] = lambda: service
    client = TestClient(app)

    response = client.post("/api/index-paper", json={"paper_id": SAMPLE_PAPER_ID})

    assert response.status_code == 404
    assert response.json() == {
        "detail": (
            f"Parsed artifact not found for paper '{SAMPLE_PAPER_ID}'. "
            "Ingest the paper before indexing it."
        )
    }


def test_index_paper_returns_422_when_parsed_artifact_has_no_usable_content(
    isolated_indexing_storage,
) -> None:
    write_parsed_document(build_document(["   ", ""], paper_id=SAMPLE_PAPER_ID))
    service, _, _ = build_indexing_service()
    app.dependency_overrides[get_indexing_service] = lambda: service
    client = TestClient(app)

    response = client.post("/api/index-paper", json={"paper_id": SAMPLE_PAPER_ID})

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Parsed artifact does not contain usable page-aware text to index."
    }


def test_index_paper_returns_cached_when_hash_matches_existing_index(
    isolated_indexing_storage,
) -> None:
    write_parsed_document(
        build_document(
            [
                "Chunk and embed this parsed paper for future grounded retrieval.",
                "Preserve the page number for provenance and citation support.",
            ]
        )
    )
    service, embedding_service, chroma_repository = build_indexing_service()
    app.dependency_overrides[get_indexing_service] = lambda: service
    client = TestClient(app)

    first_response = client.post("/api/index-paper", json={"paper_id": SAMPLE_PAPER_ID})
    second_response = client.post("/api/index-paper", json={"paper_id": SAMPLE_PAPER_ID})

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json() == {
        "paper_id": SAMPLE_PAPER_ID,
        "status": "cached",
        "chunk_count": 2,
        "collection_name": "paper_chunks",
        "message": "Paper already indexed; using cached vectors.",
    }
    assert len(embedding_service.calls) == 1
    assert len(chroma_repository.replace_calls) == 1


def test_index_paper_reindexes_when_content_hash_changes(isolated_indexing_storage) -> None:
    write_parsed_document(
        build_document(
            [
                "Original parsed content for the indexing cache test.",
                "Second page with stable provenance.",
            ]
        )
    )
    service, embedding_service, chroma_repository = build_indexing_service()
    app.dependency_overrides[get_indexing_service] = lambda: service
    client = TestClient(app)

    first_response = client.post("/api/index-paper", json={"paper_id": SAMPLE_PAPER_ID})
    write_parsed_document(
        build_document(
            [
                "Updated parsed content for the indexing cache test with extra detail.",
                "Second page with stable provenance.",
            ]
        )
    )
    second_response = client.post("/api/index-paper", json={"paper_id": SAMPLE_PAPER_ID})

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json()["status"] == "completed"
    assert len(embedding_service.calls) == 2
    assert len(chroma_repository.replace_calls) == 2

    first_ids = [chunk.chunk_id for chunk in chroma_repository.replace_calls[0]["chunks"]]
    second_ids = [chunk.chunk_id for chunk in chroma_repository.replace_calls[1]["chunks"]]
    assert first_ids != second_ids


def test_index_paper_sends_deterministic_chunk_ids_to_chroma(
    isolated_indexing_storage,
) -> None:
    write_parsed_document(
        build_document(
            [
                "Deterministic chunk identifiers matter for clean reindexing and future citations.",
                "Each chunk should map back to a specific page without ambiguity.",
            ]
        )
    )
    service, _, chroma_repository = build_indexing_service()
    app.dependency_overrides[get_indexing_service] = lambda: service
    client = TestClient(app)

    first_response = client.post("/api/index-paper", json={"paper_id": SAMPLE_PAPER_ID})
    index_cache_path(SAMPLE_PAPER_ID).unlink()
    second_response = client.post("/api/index-paper", json={"paper_id": SAMPLE_PAPER_ID})

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert len(chroma_repository.replace_calls) == 2

    first_ids = [chunk.chunk_id for chunk in chroma_repository.replace_calls[0]["chunks"]]
    second_ids = [chunk.chunk_id for chunk in chroma_repository.replace_calls[1]["chunks"]]
    assert first_ids == second_ids
