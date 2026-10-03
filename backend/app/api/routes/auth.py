from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.auth_service import authenticate_user, create_access_token, register_user
from app.auth.security import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.repositories.audit_repository import AuditRepository
from app.schemas.user import Token, UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db),
) -> User:
    user = register_user(db, user_in)
    return user


@router.post("/login", response_model=Token)
def login(
    user_in: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
) -> Token:
    user = authenticate_user(
        db,
        username=user_in.username,
        email=user_in.email,
        password=user_in.password,
    )
    AuditRepository(db).create_log(
        action="AUTH_LOGIN",
        user_id=user.id,
        entity_type="user",
        entity_id=user.id,
        description=f"Successful login for user {user.username}",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    token = create_access_token(user)
    return Token(access_token=token, token_type="bearer")


@router.post("/token", response_model=Token)
def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    user = authenticate_user(
        db,
        username=form_data.username,
        email=form_data.username,
        password=form_data.password,
    )
    AuditRepository(db).create_log(
        action="AUTH_LOGIN",
        user_id=user.id,
        entity_type="user",
        entity_id=user.id,
        description=f"Successful login for user {user.username}",
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    token = create_access_token(user)
    return Token(access_token=token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
def me(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user
