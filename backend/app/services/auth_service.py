from sqlalchemy.orm import Session

from app.auth.auth_service import authenticate_user, create_access_token, get_current_user, register_user
from app.models.user import User
from app.schemas.user import UserCreate


def create_user(db: Session, user_in: UserCreate) -> User:
    return register_user(db, user_in)


def login_user(db: Session, username: str | None = None, email: str | None = None, password: str | None = None) -> User:
    return authenticate_user(db, username=username, email=email, password=password)


def issue_token(user: User) -> str:
    return create_access_token(user)


def fetch_current_user(db: Session, token: str) -> User:
    return get_current_user(db, token)
