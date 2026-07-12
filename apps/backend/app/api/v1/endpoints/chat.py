import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.db.session import get_db
from app.domain.exceptions import ConversationNotFoundError, LLMError
from app.domain.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationRead,
    ConversationUpdate,
    MessageRead,
)
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.message_repository import MessageRepository
from app.services.chat_service import ChatService

router = APIRouter(tags=["chat"])


def get_chat_service(db: AsyncSession = Depends(get_db)) -> ChatService:
    return ChatService(ConversationRepository(db), MessageRepository(db), DocumentRepository(db))


@router.post("/chat", response_model=ChatResponse)
async def ask_question(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """Ask a question against the knowledge base. Creates a new conversation if none given.
    Optionally specify a knowledge_base_id to search within a specific knowledge base."""
    try:
        conversation_id, message = await chat_service.ask(
            user_id=current_user.id,
            question=payload.question,
            conversation_id=payload.conversation_id,
            knowledge_base_id=payload.knowledge_base_id,
            personality=payload.personality,
        )
        return ChatResponse(
            conversation_id=conversation_id,
            message=MessageRead.model_validate(message),
        )
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except LLMError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.get("/conversations", response_model=list[ConversationRead])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> list[Conversation]:
    """List all conversations for the current user, most recently active first."""
    return await chat_service.get_user_conversations(current_user.id)


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageRead])
async def list_conversation_messages(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> list[Message]:
    """List all messages in a conversation, oldest first."""
    try:
        return await chat_service.get_conversation_messages(current_user.id, conversation_id)
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/conversations/{conversation_id}", response_model=ConversationRead)
async def update_conversation(
    conversation_id: uuid.UUID,
    payload: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> Conversation:
    """Update a conversation's title and/or personality. Provide at least one field."""
    if payload.title is None and payload.personality is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide at least one of title or personality to update.",
        )
    try:
        return await chat_service.update_conversation(
            current_user.id,
            conversation_id,
            title=payload.title,
            personality=payload.personality,
        )
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> None:
    """Delete a conversation and all its messages."""
    try:
        await chat_service.delete_conversation(current_user.id, conversation_id)
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
