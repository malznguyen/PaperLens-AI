from unittest.mock import AsyncMock, patch

import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.services.arxiv_service import ArxivServiceError
from app.services.semantic_scholar_service import SemanticScholarServiceError

ARXIV_REQUEST = httpx.Request("GET", "https://export.arxiv.org/api/query")
SAMPLE_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2401.12345v1</id>
    <updated>2024-01-15T09:30:00Z</updated>
    <published>2024-01-10T12:00:00Z</published>
    <title>
      Vision   Transformers
      for   Medical Imaging
    </title>
    <summary>
      We study transformers
      for medical image classification.
    </summary>
    <author>
      <name>Alice Smith</name>
    </author>
    <author>
      <name>Bob Jones</name>
    </author>
    <link href="http://arxiv.org/abs/2401.12345v1" rel="alternate" type="text/html" />
    <link href="http://arxiv.org/pdf/2401.12345v1.pdf" rel="related" title="pdf" type="application/pdf" />
    <arxiv:primary_category term="cs.CV" scheme="http://arxiv.org/schemas/atom" />
    <category term="cs.CV" scheme="http://arxiv.org/schemas/atom" />
    <category term="cs.LG" scheme="http://arxiv.org/schemas/atom" />
  </entry>
</feed>
"""


def build_response(status_code: int, text: str) -> httpx.Response:
    return httpx.Response(
        status_code=status_code,
        text=text,
        request=ARXIV_REQUEST,
    )


@patch("app.services.arxiv_service.httpx.AsyncClient.send", new_callable=AsyncMock)
def test_search_papers_normalizes_arxiv_response(mock_send: AsyncMock) -> None:
    mock_send.return_value = build_response(200, SAMPLE_FEED)
    client = TestClient(app)

    response = client.post(
        "/api/search-papers",
        json={
            "query": "  vision transformer medical image classification  ",
            "max_results": 10,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["query"] == "vision transformer medical image classification"
    assert payload["count"] == 1

    result = payload["results"][0]
    assert result["id"] == "2401.12345"
    assert result["title"] == "Vision Transformers for Medical Imaging"
    assert result["authors"] == ["Alice Smith", "Bob Jones"]
    assert result["abstract"] == "We study transformers for medical image classification."
    assert result["published_at"] == "2024-01-10T12:00:00Z"
    assert result["updated_at"] == "2024-01-15T09:30:00Z"
    assert result["categories"] == ["cs.CV", "cs.LG"]
    assert result["primary_category"] == "cs.CV"
    assert result["pdf_url"] == "http://arxiv.org/pdf/2401.12345v1.pdf"
    assert result["source_url"] == "http://arxiv.org/abs/2401.12345v1"


@patch("app.services.arxiv_service.httpx.AsyncClient.send", new_callable=AsyncMock)
def test_search_papers_rejects_empty_query(mock_send: AsyncMock) -> None:
    client = TestClient(app)

    response = client.post(
        "/api/search-papers",
        json={
            "query": "   ",
            "max_results": 10,
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Query must not be empty."}
    mock_send.assert_not_called()


@patch("app.services.search_service.SemanticScholarService.search_papers", new_callable=AsyncMock)
@patch("app.services.search_service.ArxivService.search_papers", new_callable=AsyncMock)
def test_search_papers_handles_upstream_error(
    mock_arxiv_search: AsyncMock,
    mock_semantic_scholar_search: AsyncMock,
) -> None:
    mock_arxiv_search.side_effect = ArxivServiceError("Failed to fetch papers from arXiv.")
    mock_semantic_scholar_search.side_effect = SemanticScholarServiceError(
        "Failed to fetch papers from Semantic Scholar."
    )
    client = TestClient(app)

    response = client.post(
        "/api/search-papers",
        json={
            "query": "vision transformer",
            "max_results": 10,
        },
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Failed to fetch papers from both arXiv and Semantic Scholar."}
    mock_arxiv_search.assert_awaited_once()
    mock_semantic_scholar_search.assert_awaited_once()
