import hashlib
import hmac
import re
import secrets
import smtplib
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from google.auth.exceptions import GoogleAuthError, TransportError
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.auth_service import authenticate_user, create_access_token, register_user
from app.auth.hashing import get_password_hash
from app.auth.providers import (
    send_email,
    verify_google_id_token,
)
from app.auth.rate_limit import enforce_rate_limit
from app.auth.security import get_current_user
from app.core.config import settings
from app.core.logging import logger
from app.database.session import get_db
from app.models.auth_challenge import AuthChallenge
from app.models.email_otp_challenge import EmailOtpChallenge
from app.models.user import User
from app.repositories.audit_repository import AuditRepository
from app.schemas.auth import (
    EmailOtpSendRequest,
    EmailOtpVerifyRequest,
    GoogleSignInRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    TokenConfirm,
)
from app.schemas.user import Token, UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])
GENERIC_RESET_MESSAGE = "If an account matches that address, password reset instructions will be sent."
GENERIC_EMAIL_OTP_MESSAGE = "If this address is eligible, a one-time code has been sent."
EMAIL_OTP_MAX_ATTEMPTS = 5


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _log_login(db: Session, request: Request, user: User, method: str) -> None:
    event_time = datetime.now(timezone.utc).replace(tzinfo=None)
    AuditRepository(db).create_log(
        action="AUTH_LOGIN",
        user_id=user.id,
        entity_type="user",
        entity_id=user.id,
        description=f"Successful login; method={method}; outcome=success",
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        created_at=event_time,
    )


def _log_failed_login(db: Session, request: Request, method: str, user: User | None = None) -> None:
    AuditRepository(db).create_log(
        action="AUTH_LOGIN_FAILED",
        user_id=user.id if user else None,
        entity_type="user" if user else None,
        entity_id=user.id if user else None,
        description=f"Failed login; method={method}; outcome=failure",
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )


def _new_challenge(db: Session, user: User, purpose: str) -> str:
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    now = datetime.utcnow()
    db.query(AuthChallenge).filter(AuthChallenge.expires_at < now - timedelta(days=30)).delete()
    (
        db.query(AuthChallenge)
        .filter(
            AuthChallenge.user_id == user.id,
            AuthChallenge.purpose == purpose,
            AuthChallenge.used_at.is_(None),
        )
        .update({AuthChallenge.used_at: now}, synchronize_session=False)
    )
    db.add(
        AuthChallenge(
            user_id=user.id,
            purpose=purpose,
            token_hash=token_hash,
            expires_at=now + timedelta(minutes=30),
        )
    )
    db.commit()
    return token


