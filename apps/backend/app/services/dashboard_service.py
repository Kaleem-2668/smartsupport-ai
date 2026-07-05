import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.document import Document
from app.models.knowledge_base import KnowledgeBase
from app.models.message import Message
from app.domain.schemas.dashboard import (
    ConversationStats,
    DashboardStats,
    DocumentStats,
    KnowledgeBaseStats,
    RecentActivity,
)


class DashboardService:
    """Aggregates statistics across documents, knowledge bases, and conversations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_stats(self, user_id: uuid.UUID) -> DashboardStats:
        docs = await self._document_stats(user_id)
        kbs = await self._kb_stats(user_id)
        convos = await self._conversation_stats(user_id)
        activity = await self._recent_activity(user_id)

        return DashboardStats(
            documents=docs,
            knowledge_bases=kbs,
            conversations=convos,
            recent_activity=activity,
        )

    async def _document_stats(self, user_id: uuid.UUID) -> DocumentStats:
        # Total documents
        total_q = await self._session.execute(
            select(func.count(Document.id)).where(Document.user_id == user_id)
        )
        total = total_q.scalar_one() or 0

        # Count by status
        status_q = await self._session.execute(
            select(Document.status, func.count(Document.id))
            .where(Document.user_id == user_id)
            .group_by(Document.status)
        )
        by_status = {row[0]: row[1] for row in status_q.all()}

        # Total chunks
        chunks_q = await self._session.execute(
            select(func.coalesce(func.sum(Document.chunk_count), 0)).where(
                Document.user_id == user_id
            )
        )
        total_chunks = chunks_q.scalar_one() or 0

        # Total size
        size_q = await self._session.execute(
            select(func.coalesce(func.sum(Document.file_size), 0)).where(
                Document.user_id == user_id
            )
        )
        total_size_bytes = size_q.scalar_one() or 0

        return DocumentStats(
            total=total,
            by_status=by_status,
            total_chunks=total_chunks,
            total_size_bytes=total_size_bytes,
        )

    async def _kb_stats(self, user_id: uuid.UUID) -> KnowledgeBaseStats:
        total_q = await self._session.execute(
            select(func.count(KnowledgeBase.id)).where(KnowledgeBase.user_id == user_id)
        )
        total = total_q.scalar_one() or 0
        return KnowledgeBaseStats(total=total)

    async def _conversation_stats(self, user_id: uuid.UUID) -> ConversationStats:
        # Total conversations
        convo_q = await self._session.execute(
            select(func.count(Conversation.id)).where(Conversation.user_id == user_id)
        )
        total_conversations = convo_q.scalar_one() or 0

        # Total messages across user's conversations
        msg_q = await self._session.execute(
            select(func.count(Message.id))
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(Conversation.user_id == user_id)
        )
        total_messages = msg_q.scalar_one() or 0

        return ConversationStats(
            total=total_conversations,
            total_messages=total_messages,
        )

    async def _recent_activity(self, user_id: uuid.UUID, limit: int = 10) -> list[RecentActivity]:
        activity: list[RecentActivity] = []

        # Recent documents
        doc_q = await self._session.execute(
            select(Document.id, Document.original_filename, Document.created_at)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
            .limit(limit)
        )
        for row in doc_q.all():
            activity.append(
                RecentActivity(
                    id=row[0],
                    type="document",
                    title=row[1],
                    timestamp=row[2],
                )
            )

        # Recent conversations
        convo_q = await self._session.execute(
            select(Conversation.id, Conversation.title, Conversation.updated_at)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )
        for row in convo_q.all():
            activity.append(
                RecentActivity(
                    id=row[0],
                    type="conversation",
                    title=row[1] or "Untitled conversation",
                    timestamp=row[2],
                )
            )

        # Sort by timestamp descending and take top N
        activity.sort(key=lambda a: a.timestamp, reverse=True)
        return activity[:limit]
