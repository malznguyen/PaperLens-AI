from app.schemas.search import SearchPapersRequest, SearchPapersResponse
from app.services.arxiv_service import ArxivService, ArxivServiceError


class SearchValidationError(ValueError):
    """Raised when a search request is invalid for business rules."""


class SearchUpstreamError(RuntimeError):
    """Raised when an upstream paper search provider is unavailable."""


class SearchService:
    def __init__(self, arxiv_service: ArxivService | None = None) -> None:
        self._arxiv_service = arxiv_service or ArxivService()

    async def search_papers(self, payload: SearchPapersRequest) -> SearchPapersResponse:
        query = payload.query.strip()
        if not query:
            raise SearchValidationError("Query must not be empty.")

        try:
            results = await self._arxiv_service.search_papers(
                query=query,
                max_results=payload.max_results,
            )
        except ArxivServiceError as exc:
            raise SearchUpstreamError("Failed to fetch papers from arXiv.") from exc

        return SearchPapersResponse(
            query=query,
            count=len(results),
            results=results,
        )


search_service = SearchService()


def get_search_service() -> SearchService:
    return search_service
