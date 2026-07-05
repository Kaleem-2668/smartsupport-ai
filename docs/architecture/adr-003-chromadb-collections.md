# ADR-003: ChromaDB Collection Strategy

**Status:** Accepted
**Date:** 2026-07-01

## Context

The application stores document embeddings in ChromaDB. We needed to decide how to organize embeddings for user isolation and knowledge base scoping.

## Decision

Use **per-user and per-knowledge-base collections**:

- **Default (no KB):** `user_{user_id}` — backward compatible with the initial embedding pipeline
- **With KB:** `kb_{knowledge_base_id}` — isolates documents by knowledge base
- **Collection metadata:** `{"hnsw:space": "cosine"}` — cosine similarity for search
- **Chunk metadata:** `{document_id, chunk_index, user_id}` — enables document-level operations

**Why not:**
- **Single collection with metadata filtering** — simpler but slower at scale; ChromaDB's filtering on large collections is less efficient than collection-level isolation
- **Per-document collections** — too many collections; overhead of creating/deleting for every document
- **Metadata-only isolation** — no structural separation; risk of data leakage if metadata query is wrong
- **Separate vector databases** — overkill; ChromaDB handles multi-collection well

## Consequences

**Positive:**
- Strong data isolation — no risk of cross-user data leakage
- Knowledge base isolation enables targeted RAG queries
- Backward compatible — existing data in user collections continues to work
- Easy to delete all data for a user/KB by dropping the collection

**Trade-offs:**
- More collections to manage (one per user + per KB)
- Chat without KB specified can't search across KBs — it falls back to the user collection (legacy behavior)
- KB deletion needs to also clean up the ChromaDB collection (not yet implemented)
