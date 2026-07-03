import os
import uuid
from pathlib import Path

from app.core.config import get_settings
from app.domain.exceptions import DocumentNotFoundError, InvalidFileError, StorageError
from app.domain.schemas.document import DocumentCreate
from app.models.document import Document, DocumentStatus
from app.repositories.document_repository import DocumentRepository

settings = get_settings()


class DocumentService:
    """Business rules for document upload, validation, and storage.
    Knows nothing about HTTP — fully unit-testable in isolation.
    """

    def __init__(self, document_repository: DocumentRepository) -> None:
        self._documents = document_repository

    def validate_file(self, filename: str, file_size: int, mime_type: str) -> None:
        """Validate file size and MIME type against configuration."""
        max_size_bytes = settings.max_file_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            raise InvalidFileError(
                f"File size exceeds maximum allowed size of {settings.max_file_size_mb}MB"
            )
        if mime_type not in settings.allowed_mime_types:
            raise InvalidFileError(f"File type {mime_type} is not allowed")

    def generate_storage_path(self, user_id: uuid.UUID, original_filename: str) -> tuple[str, str]:
        """Generate a unique storage path for a file. Returns (filename, full_path)."""
        # Create user-specific directory
        user_dir = Path(settings.upload_dir) / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        file_extension = Path(original_filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        full_path = str(user_dir / unique_filename)

        return unique_filename, full_path

    async def save_file(self, file_content: bytes, file_path: str) -> None:
        """Save file content to disk."""
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(file_content)
        except OSError as exc:
            raise StorageError(f"Failed to save file: {exc}") from exc

    async def delete_file(self, file_path: str) -> None:
        """Delete file from disk."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError as exc:
            raise StorageError(f"Failed to delete file: {exc}") from exc

    async def upload_document(
        self, user_id: uuid.UUID, data: DocumentCreate, file_content: bytes
    ) -> Document:
        """Upload and store a document."""
        self.validate_file(data.original_filename, data.file_size, data.mime_type)

        filename, file_path = self.generate_storage_path(user_id, data.original_filename)
        await self.save_file(file_content, file_path)

        document = await self._documents.create(
            user_id=user_id,
            filename=filename,
            original_filename=data.original_filename,
            file_path=file_path,
            file_size=data.file_size,
            mime_type=data.mime_type,
            status=DocumentStatus.READY,
        )

        return document

    async def get_user_documents(self, user_id: uuid.UUID) -> list[Document]:
        """Get all documents for a user."""
        return await self._documents.get_by_user(user_id)

    async def get_document(self, document_id: uuid.UUID) -> Document:
        """Get a document by ID."""
        document = await self._documents.get_by_id(document_id)
        if document is None:
            raise DocumentNotFoundError(f"Document with ID {document_id} not found")
        return document

    async def delete_document(self, document_id: uuid.UUID) -> None:
        """Delete a document and its file."""
        document = await self._documents.get_by_id(document_id)
        if document is None:
            raise DocumentNotFoundError(f"Document with ID {document_id} not found")

        await self.delete_file(document.file_path)
        await self._documents.delete(document_id)
