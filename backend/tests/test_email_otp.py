import re
from contextlib import contextmanager
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.routes import auth as auth_routes
from app.core.config import settings
from app.database.session import get_db
from app.main import app
from app.models.audit_log import AuditLog
from app.models.email_otp_challenge import EmailOtpChallenge
from app.models.user import User

client = TestClient(app)


@contextmanager
def db_session():
    dependency = app.dependency_overrides[get_db]()
    db = next(dependency)
    try:
        yield db
    finally:
        dependency.close()


def create_account() -> dict[str, str]:
    suffix = uuid4().hex[:10]
    payload = {
        "email": f"otp-{suffix}@example.com",
        "username": f"otp_{suffix}",
        "password": "StrongPass123!",
        "full_name": "OTP Analyst",
        "terms_accepted": True,
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return payload


def configure_mail(monkeypatch, sent_messages):
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_from_email", "no-reply@example.com")
    monkeypatch.setattr(auth_routes, "send_email", lambda **message: sent_messages.append(message))


def send_code(email: str) -> tuple[str, dict]:
    response = client.post("/api/auth/email-otp/send", json={"email": email})
    assert response.status_code == 200, response.text
    return response.json()["message"], response.json()


def extract_code(sent_messages) -> str:
    match = re.search(r"code is (\d{6})", sent_messages[-1]["body"])
    assert match is not None
    return match.group(1)


def test_email_otp_success_authenticates_existing_account_and_consumes_challenge(monkeypatch):
    account = create_account()
    sent_messages = []
    configure_mail(monkeypatch, sent_messages)
    monkeypatch.setattr(settings, "google_client_id", None)

    send_response = client.post(
        "/api/auth/email-otp/send",
        json={"email": account["email"].upper()},
    )
    code = extract_code(sent_messages)

    assert send_response.status_code == 200
    assert send_response.json()["message"] == "If this address is eligible, a one-time code has been sent."
    assert code not in send_response.text
    assert sent_messages[0]["recipient"] == account["email"]
    with db_session() as db:
        challenge = db.query(EmailOtpChallenge).filter_by(email=account["email"]).one()
        assert challenge.code_hash != code
        assert challenge.expires_at > datetime.utcnow()
        assert challenge.attempts == 0

    verified = client.post(
        "/api/auth/email-otp/verify",
        json={"email": account["email"], "code": code},
    )

    assert verified.status_code == 200
    assert verified.json()["token_type"] == "bearer"
    assert client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {verified.json()['access_token']}"},
    ).status_code == 200
    with db_session() as db:
        user = db.query(User).filter_by(email=account["email"]).one()
        challenge = db.query(EmailOtpChallenge).filter_by(email=account["email"]).one()
        audit = db.query(AuditLog).filter_by(user_id=user.id, action="AUTH_LOGIN").one()
        assert user.email_verified is True
        assert challenge.consumed_at is not None
        assert "method=Email OTP" in audit.description


def test_email_otp_send_response_does_not_reveal_account_existence(monkeypatch):
    sent_messages = []
    configure_mail(monkeypatch, sent_messages)
    existing = create_account()["email"]
    unknown = f"unknown-{uuid4().hex[:8]}@example.com"

    existing_response = client.post("/api/auth/email-otp/send", json={"email": existing})
    unknown_response = client.post("/api/auth/email-otp/send", json={"email": unknown})

    assert existing_response.status_code == unknown_response.status_code == 200
    assert existing_response.json() == unknown_response.json()
    assert len(sent_messages) == 2
    denied = client.post(
        "/api/auth/email-otp/verify",
        json={"email": unknown, "code": extract_code(sent_messages)},
    )
    assert denied.status_code == 401


def test_email_otp_rejects_invalid_code_and_locks_after_five_attempts(monkeypatch):
    account = create_account()
    sent_messages = []
    configure_mail(monkeypatch, sent_messages)
    client.post("/api/auth/email-otp/send", json={"email": account["email"]})
    code = extract_code(sent_messages)

    for _ in range(5):
        response = client.post(
            "/api/auth/email-otp/verify",
            json={"email": account["email"], "code": "000000" if code != "000000" else "000001"},
        )
        assert response.status_code == 401

    locked = client.post(
        "/api/auth/email-otp/verify",
        json={"email": account["email"], "code": code},
    )
    assert locked.status_code == 429


