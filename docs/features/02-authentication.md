# Feature 2: Authentication & User Management

## Architecture

**Backend** — clean layering, consistent with Feature 1:
- `models/user.py` — SQLAlchemy `User` table (UUID primary key, unique email, bcrypt hash).
- `repositories/user_repository.py` — all DB queries for users. Nothing above this layer writes SQL.
- `services/auth_service.py` — business rules (registration, authentication, token issuance). Pure Python, no FastAPI imports — fully unit-testable on its own.
- `api/v1/endpoints/auth.py` — thin HTTP layer. Parses requests, calls the service, translates domain exceptions (`EmailAlreadyExistsError`, `InvalidCredentialsError`, ...) into HTTP status codes.
- `core/security.py` — password hashing (bcrypt via passlib) and JWT creation/validation.
- `api/v1/dependencies.py` — `get_current_user`, the reusable dependency any future protected endpoint plugs into via `Depends(get_current_user)`.

**Why access + refresh tokens:** the access token is short-lived (15 min, configurable) and sent on every request — a small blast radius if it leaks. The refresh token is long-lived (7 days) and only used to mint new access tokens. Both are stateless JWTs distinguished by a `type` claim. On refresh, both tokens are rotated (reissued), shrinking the window a stolen refresh token stays useful.

**Frontend** — Context + Axios interceptors:
- `AuthContext` is the single source of truth for "who's logged in." Pages call `useAuth()` rather than managing tokens themselves.
- `lib/api/client.ts` has a response interceptor: on a 401 (excluding login/register/refresh themselves), it silently calls `/auth/refresh` and retries the original request once. An expired access token never bounces a user to the login screen while their refresh token is still valid.
- `ProtectedRoute` is a wrapper component — any page becomes auth-gated by wrapping it once, rather than repeating redirect logic per page. `/dashboard` demonstrates the pattern.

## API endpoints

| Method | Path | Auth required | Purpose |
|---|---|---|---|
| POST | `/api/v1/auth/register` | No | Create an account. Returns `201` + user (no password). `409` if email taken. |
| POST | `/api/v1/auth/login` | No | Exchange email/password for an access + refresh token. `401` on bad credentials. |
| POST | `/api/v1/auth/refresh` | No (needs refresh token) | Exchange a valid refresh token for a new access + refresh token pair. |
| GET | `/api/v1/auth/me` | Yes (Bearer access token) | Returns the current user. `401` if missing/invalid/expired token. |

## Authentication flow

1. User registers → password is bcrypt-hashed before it ever touches the database.
2. User logs in → backend verifies the hash, issues an access token (15 min) and refresh token (7 days).
3. Frontend stores both tokens, attaches the access token as `Authorization: Bearer <token>` on every API request.
4. When the access token expires, the next request gets a `401`; the Axios interceptor transparently calls `/auth/refresh`, stores the new tokens, and retries — the user notices nothing.
5. If the refresh token itself is invalid/expired, the interceptor clears storage and redirects to `/login`.
6. Logout clears both tokens client-side and redirects home.

## Folder changes

```
apps/backend/app/
├── models/user.py                    [new]
├── domain/
│   ├── exceptions.py                 [new]
│   └── schemas/{user,auth,token}.py  [new]
├── repositories/user_repository.py   [new]
├── services/auth_service.py          [new]
├── core/security.py                  [new]
├── db/{base,session}.py              [new]
└── api/v1/
    ├── dependencies.py               [new]
    └── endpoints/auth.py             [new]
apps/backend/alembic/                 [new — migrations]
apps/backend/tests/unit/test_auth.py  [new — 10 tests]

apps/frontend/src/
├── lib/api/{client,auth,tokenStorage}.ts  [new]
├── context/AuthContext.tsx                [new]
├── components/ProtectedRoute.tsx          [new]
└── app/{login,register,dashboard}/page.tsx [new]
```

## Setup instructions

```bash
cd apps/backend
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash; use venv/bin/activate on Mac/Linux
pip install -r requirements.txt

# Apply the users table migration (requires Postgres running — see infra/docker-compose.yml)
alembic upgrade head

uvicorn app.main:app --reload
```

```bash
cd apps/frontend
npm install
npm run dev
```

Visit http://localhost:3000/register to create an account, then http://localhost:3000/login to sign in — you'll land on the protected `/dashboard` page.

## Testing

Backend tests run against an in-memory SQLite database (via `aiosqlite`), so they need **no Postgres connection**:

```bash
cd apps/backend
pip install -r requirements-dev.txt
pytest -v
```

Verified locally: **11/11 tests passing**, covering registration, duplicate-email rejection, password validation, login (success + failure), the protected `/me` endpoint (missing token, invalid token, valid token), and refresh (success + rejecting an access token used as a refresh token). `ruff check .` and `mypy app` are both clean. Frontend `npm run build` and `npm run lint` both pass with the new pages.

## Git commit suggestion

```
feat(auth): add JWT authentication with register, login, refresh, and protected routes

Backend:
- Add User model, Alembic migration, and UserRepository
- Add AuthService: registration, authentication, access+refresh token issuance/rotation
- Add /auth/register, /auth/login, /auth/refresh, /auth/me endpoints
- Add get_current_user dependency for protecting future endpoints
- Add 11 passing tests against an in-memory SQLite DB

Frontend:
- Add AuthContext, Axios client with automatic token refresh on 401
- Add /login, /register, /dashboard (protected) pages
- Add ProtectedRoute wrapper for auth-gating future pages
```
