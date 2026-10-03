from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AuditLogBase(BaseModel):
    action: str = Field(..., max_length=100)
    entity_type: str | None = Field(default=None, max_length=100)
    entity_id: int | None = None
    description: str | None = Field(default=None, max_length=5000)
    ip_address: str | None = Field(default=None, max_length=45)
    user_agent: str | None = Field(default=None, max_length=512)


class AuditLogResponse(AuditLogBase):
    id: int
    user_id: int | None = None
    case_id: int | None = None
    evidence_id: int | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
