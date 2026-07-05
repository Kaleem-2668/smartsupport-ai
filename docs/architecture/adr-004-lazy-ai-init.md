# ADR-004: Lazy AI Service Initialization

**Status:** Accepted
**Date:** 2026-07-05

## Context

`ChatService` depends on `EmbeddingService`, `ChromaService`, and `LLMService`, all of which require external infrastructure (OpenAI API keys, running ChromaDB instance). Read-only endpoints like listing conversations and messages don't need AI services at all.

## Decision

**Lazy initialization** — `ChatService` constructs its AI-dependent services inside `ask()`, not in `__init__`:

```python
class ChatService:
    def __init__(self, conversation_repository, message_repository):
        self._conversations = conversation_repository
        self._messages = message_repository
        self._embedder: EmbeddingService | None = None
        self._chroma: ChromaService | None = None
        self._llm: LLMService | None = None

    def _ensure_ai_services(self) -> None:
        if self._embedder is None:
            self._embedder = EmbeddingService()
        if self._chroma is None:
            self._chroma = ChromaService()
        if self._llm is None:
            self._llm = LLMService()
```

**Why not:**
- **Eager initialization** — the chat endpoint would fail on startup if AI_API_KEY isn't set or ChromaDB isn't running, even if you only want to list conversations
- **Factory/dependency injection container** — adds complexity without proportional benefit at this scale
- **Optional dependencies with try/except** — hides initialization failures; lazy init with explicit `_ensure_ai_services()` call makes the dependency boundary clear

## Consequences

**Positive:**
- Read-only endpoints work without AI infrastructure
- Tests can monkeypatch `_ensure_ai_services` to stub out all three services at once
- Clear boundary between "needs AI" and "doesn't need AI" code paths

**Trade-offs:**
- First chat request is slightly slower (initializes all three services)
- Services are re-initialized if `ChatService` is reconstructed (per-request in current architecture)
- Service initialization errors happen at request time, not at startup
