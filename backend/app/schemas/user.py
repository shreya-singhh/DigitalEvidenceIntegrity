from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def validate_strong_password(value: str) -> str:
    if len(value.encode("utf-8")) > 72:
        raise ValueError("Password must be at most 72 bytes")
    if not (
        any(char.islower() for char in value)
        and any(char.isupper() for char in value)
        and any(char.isdigit() for char in value)
        and any(not char.isalnum() for char in value)
    ):
        raise ValueError("Password must include uppercase, lowercase, numeric, and special characters")
    return value


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

    @field_validator("username")
    @classmethod
    def validate_username_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Username cannot be blank")
        return value.strip()


class UserCreate(UserBase):
    password: str = Field(..., min_length=12, max_length=72)
    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    terms_accepted: bool = True

    @field_validator("full_name")
    @classmethod
    def validate_full_name_not_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("Full name cannot be blank")
        return value.strip() if value is not None else None

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        return validate_strong_password(value)

    @field_validator("terms_accepted")
    @classmethod
    def require_terms_acceptance(cls, value: bool) -> bool:
        if not value:
            raise ValueError("You must accept the terms and privacy policy")
        return value


class UserLogin(BaseModel):
    username: str | None = None
    email: str | None = None
    password: str = Field(..., min_length=8)

    model_config = ConfigDict(extra="forbid")

    def get_identity(self) -> str:
        if self.username:
            return self.username
        if self.email:
            return self.email
        raise ValueError("Either username or email is required")


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: str | None = None
    email: str | None = None


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    email_verified: bool
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
