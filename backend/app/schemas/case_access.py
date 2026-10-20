from datetime import datetime

from pydantic import BaseModel, EmailStr


class CaseAccessGrantRequest(BaseModel):
    email: EmailStr


class CaseAccessResponse(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    granted_by: int
    granted_at: datetime
