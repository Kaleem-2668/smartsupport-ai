from fastapi import APIRouter

from app.api.v1.endpoints import auth, chat, dashboard, documents, health, knowledge_bases

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(documents.router)
api_router.include_router(knowledge_bases.router)
api_router.include_router(chat.router)
