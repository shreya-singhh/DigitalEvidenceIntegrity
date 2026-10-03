from datetime import datetime

from pydantic import BaseModel


class ChainOfCustodyEventResponse(BaseModel):
    id: int
    evidence_id: int
    user_id: int
    username: str
    action: str
    description: str | None
    timestamp: datetime


class EvidenceCustodyResponse(BaseModel):
    evidence_id: int
    file_name: str
    case_id: int
    case_number: str
    reference_hash: str
    events: list[ChainOfCustodyEventResponse]
