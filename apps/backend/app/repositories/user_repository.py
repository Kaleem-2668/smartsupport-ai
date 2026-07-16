from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Data access layer for User — isolates ORM/query details from the service layer."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self._session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def list_all(self, search: str | None = None) -> list[User]:
        query = select(User).order_by(User.created_at.desc())
        if search:
            like = f"%{search}%"
            query = query.where((User.email.ilike(like)) | (User.full_name.ilike(like)))
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def set_role(self, user_id: UUID, role: str) -> User | None:
        user = await self.get_by_id(user_id)
        if user is None:
            return None
        user.role = role
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def set_active(self, user_id: UUID, is_active: bool) -> User | None:
        user = await self.get_by_id(user_id)
        if user is None:
            return None
        user.is_active = is_active
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def delete(self, user_id: UUID) -> None:
        user = await self.get_by_id(user_id)
        if user is not None:
            await self._session.delete(user)
            await self._session.commit()

    async def create(
        self, *, email: str, hashed_password: str, full_name: str | None, role: str = "user"
    ) -> User:
        user = User(email=email, hashed_password=hashed_password, full_name=full_name, role=role)
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user
