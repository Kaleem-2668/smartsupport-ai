import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models import document, user  # noqa: F401  ensures the tables are registered

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture()
def client():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    test_session_local = async_sessionmaker(engine, expire_on_commit=False)

    async def init_models() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(init_models())

    async def override_get_db():
        async with test_session_local() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    asyncio.run(engine.dispose())


@pytest.fixture()
def auth_headers(client):
    """Create a user and return authentication headers."""
    # Register a user
    client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "testpassword123", "full_name": "Test User"},
    )
    # Login to get tokens
    login_response = client.post(
        "/api/v1/auth/login", json={"email": "test@example.com", "password": "testpassword123"}
    )
    access_token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}