def _get_challenge(db: Session, token: str, purpose: str) -> AuthChallenge:
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    challenge = (
        db.query(AuthChallenge)
        .filter(AuthChallenge.token_hash == token_hash, AuthChallenge.purpose == purpose)
        .first()
    )
    if (
        challenge is None
        or challenge.used_at is not None
        or challenge.expires_at <= datetime.utcnow()
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
    return challenge


def _send_challenge_email(user: User, purpose: str, token: str) -> None:
    route = "reset-password" if purpose == "password_reset" else "verify-email"
    subject = "DEIS password reset" if purpose == "password_reset" else "Verify your DEIS email"
    action = "reset your password" if purpose == "password_reset" else "verify your email address"
    link = f"{settings.public_app_url.rstrip('/')}/{route}#token={token}"
    send_email(
        recipient=user.email,
        subject=subject,
        body=f"Use this link to {action}. It expires in 30 minutes and can only be used once:\n\n{link}",
    )


def _email_otp_hash(email: str, salt: str, code: str) -> str:
    message = f"email-otp:{email}:{salt}:{code}".encode("utf-8")
    return hmac.new(settings.secret_key.encode("utf-8"), message, hashlib.sha256).hexdigest()


@router.get("/options")
def auth_options() -> dict[str, bool | str | None]:
    return {
        "google_enabled": settings.google_sign_in_enabled,
        "google_client_id": settings.google_client_id if settings.google_sign_in_enabled else None,
        "email_delivery_enabled": settings.email_delivery_enabled,
    }


@router.post("/email-otp/send")
def send_email_otp(
    payload: EmailOtpSendRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    if not settings.email_delivery_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email OTP is not configured. Configure SMTP settings on the backend.",
        )

    email = payload.email
    enforce_rate_limit(
        db,
        action="email_otp_send_ip",
        key=_client_ip(request),
        limit=10,
        window_seconds=3600,
    )
    enforce_rate_limit(
        db,
        action="email_otp_send_cooldown",
        key=email,
        limit=1,
        window_seconds=60,
    )
    enforce_rate_limit(
        db,
        action="email_otp_send_email",
        key=email,
        limit=5,
        window_seconds=3600,
    )

    now = datetime.utcnow()
    db.query(EmailOtpChallenge).filter(
        EmailOtpChallenge.expires_at < now - timedelta(days=1),
    ).delete(synchronize_session=False)
    db.query(EmailOtpChallenge).filter(
        EmailOtpChallenge.email == email,
        EmailOtpChallenge.consumed_at.is_(None),
    ).update({EmailOtpChallenge.consumed_at: now}, synchronize_session=False)

    code = f"{secrets.randbelow(1_000_000):06d}"
    salt = secrets.token_hex(16)
    challenge = EmailOtpChallenge(
        email=email,
        code_salt=salt,
        code_hash=_email_otp_hash(email, salt, code),
        attempts=0,
        expires_at=now + timedelta(minutes=5),
        created_at=now,
    )
    db.add(challenge)
    db.commit()

    try:
        send_email(
            recipient=email,
            subject="Your DEIS sign-in code",
            body=f"Your DEIS sign-in code is {code}. It expires in 5 minutes and can only be used once.",
        )
    except (OSError, smtplib.SMTPException) as exc:
        challenge.consumed_at = datetime.utcnow()
        db.commit()
        logger.error("Email OTP could not be accepted by the configured mail provider")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email OTP could not be sent. Please try again later.",
        ) from exc

    return {"message": GENERIC_EMAIL_OTP_MESSAGE}


@router.post("/email-otp/verify", response_model=Token)
def verify_email_otp(
    payload: EmailOtpVerifyRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> Token:
    email = payload.email
    enforce_rate_limit(
        db,
        action="email_otp_verify_ip",
        key=_client_ip(request),
        limit=20,
        window_seconds=3600,
    )
    enforce_rate_limit(
        db,
        action="email_otp_verify_email",
        key=email,
        limit=10,
        window_seconds=3600,
    )

    challenge = (
        db.query(EmailOtpChallenge)
        .filter(
            EmailOtpChallenge.email == email,
            EmailOtpChallenge.consumed_at.is_(None),
        )
        .order_by(EmailOtpChallenge.created_at.desc(), EmailOtpChallenge.id.desc())
        .with_for_update()
        .first()
    )
    now = datetime.utcnow()
    if challenge is None:
        _log_failed_login(db, request, "Email OTP")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired email code")

    if challenge.attempts >= EMAIL_OTP_MAX_ATTEMPTS:
        challenge.consumed_at = now
        db.commit()
        _log_failed_login(db, request, "Email OTP")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many incorrect codes. Request a new code.",
        )

    if challenge.expires_at <= now:
        challenge.consumed_at = now
        db.commit()
        _log_failed_login(db, request, "Email OTP")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired email code")

    expected_hash = _email_otp_hash(email, challenge.code_salt, payload.code)
    if not hmac.compare_digest(challenge.code_hash, expected_hash):
        challenge.attempts += 1
        db.commit()
        _log_failed_login(db, request, "Email OTP")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired email code")

    user = db.query(User).filter(func.lower(User.email) == email).with_for_update().first()
    if not user or not user.is_active or user.terms_accepted_at is None:
        challenge.consumed_at = now
        db.commit()
        _log_failed_login(db, request, "Email OTP", user)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired email code")

    challenge.consumed_at = now
    user.email_verified = True
    db.commit()
    _log_login(db, request, user, "Email OTP")
    return Token(access_token=create_access_token(user), token_type="bearer")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_in: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    enforce_rate_limit(
        db,
        action="register",
        key=_client_ip(request),
        limit=5,
        window_seconds=3600,
    )
    return register_user(db, user_in)


