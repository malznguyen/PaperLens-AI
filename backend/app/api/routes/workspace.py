from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.workspace import WorkspaceResponse
from app.services.workspace_service import (
    WorkspaceService,
    WorkspaceStateError,
    get_workspace_service,
)

router = APIRouter(prefix="/workspace")


@router.get(
    "",
    response_model=WorkspaceResponse,
    summary="Inspect the current local paper workspace state",
)
async def get_workspace(
    service: WorkspaceService = Depends(get_workspace_service),
) -> WorkspaceResponse:
    try:
        return await service.get_workspace()
    except WorkspaceStateError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
