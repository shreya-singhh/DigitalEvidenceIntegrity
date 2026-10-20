from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.auth_service import authenticate_user, create_access_token, register_user
from app.auth.rate_limit import enforce_rate_limit
from app.auth.security import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.repositories.audit_repository import AuditRepository
from app.schemas.user import Token, UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _log_login(db: Session, request: Request, user: User) -> None:
    event_time = datetime.now(timezone.utc).replace(tzinfo=None)
    AuditRepository(db).create_log(
        action="AUTH_LOGIN",
        user_id=user.id,
        entity_type="user",
        entity_id=user.id,
        description="Successful login; method=Password; outcome=success",
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        created_at=event_time,
    )


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
    _log_login(db, request, user)
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
    _log_login(db, request, user)
    return Token(access_token=create_access_token(user), token_type="bearer")


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
