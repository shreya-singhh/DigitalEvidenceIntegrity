from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EvidenceBase(BaseModel):
    file_name: str = Field(..., min_length=1)
    description: str | None = None


class EvidenceCreate(EvidenceBase):
    case_id: int
    file_type: str
    file_size: int
    storage_path: str
    sha256_hash: str


class EvidenceResponse(EvidenceBase):
    id: int
    case_id: int
    owner_id: int
    file_type: str
    file_size: int
    storage_path: str
    sha256_hash: str
    status: str
    uploaded_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
