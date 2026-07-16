import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class MostActiveUser(BaseModel):
    user_id: uuid.UUID
    email: str
    conversation_count: int


class AdminStats(BaseModel):
    total_users: int
    active_users_7d: int
    total_conversations: int
    total_messages: int
    total_documents: int
    total_knowledge_bases: int
    total_storage_bytes: int
    personality_breakdown: dict[str, int]
    most_active_users: list[MostActiveUser]


class AdminUserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str | None
    is_active: bool
    role: str
    created_at: datetime
    conversation_count: int
    document_count: int


class UserAdminUpdate(BaseModel):
    role: str | None = None
    is_active: bool | None = None


class AdminConversationRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    user_email: str
    title: str | None
    personality: str
    message_count: int
    created_at: datetime
    updated_at: datetime


class AdminDocumentRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    user_email: str
    original_filename: str
    status: str
    file_size: int
    created_at: datetime
