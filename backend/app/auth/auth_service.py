from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.auth.hashing import get_password_hash, verify_password
from app.auth.jwt import create_access_token as create_jwt_token
from app.auth.jwt import decode_access_token
from app.core.config import settings
from app.models.user import User
from app.repositories.audit_repository import AuditRepository
from app.schemas.user import UserCreate


def register_user(db: Session, user_in: UserCreate) -> User:
    email = user_in.email.strip().lower()
    username = user_in.username.strip()

    if not email or not username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email and username are required")

    existing_email = db.query(User).filter(func.lower(User.email) == email).first()
    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    existing_username = db.query(User).filter(func.lower(User.username) == username.lower()).first()
    if existing_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")

    user = User(
        email=email,
        username=username,
        password_hash=get_password_hash(user_in.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(
    db: Session,
    username: str | None = None,
    email: str | None = None,
    password: str | None = None,
) -> User:
    if not password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    identifier = (username or email or "").strip()
    if not identifier:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user = db.query(User).filter(
        or_(
            func.lower(User.username) == identifier.lower(),
            func.lower(User.email) == identifier.lower(),
        )
    ).first()

    if not user or not verify_password(password, user.hashed_password):
        AuditRepository(db).create_log(
            action="AUTH_LOGIN_FAILED",
            user_id=user.id if user else None,
            description="Failed login attempt",
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.is_active:
        AuditRepository(db).create_log(
            action="AUTH_LOGIN_FAILED",
            user_id=user.id,
            description="Login blocked because the user is inactive",
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")

    AuditRepository(db).create_log(
        action="AUTH_LOGIN",
        user_id=user.id,
        description=f"Successful login for user {user.username}",
    )
    return user


def create_access_token(user: User) -> str:
    expires_delta = timedelta(minutes=settings.access_token_expire_minutes)
    return create_jwt_token({"sub": user.username, "email": user.email}, expires_delta=expires_delta)


def get_current_user(db: Session, token: str) -> User:
    try:
        payload = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials") from exc

    username = payload.get("sub")
    email = payload.get("email")
    if not username and not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")

    user = db.query(User).filter(
        or_(
            func.lower(User.username) == (username.lower() if username else None),
            func.lower(User.email) == (email.lower() if email else None),
        )
    ).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")

    return user
