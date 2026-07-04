import uuid

from app.core.config import get_settings
from app.domain.exceptions import InvalidFileError, StorageError
from app.models.document import Document, DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.services.chroma_service import ChromaService
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.text_extraction_service import TextExtractionService

settings = get_settings()


class DocumentProcessingService:
    """Service for orchestrating document processing pipeline: extraction → chunking → embedding → storage."""

    def __init__(
        self,
        document_repository: DocumentRepository,
    ) -> None:
        self._documents = document_repository
        self._text_extractor = TextExtractionService()
        self._chunker = ChunkingService(
            chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap
        )
        self._embedder = EmbeddingService()
        self._chroma = ChromaService()

    async def process_document(self, document_id: uuid.UUID, user_id: uuid.UUID) -> Document:
        """Process a document through the full pipeline."""
        # Get document
        document = await self._documents.get_by_id(document_id)
        if document is None:
            raise InvalidFileError(f"Document with ID {document_id} not found")

        if document.user_id != user_id:
            raise InvalidFileError("Document does not belong to user")

        # Update status to processing
        await self._documents.update_status(document_id, DocumentStatus.PROCESSING)

        try:
            # Step 1: Extract text
            text = await self._text_extractor.extract_text(document.file_path, document.mime_type)

            if not text or len(text.strip()) == 0:
                raise InvalidFileError("No text could be extracted from document")

            # Step 2: Chunk text
            chunks = self._chunker.chunk_document(text)

            if not chunks:
                raise InvalidFileError("Document could not be chunked")

            # Step 3: Generate embeddings
            chunk_texts = [chunk["content"] for chunk in chunks]
            embeddings = await self._embedder.generate_embeddings(chunk_texts)

            # Step 4: Store in ChromaDB (using knowledge base collection if available)
            await self._chroma.add_embeddings(
                user_id=user_id,
                document_id=document_id,
                chunks=chunks,
                embeddings=embeddings,
                knowledge_base_id=document.knowledge_base_id,
            )

            # Step 5: Mark as processed
            processed_document = await self._documents.mark_processed(document_id, len(chunks))

            return processed_document

        except Exception as exc:
            # Mark as error
            await self._documents.update_status(
                document_id, DocumentStatus.ERROR, error_message=str(exc)
            )
            raise StorageError(f"Document processing failed: {exc}") from exc

    async def delete_document_embeddings(self, document_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Delete embeddings for a document from ChromaDB."""
        try:
            await self._chroma.delete_document_embeddings(user_id, document_id)
        except Exception as exc:
            raise StorageError(f"Failed to delete embeddings: {exc}") from exc
