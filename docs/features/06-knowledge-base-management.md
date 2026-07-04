# Feature 6: Knowledge Base Management

## Architecture

**Backend** — clean layering, consistent with previous features:
- `models/knowledge_base.py` — KnowledgeBase: belongs to a user, has name and optional description
- `models/document.py` — Document: updated to include optional `knowledge_base_id` foreign key
- `repositories/knowledge_base_repository.py` — data access for knowledge bases
- `services/knowledge_base_service.py` — Business rules for knowledge base CRUD operations
- `api/v1/endpoints/knowledge_bases.py` — `POST /knowledge-bases`, `GET /knowledge-bases`, `GET /knowledge-bases/{id}`, `PATCH /knowledge-bases/{id}`, `DELETE /knowledge-bases/{id}`
- `services/chroma_service.py` — Updated to support knowledge base-specific collections (`kb_{id}`) in addition to default user collections
- `services/document_processing_service.py` — Updated to use knowledge base collections when processing documents
- `services/chat_service.py` — Updated to support optional `knowledge_base_id` parameter for targeted retrieval

**Design choice — per-knowledge-base ChromaDB collections:** Each knowledge base gets its own ChromaDB collection (`kb_{knowledge_base_id}`), allowing documents to be isolated by knowledge base. For backward compatibility, documents without a knowledge base use the default user collection (`user_{user_id}`).

**Knowledge Base Isolation:**
- Documents can be assigned to a knowledge base during upload (optional)
- When a document is processed, its embeddings are stored in the knowledge base's ChromaDB collection
- Chat queries can optionally target a specific knowledge base for retrieval
- If no knowledge base is specified, chat searches across all documents (default user collection)

**Frontend** — Knowledge base management page (`/knowledge-bases`):
- List all knowledge bases for the current user
- Create new knowledge bases with name and optional description
- Delete knowledge bases
- Link to manage documents within each knowledge base
- Knowledge base selector in document upload UI
- Knowledge base selector in chat UI for targeted queries

## API endpoints

| Method | Path | Auth required | Purpose |
|---|---|---|---|
| POST | `/knowledge-bases` | Yes | Create a new knowledge base. Body: `{name, description?}`. |
| GET | `/knowledge-bases` | Yes | List all knowledge bases for the current user. |
| GET | `/knowledge-bases/{id}` | Yes | Get a specific knowledge base by ID. |
| PATCH | `/knowledge-bases/{id}` | Yes | Update a knowledge base. Body: `{name?, description?}`. |
| DELETE | `/knowledge-bases/{id}` | Yes | Delete a knowledge base. |

## Updated endpoints

| Method | Path | Changes |
|---|---|---|
| POST | `/documents/upload` | Added optional `knowledge_base_id` query parameter to assign document to a knowledge base |
| POST | `/chat` | Added optional `knowledge_base_id` in request body to target a specific knowledge base for retrieval |

## Configuration

No new environment variables. Reuses existing configuration from previous features.

## Folder changes

