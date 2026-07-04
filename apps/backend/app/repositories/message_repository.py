from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message


class MessageRepository:
    """Data access layer for Message — isolates ORM/query details from the service layer."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_conversation(self, conversation_id: UUID) -> list[Message]:
        result = await self._session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        return list(result.scalars().all())

    async def create(
        self,
        *,
        conversation_id: UUID,
        role: str,
        content: str,
        sources: list[dict] | None = None,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            sources=sources,
        )
        self._session.add(message)
        await self._session.commit()
        await self._session.refresh(message)
        return message

    async def count_by_conversation(self, conversation_id: UUID) -> int:
        messages = await self.get_by_conversation(conversation_id)
        return len(messages)
