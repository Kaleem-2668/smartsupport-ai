"""Tests for the dashboard endpoint."""

import io

from app.services.chat_service import ChatService


class _FakeEmbedder:
    async def generate_query_embedding(self, query: str) -> list[float]:
        return [0.0] * 5


class _FakeChroma:
    def search_embeddings(self, user_id, query_embedding, n_results=4, knowledge_base_id=None):
        return {"documents": [[]], "metadatas": [[]]}


class _FakeLLM:
    async def generate_answer(self, system_prompt: str, question: str) -> str:
        return f"Fake answer to: {question}"


def _register_and_login(client, email="dash@example.com"):
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpassword123", "full_name": "Dash User"},
    )
    login_response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "testpassword123"}
    )
    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}


def test_dashboard_stats_requires_authentication(client):
    response = client.get("/api/v1/dashboard/stats")
    assert response.status_code == 401


def test_dashboard_stats_empty_state(client):
    headers = _register_and_login(client)
    response = client.get("/api/v1/dashboard/stats", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["documents"]["total"] == 0
    assert body["documents"]["total_chunks"] == 0
    assert body["documents"]["total_size_bytes"] == 0
    assert body["documents"]["by_status"] == {}
    assert body["knowledge_bases"]["total"] == 0
    assert body["conversations"]["total"] == 0
    assert body["conversations"]["total_messages"] == 0
    assert body["recent_activity"] == []


def test_dashboard_stats_with_documents(client):
    headers = _register_and_login(client)

    # Upload two documents
    for name in ["doc1.txt", "doc2.txt"]:
        files = {"file": (name, io.BytesIO(b"test content"), "text/plain")}
        client.post("/api/v1/documents/upload", headers=headers, files=files)

    response = client.get("/api/v1/dashboard/stats", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["documents"]["total"] == 2
    assert body["documents"]["by_status"]["ready"] == 2
    assert body["documents"]["total_size_bytes"] > 0


def test_dashboard_stats_with_knowledge_bases(client):
    headers = _register_and_login(client)

    client.post(
        "/api/v1/knowledge-bases",
        headers=headers,
        json={"name": "Product Docs", "description": "Product documentation"},
    )
    client.post("/api/v1/knowledge-bases", headers=headers, json={"name": "FAQ"})

    response = client.get("/api/v1/dashboard/stats", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["knowledge_bases"]["total"] == 2


def test_dashboard_stats_with_conversations(client):
    from unittest.mock import patch

    headers = _register_and_login(client)

    def fake_ensure(self):
        self._embedder = _FakeEmbedder()
        self._chroma = _FakeChroma()
        self._llm = _FakeLLM()

    with patch.object(ChatService, "_ensure_ai_services", fake_ensure):
        # Create 2 conversations
        client.post("/api/v1/chat", headers=headers, json={"question": "What is the refund policy?"})
        client.post(
            "/api/v1/chat",
            headers=headers,
            json={"question": "How do I reset my password?", "conversation_id": None},
        )

    response = client.get("/api/v1/dashboard/stats", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["conversations"]["total"] == 2
    assert body["conversations"]["total_messages"] == 4  # 2 user + 2 assistant


def test_dashboard_stats_recent_activity(client):
    headers = _register_and_login(client)

    # Upload a document
    files = {"file": ("activity.txt", io.BytesIO(b"content"), "text/plain")}
    client.post("/api/v1/documents/upload", headers=headers, files=files)

    response = client.get("/api/v1/dashboard/stats", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body["recent_activity"]) == 1
    assert body["recent_activity"][0]["type"] == "document"
    assert body["recent_activity"][0]["title"] == "activity.txt"


def test_dashboard_stats_isolation_between_users(client):
    """User A's stats should not include User B's data."""
    headers_a = _register_and_login(client, email="usera@example.com")
    headers_b = _register_and_login(client, email="userb@example.com")

    # User A uploads documents
    for name in ["a1.txt", "a2.txt", "a3.txt"]:
        files = {"file": (name, io.BytesIO(b"content"), "text/plain")}
        client.post("/api/v1/documents/upload", headers=headers_a, files=files)

    # User B uploads one document
    files = {"file": ("b1.txt", io.BytesIO(b"content"), "text/plain")}
    client.post("/api/v1/documents/upload", headers=headers_b, files=files)

    # User A should only see 3 docs
    response_a = client.get("/api/v1/dashboard/stats", headers=headers_a)
    assert response_a.json()["documents"]["total"] == 3

    # User B should only see 1 doc
    response_b = client.get("/api/v1/dashboard/stats", headers=headers_b)
    assert response_b.json()["documents"]["total"] == 1
