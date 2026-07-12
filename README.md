<div align="center">
  <h1>🤖 Orin</h1>
  <p><strong>An AI-powered knowledge companion — chat with your own documents, grounded in cited sources</strong></p>
  <p>
    <a href="#features">Features</a> •
    <a href="#architecture">Architecture</a> •
    <a href="#quick-start">Quick Start</a> •
    <a href="#api-documentation">API</a> •
    <a href="#deployment">Deployment</a> •
    <a href="CONTRIBUTING.md">Contributing</a>
  </p>

  <!-- Badges placeholder -->
  <p>
    <img src="https://img.shields.io/badge/python-3.12-blue?logo=python" alt="Python 3.12">
    <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi" alt="FastAPI">
    <img src="https://img.shields.io/badge/Next.js-16-000000?logo=next.js" alt="Next.js 16">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
    <br>
    <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql" alt="PostgreSQL">
    <img src="https://img.shields.io/badge/ChromaDB-0.5-FC60A8" alt="ChromaDB">
    <img src="https://img.shields.io/badge/LangChain-0.3-1C3D5A" alt="LangChain">
    <img src="https://img.shields.io/badge/Tailwind%20CSS-4-06B6D4?logo=tailwindcss" alt="Tailwind CSS 4">
  </p>
</div>

---

## Overview

Orin is a full-stack Retrieval-Augmented Generation (RAG) knowledge companion that enables users to upload their documents and knowledge bases, allowing an AI assistant to answer questions accurately using only the provided context.

**Key capabilities:**
- Upload PDF, TXT, MD, DOC, DOCX documents
- Automatic text extraction, chunking, and embedding
- AI-powered Q&A grounded in your documents, with source citations (document name, page number, confidence)
- 5 personality modes — Professional, Tutor, Friendly, Playful, and opt-in Roast Mode
- Cross-document reasoning — synthesizes and attributes answers across multiple sources
- Document summaries, suggested questions, and related-document recommendations
- Conversation history — save, rename, search, and delete past chats
- Organize documents into knowledge bases
- Dashboard with usage analytics and recent activity
- User authentication with JWT token rotation

## Features

| # | Feature | Status |
|---|---------|--------|
| 1 | Project Scaffolding — FastAPI + Next.js monorepo with Docker Compose | ✅ |
| 2 | Authentication — JWT registration/login/refresh with token rotation | ✅ |
| 3 | Document Upload — Drag-and-drop with MIME validation (PDF, TXT, MD, DOC, DOCX) | ✅ |
| 4 | Embedding Pipeline — Text extraction → chunking → Gemini embeddings → ChromaDB | ✅ |
| 5 | RAG Chat — Context-grounded Q&A with conversation history | ✅ |
| 6 | Source Citations — Document name, page number, and confidence score per answer | ✅ |
| 7 | Personality Modes — Professional, Tutor, Friendly, Playful, opt-in Roast | ✅ |
| 8 | Conversation History — Rename, search, and delete past conversations | ✅ |
| 9 | Cross-Document Reasoning — Answers synthesize and attribute across multiple sources | ✅ |
| 10 | Document Intelligence — AI summaries, suggested questions, related-document recommendations | ✅ |
| 11 | Knowledge Base Management — Organize documents into logical groups | ✅ |
| 12 | Dashboard & Analytics — Stats cards, status breakdown, recent activity | ✅ |
| 13 | Production Deployment — Docker, Nginx, health checks, environment validation | ✅ |

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Next.js Frontend                   │
│           (App Router + TypeScript + Tailwind)        │
└──────────────────┬──────────────────────────────────┘
                   │ HTTP / JSON
┌──────────────────▼──────────────────────────────────┐
│                  FastAPI Backend                      │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐   │
│  │ API Layer │→│ Service  │→│  Repository Layer  │   │
│  │ Endpoints │  │ Layer    │  │  (SQLAlchemy)     │   │
│  └──────────┘  └──────────┘  └────────┬──────────┘   │
│                                       │              │
│       ┌─────────────┐  ┌──────────┐   │              │
│       │ LangChain   │  │ ChromaDB │   │              │
│       │ (Gemini)    │  │ (Vector) │   │              │
│       └─────────────┘  └──────────┘   │              │
└───────────────────────────────────────┼──────────────┘
                                        │
                    ┌───────────────────┴──────────┐
                    │         PostgreSQL            │
                    │   (Users, Docs, Chats, KBs)   │
                    └──────────────────────────────┘
