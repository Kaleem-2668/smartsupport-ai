from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document


class DocumentRepository:
    """Data access layer for Document — isolates ORM/query details from the service layer."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, document_id: UUID) -> Document | None:
        result = await self._session.execute(select(Document).where(Document.id == document_id))
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: UUID) -> list[Document]:
        result = await self._session.execute(
            select(Document).where(Document.user_id == user_id).order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(
        self,
        *,
        user_id: UUID,
        filename: str,
        original_filename: str,
        file_path: str,
        file_size: int,
        mime_type: str,
        status: str,
    ) -> Document:
        document = Document(
            user_id=user_id,
            filename=filename,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            status=status,
        )
        self._session.add(document)
        await self._session.commit()
        await self._session.refresh(document)
        return document

    async def update_status(self, document_id: UUID, status: str, error_message: str | None = None) -> Document | None:
        result = await self._session.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        if document is None:
            return None
        document.status = status
        if error_message is not None:
            document.error_message = error_message
        await self._session.commit()
        await self._session.refresh(document)
        return document

    async def delete(self, document_id: UUID) -> bool:
        result = await self._session.execute(delete(Document).where(Document.id == document_id))
        await self._session.commit()
        return result.rowcount > 0
