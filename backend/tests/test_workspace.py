import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import ROOT_DIR, get_settings
from app.main import app
from app.repositories.chroma_repository import IndexedPaperSnapshot
from app.schemas.indexing import IndexCacheRecord
from app.schemas.ingest import ParsedPage, ParsedPaperDocument
from app.services.workspace_service import WorkspaceService, WorkspaceStateError, get_workspace_service
from app.utils.file_utils import build_storage_stem
from app.utils.text_utils import count_words


class FakeWorkspaceChromaRepository:
    def __init__(self, papers: list[IndexedPaperSnapshot] | None = None) -> None:
        self._papers = papers or []

    def list_indexed_papers(self) -> list[IndexedPaperSnapshot]:
        return list(self._papers)


class BrokenWorkspaceService:
    async def get_workspace(self):
        raise WorkspaceStateError("Failed to inspect workspace artifacts.")


@pytest.fixture()
def isolated_workspace_storage() -> None:
    settings = get_settings()
    original_paths = {
        "data_dir": settings.data_dir,
        "raw_pdfs_dir": settings.raw_pdfs_dir,
        "parsed_dir": settings.parsed_dir,
        "cache_dir": settings.cache_dir,
        "chroma_dir": settings.chroma_dir,
    }

    test_data_dir = ROOT_DIR / "backend" / "data" / "pytest-workspace"
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


def build_document(page_texts: list[str], *, paper_id: str, title: str) -> ParsedPaperDocument:
    full_text = "\n\n".join(text.strip() for text in page_texts if text.strip())
    return ParsedPaperDocument(
        paper_id=paper_id,
        title=title,
        authors=["Alice Smith", "Bob Jones"],
        abstract="Workspace aggregation fixture.",
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


def write_index_cache(*, paper_id: str, chunk_count: int, collection_name: str = "paper_chunks") -> Path:
    settings = get_settings()
    cache_path = settings.indexing_cache_dir / f"{build_storage_stem(paper_id)}.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps(
            IndexCacheRecord(
                paper_id=paper_id,
                content_hash=f"{paper_id}-hash",
                chunk_count=chunk_count,
                collection_name=collection_name,
            ).model_dump(),
            indent=2,
        ),
        encoding="utf-8",
    )
    return cache_path


def test_workspace_route_aggregates_local_corpus_state(isolated_workspace_storage) -> None:
    write_parsed_document(
        build_document(
            [
                "Vision transformers improve medical image classification.",
                "The parsed artifact preserves page-aware text for downstream workflows.",
            ],
            paper_id="2401.12345",
            title="Vision Transformers for Medical Imaging",
        )
    )
    write_parsed_document(
        build_document(
            [
                "Diffusion policy papers can be ingested before they are indexed.",
            ],
            paper_id="2402.67890",
            title="Diffusion Policies in Robotics",
        )
    )
    write_index_cache(paper_id="2401.12345", chunk_count=5)
    write_index_cache(paper_id="2403.11111", chunk_count=2)

    workspace_service = WorkspaceService(
        chroma_repository=FakeWorkspaceChromaRepository(
            papers=[
                IndexedPaperSnapshot(
                    paper_id="2401.12345",
                    paper_title="Vision Transformers for Medical Imaging",
                    source_url="https://arxiv.org/abs/2401.12345",
                    pdf_path="backend/data/raw_pdfs/2401.12345.pdf",
                    chunk_count=5,
                ),
                IndexedPaperSnapshot(
                    paper_id="2403.11111",
                    paper_title="Indexed Only Workspace Record",
                    source_url="https://arxiv.org/abs/2403.11111",
                    pdf_path="backend/data/raw_pdfs/2403.11111.pdf",
                    chunk_count=2,
                ),
            ]
        )
    )
    app.dependency_overrides[get_workspace_service] = lambda: workspace_service
    client = TestClient(app)

    response = client.get("/api/workspace")

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"] == {
        "total_paper_count": 3,
        "ingested_paper_count": 2,
        "indexed_paper_count": 2,
        "total_chunk_count": 7,
    }

    papers_by_id = {paper["paper_id"]: paper for paper in payload["papers"]}

    assert papers_by_id["2401.12345"]["status"] == {"ingested": True, "indexed": True}
    assert papers_by_id["2401.12345"]["page_count"] == 2
    assert papers_by_id["2401.12345"]["chunk_count"] == 5
    assert papers_by_id["2401.12345"]["collection_name"] == "paper_chunks"
    assert papers_by_id["2401.12345"]["parsed_path"].endswith("backend/data/pytest-workspace/parsed/2401.12345.json")

    assert papers_by_id["2402.67890"]["status"] == {"ingested": True, "indexed": False}
    assert papers_by_id["2402.67890"]["page_count"] == 1
    assert papers_by_id["2402.67890"]["chunk_count"] == 0
    assert papers_by_id["2402.67890"]["collection_name"] is None

    assert papers_by_id["2403.11111"]["status"] == {"ingested": False, "indexed": True}
    assert papers_by_id["2403.11111"]["title"] == "Indexed Only Workspace Record"
    assert papers_by_id["2403.11111"]["chunk_count"] == 2
    assert papers_by_id["2403.11111"]["parsed_path"] is None
    assert papers_by_id["2403.11111"]["source_url"] == "https://arxiv.org/abs/2403.11111"


def test_workspace_route_returns_500_when_state_cannot_be_inspected() -> None:
    app.dependency_overrides[get_workspace_service] = lambda: BrokenWorkspaceService()
    client = TestClient(app)

    response = client.get("/api/workspace")

    assert response.status_code == 500
    assert response.json() == {"detail": "Failed to inspect workspace artifacts."}
