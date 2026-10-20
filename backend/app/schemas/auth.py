from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.user import validate_strong_password

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None


class GoogleSignInRequest(BaseModel):
    credential: str = Field(..., min_length=20, max_length=8192)
    terms_accepted: bool = False


class PasswordResetRequest(BaseModel):
    email: EmailStr


class TokenConfirm(BaseModel):
    token: str = Field(..., min_length=32, max_length=256)


class PasswordResetConfirm(BaseModel):
    token: str = Field(..., min_length=32, max_length=256)
    new_password: str = Field(..., min_length=12, max_length=72)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        return validate_strong_password(value)
