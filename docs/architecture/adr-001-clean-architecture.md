# ADR-001: Clean Architecture Layers

**Status:** Accepted
**Date:** 2026-06-01

## Context

The backend needed a clear separation of concerns that would make the codebase testable, maintainable, and easy to reason about. Common alternatives included Django-style monolithic views or a simple MVC pattern.

## Decision

We adopted a strict three-layer architecture:

```
Endpoints (HTTP) → Services (Business Logic) → Repositories (Data Access)
```

**Rules:**
- **Endpoints** know about HTTP (FastAPI Depends, Request/Response, status codes). They translate domain exceptions to HTTP responses
- **Services** contain business rules and orchestration logic. They import repositories and other services. They never import FastAPI or HTTP concepts
- **Repositories** encapsulate database queries. They take an SQLAlchemy session and return model instances

**Why not a different pattern?**
- **Django-style monolithic views** — tightly couples HTTP and business logic, making unit tests slow (need database) and fragile
- **Hexagonal (ports & adapters)** — more layers than a project of this scale needs; adds abstraction overhead without proportional benefit
- **MVC** — similar to our approach but the Controller layer often becomes a dumping ground; our Endpoint layer is deliberately thin

## Consequences

**Positive:**
- Services are fully unit-testable without HTTP or real infrastructure
- Adding a new feature means creating files in predictable locations (schema → model → repository → service → endpoint)
- Domain exceptions give clean error handling — endpoints never catch raw SQL or HTTP exceptions
- New team members can understand the code flow quickly

**Trade-offs:**
- More files per feature (5-8 files vs 1-2 in a monolithic approach)
- Simple pass-through operations (e.g., GET by ID) require a repository and service even if the service adds no logic
