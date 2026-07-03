# Feature 3: Document Upload

## Architecture

**Backend** — clean layering, consistent with Feature 2:
- `models/document.py` — SQLAlchemy `Document` table (UUID primary key, user foreign key, file metadata, status tracking).
- `repositories/document_repository.py` — all DB queries for documents. Nothing above this layer writes SQL.
- `services/document_service.py` — business rules (upload validation, file storage, document CRUD). Pure Python, no FastAPI imports — fully unit-testable on its own.
- `api/v1/endpoints/documents.py` — thin HTTP layer. Handles multipart file uploads, calls the service, translates domain exceptions into HTTP status codes.
- `core/config.py` — extended with document storage settings (upload directory, max file size, allowed MIME types).

**File Storage Strategy:**
- Files are stored in a user-specific directory structure: `uploads/{user_id}/{unique_filename}`
- Unique filenames prevent collisions while preserving original filenames in metadata
- File size and MIME type validation before storage
- Files are deleted from disk when documents are deleted
- Docker volume `uploads_data` provides persistent storage across container restarts

**Frontend** — Drag-and-drop upload + document management:
- `/documents/upload` page with drag-and-drop UI, file validation, and upload progress
- `/documents` page listing all user's documents with delete functionality
- API client functions for upload, list, get, and delete operations
- Dashboard updated with navigation links to document pages

## API endpoints

| Method | Path | Auth required | Purpose |
|---|---|---|---|
| POST | `/api/v1/documents/upload` | Yes | Upload a document. Validates file size (max 10MB) and type (PDF, TXT, MD, DOC, DOCX). Returns `201` + document metadata. |
| GET | `/api/v1/documents` | Yes | List all documents for the current user. |
| GET | `/api/v1/documents/{id}` | Yes | Get a specific document by ID. Users can only access their own documents. |
| DELETE | `/api/v1/documents/{id}` | Yes | Delete a document by ID. Removes file from disk and database record. Users can only delete their own documents. |

## Document Upload Flow

1. User selects or drags a file onto the upload page
2. Frontend validates file type and size (client-side validation)
3. File is sent as multipart/form-data to `/api/v1/documents/upload`
4. Backend validates file again (server-side validation)
5. DocumentService generates unique filename and storage path
6. File is saved to disk in user-specific directory
7. Document metadata is stored in database with status "ready"
8. User is redirected to documents list page

## Folder changes

```
apps/backend/app/
├── models/document.py                    [new]
├── domain/
│   ├── exceptions.py                      [updated - added document exceptions]
│   └── schemas/document.py                [new]
├── repositories/document_repository.py    [new]
├── services/document_service.py           [new]
├── core/config.py                         [updated - added storage settings]
└── api/v1/
    ├── endpoints/documents.py             [new]
    └── router.py                          [updated - added documents router]
apps/backend/alembic/versions/
    └── 0002_create_documents_table.py     [new]
apps/backend/tests/unit/test_documents.py  [new - 10 tests]
apps/backend/.gitignore                    [new - excludes uploads/]
apps/backend/Dockerfile                    [updated - creates uploads directory]
apps/backend/.env.example                  [updated - added storage settings]

apps/frontend/src/
├── lib/api/documents.ts                   [new]
└── app/
    ├── documents/page.tsx                 [new]
    ├── documents/upload/page.tsx          [new]
    └── dashboard/page.tsx                 [updated - added navigation links]

infra/docker-compose.yml                  [updated - added uploads_data volume]
```

## Setup instructions

```bash
cd apps/backend

# Apply the documents table migration (requires Postgres running)
alembic upgrade head

# Ensure uploads directory exists
mkdir -p uploads

uvicorn app.main:app --reload
```

```bash
cd apps/frontend
npm run dev
```

Visit http://localhost:3000/documents/upload to upload documents, then http://localhost:3000/documents to view and manage them.

## Testing

Backend tests run against an in-memory SQLite database (via `aiosqlite`), so they need **no Postgres connection**:

```bash
cd apps/backend
pip install -r requirements-dev.txt
pytest -v
```

Verified locally: **10/10 tests passing**, covering:
- Upload requires authentication
- Successful document upload
- Invalid MIME type rejection
- List documents requires authentication
- List documents (empty and with files)
- Get document requires authentication
- Get document not found
- Delete document requires authentication
- Successful document deletion
- Delete document not found

`ruff check .` and `mypy app` are both clean. Frontend `npm run build` and `npm run lint` both pass with the new pages.

## File Validation

**Allowed MIME types:**
- `application/pdf` - PDF documents
- `text/plain` - Plain text files
- `text/markdown` - Markdown files
- `application/msword` - Word documents (.doc)
- `application/vnd.openxmlformats-officedocument.wordprocessingml.document` - Word documents (.docx)

**File size limit:** 10MB (configurable via `MAX_FILE_SIZE_MB` environment variable)

## Git commit suggestion

```
feat(docs): add document upload with file validation and storage

Backend:
- Add Document model with user foreign key, file metadata, and status tracking
- Add DocumentRepository for data access
- Add DocumentService with file validation, storage, and CRUD operations
- Add /documents/upload, /documents, /documents/{id}, DELETE /documents/{id} endpoints
- Add document storage configuration (upload dir, max size, allowed types)
- Add Alembic migration for documents table
- Add 10 passing unit tests against in-memory SQLite DB
- Update Dockerfile to create uploads directory
- Add uploads_data volume to docker-compose.yml for persistent storage

Frontend:
- Add document API client (upload, list, get, delete)
- Add /documents/upload page with drag-and-drop UI and file validation
- Add /documents page with document list and delete functionality
- Update dashboard with navigation links to document pages
```
