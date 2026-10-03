from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    MISSING = "MISSING"


class VerificationBase(BaseModel):
    evidence_id: int


class VerificationResult(VerificationBase):
    verification_status: VerificationStatus
    stored_hash: str
    current_hash: str | None = None
    verified_at: datetime | None = None
    message: str

    model_config = ConfigDict(from_attributes=True)
