# SmartSupport AI Platform

SmartSupport AI Platform enables businesses to upload their documents and knowledge base,
allowing an AI assistant to answer customer questions accurately using Retrieval-Augmented
Generation (RAG).

## Architecture

- **Frontend:** Next.js (App Router) + TypeScript + Tailwind CSS
- **Backend:** FastAPI + SQLAlchemy + Alembic, clean architecture (API / service / repository layers)
- **Database:** PostgreSQL (relational data)
- **Vector store:** ChromaDB (document embeddings)
- **AI:** LangChain, provider-agnostic abstraction over OpenAI-compatible APIs

See [`docs/features/`](docs/features) for a build log of each feature, and
[`docs/architecture/`](docs/architecture) for design notes.

## Repository layout

```
apps/
  backend/    FastAPI service
  frontend/   Next.js app
infra/
  docker-compose.yml
docs/
  features/   one doc per completed feature
```

## Local development

```bash
cp apps/backend/.env.example apps/backend/.env
cp apps/frontend/.env.local.example apps/frontend/.env.local

cd infra
docker compose up --build
```

- Backend: http://localhost:8000 (Swagger docs at `/docs`)
- Frontend: http://localhost:3000

## Status

Actively under development, feature by feature.
- ✅ [Feature 1: Project Scaffolding](docs/features/01-project-scaffolding.md)
- ✅ [Feature 2: Authentication & User Management](docs/features/02-authentication.md)
- ⬜ Feature 3: Document Upload
- ⬜ Feature 4: Embedding Pipeline (RAG ingestion)
- ⬜ Feature 5: RAG Chat
- ⬜ Feature 6: Knowledge Base Management
- ⬜ Feature 7: Dashboard & Analytics
- ⬜ Feature 8: Deployment

## License

MIT — see [LICENSE](LICENSE).