@router.post("/login", response_model=Token)
def login(
    user_in: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
) -> Token:
    enforce_rate_limit(
        db,
        action="login",
        key=_client_ip(request),
        limit=10,
        window_seconds=300,
    )
    user = authenticate_user(
        db,
        username=user_in.username,
        email=user_in.email,
        password=user_in.password,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    _log_login(db, request, user, "Password")
    return Token(access_token=create_access_token(user), token_type="bearer")


@router.post("/token", response_model=Token)
def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    enforce_rate_limit(
        db,
        action="login",
        key=_client_ip(request),
        limit=10,
        window_seconds=300,
    )
    user = authenticate_user(
        db,
        username=form_data.username,
        email=form_data.username,
        password=form_data.password,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    _log_login(db, request, user, "Password")
    return Token(access_token=create_access_token(user), token_type="bearer")


@router.post("/google", response_model=Token)
def google_sign_in(
    payload: GoogleSignInRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> Token:
    if not settings.google_sign_in_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google sign-in is not configured. Set GOOGLE_CLIENT_ID on the backend.",
        )
    enforce_rate_limit(
        db,
        action="google_login",
        key=_client_ip(request),
        limit=10,
        window_seconds=300,
    )
    try:
        claims = verify_google_id_token(payload.credential)
    except (GoogleAuthError, TransportError, ValueError):
        _log_failed_login(db, request, "Google")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google credentials")

    user = db.query(User).filter(User.google_subject == claims["subject"]).first()
    if not user:
        user = db.query(User).filter(func.lower(User.email) == claims["email"]).first()
    if user:
        if not user.is_active:
            _log_failed_login(db, request, "Google", user)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google credentials")
        if user.google_subject and user.google_subject != claims["subject"]:
            _log_failed_login(db, request, "Google", user)
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Google account cannot be linked")
        user.google_subject = claims["subject"]
        user.email_verified = True
    else:
        if not payload.terms_accepted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Accept the terms and privacy notice before creating an account with Google.",
            )
        local_part = claims["email"].split("@", 1)[0]
        username_base = re.sub(r"[^a-z0-9_]", "", local_part.lower())[:40] or "user"
        username = username_base
        while db.query(User.id).filter(func.lower(User.username) == username.lower()).first():
            username = f"{username_base[:40]}_{secrets.token_hex(3)}"
        user = User(
            username=username,
            email=claims["email"],
            full_name=claims["name"][:120],
            terms_accepted_at=datetime.utcnow(),
            hashed_password=get_password_hash(secrets.token_urlsafe(48)),
            google_subject=claims["subject"],
            email_verified=True,
            is_active=True,
        )
        db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        logger.warning("Google sign-in could not link account because of a uniqueness conflict")
        _log_failed_login(db, request, "Google")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Google account cannot be linked") from exc

    _log_login(db, request, user, "Google")
    return Token(access_token=create_access_token(user), token_type="bearer")


@router.post("/password-reset/request")
def request_password_reset(
    payload: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    if not settings.email_delivery_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password recovery is not configured. Configure SMTP settings on the backend.",
        )
    enforce_rate_limit(
        db,
        action="password_reset_request",
        key=_client_ip(request),
        limit=5,
        window_seconds=3600,
    )
    email = str(payload.email).strip().lower()
    enforce_rate_limit(
        db,
        action="password_reset_email_cooldown",
        key=email,
        limit=1,
        window_seconds=60,
    )
    user = db.query(User).filter(func.lower(User.email) == email).first()
    if user and user.is_active:
        token = _new_challenge(db, user, "password_reset")
        try:
            _send_challenge_email(user, "password_reset", token)
        except (OSError, smtplib.SMTPException) as exc:
            challenge_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
            db.query(AuthChallenge).filter(AuthChallenge.token_hash == challenge_hash).update(
                {AuthChallenge.used_at: datetime.utcnow()}
            )
            db.commit()
            logger.error("Password recovery email could not be accepted by the configured mail provider")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Password recovery email could not be sent. Please try again later.",
            ) from exc
    return {"message": GENERIC_RESET_MESSAGE}


