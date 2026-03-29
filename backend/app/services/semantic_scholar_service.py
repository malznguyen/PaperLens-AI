from __future__ import annotations

import asyncio
import logging

import httpx

from app.schemas.search import PaperSearchResult

logger = logging.getLogger(__name__)

SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/search"
FIELDS = "externalIds,title,authors,abstract,publicationDate,tldr,url"


class SemanticScholarServiceError(RuntimeError):
    """Raised when the Semantic Scholar API cannot be queried."""


class SemanticScholarService:
    def __init__(self, timeout_seconds: float = 30.0, max_retries: int = 3) -> None:
        self.timeout = httpx.Timeout(timeout_seconds)
        self.max_retries = max_retries
        self._logger = logger

    async def search_papers(self, query: str, max_results: int) -> list[PaperSearchResult]:
        params = {
            "query": query,
            "limit": min(max_results, 25),
            "fields": FIELDS,
        }

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            data = await self._fetch_with_retries(client, params)

        papers: list[PaperSearchResult] = []
        for item in data.get("data") or []:
            external_ids = item.get("externalIds") or {}
            arxiv_id = external_ids.get("ArXiv", "")
            paper_id = arxiv_id or item.get("paperId", "")
            source_url = (
                f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id
                else item.get("url", "")
            )
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf" if arxiv_id else None

            authors = [
                a.get("name", "") for a in (item.get("authors") or []) if a.get("name")
            ]

            papers.append(PaperSearchResult(
                id=paper_id,
                title=item.get("title", ""),
                authors=authors,
                abstract=item.get("abstract") or "",
                published_at=item.get("publicationDate") or "",
                updated_at=item.get("publicationDate") or "",
                categories=[],
                pdf_url=pdf_url,
                source_url=source_url,
                primary_category=None,
            ))

        return papers

    async def _fetch_with_retries(
        self, client: httpx.AsyncClient, params: dict
    ) -> dict:
        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = await client.get(SEMANTIC_SCHOLAR_API, params=params)
                if response.status_code == 429:
                    if attempt < self.max_retries:
                        retry_after = response.headers.get("retry-after")
                        delay = float(retry_after) if retry_after else 2.0 * 2 ** attempt
                        self._logger.warning(
                            "Semantic Scholar 429, retrying in %.1fs. attempt=%s/%s",
                            delay, attempt + 1, self.max_retries + 1,
                        )
                        await asyncio.sleep(delay)
                        continue
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as exc:
                last_exc = exc
                if attempt < self.max_retries:
                    delay = 1.0 * (attempt + 1)
                    self._logger.warning(
                        "Semantic Scholar request error, retrying in %.1fs. attempt=%s/%s error=%s",
                        delay, attempt + 1, self.max_retries + 1, exc,
                    )
                    await asyncio.sleep(delay)
                    continue
                break

        raise SemanticScholarServiceError(
            "Semantic Scholar request failed."
        ) from last_exc
