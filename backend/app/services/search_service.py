import asyncio
import logging
import time

from app.schemas.search import PaperSearchResult, SearchPapersRequest, SearchPapersResponse
from app.services.arxiv_service import ArxivService, ArxivServiceError
from app.services.semantic_scholar_service import (
    SemanticScholarService,
    SemanticScholarServiceError,
)

logger = logging.getLogger(__name__)


class SearchValidationError(ValueError):
    """Raised when a search request is invalid for business rules."""


class SearchUpstreamError(RuntimeError):
    """Raised when an upstream paper search provider is unavailable."""


CACHE_TTL_SECONDS = 300  # 5 minutes


class SearchService:
    def __init__(
        self,
        arxiv_service: ArxivService | None = None,
        semantic_scholar_service: SemanticScholarService | None = None,
    ) -> None:
        self._arxiv_service = arxiv_service or ArxivService()
        self._semantic_scholar = semantic_scholar_service or SemanticScholarService()
        self._cache: dict[str, tuple[float, list[PaperSearchResult]]] = {}

    def _cache_key(self, query: str, max_results: int) -> str:
        return f"{query.lower().strip()}::{max_results}"

    def _get_cached(self, key: str) -> list[PaperSearchResult] | None:
        entry = self._cache.get(key)
        if entry is None:
            return None
        cached_at, results = entry
        if time.monotonic() - cached_at > CACHE_TTL_SECONDS:
            del self._cache[key]
            return None
        return results

    def _set_cached(self, key: str, results: list[PaperSearchResult]) -> None:
        self._cache[key] = (time.monotonic(), results)

    async def search_papers(self, payload: SearchPapersRequest) -> SearchPapersResponse:
        query = payload.query.strip()
        if not query:
            raise SearchValidationError("Query must not be empty.")

        cache_key = self._cache_key(query, payload.max_results)
        cached = self._get_cached(cache_key)
        if cached is not None:
            logger.info("Search cache hit for %r (%d results).", query, len(cached))
            return SearchPapersResponse(query=query, count=len(cached), results=cached)

        results = await self._search_with_fallback(query, payload.max_results)
        self._set_cached(cache_key, results)

        return SearchPapersResponse(
            query=query,
            count=len(results),
            results=results,
        )

    async def _search_with_fallback(
        self, query: str, max_results: int
    ) -> list[PaperSearchResult]:
        arxiv_task = asyncio.create_task(
            self._arxiv_service.search_papers(query=query, max_results=max_results)
        )
        scholar_task = asyncio.create_task(
            self._semantic_scholar.search_papers(query=query, max_results=max_results)
        )

        # Return whichever succeeds first; cancel the other.
        done, pending = await asyncio.wait(
            [arxiv_task, scholar_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in done:
            try:
                results = task.result()
                # Got a successful result — cancel pending tasks.
                for p in pending:
                    p.cancel()
                source = "arXiv" if task is arxiv_task else "Semantic Scholar"
                logger.info("Search fulfilled by %s (%d results).", source, len(results))
                return results
            except (ArxivServiceError, SemanticScholarServiceError, Exception):
                pass

        # First completed task failed — wait for the remaining one.
        if pending:
            remaining = pending.pop()
            try:
                results = await remaining
                source = "arXiv" if remaining is arxiv_task else "Semantic Scholar"
                logger.info("Search fulfilled by %s (%d results).", source, len(results))
                return results
            except (ArxivServiceError, SemanticScholarServiceError, Exception) as exc:
                raise SearchUpstreamError(
                    "Failed to fetch papers from both arXiv and Semantic Scholar."
                ) from exc

        raise SearchUpstreamError(
            "Failed to fetch papers from both arXiv and Semantic Scholar."
        )


search_service = SearchService()


def get_search_service() -> SearchService:
    return search_service
