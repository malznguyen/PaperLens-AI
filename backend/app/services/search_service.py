from app.schemas.search import SearchPapersRequest, SearchPapersResponse


def preview_search(payload: SearchPapersRequest) -> SearchPapersResponse:
    return SearchPapersResponse(
        query=payload.query,
        status="not_implemented",
        message="Phase 2 will connect this endpoint to the arXiv API and return normalized paper results.",
    )
