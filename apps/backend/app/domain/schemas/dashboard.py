import uuid
from datetime import datetime

from pydantic import BaseModel


class DocumentStats(BaseModel):
    total: int
    by_status: dict[str, int]
    total_chunks: int
    total_size_bytes: int


class KnowledgeBaseStats(BaseModel):
    total: int


class ConversationStats(BaseModel):
    total: int
    total_messages: int


class RecentActivity(BaseModel):
    id: uuid.UUID
    type: str
    title: str
    timestamp: datetime


class DashboardStats(BaseModel):
    documents: DocumentStats
    knowledge_bases: KnowledgeBaseStats
    conversations: ConversationStats
    recent_activity: list[RecentActivity]
