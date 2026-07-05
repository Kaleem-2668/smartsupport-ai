# ADR-002: JWT Token Strategy

**Status:** Accepted
**Date:** 2026-06-15

## Context

The application needed stateless authentication. Session-based auth would require a session store and add latency. Pure access tokens without refresh tokens would require frequent re-login.

## Decision

We use **dual JWT tokens** (access + refresh) with **rotation on refresh**:

- **Access token** — short-lived (15 min), sent on every API request as `Authorization: Bearer`
- **Refresh token** — long-lived (7 days), only used to obtain new token pairs
- **Token type claim** — each JWT has a `type` claim distinguishing access from refresh tokens
- **Rotation** — on every refresh, both tokens are reissued (old refresh token expires)

**Why not:**
- **Single JWT** — forces trade-off between security (short expiry = frequent re-login) and UX (long expiry = large blast radius)
- **Session cookies** — requires server-side state, adds latency, complicates mobile/API clients
- **OAuth2** — overkill for a single-party app (no third-party auth providers)

## Consequences

**Positive:**
- Stateless — no database lookup per request (just JWT decode)
- Refresh token rotation shrinks the window a stolen refresh token is useful
- Token type validation prevents access tokens from being used as refresh tokens
- Frontend Axios interceptor handles transparent refresh — users don't notice expired tokens

**Trade-offs:**
- JWT invalidation before expiry requires a blocklist (not implemented — acceptable for v1)
- Client must manage two tokens (access + refresh) in localStorage
