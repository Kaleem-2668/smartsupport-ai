from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_base import KnowledgeBase


class KnowledgeBaseRepository:
    """Data access layer for KnowledgeBase — isolates ORM/query details from the service layer."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, knowledge_base_id: UUID) -> KnowledgeBase | None:
        result = await self._session.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: UUID) -> list[KnowledgeBase]:
        result = await self._session.execute(
            select(KnowledgeBase)
            .where(KnowledgeBase.user_id == user_id)
            .order_by(KnowledgeBase.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(
        self,
        *,
        user_id: UUID,
        name: str,
        description: str | None = None,
    ) -> KnowledgeBase:
        knowledge_base = KnowledgeBase(
            user_id=user_id,
            name=name,
            description=description,
        )
        self._session.add(knowledge_base)
        await self._session.commit()
        await self._session.refresh(knowledge_base)
        return knowledge_base

    async def update(
        self,
        knowledge_base_id: UUID,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> KnowledgeBase | None:
        result = await self._session.execute(
            select(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id)
        )
        knowledge_base = result.scalar_one_or_none()
        if knowledge_base is None:
            return None
        if name is not None:
            knowledge_base.name = name
        if description is not None:
            knowledge_base.description = description
        await self._session.commit()
        await self._session.refresh(knowledge_base)
        return knowledge_base

    async def delete(self, knowledge_base_id: UUID) -> bool:
        result = await self._session.execute(
            delete(KnowledgeBase).where(KnowledgeBase.id == knowledge_base_id)
        )
        await self._session.commit()
        return result.rowcount > 0
