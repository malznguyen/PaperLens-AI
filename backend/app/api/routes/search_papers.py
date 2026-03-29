from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.search import SearchPapersRequest, SearchPapersResponse
from app.services.search_service import (
    SearchService,
    SearchUpstreamError,
    SearchValidationError,
    get_search_service,
)

router = APIRouter(prefix="/search-papers")


@router.post("", response_model=SearchPapersResponse, summary="Search papers from supported providers")
async def search_papers(
    payload: SearchPapersRequest,
    service: SearchService = Depends(get_search_service),
) -> SearchPapersResponse:
    try:
        return await service.search_papers(payload)
    except SearchValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except SearchUpstreamError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
