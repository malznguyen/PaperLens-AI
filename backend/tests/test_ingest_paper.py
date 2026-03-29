import json
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, patch

import fitz
import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import ROOT_DIR, get_settings
from app.main import app

PDF_REQUEST = httpx.Request("GET", "https://arxiv.org/pdf/2401.12345.pdf")
SAMPLE_PAYLOAD = {
    "id": "2401.12345",
    "title": "Vision Transformers for Medical Imaging",
    "pdf_url": "https://arxiv.org/pdf/2401.12345.pdf",
    "source_url": "https://arxiv.org/abs/2401.12345",
    "authors": ["Alice Smith", "Bob Jones"],
    "abstract": "We study transformers for medical image classification.",
    "published_at": "2024-01-10T12:00:00Z",
    "updated_at": "2024-01-15T09:30:00Z",
    "categories": ["cs.CV", "cs.LG"],
    "primary_category": "cs.CV",
}


@pytest.fixture()
def isolated_ingest_storage() -> None:
    settings = get_settings()
    original_paths = {
        "data_dir": settings.data_dir,
        "raw_pdfs_dir": settings.raw_pdfs_dir,
        "parsed_dir": settings.parsed_dir,
        "cache_dir": settings.cache_dir,
        "chroma_dir": settings.chroma_dir,
    }

    test_data_dir = ROOT_DIR / "backend" / "data" / "pytest-ingest"
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


def build_pdf_bytes(page_texts: list[str]) -> bytes:
    document = fitz.open()

    for page_text in page_texts:
        page = document.new_page()
        page.insert_text((72, 72), page_text)

    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


def build_pdf_response(content: bytes, content_type: str = "application/pdf") -> httpx.Response:
    return httpx.Response(
        status_code=200,
        content=content,
        headers={"Content-Type": content_type},
        request=PDF_REQUEST,
    )


def resolve_repo_path(path_value: str) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else ROOT_DIR / path


@patch("app.services.pdf_service.httpx.AsyncClient.get", new_callable=AsyncMock)
def test_ingest_paper_downloads_parses_and_persists_pdf(
    mock_get: AsyncMock,
    isolated_ingest_storage,
) -> None:
    mock_get.return_value = build_pdf_response(
        build_pdf_bytes(
            [
                "Vision transformers improve medical image classification.",
                "We evaluate the approach across benchmark datasets.",
            ]
        )
    )
    client = TestClient(app)

    response = client.post("/api/ingest", json=SAMPLE_PAYLOAD)

    assert response.status_code == 200
    payload = response.json()

    assert payload["paper_id"] == SAMPLE_PAYLOAD["id"]
    assert payload["status"] == "completed"
    assert payload["page_count"] == 2
    assert payload["word_count"] > 5
    assert payload["message"] == "Paper ingested and parsed successfully."

    pdf_path = resolve_repo_path(payload["pdf_path"])
    parsed_path = resolve_repo_path(payload["parsed_path"])

    assert pdf_path.exists()
    assert parsed_path.exists()

    parsed_payload = json.loads(parsed_path.read_text(encoding="utf-8"))
    assert set(parsed_payload) >= {
        "paper_id",
        "title",
        "pdf_path",
        "page_count",
        "character_count",
        "word_count",
        "pages",
        "full_text",
    }
    assert parsed_payload["paper_id"] == SAMPLE_PAYLOAD["id"]
    assert parsed_payload["page_count"] == 2
    assert parsed_payload["pages"][0]["page_number"] == 1
    assert "medical image classification" in parsed_payload["full_text"].lower()


def test_ingest_paper_rejects_invalid_pdf_url(isolated_ingest_storage) -> None:
    client = TestClient(app)

    response = client.post(
        "/api/ingest",
        json={
            **SAMPLE_PAYLOAD,
            "pdf_url": "not-a-valid-url",
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "pdf_url: Value error, pdf_url must be a valid HTTP or HTTPS URL."}


@patch("app.services.pdf_service.httpx.AsyncClient.get", new_callable=AsyncMock)
def test_ingest_paper_returns_download_failure_when_pdf_source_errors(
    mock_get: AsyncMock,
    isolated_ingest_storage,
) -> None:
    mock_get.side_effect = httpx.ConnectError("network failure", request=PDF_REQUEST)
    client = TestClient(app)

    response = client.post("/api/ingest", json=SAMPLE_PAYLOAD)

    assert response.status_code == 502
    assert response.json() == {"detail": "Failed to download the PDF."}


@patch("app.services.pdf_service.httpx.AsyncClient.get", new_callable=AsyncMock)
def test_ingest_paper_returns_cached_when_artifacts_already_exist(
    mock_get: AsyncMock,
    isolated_ingest_storage,
) -> None:
    mock_get.return_value = build_pdf_response(
        build_pdf_bytes(["Cached ingestion test text for the paper."])
    )
    client = TestClient(app)

    first_response = client.post("/api/ingest", json=SAMPLE_PAYLOAD)
    second_response = client.post("/api/ingest", json=SAMPLE_PAYLOAD)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json()["status"] == "cached"
    assert second_response.json()["message"] == "Paper already ingested; using cached artifacts."
    assert mock_get.await_count == 1