```
apps/backend/
├── .env.example                                     [no changes]
├── alembic/versions/
│   └── 0005_create_knowledge_bases_table.py        [new]
├── app/
│   ├── core/config.py                               [no changes]
│   ├── domain/
│   │   ├── exceptions.py                            [updated - added KnowledgeBaseNotFoundError]
│   │   └── schemas/
│   │       ├── chat.py                             [updated - added knowledge_base_id to ChatRequest]
│   │       ├── document.py                          [updated - added knowledge_base_id to schemas]
│   │       └── knowledge_base.py                    [new]
│   ├── models/
│   │   ├── __init__.py                              [updated - exported all models]
│   │   ├── document.py                              [updated - added knowledge_base_id field]
│   │   └── knowledge_base.py                        [new]
│   ├── repositories/
│   │   ├── __init__.py                              [updated - exported all repositories]
│   │   └── knowledge_base_repository.py             [new]
│   ├── services/
│   │   ├── chat_service.py                          [updated - added knowledge_base_id support]
│   │   ├── chroma_service.py                        [updated - added knowledge_base collection support]
│   │   ├── document_processing_service.py           [updated - uses knowledge base collections]
│   │   ├── document_service.py                       [updated - accepts knowledge_base_id]
│   │   └── knowledge_base_service.py                 [new]
│   └── api/v1/
│       ├── endpoints/
│       │   ├── chat.py                              [updated - passes knowledge_base_id to service]
│       │   ├── documents.py                         [updated - accepts knowledge_base_id parameter]
│       │   └── knowledge_bases.py                   [new]
│       └── router.py                                [updated - registered knowledge_bases router]
└── tests/
    ├── conftest.py                                  [updated - register KnowledgeBase model]
    └── unit/                                        [knowledge base tests to be added]

apps/frontend/src/
├── lib/api/
│   ├── chat.ts                                      [updated - added knowledge_base_id parameter]
│   ├── documents.ts                                 [updated - added knowledge_base_id parameter]
│   └── knowledge-bases.ts                           [new]
├── app/
│   ├── chat/page.tsx                                [updated - added knowledge base selector]
│   ├── dashboard/page.tsx                            [updated - added Knowledge Bases link]
│   ├── documents/upload/page.tsx                    [updated - added knowledge base selector]
│   └── knowledge-bases/page.tsx                      [new]
```

## Setup instructions

```bash
cd apps/backend

# Apply the knowledge bases migration
alembic upgrade head

# No new environment variables needed
uvicorn app.main:app --reload
```

```bash
cd apps/frontend
npm run dev
```

## Usage

1. Navigate to `/knowledge-bases` to create and manage knowledge bases
2. Create a knowledge base (e.g., "Product Documentation", "Support Articles")
3. Upload documents and assign them to a knowledge base via the dropdown selector
4. Process documents to generate embeddings (embeddings stored in knowledge base's ChromaDB collection)
5. Navigate to `/chat` and select a knowledge base to ask questions targeted to that specific knowledge base
6. Or leave the selector at "All documents" to search across all documents

## Testing

Unit tests for knowledge base features should be added to `tests/unit/test_knowledge_base.py`. These should follow the pattern established in previous features, stubbing external dependencies like ChromaDB.

```bash
cd apps/backend
python -m pytest tests/unit/test_knowledge_base.py -v
```

## Error Handling

- **Unknown/foreign knowledge_base_id**: 404 `KnowledgeBaseNotFoundError`
- **Cross-user access**: 403 for knowledge bases, documents, and conversations belonging to other users

## Performance Considerations

- Each knowledge base has its own ChromaDB collection, which may increase memory usage for large numbers of knowledge bases
- Knowledge base deletion does not automatically clean up ChromaDB collections (this should be added in production)
- Document deletion from ChromaDB is handled by the existing cleanup logic

## Data Migration

Existing documents without a `knowledge_base_id` will continue to use the default user collection (`user_{user_id}`). New documents can be assigned to knowledge bases, and their embeddings will be stored in the appropriate collection.

## Git commit suggestion

```
feat(knowledge-bases): add knowledge base management with document isolation

Backend:
- Add KnowledgeBase model with Alembic migration
- Add knowledge_base_id foreign key to documents table
- Add KnowledgeBaseRepository and KnowledgeBaseService
- Add knowledge base CRUD endpoints (POST, GET, PATCH, DELETE /knowledge-bases)
- Update ChromaService to support per-knowledge-base collections
- Update document processing to use knowledge base collections
- Update chat to support optional knowledge base targeting
- Add KnowledgeBaseNotFoundError domain exception
- Update document upload to accept optional knowledge_base_id

Frontend:
- Add knowledge base API client (createKnowledgeBase, getKnowledgeBases, etc.)
- Add /knowledge-bases page with CRUD UI
- Add knowledge base selector to document upload
- Add knowledge base selector to chat for targeted queries
- Add Knowledge Bases link to dashboard
```
