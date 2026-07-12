# Changelog

## [1.1.0] - 2026-07-12

### Added
- **Source Citations** — chat answers now show document name, page number, and a
  confidence score (derived from vector search distance) per source, in an expandable UI
- **Personality Modes** — Professional, Tutor, Friendly, Playful, and opt-in Roast Mode;
  set per-conversation, changeable via the chat UI
- **Conversation History** — rename and search past conversations (delete already existed)
- **Cross-Document Reasoning** — retrieved context is now labeled by source document/page,
  and the system prompt explicitly instructs synthesizing across multiple documents
- **Document Intelligence** — AI-generated summaries and suggested questions per document,
  generated once at processing time; suggested questions are clickable and prefill chat
- **Related Document Recommendations** — embedding-similarity-based, reusing each
  document's already-computed embeddings rather than making extra API calls
- **Navigation shell** — persistent nav bar across all pages (previously missing entirely)
- **Toast notifications** — success/error feedback on document, knowledge base, and
  conversation actions
- Mobile-responsive layout: card-based document grid, collapsible chat sidebar, responsive
  navigation

### Changed
- Default AI provider switched from OpenAI to Gemini (free tier), including updating to
  currently-live model names — the previous defaults (`gpt-4o-mini` /
  `text-embedding-3-small`) were OpenAI-only and never actually reachable under Gemini
- Rebranded from SmartSupport AI Platform to Orin
- `chat_retrieval_top_k` default raised 4 → 6 for better multi-document coverage

### Fixed
- `delete_document_embeddings` only ever checked the default per-user ChromaDB
  collection, silently orphaning embeddings for any document that belonged to a
  knowledge base when deleted
- 3 pre-existing ESLint errors (function/effect ordering) on the frontend

### Known limitations
- `langchain-google-genai` is pinned to a version that depends on Google's legacy,
  deprecated `google-generativeai` SDK. It still works (same underlying REST API), but a
  future upgrade to the current `google-genai`-based SDK is recommended.
- The Qdrant integration (`qdrant_service.py`) exists but is unused dead code — the
  active vector store is ChromaDB.
- 2 backend tests require a live ChromaDB instance to pass and will fail in a sandbox
  without one running.

## [1.0.0] - 2026-07-05

### Added
- **Authentication System** — JWT-based registration, login, token refresh with bcrypt password hashing
- **Document Upload** — Drag-and-drop upload supporting PDF, TXT, MD, DOC, DOCX files with MIME validation
- **Embedding Pipeline** — Text extraction, recursive character chunking, OpenAI embeddings via LangChain
- **RAG Chat** — Conversational AI assistant with context retrieval from ChromaDB vector store
- **Knowledge Base Management** — CRUD for organizing documents into logical groups
- **Dashboard & Analytics** — Aggregated stats: document/KB/conversation counts, status breakdown, recent activity
- **Testing** — 40+ tests covering auth, chat, documents, knowledge bases, dashboard, cross-user isolation

### Infrastructure
- FastAPI backend with clean architecture (API → Service → Repository)
- Next.js 16 frontend with TypeScript and Tailwind CSS 4
- PostgreSQL for relational data, ChromaDB for vector embeddings
- Docker Compose for local development
- Production-ready Docker setup with multi-stage builds

### Security
- JWT access/refresh token rotation
- bcrypt password hashing
- CORS middleware
- File type and size validation
- User isolation across all resources
