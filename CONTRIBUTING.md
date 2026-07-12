# Contributing to Orin

Thank you for your interest in contributing! We welcome contributions from everyone.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/smartsupport-ai.git`
3. Create a feature branch: `git checkout -b feat/your-feature`
4. Install dependencies:
   ```bash
   cd apps/backend && pip install -r requirements.txt
   cd apps/frontend && npm install
   ```
5. Make your changes
6. Run tests: `cd apps/backend && pytest`
7. Submit a pull request

## Development Setup

See [README.md](README.md#local-development) for detailed setup instructions.

## Code Standards

### Backend (Python)
- **Type hints** — All functions must have type annotations; `mypy --strict` should pass
- **Formatting** — Use `ruff format` (line length: 100)
- **Linting** — Run `ruff check` before committing
- **Testing** — Write tests for new features; pytest with `pytest-asyncio`

### Frontend (TypeScript)
- **TypeScript strict mode** — All code must compile with `strict: true`
- **Formatting** — Use Prettier with default config
- **Components** — Prefer functional components with hooks
- **CSS** — Use Tailwind utility classes; avoid custom CSS

## Pull Request Process

1. Update documentation for any changed behavior
2. Add or update tests as needed
3. Ensure all tests pass: `cd apps/backend && pytest`
4. Ensure frontend builds: `cd apps/frontend && npm run build`
5. Update `CHANGELOG.md` with a description of your changes
6. Request review from a maintainer

## Project Structure

```
smartsupport-ai/
  apps/
    backend/    — FastAPI service with clean architecture
    frontend/   — Next.js app with TypeScript + Tailwind
  docs/
    features/   — Feature documentation
    architecture/ — Architecture decisions
  infra/
    docker-compose.yml
```

## Questions?

Open an issue with the `question` label or start a discussion.
