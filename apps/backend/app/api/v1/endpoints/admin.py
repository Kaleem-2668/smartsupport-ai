import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_admin_user
from app.db.session import get_db
from app.domain.exceptions import ConversationNotFoundError, DocumentNotFoundError, UserNotFoundError
from app.domain.schemas.admin import (
    AdminConversationRead,
    AdminDocumentRead,
    AdminStats,
    AdminUserRead,
    UserAdminUpdate,
)
from app.models.user import User
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.user_repository import UserRepository
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["admin"])

VALID_ROLES = {"user", "admin"}


def get_admin_service(db: AsyncSession = Depends(get_db)) -> AdminService:
    return AdminService(db, UserRepository(db), ConversationRepository(db), DocumentRepository(db))


@router.get("/stats", response_model=AdminStats)
async def get_admin_stats(
    _admin: User = Depends(get_current_admin_user),
    admin_service: AdminService = Depends(get_admin_service),
) -> AdminStats:
    return await admin_service.get_stats()


@router.get("/users", response_model=list[AdminUserRead])
async def list_users(
    search: str | None = None,
    _admin: User = Depends(get_current_admin_user),
    admin_service: AdminService = Depends(get_admin_service),
) -> list[AdminUserRead]:
    return await admin_service.list_users(search)


@router.patch("/users/{user_id}", response_model=AdminUserRead)
async def update_user(
    user_id: uuid.UUID,
    payload: UserAdminUpdate,
    admin: User = Depends(get_current_admin_user),
    admin_service: AdminService = Depends(get_admin_service),
) -> AdminUserRead:
    if payload.role is None and payload.is_active is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide at least one of role or is_active to update.",
        )
    if payload.role is not None and payload.role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"role must be one of {sorted(VALID_ROLES)}",
        )
    # Guard against an admin locking themselves out — demoting or deactivating your own
    # account through this endpoint would leave you unable to fix it without DB access.
    is_self = user_id == admin.id
    if is_self and payload.role == "user":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="You can't remove your own admin role."
        )
    if is_self and payload.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="You can't deactivate your own account."
        )

    try:
        updated_user = await admin_service.update_user(user_id, payload.role, payload.is_active)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    users = await admin_service.list_users()
    return next(u for u in users if u.id == updated_user.id)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    admin: User = Depends(get_current_admin_user),
    admin_service: AdminService = Depends(get_admin_service),
) -> None:
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="You can't delete your own account."
        )
    try:
        await admin_service.delete_user(user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/conversations", response_model=list[AdminConversationRead])
async def list_recent_conversations(
    _admin: User = Depends(get_current_admin_user),
    admin_service: AdminService = Depends(get_admin_service),
) -> list[AdminConversationRead]:
    """Recent conversations across all users, for content oversight."""
    return await admin_service.list_recent_conversations()


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation_as_admin(
    conversation_id: uuid.UUID,
    _admin: User = Depends(get_current_admin_user),
    admin_service: AdminService = Depends(get_admin_service),
) -> None:
    try:
        await admin_service.delete_conversation_as_admin(conversation_id)
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/documents", response_model=list[AdminDocumentRead])
async def list_recent_documents(
    _admin: User = Depends(get_current_admin_user),
    admin_service: AdminService = Depends(get_admin_service),
) -> list[AdminDocumentRead]:
    """Recent documents across all users, for content oversight."""
    return await admin_service.list_recent_documents()


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_as_admin(
    document_id: uuid.UUID,
    _admin: User = Depends(get_current_admin_user),
    admin_service: AdminService = Depends(get_admin_service),
) -> None:
    try:
        await admin_service.delete_document_as_admin(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