```

### Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js 16, TypeScript, Tailwind CSS 4 | Web UI |
| **Backend** | FastAPI, Python 3.12, Pydantic v2 | REST API |
| **ORM** | SQLAlchemy 2.0 (async) | Database access |
| **Migrations** | Alembic | Schema management |
| **Database** | PostgreSQL 16 | Relational data |
| **Vector DB** | ChromaDB | Document embeddings |
| **AI** | LangChain + Gemini | Embeddings & chat |
| **Auth** | JWT (access/refresh tokens), bcrypt | Authentication |
| **Infrastructure** | Docker, Docker Compose, Nginx | Deployment |

### Clean Architecture

The backend follows a strict layered architecture:

```
Endpoints (HTTP) → Services (Business Logic) → Repositories (Data Access)
```

- **Endpoints** handle HTTP concerns (parsing requests, returning responses, translating domain exceptions)
- **Services** contain business rules and orchestration logic — no HTTP or SQL knowledge
- **Repositories** encapsulate all database queries — nothing above writes raw SQL
- **Domain** (schemas + exceptions) is shared across layers for type safety

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for local frontend dev)
- Python 3.12+ (for local backend dev)
- Gemini API key (free at [aistudio.google.com](https://aistudio.google.com/apikey))

### Local Development (Docker)

```bash
# 1. Clone the repository
git clone https://github.com/your-username/smartsupport-ai.git
cd smartsupport-ai

# 2. Set up environment variables
cp apps/backend/.env.example apps/backend/.env
cp apps/frontend/.env.local.example apps/frontend/.env.local

# 3. Edit .env files with your values (especially AI_API_KEY and SECRET_KEY)

# 4. Start all services
cd infra
docker compose up --build
```

- **Frontend:** http://localhost:3000
- **Backend:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### Manual Local Development

```bash
# Backend
cd apps/backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd apps/frontend
npm install
npm run dev
```

### Running Tests

```bash
cd apps/backend
pip install -r requirements.txt
python -m pytest -v
```

## API Documentation

### Authentication

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/register` | Create an account |
| POST | `/api/v1/auth/login` | Log in (returns access + refresh tokens) |
| POST | `/api/v1/auth/refresh` | Refresh expired access token |
| GET | `/api/v1/auth/me` | Get current user |

### Documents

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/documents/upload` | Upload a document (multipart/form-data) |
| GET | `/api/v1/documents` | List user's documents |
| GET | `/api/v1/documents/{id}` | Get document details |
| DELETE | `/api/v1/documents/{id}` | Delete a document |
| POST | `/api/v1/documents/{id}/process` | Process document (extract → chunk → embed) |

### Chat

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/chat` | Ask a question (creates/reuses conversation) |
| GET | `/api/v1/conversations` | List conversations |
| GET | `/api/v1/conversations/{id}/messages` | Get conversation messages |
| DELETE | `/api/v1/conversations/{id}` | Delete conversation |

### Knowledge Bases

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/knowledge-bases` | Create knowledge base |
| GET | `/api/v1/knowledge-bases` | List knowledge bases |
| GET | `/api/v1/knowledge-bases/{id}` | Get knowledge base |
| PATCH | `/api/v1/knowledge-bases/{id}` | Update knowledge base |
| DELETE | `/api/v1/knowledge-bases/{id}` | Delete knowledge base |

### Dashboard & Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/dashboard/stats` | Dashboard analytics |
| GET | `/api/v1/health` | Health check |

## Project Structure

```
smartsupport-ai/
├── apps/
│   ├── backend/                    # FastAPI service
│   │   ├── alembic/                # Database migrations
│   │   ├── app/
│   │   │   ├── api/v1/endpoints/   # HTTP route handlers
│   │   │   ├── core/               # Config, security, logging
│   │   │   ├── db/                 # Database session management
│   │   │   ├── domain/schemas/     # Pydantic request/response models
│   │   │   ├── models/             # SQLAlchemy ORM models
│   │   │   ├── repositories/       # Data access layer
│   │   │   ├── services/           # Business logic layer
│   │   │   └── main.py             # FastAPI app factory
│   │   ├── tests/unit/             # Unit tests
│   │   └── requirements.txt        # Python dependencies
│   └── frontend/                   # Next.js app
│       └── src/
│           ├── app/                # App Router pages
│           ├── components/         # Shared React components
│           ├── context/            # React context providers
│           └── lib/api/            # API client modules
├── docs/
│   ├── features/                   # Feature documentation
│   └── architecture/               # Architecture decisions
├── infra/
│   ├── docker-compose.yml          # Development setup
│   ├── docker-compose.prod.yml     # Production setup
│   ├── nginx.conf                  # Reverse proxy config
│   └── startup.sh                  # Production startup script
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── ROADMAP.md
└── SECURITY.md
```

