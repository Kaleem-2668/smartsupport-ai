import io
import uuid

from fastapi.testclient import TestClient

from app.main import create_app


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
