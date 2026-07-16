import uuid

import pytest

from app.services import auth_service as auth_service_module
from app.services.chat_service import ChatService


class _FakeEmbedder:
    async def generate_query_embedding(self, text: str) -> list[float]:
        return [0.1, 0.2, 0.3]


class _FakeChroma:
    def search_embeddings(self, user_id, query_embedding, n_results=4, knowledge_base_id=None):
        return {"documents": [[]], "metadatas": [[]]}


class _FakeLLM:
    async def generate_answer(self, system_prompt: str, question: str) -> str:
        return "A fake answer for stats testing."


@pytest.fixture()
def admin_headers(client, monkeypatch):
    """Create an admin user via the first-admin-email bootstrap and return auth headers."""
    monkeypatch.setattr(auth_service_module.settings, "first_admin_email", "admin@example.com")
    client.post(
        "/api/v1/auth/register",
        json={"email": "admin@example.com", "password": "adminpassword123", "full_name": "Admin"},
    )
    login = client.post(
        "/api/v1/auth/login", json={"email": "admin@example.com", "password": "adminpassword123"}
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_first_admin_email_bootstrap_promotes_matching_registration(client, monkeypatch):
    monkeypatch.setattr(auth_service_module.settings, "first_admin_email", "boss@example.com")
    client.post(
        "/api/v1/auth/register",
        json={"email": "boss@example.com", "password": "password12345"},
    )
    login = client.post(
        "/api/v1/auth/login", json={"email": "boss@example.com", "password": "password12345"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.json()["role"] == "admin"


def test_registration_defaults_to_user_role(client, auth_headers):
    me = client.get("/api/v1/auth/me", headers=auth_headers)
    assert me.json()["role"] == "user"


def test_non_admin_cannot_access_admin_stats(client, auth_headers):
    response = client.get("/api/v1/admin/stats", headers=auth_headers)
    assert response.status_code == 403


def test_admin_stats_requires_authentication(client):
    response = client.get("/api/v1/admin/stats")
    assert response.status_code == 401


def test_admin_can_view_stats(client, admin_headers, auth_headers, monkeypatch):
    # auth_headers registers a second (regular) user + a conversation, giving the
    # stats something real to count. Stubbed so this doesn't need a live ChromaDB.
    def fake_ensure(self) -> None:
        self._embedder = _FakeEmbedder()
        self._chroma = _FakeChroma()
        self._llm = _FakeLLM()

    monkeypatch.setattr(ChatService, "_ensure_ai_services", fake_ensure)
    client.post("/api/v1/chat", headers=auth_headers, json={"question": "Hello"})

    response = client.get("/api/v1/admin/stats", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total_users"] == 2
    assert body["total_conversations"] == 1
    assert "professional" in body["personality_breakdown"]


def test_admin_can_list_and_search_users(client, admin_headers, auth_headers):
    response = client.get("/api/v1/admin/users", headers=admin_headers)
    assert response.status_code == 200
    emails = {u["email"] for u in response.json()}
    assert {"admin@example.com", "test@example.com"} <= emails

    search_response = client.get("/api/v1/admin/users?search=test@", headers=admin_headers)
    assert [u["email"] for u in search_response.json()] == ["test@example.com"]


def test_non_admin_cannot_list_users(client, auth_headers):
    response = client.get("/api/v1/admin/users", headers=auth_headers)
    assert response.status_code == 403


def test_admin_can_deactivate_and_reactivate_a_user(client, admin_headers, auth_headers):
    users = client.get("/api/v1/admin/users", headers=admin_headers).json()
    target = next(u for u in users if u["email"] == "test@example.com")

    deactivate = client.patch(
        f"/api/v1/admin/users/{target['id']}", headers=admin_headers, json={"is_active": False}
    )
    assert deactivate.status_code == 200
    assert deactivate.json()["is_active"] is False

    # The deactivated user can no longer log in
    login_attempt = client.post(
        "/api/v1/auth/login", json={"email": "test@example.com", "password": "testpassword123"}
    )
    assert login_attempt.status_code in (400, 401, 403)

    reactivate = client.patch(
        f"/api/v1/admin/users/{target['id']}", headers=admin_headers, json={"is_active": True}
    )
    assert reactivate.json()["is_active"] is True


def test_admin_can_promote_a_user_to_admin(client, admin_headers, auth_headers):
    users = client.get("/api/v1/admin/users", headers=admin_headers).json()
    target = next(u for u in users if u["email"] == "test@example.com")

    response = client.patch(
        f"/api/v1/admin/users/{target['id']}", headers=admin_headers, json={"role": "admin"}
    )
    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_admin_cannot_demote_themselves(client, admin_headers):
    me = client.get("/api/v1/auth/me", headers=admin_headers).json()
    response = client.patch(
        f"/api/v1/admin/users/{me['id']}", headers=admin_headers, json={"role": "user"}
    )
    assert response.status_code == 400


def test_admin_cannot_deactivate_themselves(client, admin_headers):
    me = client.get("/api/v1/auth/me", headers=admin_headers).json()
    response = client.patch(
        f"/api/v1/admin/users/{me['id']}", headers=admin_headers, json={"is_active": False}
    )
    assert response.status_code == 400


def test_admin_cannot_delete_themselves(client, admin_headers):
    me = client.get("/api/v1/auth/me", headers=admin_headers).json()
    response = client.delete(f"/api/v1/admin/users/{me['id']}", headers=admin_headers)
    assert response.status_code == 400


def test_update_user_rejects_invalid_role(client, admin_headers, auth_headers):
    users = client.get("/api/v1/admin/users", headers=admin_headers).json()
    target = next(u for u in users if u["email"] == "test@example.com")
    response = client.patch(
        f"/api/v1/admin/users/{target['id']}", headers=admin_headers, json={"role": "superuser"}
    )
    assert response.status_code == 422


def test_update_user_requires_at_least_one_field(client, admin_headers, auth_headers):
    users = client.get("/api/v1/admin/users", headers=admin_headers).json()
    target = next(u for u in users if u["email"] == "test@example.com")
    response = client.patch(f"/api/v1/admin/users/{target['id']}", headers=admin_headers, json={})
    assert response.status_code == 422


def test_admin_can_delete_a_user(client, admin_headers, auth_headers):
    users = client.get("/api/v1/admin/users", headers=admin_headers).json()
    target = next(u for u in users if u["email"] == "test@example.com")

    response = client.delete(f"/api/v1/admin/users/{target['id']}", headers=admin_headers)
    assert response.status_code == 204

    remaining = client.get("/api/v1/admin/users", headers=admin_headers).json()
    assert all(u["email"] != "test@example.com" for u in remaining)


def test_non_admin_cannot_delete_users(client, auth_headers):
    response = client.delete(f"/api/v1/admin/users/{'0' * 8}-0000-0000-0000-{'0' * 12}", headers=auth_headers)
    assert response.status_code in (403, 422)


def test_admin_can_list_recent_conversations(client, admin_headers, auth_headers, monkeypatch):
    from app.services.chat_service import ChatService

    def fake_ensure(self) -> None:
        self._embedder = _FakeEmbedder()
        self._chroma = _FakeChroma()
        self._llm = _FakeLLM()

    monkeypatch.setattr(ChatService, "_ensure_ai_services", fake_ensure)
    client.post("/api/v1/chat", headers=auth_headers, json={"question": "Hello"})

    response = client.get("/api/v1/admin/conversations", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["user_email"] == "test@example.com"
    assert body[0]["message_count"] == 2  # user question + assistant answer


def test_non_admin_cannot_list_conversations(client, auth_headers):
    response = client.get("/api/v1/admin/conversations", headers=auth_headers)
    assert response.status_code == 403


def test_admin_can_delete_any_conversation(client, admin_headers, auth_headers, monkeypatch):
    from app.services.chat_service import ChatService

    def fake_ensure(self) -> None:
        self._embedder = _FakeEmbedder()
        self._chroma = _FakeChroma()
        self._llm = _FakeLLM()

    monkeypatch.setattr(ChatService, "_ensure_ai_services", fake_ensure)
    client.post("/api/v1/chat", headers=auth_headers, json={"question": "Hello"})

    conversations = client.get("/api/v1/admin/conversations", headers=admin_headers).json()
    target_id = conversations[0]["id"]

    response = client.delete(f"/api/v1/admin/conversations/{target_id}", headers=admin_headers)
    assert response.status_code == 204

    remaining = client.get("/api/v1/admin/conversations", headers=admin_headers).json()
    assert remaining == []


def test_admin_delete_conversation_not_found(client, admin_headers):
    response = client.delete(f"/api/v1/admin/conversations/{uuid.uuid4()}", headers=admin_headers)
    assert response.status_code == 404


def test_admin_can_list_recent_documents(client, admin_headers, auth_headers):
    import io

    client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        files={"file": ("policy.txt", io.BytesIO(b"content"), "text/plain")},
    )

    response = client.get("/api/v1/admin/documents", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["original_filename"] == "policy.txt"
    assert body[0]["user_email"] == "test@example.com"


def test_non_admin_cannot_list_documents(client, auth_headers):
    response = client.get("/api/v1/admin/documents", headers=auth_headers)
    assert response.status_code == 403


def test_admin_can_delete_any_document(client, admin_headers, auth_headers):
    import io

    upload = client.post(
        "/api/v1/documents/upload",
        headers=auth_headers,
        files={"file": ("policy.txt", io.BytesIO(b"content"), "text/plain")},
    )
    document_id = upload.json()["id"]

    response = client.delete(f"/api/v1/admin/documents/{document_id}", headers=admin_headers)
    assert response.status_code == 204

    remaining = client.get("/api/v1/admin/documents", headers=admin_headers).json()
    assert remaining == []


def test_admin_delete_document_not_found(client, admin_headers):
    response = client.delete(f"/api/v1/admin/documents/{uuid.uuid4()}", headers=admin_headers)
    assert response.status_code == 404
