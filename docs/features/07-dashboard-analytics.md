# Feature 7: Dashboard & Analytics

## Summary

Added a dashboard endpoint and a rich analytics page giving users a real-time overview of their platform usage: document counts, embedding chunks, knowledge bases, conversations, document status breakdown, and a recent activity feed.

## Backend Changes

### New Files
- `app/domain/schemas/dashboard.py` — Pydantic response models (`DashboardStats`, `DocumentStats`, `KnowledgeBaseStats`, `ConversationStats`, `RecentActivity`)
- `app/services/dashboard_service.py` — `DashboardService` aggregates counts across documents, knowledge bases, and conversations via SQLAlchemy aggregate queries
- `app/api/v1/endpoints/dashboard.py` — Single `GET /api/v1/dashboard/stats` endpoint (authenticated)

### Modified Files
- `app/api/v1/router.py` — Registered the new dashboard router

### API Design

```
GET /api/v1/dashboard/stats
Authorization: Bearer <access_token>

Response 200:
{
  "documents": {
    "total": 12,
    "by_status": { "ready": 8, "processing": 1, "error": 1 },
    "total_chunks": 342,
    "total_size_bytes": 5242880
  },
  "knowledge_bases": { "total": 3 },
  "conversations": { "total": 27, "total_messages": 156 },
  "recent_activity": [
    { "id": "...", "type": "document", "title": "guide.pdf", "timestamp": "..." },
    { "id": "...", "type": "conversation", "title": "How do I reset my password?", "timestamp": "..." }
  ]
}
```

## Frontend Changes

### New Files
- `src/lib/api/dashboard.ts` — API client for `GET /api/v1/dashboard/stats`

### Modified Files
- `src/app/dashboard/page.tsx` — Complete rewrite with:
  - 4 stat cards (Documents, Embeddings, Knowledge Bases, Conversations) with icons and sub-labels
  - Document status breakdown with color-coded status dots
  - 3 quick-action cards (Open Chat, Upload Document, Knowledge Bases) with hover effects
  - Recent activity feed merging documents and conversations sorted by recency
  - Loading spinner and error state handling
  - Relative time formatting ("5m ago", "2h ago", "3d ago")

## Design Decisions

- **Single endpoint** — One `GET /stats` call avoids waterfall requests on page load; the dashboard is a read-only overview so aggregation in Python is fine at current scale.
- **Relative timestamps** — Activity feed uses human-readable relative times ("5m ago") instead of raw dates for quicker scanning.
- **Status breakdown** — Documents show status badges with animated pulse on "processing" status for real-time feedback feel.
- **Quick actions** — Primary actions surfaced as cards with hover scale transitions to reduce navigation friction.
