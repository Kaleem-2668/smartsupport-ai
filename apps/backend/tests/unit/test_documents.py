import io
import uuid

from app.services.document_processing_service import _parse_intelligence_response


def test_parse_intelligence_response_valid_json():
    response = (
        '{"summary": "A short summary.", '
        '"suggested_questions": ["Q1?", "Q2?", ""]}'
    )
    result = _parse_intelligence_response(response)
    assert result == ("A short summary.", ["Q1?", "Q2?"])


def test_parse_intelligence_response_strips_markdown_fences():
    response = '```json\n{"summary": "Fenced summary.", "suggested_questions": ["Q1?"]}\n```'
    result = _parse_intelligence_response(response)
    assert result == ("Fenced summary.", ["Q1?"])


def test_parse_intelligence_response_rejects_garbage():
    assert _parse_intelligence_response("not json at all") is None
    assert _parse_intelligence_response('{"summary": ""}') is None
    assert _parse_intelligence_response('{"suggested_questions": ["Q1?"]}') is None


def test_parse_intelligence_response_caps_and_filters_questions():
    response = (
        '{"summary": "Summary.", '
        '"suggested_questions": ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", 42, null]}'
    )
    _, questions = _parse_intelligence_response(response)
    assert questions == ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"]


class _FakeEmbeddingService:
    async def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * 5 for _ in texts]


class _FakeChromaForProcessing:
    def add_embeddings(self, user_id, document_id, chunks, embeddings, knowledge_base_id=None):
        pass


class _FakeIntelligenceLLM:
    async def generate_answer(self, system_prompt: str, question: str) -> str:
        return (
            '{"summary": "Covers the refund and shipping policy.", '
            '"suggested_questions": ["What is the refund window?", "How long does shipping take?"]}'
        )


class _FailingLLM:
    async def generate_answer(self, system_prompt: str, question: str) -> str:
        raise RuntimeError("simulated Gemini rate limit")


class _GarbageLLM:
    async def generate_answer(self, system_prompt: str, question: str) -> str:
        return "Sure! Here's a summary: this document is about refunds."


def _upload_text_document(client, auth_headers, content: bytes = b"Refunds are accepted within 30 days of purchase. " * 20):
    files = {"file": ("policy.txt", io.BytesIO(content), "text/plain")}
    response = client.post("/api/v1/documents/upload", headers=auth_headers, files=files)
    return response.json()["id"]


def test_process_document_generates_summary_and_suggested_questions(
    client, auth_headers, monkeypatch
):
    monkeypatch.setattr(
        "app.services.document_processing_service.EmbeddingService", _FakeEmbeddingService
    )
    monkeypatch.setattr(
        "app.services.document_processing_service.ChromaService", _FakeChromaForProcessing
    )
    monkeypatch.setattr(
        "app.services.document_processing_service.LLMService", _FakeIntelligenceLLM
    )

    document_id = _upload_text_document(client, auth_headers)
    response = client.post(f"/api/v1/documents/{document_id}/process", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["chunk_count"] > 0
    assert body["summary"] == "Covers the refund and shipping policy."
    assert body["suggested_questions"] == [
        "What is the refund window?",
        "How long does shipping take?",
    ]


def test_process_document_survives_intelligence_generation_failure(
    client, auth_headers, monkeypatch
):
    """If the summary/questions LLM call fails, the document should still be marked
    ready with its embeddings intact — that's the critical path, and must not be
    undone by a failure in an optional enrichment step."""
    monkeypatch.setattr(
        "app.services.document_processing_service.EmbeddingService", _FakeEmbeddingService
    )
    monkeypatch.setattr(
        "app.services.document_processing_service.ChromaService", _FakeChromaForProcessing
    )
    monkeypatch.setattr("app.services.document_processing_service.LLMService", _FailingLLM)

    document_id = _upload_text_document(client, auth_headers)
    response = client.post(f"/api/v1/documents/{document_id}/process", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["chunk_count"] > 0
    assert body["summary"] is None
    assert body["suggested_questions"] is None


def test_process_document_survives_unparseable_intelligence_response(
    client, auth_headers, monkeypatch
):
    monkeypatch.setattr(
        "app.services.document_processing_service.EmbeddingService", _FakeEmbeddingService
    )
    monkeypatch.setattr(
        "app.services.document_processing_service.ChromaService", _FakeChromaForProcessing
    )
    monkeypatch.setattr("app.services.document_processing_service.LLMService", _GarbageLLM)

    document_id = _upload_text_document(client, auth_headers)
    response = client.post(f"/api/v1/documents/{document_id}/process", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["summary"] is None


class _FakeChromaForRelated:
    def find_related_documents(self, user_id, document_id, knowledge_base_id=None, n_results=5):
        return [
            {"document_id": _FakeChromaForRelated.related_id, "similarity": 0.87},
            {"document_id": str(uuid.uuid4()), "similarity": 0.5},  # orphaned/deleted doc
        ]


def test_get_related_documents(client, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "app.services.document_processing_service.EmbeddingService", _FakeEmbeddingService
    )
    monkeypatch.setattr(
        "app.services.document_processing_service.ChromaService", _FakeChromaForProcessing
    )
    monkeypatch.setattr(
        "app.services.document_processing_service.LLMService", _FakeIntelligenceLLM
    )

    document_id = _upload_text_document(client, auth_headers, b"Refund policy content. " * 20)
    client.post(f"/api/v1/documents/{document_id}/process", headers=auth_headers)

    related_document_id = _upload_text_document(client, auth_headers, b"Shipping policy content. " * 20)
    _FakeChromaForRelated.related_id = related_document_id

    monkeypatch.setattr("app.services.chroma_service.ChromaService", _FakeChromaForRelated)

    response = client.get(f"/api/v1/documents/{document_id}/related", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    # The orphaned document_id (no matching row) should be silently dropped.
    assert len(body) == 1
    assert body[0]["document_id"] == related_document_id
    assert body[0]["filename"] == "policy.txt"
    assert body[0]["similarity"] == 0.87


def test_get_related_documents_empty_for_unprocessed_document(client, auth_headers):
    files = {"file": ("unprocessed.txt", io.BytesIO(b"not processed yet"), "text/plain")}
    upload = client.post("/api/v1/documents/upload", headers=auth_headers, files=files)
    document_id = upload.json()["id"]

    response = client.get(f"/api/v1/documents/{document_id}/related", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_get_related_documents_requires_authentication(client):
    response = client.get(f"/api/v1/documents/{uuid.uuid4()}/related")
    assert response.status_code == 401


def test_get_related_documents_not_found(client, auth_headers):
    response = client.get(f"/api/v1/documents/{uuid.uuid4()}/related", headers=auth_headers)
    assert response.status_code == 404


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