## Environment Variables

### Backend (`apps/backend/.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | ✅ | — | JWT signing key (generate with `openssl rand -hex 32`) |
| `AI_API_KEY` | ✅ | — | Gemini API key |
| `AI_PROVIDER` | — | `gemini` | AI provider: `gemini` or `openai` |
| `POSTGRES_PASSWORD` | ✅ | — | Database password |
| `POSTGRES_USER` | — | `orin` | Database user |
| `POSTGRES_DB` | — | `orin` | Database name |
| `POSTGRES_HOST` | — | `postgres` | Database host |
| `POSTGRES_PORT` | — | `5432` | Database port |
| `CHROMA_HOST` | — | `localhost` | ChromaDB host |
| `CHROMA_PORT` | — | `8000` | ChromaDB port |
| `AI_CHAT_MODEL` | — | `gemini-2.5-flash` | Chat completion model |
| `AI_MODEL` | — | `models/gemini-embedding-001` | Embedding model |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | — | `15` | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | — | `7` | Refresh token TTL |
| `CHUNK_SIZE` | — | `1000` | Document chunk size (chars) |
| `CHUNK_OVERLAP` | — | `200` | Chunk overlap (chars) |
| `MAX_FILE_SIZE_MB` | — | `10` | Max upload file size |
| `APP_ENV` | — | `development` | Environment name |
| `DEBUG` | — | `true` | Debug mode |

### Frontend (`apps/frontend/.env.local`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | ✅ | `http://localhost:8000/api/v1` | Backend API URL |

## Deployment

### Production Docker

```bash
# Ensure required env vars are set (will fail fast if missing)
export SECRET_KEY="your-32-byte-hex-key"
export POSTGRES_PASSWORD="your-db-password"
export AI_API_KEY="your-gemini-api-key"

# Start production stack
cd infra
docker compose -f docker-compose.prod.yml up --build -d
```

### Using the startup script

```bash
chmod +x infra/startup.sh
./infra/startup.sh prod    # Start production
./infra/startup.sh dev     # Start development
./infra/startup.sh stop    # Stop all services
./infra/startup.sh logs    # View logs
./infra/startup.sh status  # Check service status
```

### Production Architecture

```
                     ┌──────────┐
                     │  Nginx   │  (port 80/443)
                     └────┬─────┘
                  ┌───────┴────────┐
                  ▼                ▼
            ┌──────────┐    ┌──────────┐
            │  Backend  │    │ Frontend │
            │  FastAPI  │    │  Next.js │
            └─────┬─────┘    └──────────┘
          ┌───────┴────────┐
          ▼                ▼
    ┌──────────┐    ┌──────────┐
    │PostgreSQL│    │ ChromaDB │
    └──────────┘    └──────────┘
```

## Security

- **JWT access tokens** (15 min expiry) with refresh token rotation
- **bcrypt** password hashing (12 rounds)
- **Token type validation** — access tokens cannot be used as refresh tokens
- **User isolation** — all resources scoped to user ID; cross-user access returns 403
- **File validation** — MIME type whitelist, size limit, path traversal prevention
- **CORS** — restricted to configured origins
- **Input validation** — Pydantic schemas on every endpoint

See [SECURITY.md](SECURITY.md) for the full security policy.

## Testing

The backend has **84 unit tests** covering all features, running against an in-memory SQLite database:

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_auth.py` | 10 | Registration, login, token refresh, access control |
| `test_health.py` | 1 | Health check endpoint |
| `test_chat.py` | 26 | RAG pipeline, conversations, citations, personality modes, rename/search, isolation |
| `test_documents.py` | 28 | Upload, CRUD, processing, summaries/suggested questions, related documents, cross-user isolation |
| `test_knowledge_base.py` | 12 | CRUD, cross-user isolation |
| `test_dashboard.py` | 7 | Stats, empty state, with data, isolation |

Two tests in `test_documents.py` (`test_process_document_not_found`,
`test_process_document_cannot_process_other_users`) require a **live ChromaDB** instance
(the `docker compose` service) to pass — they'll fail in any environment without one
running, since document processing constructs a real `ChromaService` client.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Roadmap

See [ROADMAP.md](ROADMAP.md) for planned features and future direction.

---

<div align="center">
  <sub>Built with ❤️ using FastAPI, Next.js, and LangChain</sub>
</div>
