import re
from contextlib import contextmanager
from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.auth import providers
from app.api.routes import auth as auth_routes
from app.core.config import settings
from app.database.session import get_db
from app.main import app
from app.models.auth_challenge import AuthChallenge
from app.models.user import User

client = TestClient(app)
STRONG_PASSWORD = "StrongPass123!"


@contextmanager
def db_session():
    dependency = app.dependency_overrides[get_db]()
    db = next(dependency)
    try:
        yield db
    finally:
        dependency.close()


def create_account(**values):
    suffix = uuid4().hex[:10]
    payload = {
        "email": f"auth-{suffix}@example.com",
        "username": f"auth_{suffix}",
        "password": STRONG_PASSWORD,
        "full_name": "Evidence Analyst",
        "terms_accepted": True,
    }
    payload.update(values)
    registration_client = TestClient(app, client=(f"192.0.2.{int(suffix[:2], 16) or 1}", 4312))
    response = registration_client.post("/api/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return payload


def test_password_reset_is_generic_single_use_and_revokes_existing_tokens(monkeypatch):
    payload = create_account()
    login = client.post(
        "/api/auth/login",
        json={"username": payload["username"], "password": STRONG_PASSWORD},
    )
    old_token = login.json()["access_token"]

    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_from_email", "no-reply@example.com")
    sent_messages = []
    monkeypatch.setattr(auth_routes, "send_email", lambda **message: sent_messages.append(message))

    response = client.post("/api/auth/password-reset/request", json={"email": payload["email"]})
    assert response.status_code == 200
    assert payload["email"] not in response.text
    assert len(sent_messages) == 1
    token = re.search(r"token=([A-Za-z0-9_-]+)", sent_messages[0]["body"]).group(1)
    assert token not in response.text

    reset = client.post(
        "/api/auth/password-reset/confirm",
        json={"token": token, "new_password": "NewStrongPass456!"},
    )
    assert reset.status_code == 200
    assert client.post(
        "/api/auth/password-reset/confirm",
        json={"token": token, "new_password": "AnotherStrong789!"},
    ).status_code == 400
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {old_token}"}).status_code == 401
    assert client.post(
        "/api/auth/login",
        json={"username": payload["username"], "password": "NewStrongPass456!"},
    ).status_code == 200


def test_expired_password_reset_challenge_is_rejected(monkeypatch):
    payload = create_account()
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_from_email", "no-reply@example.com")
    sent_messages = []
    monkeypatch.setattr(auth_routes, "send_email", lambda **message: sent_messages.append(message))

    assert client.post("/api/auth/password-reset/request", json={"email": payload["email"]}).status_code == 200
    token = re.search(r"token=([A-Za-z0-9_-]+)", sent_messages[0]["body"]).group(1)
    with db_session() as db:
        challenge = db.query(AuthChallenge).filter(AuthChallenge.user_id == db.query(User.id).filter_by(email=payload["email"]).scalar()).one()
        challenge.expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.commit()

    response = client.post(
        "/api/auth/password-reset/confirm",
        json={"token": token, "new_password": "NewStrongPass456!"},
    )
    assert response.status_code == 400


def test_google_token_requires_verified_email_and_uses_configured_audience(monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", "client-id.apps.googleusercontent.com")
    calls = []
    claims = {
        "iss": "https://accounts.google.com",
        "sub": "google-subject",
        "email": "verified@example.com",
        "email_verified": True,
        "name": "Verified Analyst",
    }
    monkeypatch.setattr(
        providers.id_token,
        "verify_oauth2_token",
        lambda token, request, audience: calls.append((token, audience)) or claims,
    )

    assert providers.verify_google_id_token("id-token")["subject"] == "google-subject"
    assert calls == [("id-token", "client-id.apps.googleusercontent.com")]

    claims["email_verified"] = False
    with pytest.raises(ValueError, match="not verified"):
        providers.verify_google_id_token("id-token")


def test_google_client_id_whitespace_is_treated_as_disabled(monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", "   ")
    assert settings.google_sign_in_enabled is False


def test_google_login_links_verified_email_and_requires_terms_for_new_accounts(monkeypatch):
    existing = create_account()
    monkeypatch.setattr(settings, "google_client_id", "client-id.apps.googleusercontent.com")
    google_claims = {
        "existing-credential-token-12345": {
            "subject": "google-existing-subject",
            "email": existing["email"],
            "name": "Existing Analyst",
        },
        "new-credential-token-123456789": {
            "subject": "google-new-subject",
            "email": f"google-{uuid4().hex[:8]}@example.com",
            "name": "Google Analyst",
        },
    }
    monkeypatch.setattr(auth_routes, "verify_google_id_token", lambda credential: google_claims[credential])

    linked = client.post(
        "/api/auth/google",
        json={"credential": "existing-credential-token-12345", "terms_accepted": False},
    )
    assert linked.status_code == 200
    with db_session() as db:
        linked_user = db.query(User).filter_by(email=existing["email"]).one()
        assert linked_user.email_verified is True
        assert linked_user.google_subject == "google-existing-subject"

    denied = client.post(
        "/api/auth/google",
        json={"credential": "new-credential-token-123456789", "terms_accepted": False},
    )
    assert denied.status_code == 400
    created = client.post(
        "/api/auth/google",
        json={"credential": "new-credential-token-123456789", "terms_accepted": True},
    )
    assert created.status_code == 200
    with db_session() as db:
        created_user = db.query(User).filter_by(email=google_claims["new-credential-token-123456789"]["email"]).one()
        assert created_user.email_verified is True
        assert created_user.terms_accepted_at is not None


def test_google_login_rejects_invalid_id_token(monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", "client-id.apps.googleusercontent.com")

    def reject_token(credential):
        raise ValueError("Google token signature is invalid")

    monkeypatch.setattr(auth_routes, "verify_google_id_token", reject_token)
    response = client.post(
        "/api/auth/google",
        json={"credential": "invalid-google-id-token-123456789", "terms_accepted": True},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Google credentials"


def test_google_login_reports_missing_server_configuration(monkeypatch):
    monkeypatch.setattr(settings, "google_client_id", None)

    response = client.post(
        "/api/auth/google",
        json={"credential": "google-id-token-1234567890", "terms_accepted": True},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Google sign-in is not configured. Set GOOGLE_CLIENT_ID on the backend."
    )


def test_auth_options_preserve_google_and_omit_phone_settings(monkeypatch):
    client_id = "client-id.apps.googleusercontent.com"
    monkeypatch.setattr(settings, "google_client_id", client_id)

    response = client.get("/api/auth/options")

    assert response.status_code == 200
    assert response.json()["google_enabled"] is True
    assert response.json()["google_client_id"] == client_id
    assert not {"phone_enabled", "phone_password_reset_enabled", "sms_alerts_enabled"} & response.json().keys()


def test_phone_auth_and_sms_alert_routes_are_removed():
    removed_routes = (
        ("post", "/api/auth/phone/request"),
        ("post", "/api/auth/phone/verify"),
        ("post", "/api/auth/phone/verify/request"),
        ("put", "/api/auth/me/phone"),
        ("post", "/api/auth/phone/verify/confirm"),
        ("post", "/api/auth/password-reset/phone/request"),
        ("post", "/api/auth/password-reset/phone/confirm"),
        ("put", "/api/auth/me/security-alerts"),
    )

    for method, path in removed_routes:
        response = getattr(client, method)(path)
        assert response.status_code == 404, path


def test_login_rate_limit_returns_429_for_repeated_attempts():
    isolated_client = TestClient(app, client=("203.0.113.77", 4242))
    for _ in range(10):
        response = isolated_client.post(
            "/api/auth/login",
            json={"username": "missing-account", "password": STRONG_PASSWORD},
        )
        assert response.status_code == 401
    limited = isolated_client.post(
        "/api/auth/login",
        json={"username": "missing-account", "password": STRONG_PASSWORD},
    )
    assert limited.status_code == 429


def test_logout_revokes_access_token():
    payload = create_account()
    isolated_client = TestClient(app, client=("198.51.100.188", 4242))
    login = isolated_client.post(
        "/api/auth/login",
        json={"username": payload["username"], "password": STRONG_PASSWORD},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    logged_out = isolated_client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logged_out.status_code == 200
    assert isolated_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401
