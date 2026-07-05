# Changelog

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
