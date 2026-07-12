import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PersonalityKey = Literal["professional", "tutor", "friendly", "playful", "roast"]


class SourceRead(BaseModel):
    document_id: uuid.UUID
    document_name: str
    chunk_index: int
    page_number: int | None
    confidence: float | None
    snippet: str


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    sources: list[SourceRead] | None
    created_at: datetime


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    title: str | None
    personality: PersonalityKey
    created_at: datetime
    updated_at: datetime


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    conversation_id: uuid.UUID | None = None
    knowledge_base_id: uuid.UUID | None = None
    personality: PersonalityKey | None = None
    """Only applied when starting a NEW conversation (conversation_id is None).
    Ignored for existing conversations, which keep their own stored personality —
    change it via PATCH /conversations/{id} instead."""


class ConversationUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    personality: PersonalityKey | None = None


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    message: MessageRead
