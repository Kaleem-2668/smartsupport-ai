import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentStatus(str):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


class DocumentBase(BaseModel):
    filename: str = Field(..., max_length=255)
    original_filename: str = Field(..., max_length=255)
    file_size: int = Field(..., gt=0)
    mime_type: str = Field(..., max_length=100)


class DocumentCreate(DocumentBase):
    knowledge_base_id: uuid.UUID | None = None


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    knowledge_base_id: uuid.UUID | None
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str
    status: str
    error_message: str | None
    chunk_count: int | None
    summary: str | None
    suggested_questions: list[str] | None
    processed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class DocumentUpdate(BaseModel):
    status: str | None = None
    error_message: str | None = None


class RelatedDocument(BaseModel):
    document_id: uuid.UUID
    filename: str
    similarity: float
