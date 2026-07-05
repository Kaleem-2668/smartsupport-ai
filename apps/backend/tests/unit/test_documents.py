import io
import uuid


def test_upload_document_requires_authentication(client):
    """Test that uploading a document requires authentication."""
    file_content = b"test content"
    files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
    response = client.post("/api/v1/documents/upload", files=files)
    assert response.status_code == 401


def test_upload_document_success(client, auth_headers):
    """Test successful document upload."""
    file_content = b"test content"
    files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
    response = client.post("/api/v1/documents/upload", headers=auth_headers, files=files)
    assert response.status_code == 201
    body = response.json()
    assert body["original_filename"] == "test.txt"
    assert body["file_size"] == len(file_content)
    assert body["status"] == "ready"


def test_upload_document_invalid_mime_type(client, auth_headers):
    """Test that uploading an invalid file type is rejected."""
    file_content = b"test content"
    files = {"file": ("test.exe", io.BytesIO(file_content), "application/x-msdownload")}
    response = client.post("/api/v1/documents/upload", headers=auth_headers, files=files)
    assert response.status_code == 422


def test_list_documents_requires_authentication(client):
    """Test that listing documents requires authentication."""
    response = client.get("/api/v1/documents")
    assert response.status_code == 401


def test_list_documents_empty(client, auth_headers):
    """Test listing documents when user has none."""
    response = client.get("/api/v1/documents", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_list_documents_with_files(client, auth_headers):
    """Test listing documents after uploading."""
    # Upload a document first
    file_content = b"test content"
    files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
    client.post("/api/v1/documents/upload", headers=auth_headers, files=files)

    # List documents
    response = client.get("/api/v1/documents", headers=auth_headers)
    assert response.status_code == 200
    documents = response.json()
    assert len(documents) == 1
    assert documents[0]["original_filename"] == "test.txt"


def test_get_document_requires_authentication(client):
    """Test that getting a document requires authentication."""
    document_id = uuid.uuid4()
    response = client.get(f"/api/v1/documents/{document_id}")
    assert response.status_code == 401


def test_get_document_not_found(client, auth_headers):
    """Test getting a non-existent document."""
    document_id = uuid.uuid4()
    response = client.get(f"/api/v1/documents/{document_id}", headers=auth_headers)
    assert response.status_code == 404


def test_delete_document_requires_authentication(client):
    """Test that deleting a document requires authentication."""
    document_id = uuid.uuid4()
    response = client.delete(f"/api/v1/documents/{document_id}")
    assert response.status_code == 401


def test_delete_document_success(client, auth_headers):
    """Test successful document deletion."""
    # Upload a document first
    file_content = b"test content"
    files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
    upload_response = client.post("/api/v1/documents/upload", headers=auth_headers, files=files)
    document_id = upload_response.json()["id"]

    # Delete the document
    response = client.delete(f"/api/v1/documents/{document_id}", headers=auth_headers)
    assert response.status_code == 204

    # Verify it's deleted
    get_response = client.get(f"/api/v1/documents/{document_id}", headers=auth_headers)
    assert get_response.status_code == 404


def test_delete_document_not_found(client, auth_headers):
    """Test deleting a non-existent document."""
    document_id = uuid.uuid4()
    response = client.delete(f"/api/v1/documents/{document_id}", headers=auth_headers)
    assert response.status_code == 404


# --- Cross-user isolation tests ---


def _register_and_login(client, email):
    """Helper to register a user and return auth headers."""
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpassword123", "full_name": "User"},
    )
    login_response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "testpassword123"}
    )
    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}


def test_cannot_access_other_users_document(client):
    """User A should not be able to get User B's document."""
    headers_a = _register_and_login(client, "docuser_a@example.com")
    headers_b = _register_and_login(client, "docuser_b@example.com")

    # User A uploads
    files = {"file": ("a.txt", io.BytesIO(b"secret"), "text/plain")}
    doc_id = client.post("/api/v1/documents/upload", headers=headers_a, files=files).json()["id"]

    # User B tries to get it
    response = client.get(f"/api/v1/documents/{doc_id}", headers=headers_b)
    assert response.status_code == 403


def test_cannot_delete_other_users_document(client):
    """User A should not be able to delete User B's document."""
    headers_a = _register_and_login(client, "deluser_a@example.com")
    headers_b = _register_and_login(client, "deluser_b@example.com")

    files = {"file": ("a.txt", io.BytesIO(b"secret"), "text/plain")}
    doc_id = client.post("/api/v1/documents/upload", headers=headers_a, files=files).json()["id"]

    response = client.delete(f"/api/v1/documents/{doc_id}", headers=headers_b)
    assert response.status_code == 403


def test_list_documents_isolation(client):
    """Each user should only see their own documents."""
    headers_a = _register_and_login(client, "iso_doc_a@example.com")
    headers_b = _register_and_login(client, "iso_doc_b@example.com")

    # User A uploads 2 docs
    for name in ["a1.txt", "a2.txt"]:
        files = {"file": (name, io.BytesIO(b"content"), "text/plain")}
        client.post("/api/v1/documents/upload", headers=headers_a, files=files)

    # User B uploads 1 doc
    files = {"file": ("b1.txt", io.BytesIO(b"content"), "text/plain")}
    client.post("/api/v1/documents/upload", headers=headers_b, files=files)

    # User A sees only 2
    response_a = client.get("/api/v1/documents", headers=headers_a)
    assert len(response_a.json()) == 2

    # User B sees only 1
    response_b = client.get("/api/v1/documents", headers=headers_b)
    assert len(response_b.json()) == 1


# --- Document processing tests ---


def test_process_document_requires_authentication(client):
    """Test that processing a document requires authentication."""
    document_id = uuid.uuid4()
    response = client.post(f"/api/v1/documents/{document_id}/process")
    assert response.status_code == 401


def test_process_document_not_found(client, auth_headers):
    """Test processing a non-existent document."""
    document_id = uuid.uuid4()
    response = client.post(f"/api/v1/documents/{document_id}/process", headers=auth_headers)
    assert response.status_code == 422


def test_process_document_cannot_process_other_users(client):
    """User should not be able to process another user's document."""
    headers_a = _register_and_login(client, "proc_a@example.com")
    headers_b = _register_and_login(client, "proc_b@example.com")

    files = {"file": ("a.txt", io.BytesIO(b"content"), "text/plain")}
    doc_id = client.post("/api/v1/documents/upload", headers=headers_a, files=files).json()["id"]

    response = client.post(f"/api/v1/documents/{doc_id}/process", headers=headers_b)
    assert response.status_code in (403, 422)  # Forbidden or invalid
