import smtplib
from email.message import EmailMessage

from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token

from app.core.config import settings


def send_email(*, recipient: str, subject: str, body: str) -> None:
    if not settings.email_delivery_enabled:
        raise RuntimeError("Email delivery is not configured")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from_email
    message["To"] = recipient
    message.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_username and settings.smtp_password:
            server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(message)


def verify_google_id_token(token: str) -> dict[str, str]:
    if not settings.google_client_id:
        raise RuntimeError("Google sign-in is not configured")
    claims = id_token.verify_oauth2_token(token, GoogleRequest(), settings.google_client_id)
    if claims.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        raise ValueError("Google token issuer is invalid")
    if claims.get("email_verified") is not True or not claims.get("email") or not claims.get("sub"):
        raise ValueError("Google account email is not verified")
    return {
        "subject": str(claims["sub"]),
        "email": str(claims["email"]).strip().lower(),
        "name": str(claims.get("name") or ""),
    }
