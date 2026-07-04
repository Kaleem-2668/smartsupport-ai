# Feature 5: RAG Chat

## Architecture

**Backend** — clean layering, consistent with previous features:
- `models/conversation.py` — Conversation: belongs to a user, has an optional auto-generated title
- `models/message.py` — Message: belongs to a conversation, role (`user`/`assistant`), content, optional `sources`
- `repositories/conversation_repository.py`, `repositories/message_repository.py` — data access
- `services/llm_service.py` — Wraps a LangChain chat model (`ChatOpenAI`), provider-agnostic like `EmbeddingService`
- `services/chat_service.py` — Orchestrates the RAG pipeline: embed question → retrieve top-k chunks from ChromaDB → build a grounded system prompt → call the LLM → persist both turns
- `api/v1/endpoints/chat.py` — `POST /chat`, `GET /conversations`, `GET /conversations/{id}/messages`, `DELETE /conversations/{id}`

**Design choice — lazy AI service initialization:** `ChatService` only constructs `EmbeddingService`, `ChromaService`, and `LLMService` inside `ask()`, not in `__init__`. This means listing conversations/messages never requires `AI_API_KEY` or a live ChromaDB connection, and made the read endpoints fully unit-testable without external dependencies.

**RAG Pipeline (per question):**
1. Persist the user's message immediately
2. Generate a query embedding (`EmbeddingService`)
3. Retrieve top-k similar chunks from the user's ChromaDB collection (`chat_retrieval_top_k`, default 4)
4. Build a system prompt instructing the model to answer only from the retrieved context, and to say so if the context is insufficient
5. Call the chat model (`ai_chat_model`, default `gpt-4o-mini`) via LangChain
6. Persist the assistant's reply along with the source chunks it was grounded in
7. Touch the conversation's `updated_at` so active conversations sort first

**Conversations:**
- A new conversation is created automatically on the first question (title = first 80 chars of the question)
- Passing `conversation_id` on subsequent requests continues that conversation
- Users can only access their own conversations (403/404 on cross-user access)

**Frontend** — Chat page (`/chat`):
- Sidebar listing conversations, newest-active first, with delete
- "New chat" button to start a fresh conversation
- Message thread with optimistic user-message rendering, "Thinking…" indicator, and a note on how many document chunks an answer was sourced from
- Enter to send, Shift+Enter for newline
- Linked from the dashboard via an "Open Chat" button

## API endpoints

| Method | Path | Auth required | Purpose |
|---|---|---|---|
| POST | `/api/v1/chat` | Yes | Ask a question. Body: `{question, conversation_id?}`. Creates a conversation if `conversation_id` is omitted. |
| GET | `/api/v1/conversations` | Yes | List the current user's conversations, most recently active first. |
| GET | `/api/v1/conversations/{id}/messages` | Yes | List all messages in a conversation, oldest first. |
| DELETE | `/api/v1/conversations/{id}` | Yes | Delete a conversation and all its messages. |

## Configuration

**New environment variables:**
- `AI_CHAT_MODEL` — Chat completion model (default: `gpt-4o-mini`)
- `AI_CHAT_TEMPERATURE` — Sampling temperature (default: `0.2`)
- `CHAT_RETRIEVAL_TOP_K` — Number of chunks retrieved per question (default: `4`)

Reuses the existing `AI_PROVIDER` / `AI_API_KEY` settings from Feature 4.

## Folder changes

```
apps/backend/
├── .env.example                                     [updated - added chat settings]
├── alembic/versions/
│   └── 0004_create_conversations_and_messages_tables.py  [new]
├── app/
│   ├── core/config.py                               [updated - added chat config]
│   ├── domain/exceptions.py                         [updated - ConversationNotFoundError, LLMError]
│   ├── domain/schemas/chat.py                       [new]
│   ├── models/conversation.py                       [new]
│   ├── models/message.py                            [new]
│   ├── repositories/conversation_repository.py      [new]
│   ├── repositories/message_repository.py           [new]
│   ├── services/llm_service.py                      [new]
│   ├── services/chat_service.py                     [new]
│   └── api/v1/
│       ├── router.py                                [updated - registered chat router]
│       └── endpoints/chat.py                        [new]
└── tests/
    ├── conftest.py                                  [updated - register conversation/message models]
    └── unit/test_chat.py                            [new]

apps/frontend/src/
├── lib/api/chat.ts                                  [new]
├── app/chat/page.tsx                                [new]
└── app/dashboard/page.tsx                           [updated - "Open Chat" link]
```

## Setup instructions

```bash
cd apps/backend

# Apply the conversations/messages migration
alembic upgrade head

# AI_API_KEY should already be set from Feature 4; chat reuses it
uvicorn app.main:app --reload
```

```bash
cd apps/frontend
npm run dev
```

## Usage

1. Upload and process at least one document (Features 3–4)
2. Navigate to `/chat`
3. Ask a question — a new conversation is created automatically
4. Continue asking follow-ups in the same conversation, or start a "New chat"
5. Answers indicate how many document chunks they were sourced from

## Testing

Automated tests (`tests/unit/test_chat.py`) stub out `EmbeddingService`, `ChromaService`, and `LLMService` via a `ChatService._ensure_ai_services` monkeypatch, so the full pipeline — auth guards, conversation creation/reuse, message ordering, cross-user access control, deletion — is covered without real OpenAI/ChromaDB calls.

```bash
cd apps/backend
python -m pytest tests/unit/test_chat.py -v
```

## Error Handling

- **Unknown/foreign conversation_id**: 404 `ConversationNotFoundError`
- **LLM call failure**: 502 `LLMError`
- **No relevant chunks found**: the model is told explicitly that no context was found and instructed to say so, rather than guessing

## Performance Considerations

- Chat completion is synchronous — for production, consider streaming responses (see Feature 4's note on background processing for a similar tradeoff)
- Retrieval and generation happen sequentially per request; there's no caching of repeated questions

## Git commit suggestion

```
feat(chat): add RAG chat with conversations and message history

Backend:
- Add Conversation and Message models with Alembic migration
- Add LLMService wrapping LangChain ChatOpenAI, provider-agnostic like EmbeddingService
- Add ChatService orchestrating retrieval -> grounded prompt -> generation -> persistence
- Lazily initialize AI-dependent services so read-only endpoints don't need AI_API_KEY/ChromaDB
- Add POST /chat, GET /conversations, GET /conversations/{id}/messages, DELETE /conversations/{id}
- Add ConversationNotFoundError and LLMError domain exceptions
- Add AI_CHAT_MODEL, AI_CHAT_TEMPERATURE, CHAT_RETRIEVAL_TOP_K settings
- Add unit tests with stubbed AI services (no external calls)

Frontend:
- Add chat API client (askQuestion, getConversations, getConversationMessages, deleteConversation)
- Add /chat page with conversation sidebar and message thread
- Link chat page from the dashboard
```
