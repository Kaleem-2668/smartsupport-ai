from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation


class ConversationRepository:
    """Data access layer for Conversation — isolates ORM/query details from the service layer."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, conversation_id: UUID) -> Conversation | None:
        result = await self._session.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: UUID) -> list[Conversation]:
        result = await self._session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, *, user_id: UUID, title: str | None = None) -> Conversation:
        conversation = Conversation(user_id=user_id, title=title)
        self._session.add(conversation)
        await self._session.commit()
        await self._session.refresh(conversation)
        return conversation

    async def touch(self, conversation_id: UUID) -> None:
        """Bump updated_at so recently-active conversations sort first."""
        conversation = await self.get_by_id(conversation_id)
        if conversation is None:
            return
        conversation.updated_at = datetime.now()
        await self._session.commit()

    async def set_title(self, conversation_id: UUID, title: str) -> Conversation | None:
        conversation = await self.get_by_id(conversation_id)
        if conversation is None:
            return None
        conversation.title = title
        await self._session.commit()
        await self._session.refresh(conversation)
        return conversation

    async def delete(self, conversation_id: UUID) -> bool:
        conversation = await self.get_by_id(conversation_id)
        if conversation is None:
            return False
        await self._session.delete(conversation)
        await self._session.commit()
        return True
