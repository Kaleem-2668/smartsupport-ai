import uuid
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import ConversationNotFoundError, DocumentNotFoundError, UserNotFoundError
from app.domain.schemas.admin import (
    AdminConversationRead,
    AdminDocumentRead,
    AdminStats,
    AdminUserRead,
    MostActiveUser,
)
from app.models.conversation import Conversation
from app.models.document import Document
from app.models.knowledge_base import KnowledgeBase
from app.models.message import Message
from app.models.user import User
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.user_repository import UserRepository


class AdminService:
    """Aggregate statistics and user management for the admin dashboard.
    Read-heavy by design — none of this is on the hot path for regular users.
    """

    def __init__(
        self,
        session: AsyncSession,
        user_repository: UserRepository,
        conversation_repository: ConversationRepository,
        document_repository: DocumentRepository,
    ) -> None:
        self._session = session
        self._users = user_repository
        self._conversations = conversation_repository
        self._documents = document_repository

    async def get_stats(self) -> AdminStats:
        total_users = (await self._session.execute(select(func.count(User.id)))).scalar_one()

        seven_days_ago = datetime.now() - timedelta(days=7)
        active_users_q = await self._session.execute(
            select(func.count(func.distinct(Conversation.user_id))).where(
                Conversation.updated_at >= seven_days_ago
            )
        )
        active_users_7d = active_users_q.scalar_one() or 0

        total_conversations = (
            await self._session.execute(select(func.count(Conversation.id)))
        ).scalar_one()
        total_messages = (await self._session.execute(select(func.count(Message.id)))).scalar_one()
        total_documents = (await self._session.execute(select(func.count(Document.id)))).scalar_one()
        total_knowledge_bases = (
            await self._session.execute(select(func.count(KnowledgeBase.id)))
        ).scalar_one()
        total_storage_q = await self._session.execute(
            select(func.coalesce(func.sum(Document.file_size), 0))
        )
        total_storage_bytes = total_storage_q.scalar_one() or 0

        personality_q = await self._session.execute(
            select(Conversation.personality, func.count(Conversation.id)).group_by(
                Conversation.personality
            )
        )
        personality_breakdown = {row[0]: row[1] for row in personality_q.all()}

        most_active_q = await self._session.execute(
            select(User.id, User.email, func.count(Conversation.id).label("count"))
            .join(Conversation, Conversation.user_id == User.id)
            .group_by(User.id, User.email)
            .order_by(func.count(Conversation.id).desc())
            .limit(5)
        )
        most_active_users = [
            MostActiveUser(user_id=row[0], email=row[1], conversation_count=row[2])
            for row in most_active_q.all()
        ]

        return AdminStats(
            total_users=total_users,
            active_users_7d=active_users_7d,
            total_conversations=total_conversations,
            total_messages=total_messages,
            total_documents=total_documents,
            total_knowledge_bases=total_knowledge_bases,
            total_storage_bytes=total_storage_bytes,
            personality_breakdown=personality_breakdown,
            most_active_users=most_active_users,
        )

    async def list_users(self, search: str | None = None) -> list[AdminUserRead]:
        users = await self._users.list_all(search)
        if not users:
            return []

        user_ids = [u.id for u in users]
        convo_counts_q = await self._session.execute(
            select(Conversation.user_id, func.count(Conversation.id))
            .where(Conversation.user_id.in_(user_ids))
            .group_by(Conversation.user_id)
        )
        convo_counts = dict(convo_counts_q.all())

        doc_counts_q = await self._session.execute(
            select(Document.user_id, func.count(Document.id))
            .where(Document.user_id.in_(user_ids))
            .group_by(Document.user_id)
        )
        doc_counts = dict(doc_counts_q.all())

        return [
            AdminUserRead(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                is_active=u.is_active,
                role=u.role,
                created_at=u.created_at,
                conversation_count=convo_counts.get(u.id, 0),
                document_count=doc_counts.get(u.id, 0),
            )
            for u in users
        ]

    async def update_user(
        self, user_id: uuid.UUID, role: str | None, is_active: bool | None
    ) -> User:
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User with ID {user_id} not found")

        if role is not None:
            user = await self._users.set_role(user_id, role)
        if is_active is not None:
            user = await self._users.set_active(user_id, is_active)

        assert user is not None  # existence already confirmed above
        return user

    async def delete_user(self, user_id: uuid.UUID) -> None:
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User with ID {user_id} not found")

        # Best-effort cleanup of the user's default ChromaDB collection. Postgres rows
        # (conversations, documents, knowledge bases, messages) cascade-delete via FK
        # constraints; ChromaDB is a separate store and isn't covered by that, so we
        # clean up what we can here and don't let a Chroma failure block the deletion —
        # an admin removing an account shouldn't get stuck on a vector store hiccup.
        from app.services.chroma_service import ChromaService

        try:
            ChromaService().delete_user_collection(user_id)
        except Exception:
            pass

        await self._users.delete(user_id)

    async def list_recent_conversations(self, limit: int = 50) -> list[AdminConversationRead]:
        conversations = await self._conversations.list_recent(limit)
        if not conversations:
            return []

        user_ids = list({c.user_id for c in conversations})
        emails_q = await self._session.execute(select(User.id, User.email).where(User.id.in_(user_ids)))
        emails_by_id = dict(emails_q.all())

        conversation_ids = [c.id for c in conversations]
        counts_q = await self._session.execute(
            select(Message.conversation_id, func.count(Message.id))
            .where(Message.conversation_id.in_(conversation_ids))
            .group_by(Message.conversation_id)
        )
        counts_by_id = dict(counts_q.all())

        return [
            AdminConversationRead(
                id=c.id,
                user_id=c.user_id,
                user_email=emails_by_id.get(c.user_id, "unknown"),
                title=c.title,
                personality=c.personality,
                message_count=counts_by_id.get(c.id, 0),
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in conversations
        ]

    async def delete_conversation_as_admin(self, conversation_id: uuid.UUID) -> None:
        conversation = await self._conversations.get_by_id(conversation_id)
        if conversation is None:
            raise ConversationNotFoundError(f"Conversation with ID {conversation_id} not found")
        await self._conversations.delete(conversation_id)

    async def list_recent_documents(self, limit: int = 50) -> list[AdminDocumentRead]:
        documents = await self._documents.list_recent(limit)
        if not documents:
            return []

        user_ids = list({d.user_id for d in documents})
        emails_q = await self._session.execute(select(User.id, User.email).where(User.id.in_(user_ids)))
        emails_by_id = dict(emails_q.all())

        return [
            AdminDocumentRead(
                id=d.id,
                user_id=d.user_id,
                user_email=emails_by_id.get(d.user_id, "unknown"),
                original_filename=d.original_filename,
                status=d.status,
                file_size=d.file_size,
                created_at=d.created_at,
            )
            for d in documents
        ]

    async def delete_document_as_admin(self, document_id: uuid.UUID) -> None:
        # Reuse DocumentService's delete so file + ChromaDB cleanup happen exactly the
        # same way as when a user deletes their own document — no duplicated logic.
        from app.services.document_service import DocumentService

        try:
            await DocumentService(self._documents).delete_document(document_id)
        except DocumentNotFoundError:
            raise
