from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.indexing import IndexPaperResponse
from app.services.indexing_service import (
    IndexingArtifactError,
    IndexingEmbeddingError,
    IndexingNoContentError,
    IndexingNotFoundError,
    IndexingService,
    IndexingStorageError,
    IndexingValidationError,
    get_indexing_service,
)

router = APIRouter(prefix="/index-paper")


@router.post(
    "",
    response_model=IndexPaperResponse,
    summary="Chunk, embed, and index an ingested paper into Chroma",
)
async def index_paper(
    payload: dict[str, Any],
    service: IndexingService = Depends(get_indexing_service),
) -> IndexPaperResponse:
    try:
        return await service.index_paper(payload)
    except IndexingValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except IndexingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except IndexingNoContentError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except (IndexingArtifactError, IndexingEmbeddingError, IndexingStorageError) as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
