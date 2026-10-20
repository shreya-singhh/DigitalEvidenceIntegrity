import asyncio
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import StaticPool
from starlette.requests import Request

from app.core.config import DEPLOYED_FRONTEND_ORIGIN, Settings, settings
from app.database.base import Base
from app.database.session import get_db
from app.main import app, database_unavailable_exception_handler

client = TestClient(app)


def test_deployed_frontend_is_in_cors_allowlist():
    configured = Settings(
        _env_file=None,
        DATABASE_URL="sqlite://",
        SECRET_KEY="test-secret",
        CORS_ORIGINS="https://staging.example",
    )
    assert DEPLOYED_FRONTEND_ORIGIN in configured.cors_origins


def test_removed_email_and_google_auth_endpoints_are_not_exposed():
    removed_endpoints = (
        ("get", "/api/auth/options"),
        ("post", "/api/auth/email-otp/send"),
        ("post", "/api/auth/email-otp/verify"),
        ("post", "/api/auth/google"),
        ("post", "/api/auth/password-reset/request"),
        ("post", "/api/auth/password-reset/confirm"),
        ("post", "/api/auth/email-verification/request"),
        ("post", "/api/auth/email-verification/confirm"),
    )

    for method, path in removed_endpoints:
        response = getattr(client, method)(path)
        assert response.status_code == 404, path


def test_login_rate_limit_remains_enabled():
    isolated_client = TestClient(app, client=("203.0.113.77", 4242))
    for _ in range(10):
        response = isolated_client.post(
            "/api/auth/login",
            json={"username": "missing-account", "password": "WrongPassword123!"},
        )
        assert response.status_code == 401
    limited = isolated_client.post(
        "/api/auth/login",
        json={"username": "missing-account", "password": "WrongPassword123!"},
    )
    assert limited.status_code == 429


def test_logout_revokes_existing_access_token():
    isolated_client = TestClient(app, client=("198.51.100.188", 4242))
    suffix = uuid4().hex[:10]
    registration = isolated_client.post(
        "/api/auth/register",
        json={
            "email": f"logout-{suffix}@example.com",
            "username": f"logout_{suffix}",
            "password": "StrongPass123!",
            "terms_accepted": True,
        },
    )
    assert registration.status_code == 201

    login = isolated_client.post(
        "/api/auth/login",
        json={"username": f"logout_{suffix}", "password": "StrongPass123!"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    logged_out = isolated_client.post(
        "/api/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert logged_out.status_code == 200
    assert isolated_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    ).status_code == 401


def test_database_operational_errors_return_safe_retryable_response():
    request = Request({"type": "http", "method": "GET", "path": "/api/auth/me", "headers": []})
    error = OperationalError("SELECT 1", {"password": "must-not-leak"}, Exception("db unavailable"))

    response = asyncio.run(database_unavailable_exception_handler(request, error))

    assert response.status_code == 503
    assert response.headers["retry-after"] == "5"
    assert b"must-not-leak" not in response.body


def test_unhandled_login_error_returns_safe_response_with_frontend_cors(monkeypatch):
    def fail_database():
        raise RuntimeError("database details must not reach the client")

    original_override = app.dependency_overrides[get_db]
    original_middleware_stack = app.middleware_stack
    monkeypatch.setattr(app, "debug", False)
    monkeypatch.setattr(app, "middleware_stack", None)
    monkeypatch.setattr(settings, "cors_origins", [DEPLOYED_FRONTEND_ORIGIN])
    app.dependency_overrides[get_db] = fail_database
    try:
        response = TestClient(app, raise_server_exceptions=False).post(
            "/api/auth/login",
            headers={"Origin": DEPLOYED_FRONTEND_ORIGIN},
            json={"username": "diagnostic-user", "password": "diagnostic-password"},
        )
    finally:
        app.dependency_overrides[get_db] = original_override
        app.middleware_stack = original_middleware_stack

    assert response.status_code == 500
    assert response.headers["access-control-allow-origin"] in {
        DEPLOYED_FRONTEND_ORIGIN,
        "*",
    }
    assert "server could not complete" in response.json()["detail"].lower()
    assert "database details" not in response.text
    assert "diagnostic-password" not in response.text


def test_ready_endpoint_requires_user_profile_schema(monkeypatch):
    from app.database import readiness
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    monkeypatch.setattr(readiness, "engine", engine)

    response = client.get("/api/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