def test_email_otp_rejects_expired_and_reused_codes(monkeypatch):
    account = create_account()
    sent_messages = []
    configure_mail(monkeypatch, sent_messages)
    client.post("/api/auth/email-otp/send", json={"email": account["email"]})
    code = extract_code(sent_messages)
    with db_session() as db:
        challenge = db.query(EmailOtpChallenge).filter_by(email=account["email"]).one()
        challenge.expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.commit()

    expired = client.post(
        "/api/auth/email-otp/verify",
        json={"email": account["email"], "code": code},
    )
    assert expired.status_code == 401

    account2 = create_account()
    client.post("/api/auth/email-otp/send", json={"email": account2["email"]})
    reusable_code = extract_code(sent_messages)
    first = client.post(
        "/api/auth/email-otp/verify",
        json={"email": account2["email"], "code": reusable_code},
    )
    second = client.post(
        "/api/auth/email-otp/verify",
        json={"email": account2["email"], "code": reusable_code},
    )
    assert first.status_code == 200
    assert second.status_code == 401


def test_email_otp_send_enforces_resend_cooldown(monkeypatch):
    account = create_account()
    sent_messages = []
    configure_mail(monkeypatch, sent_messages)

    first = client.post("/api/auth/email-otp/send", json={"email": account["email"]})
    second = client.post("/api/auth/email-otp/send", json={"email": account["email"]})

    assert first.status_code == 200
    assert second.status_code == 429
    assert len(sent_messages) == 1


def test_email_otp_send_enforces_per_ip_rate_limit(monkeypatch):
    sent_messages = []
    configure_mail(monkeypatch, sent_messages)

    responses = [
        client.post(
            "/api/auth/email-otp/send",
            json={"email": f"bulk-{index}-{uuid4().hex[:8]}@example.com"},
        )
        for index in range(11)
    ]

    assert all(response.status_code == 200 for response in responses[:10])
    assert responses[10].status_code == 429
    assert len(sent_messages) == 10


def test_email_otp_requires_email_provider_configuration(monkeypatch):
    monkeypatch.setattr(settings, "smtp_host", None)
    monkeypatch.setattr(settings, "smtp_from_email", None)

    response = client.post(
        "/api/auth/email-otp/send",
        json={"email": "person@example.com"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Email OTP is not configured. Configure SMTP settings on the backend."
    )


def test_email_otp_invalidates_challenge_when_mail_delivery_fails(monkeypatch):
    account = create_account()
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_from_email", "no-reply@example.com")

    def fail_delivery(**_message):
        raise auth_routes.smtplib.SMTPException("provider failure")

    monkeypatch.setattr(auth_routes, "send_email", fail_delivery)
    sent = client.post("/api/auth/email-otp/send", json={"email": account["email"]})

    assert sent.status_code == 503
    with db_session() as db:
        challenge = db.query(EmailOtpChallenge).filter_by(email=account["email"]).one()
        assert challenge.consumed_at is not None


def test_email_otp_does_not_authenticate_inactive_or_terms_unaccepted_accounts(monkeypatch):
    sent_messages = []
    configure_mail(monkeypatch, sent_messages)
    inactive = create_account()
    unaccepted = create_account()
    with db_session() as db:
        db.query(User).filter_by(email=inactive["email"]).one().is_active = False
        db.query(User).filter_by(email=unaccepted["email"]).one().terms_accepted_at = None
        db.commit()

    for account in (inactive, unaccepted):
        client.post("/api/auth/email-otp/send", json={"email": account["email"]})
        response = client.post(
            "/api/auth/email-otp/verify",
            json={"email": account["email"], "code": extract_code(sent_messages)},
        )
        assert response.status_code == 401
