import uuid

import pytest

from app.services.chat_service import ChatService


class _FakeEmbedder:
    async def generate_query_embedding(self, query: str) -> list[float]:
        return [0.0] * 5


class _FakeChroma:
    def search_embeddings(self, user_id, query_embedding, n_results=4):
        return {"documents": [[]], "metadatas": [[]]}


class _FakeLLM:
    async def generate_answer(self, system_prompt: str, question: str) -> str:
        return f"Fake answer to: {question}"


@pytest.fixture(autouse=True)
def stub_ai_services(monkeypatch):
    """Every test in this module runs without real AI_API_KEY/ChromaDB/OpenAI calls."""

    def fake_ensure(self) -> None:
        self._embedder = _FakeEmbedder()
        self._chroma = _FakeChroma()
        self._llm = _FakeLLM()

    monkeypatch.setattr(ChatService, "_ensure_ai_services", fake_ensure)


def test_ask_requires_authentication(client):
    response = client.post("/api/v1/chat", json={"question": "What is your refund policy?"})
    assert response.status_code == 401


def test_ask_creates_conversation_and_answer(client, auth_headers):
    response = client.post(
        "/api/v1/chat", headers=auth_headers, json={"question": "What is your refund policy?"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["message"]["role"] == "assistant"
    assert "Fake answer" in body["message"]["content"]
    assert body["conversation_id"] == body["message"]["conversation_id"]


def test_ask_reuses_existing_conversation(client, auth_headers):
    first = client.post(
        "/api/v1/chat", headers=auth_headers, json={"question": "First question"}
    ).json()
    conversation_id = first["conversation_id"]

    second = client.post(
        "/api/v1/chat",
        headers=auth_headers,
        json={"question": "Follow-up question", "conversation_id": conversation_id},
    ).json()
    assert second["conversation_id"] == conversation_id


def test_ask_with_unknown_conversation_returns_404(client, auth_headers):
    response = client.post(
        "/api/v1/chat",
        headers=auth_headers,
        json={"question": "hi", "conversation_id": str(uuid.uuid4())},
    )
    assert response.status_code == 404


def test_list_conversations_requires_authentication(client):
    response = client.get("/api/v1/conversations")
    assert response.status_code == 401


def test_list_conversations_empty(client, auth_headers):
    response = client.get("/api/v1/conversations", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_list_conversations_after_asking(client, auth_headers):
    client.post("/api/v1/chat", headers=auth_headers, json={"question": "Hello there"})
    response = client.get("/api/v1/conversations", headers=auth_headers)
    assert response.status_code == 200
    conversations = response.json()
    assert len(conversations) == 1
    assert conversations[0]["title"] == "Hello there"


def test_list_conversation_messages(client, auth_headers):
    ask_response = client.post(
        "/api/v1/chat", headers=auth_headers, json={"question": "Hello there"}
    ).json()
    conversation_id = ask_response["conversation_id"]

    response = client.get(f"/api/v1/conversations/{conversation_id}/messages", headers=auth_headers)
    assert response.status_code == 200
    messages = response.json()
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


def test_list_messages_for_unknown_conversation_returns_404(client, auth_headers):
    response = client.get(f"/api/v1/conversations/{uuid.uuid4()}/messages", headers=auth_headers)
    assert response.status_code == 404


def test_delete_conversation(client, auth_headers):
    ask_response = client.post(
        "/api/v1/chat", headers=auth_headers, json={"question": "Hello there"}
    ).json()
    conversation_id = ask_response["conversation_id"]

    response = client.delete(f"/api/v1/conversations/{conversation_id}", headers=auth_headers)
    assert response.status_code == 204

    get_response = client.get(
        f"/api/v1/conversations/{conversation_id}/messages", headers=auth_headers
    )
    assert get_response.status_code == 404


def test_cannot_access_another_users_conversation(client, auth_headers):
    ask_response = client.post(
        "/api/v1/chat", headers=auth_headers, json={"question": "Hello there"}
    ).json()
    conversation_id = ask_response["conversation_id"]

    client.post(
        "/api/v1/auth/register",
        json={
            "email": "other@example.com",
            "password": "testpassword123",
            "full_name": "Other User",
        },
    )
    other_login = client.post(
        "/api/v1/auth/login", json={"email": "other@example.com", "password": "testpassword123"}
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    response = client.get(
        f"/api/v1/conversations/{conversation_id}/messages", headers=other_headers
    )
    assert response.status_code == 404


def test_ask_with_knowledge_base_id(client, auth_headers):
    """Test that chat accepts a knowledge_base_id parameter."""
    response = client.post(
        "/api/v1/chat",
        headers=auth_headers,
        json={"question": "What is the return policy?", "knowledge_base_id": str(uuid.uuid4())},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["message"]["role"] == "assistant"
    assert "Fake answer" in body["message"]["content"]


def test_conversations_isolation_between_users(client, auth_headers):
    """User A should not see User B's conversations in the list."""
    # User A asks a question
    client.post("/api/v1/chat", headers=auth_headers, json={"question": "Hello from A"})

    # Register User B
    client.post(
        "/api/v1/auth/register",
        json={"email": "convo_b@example.com", "password": "testpassword123"},
    )
    login_b = client.post(
        "/api/v1/auth/login", json={"email": "convo_b@example.com", "password": "testpassword123"}
    )
    headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}

    # User A has 1 conversation
    response_a = client.get("/api/v1/conversations", headers=auth_headers)
    assert len(response_a.json()) == 1

    # User B has 0 conversations
    response_b = client.get("/api/v1/conversations", headers=headers_b)
    assert len(response_b.json()) == 0
