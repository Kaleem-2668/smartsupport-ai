import uuid

import pytest

from app.domain.exceptions import KnowledgeBaseNotFoundError
from app.domain.schemas.knowledge_base import KnowledgeBaseCreate, KnowledgeBaseUpdate
from app.models.knowledge_base import KnowledgeBase
from app.repositories.knowledge_base_repository import KnowledgeBaseRepository
from app.services.knowledge_base_service import KnowledgeBaseService


@pytest.mark.asyncio
async def test_create_knowledge_base(db_session):
    """Test creating a knowledge base."""
    user_id = uuid.uuid4()
    repository = KnowledgeBaseRepository(db_session)
    service = KnowledgeBaseService(repository)

    data = KnowledgeBaseCreate(name="Test KB", description="A test knowledge base")
    kb = await service.create_knowledge_base(user_id, data)

    assert kb.id is not None
    assert kb.user_id == user_id
    assert kb.name == "Test KB"
    assert kb.description == "A test knowledge base"


@pytest.mark.asyncio
async def test_get_user_knowledge_bases(db_session):
    """Test retrieving all knowledge bases for a user."""
    user_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    repository = KnowledgeBaseRepository(db_session)
    service = KnowledgeBaseService(repository)

    # Create knowledge bases for the user
    await service.create_knowledge_base(user_id, KnowledgeBaseCreate(name="KB 1"))
    await service.create_knowledge_base(user_id, KnowledgeBaseCreate(name="KB 2"))

    # Create a knowledge base for another user
    await service.create_knowledge_base(other_user_id, KnowledgeBaseCreate(name="Other KB"))

    kbs = await service.get_user_knowledge_bases(user_id)

    assert len(kbs) == 2
    assert all(kb.user_id == user_id for kb in kbs)
    assert kb_names = {kb.name for kb in kbs}
    assert "KB 1" in kb_names
    assert "KB 2" in kb_names
    assert "Other KB" not in kb_names


@pytest.mark.asyncio
async def test_get_knowledge_base_by_id(db_session):
    """Test retrieving a specific knowledge base by ID."""
    user_id = uuid.uuid4()
    repository = KnowledgeBaseRepository(db_session)
    service = KnowledgeBaseService(repository)

    created = await service.create_knowledge_base(user_id, KnowledgeBaseCreate(name="Test KB"))
    retrieved = await service.get_knowledge_base(created.id)

    assert retrieved.id == created.id
    assert retrieved.name == "Test KB"


@pytest.mark.asyncio
async def test_get_knowledge_base_not_found(db_session):
    """Test that retrieving a non-existent knowledge base raises an error."""
    user_id = uuid.uuid4()
    repository = KnowledgeBaseRepository(db_session)
    service = KnowledgeBaseService(repository)

    with pytest.raises(KnowledgeBaseNotFoundError):
        await service.get_knowledge_base(uuid.uuid4())


@pytest.mark.asyncio
async def test_update_knowledge_base(db_session):
    """Test updating a knowledge base."""
    user_id = uuid.uuid4()
    repository = KnowledgeBaseRepository(db_session)
    service = KnowledgeBaseService(repository)

    created = await service.create_knowledge_base(
        user_id, KnowledgeBaseCreate(name="Old Name", description="Old description")
    )

    updated = await service.update_knowledge_base(
        created.id, KnowledgeBaseUpdate(name="New Name", description="New description")
    )

    assert updated.id == created.id
    assert updated.name == "New Name"
    assert updated.description == "New description"


@pytest.mark.asyncio
async def test_update_knowledge_base_partial(db_session):
    """Test partially updating a knowledge base (only name)."""
    user_id = uuid.uuid4()
    repository = KnowledgeBaseRepository(db_session)
    service = KnowledgeBaseService(repository)

    created = await service.create_knowledge_base(
        user_id, KnowledgeBaseCreate(name="Old Name", description="Description")
    )

    updated = await service.update_knowledge_base(created.id, KnowledgeBaseUpdate(name="New Name"))

    assert updated.name == "New Name"
    assert updated.description == "Description"  # Unchanged


@pytest.mark.asyncio
async def test_update_knowledge_base_not_found(db_session):
    """Test that updating a non-existent knowledge base raises an error."""
    user_id = uuid.uuid4()
    repository = KnowledgeBaseRepository(db_session)
    service = KnowledgeBaseService(repository)

    with pytest.raises(KnowledgeBaseNotFoundError):
        await service.update_knowledge_base(uuid.uuid4(), KnowledgeBaseUpdate(name="New Name"))


@pytest.mark.asyncio
async def test_delete_knowledge_base(db_session):
    """Test deleting a knowledge base."""
    user_id = uuid.uuid4()
    repository = KnowledgeBaseRepository(db_session)
    service = KnowledgeBaseService(repository)

    created = await service.create_knowledge_base(user_id, KnowledgeBaseCreate(name="Test KB"))
    await service.delete_knowledge_base(created.id)

    # Verify it's deleted
    with pytest.raises(KnowledgeBaseNotFoundError):
        await service.get_knowledge_base(created.id)


@pytest.mark.asyncio
async def test_delete_knowledge_base_not_found(db_session):
    """Test that deleting a non-existent knowledge base raises an error."""
    user_id = uuid.uuid4()
    repository = KnowledgeBaseRepository(db_session)
    service = KnowledgeBaseService(repository)

    with pytest.raises(KnowledgeBaseNotFoundError):
        await service.delete_knowledge_base(uuid.uuid4())
