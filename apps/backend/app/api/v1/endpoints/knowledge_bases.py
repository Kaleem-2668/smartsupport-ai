import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.db.session import get_db
from app.domain.exceptions import KnowledgeBaseNotFoundError
from app.domain.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseRead,
    KnowledgeBaseUpdate,
)
from app.models.knowledge_base import KnowledgeBase
from app.models.user import User
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.services.knowledge_base_service import KnowledgeBaseService

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])


def get_knowledge_base_service(db: AsyncSession = Depends(get_db)) -> KnowledgeBaseService:
    return KnowledgeBaseService(KnowledgeBaseRepository(db))


@router.post("", response_model=KnowledgeBaseRead, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(
    data: KnowledgeBaseCreate,
    current_user: User = Depends(get_current_user),
    kb_service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> KnowledgeBase:
    """Create a new knowledge base for the current user."""
    return await kb_service.create_knowledge_base(current_user.id, data)


@router.get("", response_model=list[KnowledgeBaseRead])
async def list_knowledge_bases(
    current_user: User = Depends(get_current_user),
    kb_service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> list[KnowledgeBase]:
    """List all knowledge bases for the current user."""
    return await kb_service.get_user_knowledge_bases(current_user.id)


@router.get("/{knowledge_base_id}", response_model=KnowledgeBaseRead)
async def get_knowledge_base(
    knowledge_base_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    kb_service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> KnowledgeBase:
    """Get a specific knowledge base by ID."""
    try:
        knowledge_base = await kb_service.get_knowledge_base(knowledge_base_id)
        # Ensure user can only access their own knowledge bases
        if knowledge_base.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        return knowledge_base
    except KnowledgeBaseNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{knowledge_base_id}", response_model=KnowledgeBaseRead)
async def update_knowledge_base(
    knowledge_base_id: uuid.UUID,
    data: KnowledgeBaseUpdate,
    current_user: User = Depends(get_current_user),
    kb_service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> KnowledgeBase:
    """Update a knowledge base."""
    try:
        knowledge_base = await kb_service.get_knowledge_base(knowledge_base_id)
        # Ensure user can only update their own knowledge bases
        if knowledge_base.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        return await kb_service.update_knowledge_base(knowledge_base_id, data)
    except KnowledgeBaseNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{knowledge_base_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base(
    knowledge_base_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    kb_service: KnowledgeBaseService = Depends(get_knowledge_base_service),
) -> None:
    """Delete a knowledge base by ID."""
    try:
        knowledge_base = await kb_service.get_knowledge_base(knowledge_base_id)
        # Ensure user can only delete their own knowledge bases
        if knowledge_base.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        await kb_service.delete_knowledge_base(knowledge_base_id)
    except KnowledgeBaseNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
