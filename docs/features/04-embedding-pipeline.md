# Feature 4: Embedding Pipeline (RAG Ingestion)

## Architecture

**Backend** — clean layering, consistent with previous features:
- `services/text_extraction_service.py` — Extracts text from PDF, TXT, MD, DOCX files (legacy .doc not supported)
- `services/chunking_service.py` — Splits documents into chunks using LangChain's RecursiveCharacterTextSplitter
- `services/embedding_service.py` — Generates embeddings using OpenAI's text-embedding-3-small model
- `services/chroma_service.py` — Manages ChromaDB collections and embeddings storage/retrieval
- `services/document_processing_service.py` — Orchestrates the full pipeline: extraction → chunking → embedding → storage
- `models/document.py` — Extended with `chunk_count` and `processed_at` fields for embedding metadata
- `api/v1/endpoints/documents.py` — Added POST `/documents/{id}/process` endpoint to trigger processing

**Processing Pipeline:**
1. **Text Extraction**: File is read and text is extracted based on MIME type
2. **Chunking**: Text is split into 1000-character chunks with 200-character overlap
3. **Embedding Generation**: Each chunk is converted to a 1536-dimensional vector using OpenAI embeddings
4. **ChromaDB Storage**: Embeddings are stored in user-specific collections with metadata
5. **Status Update**: Document is marked as "ready" with chunk count and processing timestamp

**ChromaDB Integration:**
- Per-user collections: `user_{user_id}` for data isolation
- Metadata includes: document_id, chunk_index, user_id
- Cosine similarity for vector search
- Automatic collection creation on first use

**Frontend** — Processing status and controls:
- Documents list page shows processing status (uploading/processing/ready/error)
- Added "Chunks" column displaying chunk count
- "Process" button appears for unprocessed documents
- Real-time status updates after processing
- Delete button disabled during processing

## API endpoints

| Method | Path | Auth required | Purpose |
|---|---|---|---|
| POST | `/api/v1/documents/{id}/process` | Yes | Process a document through the embedding pipeline. Returns updated document with chunk_count and processed_at. |

## Document Processing Flow

1. User uploads document → status "ready" (file uploaded but not processed)
2. User clicks "Process" button → POST to `/documents/{id}/process`
3. Backend updates status to "processing"
4. Text extraction from file (PDF/TXT/MD/DOCX)
5. Document chunking (1000 chars, 200 overlap)
6. Embedding generation via OpenAI API
7. Embeddings stored in ChromaDB user collection
8. Document updated with chunk_count and processed_at
9. Status set to "ready" (processed)
10. Frontend refreshes to show updated status

## Configuration

**New environment variables:**
- `AI_MODEL` — OpenAI embedding model (default: text-embedding-3-small)
- `AI_EMBEDDING_DIMENSIONS` — Embedding vector dimensions (default: 1536)
- `CHUNK_SIZE` — Characters per chunk (default: 1000)
- `CHUNK_OVERLAP` — Character overlap between chunks (default: 200)

**File type support:**
- PDF (via pypdf)
- TXT (plain text)
- MD (markdown)
- DOCX (via python-docx)
- DOC (legacy Word) — not currently supported

## Folder changes

```
apps/backend/
├── requirements.txt                         [updated - added text processing libraries]
├── .env.example                            [updated - added AI/embedding settings]
├── alembic/versions/
│   └── 0003_add_embedding_metadata_to_documents.py  [new]
├── app/
│   ├── core/config.py                      [updated - added AI/embedding config]
│   ├── models/document.py                  [updated - added chunk_count, processed_at]
│   ├── domain/schemas/document.py          [updated - added chunk_count, processed_at]
│   ├── repositories/document_repository.py [updated - added mark_processed method]
│   ├── services/
│   │   ├── text_extraction_service.py      [new]
│   │   ├── chunking_service.py            [new]
│   │   ├── embedding_service.py            [new]
│   │   ├── chroma_service.py               [new]
│   │   ├── document_processing_service.py  [new]
│   │   └── document_service.py             [updated - deletes embeddings on doc delete]
│   └── api/v1/endpoints/documents.py      [updated - added process endpoint]

apps/frontend/src/
├── lib/api/documents.ts                    [updated - added processDocument, chunk_count]
└── app/documents/page.tsx                  [updated - processing status, chunks column, process button]
```

## Setup instructions

```bash
cd apps/backend

# Install new dependencies
pip install -r requirements.txt

# Apply the embedding metadata migration
alembic upgrade head

# Set AI_API_KEY in .env (required for OpenAI embeddings)
echo "AI_API_KEY=your-openai-api-key" >> .env

uvicorn app.main:app --reload
```

```bash
cd apps/frontend
npm run dev
```

## Usage

1. Upload a document at `/documents/upload`
2. Navigate to `/documents`
3. Click "Process" button on an unprocessed document
4. Wait for processing to complete (status changes to "ready")
5. View chunk count in the "Chunks" column
6. Document is now ready for RAG queries (Feature 5)

## Testing

Manual testing required for this feature due to external API dependencies:

```bash
# Test text extraction
cd apps/backend
python -c "
import asyncio
from app.services.text_extraction_service import TextExtractionService

async def test():
    extractor = TextExtractionService()
    text = await extractor.extract_text('test.txt', 'text/plain')
    print(f'Extracted {len(text)} characters')

asyncio.run(test())
"

# Test chunking
python -c "
from app.services.chunking_service import ChunkingService

chunker = ChunkingService(chunk_size=1000, chunk_overlap=200)
chunks = chunker.chunk_text('This is a test. ' * 100)
print(f'Created {len(chunks)} chunks')
"
```

## Error Handling

- **Text extraction failures**: Document status set to "error" with error message
- **Embedding API failures**: Document status set to "error" with error message
- **ChromaDB failures**: Document status set to "error" with error message
- **Invalid file types**: Rejected at upload time (Feature 3)
- **Missing AI_API_KEY**: Embedding service initialization fails with clear error

## Performance Considerations

- Processing is synchronous (blocking) — for production, consider background tasks (Celery, etc.)
- Large documents may take significant time to process
- OpenAI API rate limits may affect processing speed
- ChromaDB operations are in-memory for the HTTP client configuration

## Git commit suggestion

```
feat(embeddings): add document processing pipeline with text extraction, chunking, and embeddings

Backend:
- Add TextExtractionService for PDF, TXT, MD, DOCX files
- Add ChunkingService with LangChain RecursiveCharacterTextSplitter
- Add EmbeddingService using OpenAI text-embedding-3-small
- Add ChromaService for vector storage and retrieval
- Add DocumentProcessingService orchestrating the full pipeline
- Add chunk_count and processed_at fields to Document model
- Add Alembic migration for embedding metadata
- Add POST /documents/{id}/process endpoint
- Update document deletion to remove embeddings from ChromaDB
- Add AI/embedding configuration settings

Frontend:
- Add processDocument API function
- Update Document interface with chunk_count and processed_at
- Add processing status indicator (uploading/processing/ready/error)
- Add "Chunks" column to documents table
- Add "Process" button for unprocessed documents
- Disable delete button during processing
```
