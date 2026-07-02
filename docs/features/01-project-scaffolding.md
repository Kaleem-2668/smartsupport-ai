# Feature 1: Project Scaffolding

## What this delivers
- Monorepo layout: `apps/backend` (FastAPI), `apps/frontend` (Next.js)
- Docker Compose for local dev: Postgres, ChromaDB, backend, frontend
- Pydantic-validated environment configuration (`app/core/config.py`)
- FastAPI app factory pattern (`create_app()`), CORS configured
- Health check endpoint proving the whole chain boots correctly
- GitHub Actions CI: lint + type-check + test for both apps

## API endpoints
| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/health` | Liveness probe — returns `{"status": "ok"}` |

## Verified locally
- `pytest` — 1/1 tests passing
- Live `uvicorn` server responded `200 {"status":"ok"}` on `/api/v1/health`
- `/docs` (Swagger UI) responded `200`
- `npm run build` — Next.js production build succeeded
- `npm run lint` — no errors

## Testing instructions
```bash
git checkout -b feature/project-scaffolding

cp apps/backend/.env.example apps/backend/.env
cp apps/frontend/.env.local.example apps/frontend/.env.local

cd infra
docker compose up --build

curl http://localhost:8000/api/v1/health
# -> {"status":"ok"}
# open http://localhost:3000 in a browser
```

## Git commit suggestion
```
chore(scaffold): initialize monorepo with docker compose, fastapi skeleton, and CI pipeline

- Add docker-compose.yml wiring postgres, chromadb, backend, frontend
- Add FastAPI app factory with Pydantic Settings and health check endpoint
- Scaffold Next.js frontend with TypeScript, Tailwind, App Router
- Add GitHub Actions CI for backend (ruff, mypy, pytest) and frontend (lint, tsc, build)
```
