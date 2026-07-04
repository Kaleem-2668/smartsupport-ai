import uuid

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.db.session import get_db
from app.domain.exceptions import DocumentNotFoundError, InvalidFileError, StorageError
from app.domain.schemas.document import DocumentCreate, DocumentRead
from app.models.document import Document
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.services.document_processing_service import DocumentProcessingService
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


def get_document_service(db: AsyncSession = Depends(get_db)) -> DocumentService:
    return DocumentService(DocumentRepository(db))


def get_document_processing_service(db: AsyncSession = Depends(get_db)) -> DocumentProcessingService:
    return DocumentProcessingService(DocumentRepository(db))


@router.post("/upload", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
) -> Document:
    """Upload a document. Validates file size and type."""
    try:
        file_content = await file.read()
        
        document_data = DocumentCreate(
            filename=file.filename or "unknown",
            original_filename=file.filename or "unknown",
            file_size=len(file_content),
            mime_type=file.content_type or "application/octet-stream",
        )
        
        return await document_service.upload_document(
            user_id=current_user.id,
            data=document_data,
            file_content=file_content,
        )
    except InvalidFileError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except StorageError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("", response_model=list[DocumentRead])
async def list_documents(
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
) -> list[Document]:
    """List all documents for the current user."""
    return await document_service.get_user_documents(current_user.id)


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
) -> Document:
    """Get a specific document by ID."""
    try:
        document = await document_service.get_document(document_id)
        # Ensure user can only access their own documents
        if document.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        return document
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    document_service: DocumentService = Depends(get_document_service),
) -> None:
    """Delete a document by ID."""
    try:
        document = await document_service.get_document(document_id)
        # Ensure user can only delete their own documents
        if document.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        await document_service.delete_document(document_id)
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{document_id}/process", response_model=DocumentRead)
async def process_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    processing_service: DocumentProcessingService = Depends(get_document_processing_service),
) -> Document:
    """Process a document to extract text, generate embeddings, and store in ChromaDB."""
    try:
        return await processing_service.process_document(document_id, current_user.id)
    except (InvalidFileError, StorageError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
