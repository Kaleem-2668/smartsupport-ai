def test_register_creates_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "jane@example.com", "password": "supersecret123", "full_name": "Jane Doe"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "jane@example.com"
    assert "hashed_password" not in body
    assert "password" not in body


def test_register_duplicate_email_returns_409(client):
    payload = {"email": "dup@example.com", "password": "supersecret123"}
    client.post("/api/v1/auth/register", json=payload)

    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 409


def test_register_rejects_short_password(client):
    response = client.post(
        "/api/v1/auth/register", json={"email": "short@example.com", "password": "short"}
    )

    assert response.status_code == 422


def test_login_returns_access_and_refresh_tokens(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "login@example.com", "password": "supersecret123"},
    )

    response = client.post(
        "/api/v1/auth/login", json={"email": "login@example.com", "password": "supersecret123"}
    )

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password_returns_401(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "wrong@example.com", "password": "supersecret123"},
    )

    response = client.post(
        "/api/v1/auth/login", json={"email": "wrong@example.com", "password": "notright123"}
    )

    assert response.status_code == 401


def test_me_requires_authentication(client):
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_me_returns_current_user_with_valid_token(client):
    client.post(
        "/api/v1/auth/register", json={"email": "me@example.com", "password": "supersecret123"}
    )
    login_response = client.post(
        "/api/v1/auth/login", json={"email": "me@example.com", "password": "supersecret123"}
    )
    access_token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


def test_me_rejects_garbage_token(client):
    response = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )

    assert response.status_code == 401


def test_refresh_returns_new_access_token(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "refresh@example.com", "password": "supersecret123"},
    )
    login_response = client.post(
        "/api/v1/auth/login", json={"email": "refresh@example.com", "password": "supersecret123"}
    )
    refresh_token = login_response.json()["refresh_token"]

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 200
    assert "access_token" in response.json()


def test_refresh_rejects_access_token_used_as_refresh_token(client):
    client.post(
        "/api/v1/auth/register", json={"email": "swap@example.com", "password": "supersecret123"}
    )
    login_response = client.post(
        "/api/v1/auth/login", json={"email": "swap@example.com", "password": "supersecret123"}
    )
    access_token = login_response.json()["access_token"]

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})

    assert response.status_code == 401
