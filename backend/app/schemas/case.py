from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CaseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    status: str = Field(default="OPEN", pattern=r"^(OPEN|UNDER_REVIEW|CLOSED|ARCHIVED)$")
    priority: str = Field(default="MEDIUM", pattern=r"^(LOW|MEDIUM|HIGH|CRITICAL)$")

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Title is required")
        return value.strip()


class CaseCreate(CaseBase):
    case_number: str = Field(..., min_length=3, max_length=100)

    @field_validator("case_number")
    @classmethod
    def validate_case_number(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Case number is required")
        if len(normalized) < 3:
            raise ValueError("Case number must be at least 3 characters")
        return normalized


class CaseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    status: str | None = Field(default=None, pattern=r"^(OPEN|UNDER_REVIEW|CLOSED|ARCHIVED)$")
    priority: str | None = Field(default=None, pattern=r"^(LOW|MEDIUM|HIGH|CRITICAL)$")

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not value.strip():
            raise ValueError("Title cannot be empty")
        return value.strip()


class CaseResponse(CaseBase):
    id: int
    case_number: str
    created_by: int
    creator_username: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CaseListResponse(BaseModel):
    items: list[CaseResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)
