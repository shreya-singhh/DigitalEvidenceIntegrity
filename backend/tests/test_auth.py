from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_successful_registration():
    payload = {"email": "alice@example.com", "username": "alice", "password": "StrongPass123!"}
    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["username"] == payload["username"]
    assert "password" not in data
    assert "password_hash" not in data


def test_duplicate_email():
    payload = {"email": "alice@example.com", "username": "newalice", "password": "StrongPass123!"}
    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 400


def test_duplicate_username():
    payload = {"email": "bob@example.com", "username": "alice", "password": "StrongPass123!"}
    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 400


def test_successful_login():
    payload = {"username": "alice", "password": "StrongPass123!"}
    response = client.post("/api/auth/login", json=payload)

    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_invalid_password():
    response = client.post(
        "/api/auth/login",
        json={"username": "alice", "password": "WrongPassword!"},
    )

    assert response.status_code == 401


def test_oauth2_token_with_email_username_works():
    response = client.post(
        "/api/auth/token",
        data={"username": "alice@example.com", "password": "StrongPass123!"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_oauth2_token_with_invalid_password_returns_401():
    response = client.post(
        "/api/auth/token",
        data={"username": "alice@example.com", "password": "WrongPassword!"},
    )

    assert response.status_code == 401


def test_me_requires_token():
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_me_with_valid_token():
    login_response = client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "StrongPass123!"},
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "alice@example.com"
    assert data["username"] == "alice"


def test_invalid_token():
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid.token.value"},
    )

    assert response.status_code == 401
