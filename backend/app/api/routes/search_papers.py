from fastapi import APIRouter

from app.schemas.search import SearchPapersRequest, SearchPapersResponse
from app.services.search_service import preview_search

router = APIRouter(prefix="/search-papers")


@router.post("", response_model=SearchPapersResponse, summary="Phase 2 arXiv search placeholder")
def search_papers(payload: SearchPapersRequest) -> SearchPapersResponse:
    return preview_search(payload)