@router.post("/password-reset/confirm")
def confirm_password_reset(
    payload: PasswordResetConfirm,
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    enforce_rate_limit(
        db,
        action="password_reset_confirm",
        key=_client_ip(request),
        limit=10,
        window_seconds=600,
    )
    challenge = _get_challenge(db, payload.token, "password_reset")
    user = db.query(User).filter(User.id == challenge.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
    now = datetime.utcnow()
    user.hashed_password = get_password_hash(payload.new_password)
    user.token_version += 1
    challenge.used_at = now
    (
        db.query(AuthChallenge)
        .filter(
            AuthChallenge.user_id == user.id,
            AuthChallenge.purpose == "password_reset",
            AuthChallenge.used_at.is_(None),
        )
        .update({AuthChallenge.used_at: now}, synchronize_session=False)
    )
    db.commit()
    AuditRepository(db).create_log(
        action="AUTH_PASSWORD_RESET",
        user_id=user.id,
        entity_type="user",
        entity_id=user.id,
        description="Password reset completed; outcome=success",
        ip_address=_client_ip(request),
    )
    return {"message": "Password updated. Sign in again with your new password."}


@router.post("/email-verification/request")
def request_email_verification(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    if not settings.email_delivery_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email verification is not configured. Configure SMTP settings on the backend.",
        )
    if current_user.email_verified:
        return {"message": "Email address is already verified."}
    enforce_rate_limit(
        db,
        action="email_verification_request_ip",
        key=_client_ip(request),
        limit=5,
        window_seconds=3600,
    )
    enforce_rate_limit(
        db,
        action="email_verification_cooldown",
        key=current_user.email,
        limit=1,
        window_seconds=60,
    )
    token = _new_challenge(db, current_user, "email_verification")
    try:
        _send_challenge_email(current_user, "email_verification", token)
    except (OSError, smtplib.SMTPException) as exc:
        challenge_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        db.query(AuthChallenge).filter(AuthChallenge.token_hash == challenge_hash).update(
            {AuthChallenge.used_at: datetime.utcnow()}
        )
        db.commit()
        logger.error("Email verification could not be accepted by the configured mail provider")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Verification email could not be sent. Please try again later.",
        ) from exc
    return {"message": "Verification instructions were sent to your registered email address."}


@router.post("/email-verification/confirm")
def confirm_email_verification(
    payload: TokenConfirm,
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    enforce_rate_limit(
        db,
        action="email_verification_confirm",
        key=_client_ip(request),
        limit=10,
        window_seconds=600,
    )
    challenge = _get_challenge(db, payload.token, "email_verification")
    user = db.query(User).filter(User.id == challenge.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")
    user.email_verified = True
    challenge.used_at = datetime.utcnow()
    db.commit()
    return {"message": "Email address verified"}


@router.post("/logout")
def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    current_user.token_version += 1
    db.commit()
    AuditRepository(db).create_log(
        action="AUTH_LOGOUT",
        user_id=current_user.id,
        entity_type="user",
        entity_id=current_user.id,
        description="Logout completed; outcome=success",
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return {"message": "Session revoked"}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
