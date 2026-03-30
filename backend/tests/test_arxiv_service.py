import asyncio

import httpx
import pytest

from app.services import arxiv_service as arxiv_service_module
from app.services.arxiv_service import ArxivService, ArxivServiceError

SAMPLE_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>https://arxiv.org/abs/2401.12345v1</id>
    <updated>2024-01-15T09:30:00Z</updated>
    <published>2024-01-10T12:00:00Z</published>
    <title>Vision Transformers for Medical Imaging</title>
    <summary>We study transformers for medical image classification.</summary>
    <author>
      <name>Alice Smith</name>
    </author>
    <link href="https://arxiv.org/abs/2401.12345v1" rel="alternate" type="text/html" />
    <link href="https://arxiv.org/pdf/2401.12345v1.pdf" rel="related" title="pdf" type="application/pdf" />
    <arxiv:primary_category term="cs.CV" scheme="http://arxiv.org/schemas/atom" />
    <category term="cs.CV" scheme="http://arxiv.org/schemas/atom" />
  </entry>
</feed>
"""


def test_arxiv_service_follows_redirects_when_arxiv_redirects(monkeypatch) -> None:
    seen_urls: list[str] = []
    seen_user_agents: list[str] = []
    client_kwargs: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen_urls.append(str(request.url))
        seen_user_agents.append(request.headers["user-agent"])
        if request.url.scheme == "http":
            redirected_url = str(request.url).replace("http://", "https://", 1)
            return httpx.Response(
                301,
                headers={"location": redirected_url},
                request=request,
            )
        return httpx.Response(200, text=SAMPLE_FEED, request=request)

    class RedirectingAsyncClient(httpx.AsyncClient):
        def __init__(self, *args, **kwargs) -> None:
            client_kwargs.update(kwargs)
            super().__init__(*args, transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(arxiv_service_module.httpx, "AsyncClient", RedirectingAsyncClient)

    service = ArxivService(
        base_url="http://export.arxiv.org/api/query",
        user_agent="ResearchApp/1.0 (mailto:test@example.com)",
        max_retries=0,
    )

    results = asyncio.run(service.search_papers("vision transformer", 1))

    assert len(results) == 1
    assert client_kwargs["follow_redirects"] is True
    assert seen_urls[0].startswith("http://export.arxiv.org/api/query")
    assert seen_urls[1].startswith("https://export.arxiv.org/api/query")
    assert seen_user_agents == [
        "ResearchApp/1.0 (mailto:test@example.com)",
        "ResearchApp/1.0 (mailto:test@example.com)",
    ]


def test_arxiv_service_logs_diagnostic_context_for_http_status_errors(
    monkeypatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            503,
            headers={"location": "https://export.arxiv.org/maintenance"},
            text="temporarily unavailable",
            request=request,
        )

    class ErroringAsyncClient(httpx.AsyncClient):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(arxiv_service_module.httpx, "AsyncClient", ErroringAsyncClient)

    service = ArxivService(base_url="https://export.arxiv.org/api/query", max_retries=0)

    with caplog.at_level("ERROR", logger="app.services.arxiv_service"):
        with pytest.raises(ArxivServiceError, match="arXiv returned an unexpected response."):
            asyncio.run(service.search_papers("vision transformer", 1))

    assert "status=503" in caplog.text
    assert "request_url=https://export.arxiv.org/api/query" in caplog.text
    assert "redirect_location=https://export.arxiv.org/maintenance" in caplog.text


def test_arxiv_service_waits_between_requests(monkeypatch) -> None:
    sleep_calls: list[float] = []
    monotonic_values = iter([0.0, 1.0, 3.0])

    async def fake_sleep(delay: float) -> None:
        sleep_calls.append(delay)

    service = ArxivService(max_retries=0)
    monkeypatch.setattr(service, "_monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr(service, "_sleep", fake_sleep)

    async def run() -> None:
        await service._wait_for_request_slot()
        await service._wait_for_request_slot()

    asyncio.run(run())

    assert sleep_calls == [2.0]
