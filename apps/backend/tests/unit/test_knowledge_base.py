"""Tests for knowledge base HTTP endpoints."""

import uuid


def _register_and_login(client, email="kb@example.com"):
    """Helper to register a user and return auth headers."""
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpassword123", "full_name": "KB User"},
    )
    login_response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "testpassword123"}
    )
    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}


def test_create_knowledge_base(client):
    headers = _register_and_login(client)
    response = client.post(
        "/api/v1/knowledge-bases",
        headers=headers,
        json={"name": "Product Docs", "description": "Product documentation"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Product Docs"
    assert body["description"] == "Product documentation"
    assert "id" in body
    assert "created_at" in body


def test_create_knowledge_base_requires_authentication(client):
    response = client.post(
        "/api/v1/knowledge-bases",
        json={"name": "Test"},
    )
    assert response.status_code == 401


def test_list_knowledge_bases_empty(client):
    headers = _register_and_login(client)
    response = client.get("/api/v1/knowledge-bases", headers=headers)

    assert response.status_code == 200
    assert response.json() == []


def test_list_knowledge_bases(client):
    headers = _register_and_login(client)

    client.post(
        "/api/v1/knowledge-bases",
        headers=headers,
        json={"name": "KB 1"},
    )
    client.post(
        "/api/v1/knowledge-bases",
        headers=headers,
        json={"name": "KB 2"},
    )

    response = client.get("/api/v1/knowledge-bases", headers=headers)
    assert response.status_code == 200
    kbs = response.json()
    assert len(kbs) == 2
    names = {kb["name"] for kb in kbs}
    assert "KB 1" in names
    assert "KB 2" in names


def test_get_knowledge_base(client):
    headers = _register_and_login(client)

    create_response = client.post(
        "/api/v1/knowledge-bases",
        headers=headers,
        json={"name": "My KB", "description": "Description"},
    )
    kb_id = create_response.json()["id"]

    response = client.get(f"/api/v1/knowledge-bases/{kb_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["name"] == "My KB"


def test_get_knowledge_base_not_found(client):
    headers = _register_and_login(client)
    response = client.get(f"/api/v1/knowledge-bases/{uuid.uuid4()}", headers=headers)
    assert response.status_code == 404


def test_update_knowledge_base(client):
    headers = _register_and_login(client)

    create_response = client.post(
        "/api/v1/knowledge-bases",
        headers=headers,
        json={"name": "Old Name", "description": "Old description"},
    )
    kb_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/knowledge-bases/{kb_id}",
        headers=headers,
        json={"name": "New Name", "description": "New description"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"
    assert response.json()["description"] == "New description"


def test_update_knowledge_base_partial(client):
    headers = _register_and_login(client)

    create_response = client.post(
        "/api/v1/knowledge-bases",
        headers=headers,
        json={"name": "Keep Desc", "description": "Should stay"},
    )
    kb_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/knowledge-bases/{kb_id}",
        headers=headers,
        json={"name": "Changed Name"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Changed Name"
    assert response.json()["description"] == "Should stay"


def test_delete_knowledge_base(client):
    headers = _register_and_login(client)

    create_response = client.post(
        "/api/v1/knowledge-bases",
        headers=headers,
        json={"name": "To Delete"},
    )
    kb_id = create_response.json()["id"]

    response = client.delete(f"/api/v1/knowledge-bases/{kb_id}", headers=headers)
    assert response.status_code == 204

    # Verify it's gone
    get_response = client.get(f"/api/v1/knowledge-bases/{kb_id}", headers=headers)
    assert get_response.status_code == 404


def test_delete_knowledge_base_not_found(client):
    headers = _register_and_login(client)
    response = client.delete(f"/api/v1/knowledge-bases/{uuid.uuid4()}", headers=headers)
    assert response.status_code == 404


def test_cannot_access_other_users_knowledge_base(client):
    """User A should not be able to access User B's knowledge base."""
    headers_a = _register_and_login(client, email="kba@example.com")
    headers_b = _register_and_login(client, email="kbb@example.com")

    # User A creates a KB
    create_response = client.post(
        "/api/v1/knowledge-bases",
        headers=headers_a,
        json={"name": "Private KB"},
    )
    kb_id = create_response.json()["id"]

    # User B tries to get it
    response = client.get(f"/api/v1/knowledge-bases/{kb_id}", headers=headers_b)
    assert response.status_code == 403

    # User B tries to update it
    response = client.patch(
        f"/api/v1/knowledge-bases/{kb_id}",
        headers=headers_b,
        json={"name": "Hacked"},
    )
    assert response.status_code == 403

    # User B tries to delete it
    response = client.delete(f"/api/v1/knowledge-bases/{kb_id}", headers=headers_b)
    assert response.status_code == 403


def test_list_knowledge_bases_isolation(client):
    """Each user should only see their own knowledge bases."""
    headers_a = _register_and_login(client, email="iso_a@example.com")
    headers_b = _register_and_login(client, email="iso_b@example.com")

    # User A creates 2 KBs
    client.post("/api/v1/knowledge-bases", headers=headers_a, json={"name": "A1"})
    client.post("/api/v1/knowledge-bases", headers=headers_a, json={"name": "A2"})

    # User B creates 1 KB
    client.post("/api/v1/knowledge-bases", headers=headers_b, json={"name": "B1"})

    # User A sees only their 2
    response_a = client.get("/api/v1/knowledge-bases", headers=headers_a)
    assert len(response_a.json()) == 2

    # User B sees only their 1
    response_b = client.get("/api/v1/knowledge-bases", headers=headers_b)
    assert len(response_b.json()) == 1
