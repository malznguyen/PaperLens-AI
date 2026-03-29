from fastapi import APIRouter

from app.api.routes import chat, compare, health, index_paper, ingest, search_papers

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(search_papers.router, tags=["search"])
api_router.include_router(ingest.router, tags=["ingest"])
api_router.include_router(index_paper.router, tags=["indexing"])
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(compare.router, tags=["compare"])
