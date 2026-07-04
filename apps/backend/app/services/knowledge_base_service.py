import uuid

from app.domain.exceptions import KnowledgeBaseNotFoundError
from app.domain.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseUpdate
from app.models.knowledge_base import KnowledgeBase
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository


class KnowledgeBaseService:
    """Business rules for knowledge base management.
    Knows nothing about HTTP — fully unit-testable in isolation.
    """

    def __init__(self, knowledge_base_repository: KnowledgeBaseRepository) -> None:
        self._knowledge_bases = knowledge_base_repository

    async def create_knowledge_base(
        self, user_id: uuid.UUID, data: KnowledgeBaseCreate
    ) -> KnowledgeBase:
        """Create a new knowledge base for a user."""
        return await self._knowledge_bases.create(
            user_id=user_id,
            name=data.name,
            description=data.description,
        )

    async def get_user_knowledge_bases(self, user_id: uuid.UUID) -> list[KnowledgeBase]:
        """Get all knowledge bases for a user."""
        return await self._knowledge_bases.get_by_user(user_id)

    async def get_knowledge_base(self, knowledge_base_id: uuid.UUID) -> KnowledgeBase:
        """Get a knowledge base by ID."""
        knowledge_base = await self._knowledge_bases.get_by_id(knowledge_base_id)
        if knowledge_base is None:
            raise KnowledgeBaseNotFoundError(f"Knowledge base with ID {knowledge_base_id} not found")
        return knowledge_base

    async def update_knowledge_base(
        self, knowledge_base_id: uuid.UUID, data: KnowledgeBaseUpdate
    ) -> KnowledgeBase:
        """Update a knowledge base."""
        knowledge_base = await self._knowledge_bases.update(
            knowledge_base_id,
            name=data.name,
            description=data.description,
        )
        if knowledge_base is None:
            raise KnowledgeBaseNotFoundError(f"Knowledge base with ID {knowledge_base_id} not found")
        return knowledge_base

    async def delete_knowledge_base(self, knowledge_base_id: uuid.UUID) -> None:
        """Delete a knowledge base and its associated documents."""
        knowledge_base = await self._knowledge_bases.get_by_id(knowledge_base_id)
        if knowledge_base is None:
            raise KnowledgeBaseNotFoundError(f"Knowledge base with ID {knowledge_base_id} not found")

        # Delete the knowledge base (documents will be handled by CASCADE or need separate cleanup)
        await self._knowledge_bases.delete(knowledge_base_id)
